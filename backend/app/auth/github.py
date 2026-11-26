"""
repo_buddy — GitHub OAuth Authentication

Flow:
  1. /login sets a random `state` in a short-lived httpOnly cookie and
     redirects to GitHub (state protects against login CSRF).
  2. /callback checks `state`, exchanges GitHub's code for an access token,
     sets the httpOnly `gh_token` cookie, and redirects to the frontend with a
     one-time `handoff` code — never the token itself, so it can't leak via
     browser history, server logs or Referer headers.
  3. The frontend POSTs the handoff code to /exchange (valid once, 60 s) and
     gets the token back in the response body.

/me accepts the gh_token cookie or an `Authorization: Bearer` header.
"""
import os
import secrets
import threading
import time
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
import httpx

from app.config import (
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    FRONTEND_URL,
    BACKEND_URL,
)

router = APIRouter()

COOKIE_NAME = "gh_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days
STATE_COOKIE = "oauth_state"
HANDOFF_TTL_SECONDS = 60

# One-time handoff codes: code -> (access_token, expires_at). In-memory is
# fine for a single backend instance; codes live for 60 seconds.
_handoffs: dict[str, tuple[str, float]] = {}
_handoff_lock = threading.Lock()


def create_handoff(token: str) -> str:
    code = secrets.token_urlsafe(32)
    now = time.time()
    with _handoff_lock:
        for k in [k for k, (_, exp) in _handoffs.items() if exp < now]:
            del _handoffs[k]
        _handoffs[code] = (token, now + HANDOFF_TTL_SECONDS)
    return code


def redeem_handoff(code: str) -> Optional[str]:
    with _handoff_lock:
        entry = _handoffs.pop(code, None)
    if not entry or entry[1] < time.time():
        return None
    return entry[0]


def _is_secure() -> bool:
    """Cookie should be Secure when we're behind HTTPS."""
    return BACKEND_URL.startswith("https://") or os.getenv("FORCE_SECURE_COOKIES", "") == "1"


def _cookie_domain() -> Optional[str]:
    try:
        host = urlparse(BACKEND_URL).hostname or ""
    except Exception:
        host = ""
    if not host or host in ("localhost", "127.0.0.1"):
        return None
    return host


def _set_token_cookie(response: Response, token: str):
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        secure=_is_secure(),
        samesite="lax",
        domain=_cookie_domain(),
        path="/",
    )


def _read_token(request: Request) -> Optional[str]:
    """Prefer cookie; fall back to Authorization: Bearer."""
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(None, 1)[1].strip()
    return None


@router.get("/login")
def github_login():
    """Redirect user to GitHub OAuth consent screen."""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID in .env",
        )

    state = secrets.token_urlsafe(24)
    callback_url = f"{BACKEND_URL}/auth/github/callback"
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={callback_url}"
        f"&scope=repo read:user user:email"
        f"&state={state}"
    )
    response = RedirectResponse(url)
    response.set_cookie(
        STATE_COOKIE, state, max_age=600, httponly=True,
        secure=_is_secure(), samesite="lax", path="/auth/github",
    )
    return response


@router.get("/callback")
async def github_callback(request: Request, code: str, state: str = ""):
    """Verify state, exchange GitHub's code for a token, hand off via one-time code."""
    if not GITHUB_CLIENT_SECRET:
        return RedirectResponse(f"{FRONTEND_URL}/auth/callback?error=server_not_configured")

    expected = request.cookies.get(STATE_COOKIE)
    if not expected or not secrets.compare_digest(expected, state):
        return RedirectResponse(f"{FRONTEND_URL}/auth/callback?error=invalid_state")

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
        )

    access_token = token_res.json().get("access_token")
    if not access_token:
        return RedirectResponse(f"{FRONTEND_URL}/auth/callback?error=token_exchange_failed")

    redirect = RedirectResponse(f"{FRONTEND_URL}/auth/callback?handoff={create_handoff(access_token)}")
    _set_token_cookie(redirect, access_token)
    redirect.delete_cookie(STATE_COOKIE, path="/auth/github")
    return redirect


class HandoffRequest(BaseModel):
    handoff: str


@router.post("/exchange")
async def exchange_handoff(payload: HandoffRequest):
    """Trade a one-time handoff code for the access token (single use, 60 s)."""
    token = redeem_handoff(payload.handoff)
    if not token:
        raise HTTPException(status_code=400, detail="Login link expired. Please sign in again.")
    return {"access_token": token}


@router.get("/me")
async def github_me(request: Request):
    """
    Return the currently signed-in GitHub user given the cookie or
    Authorization header. Used by the frontend instead of trusting a
    localStorage token blindly. Also upserts the user row so repo
    tracking works.
    """
    token = _read_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    async with httpx.AsyncClient(timeout=10.0) as client:
        user_res = await client.get(
            "https://api.github.com/user",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
            },
        )

    if user_res.status_code != 200:
        # Treat as unauthenticated — don't leak GitHub status codes.
        raise HTTPException(status_code=401, detail="Token rejected by GitHub")

    gh = user_res.json()

    # Upsert into our DB so repo tracking works.
    from app.database import upsert_user

    user_row = upsert_user(
        github_id=gh["id"],
        login=gh.get("login"),
        name=gh.get("name"),
        avatar_url=gh.get("avatar_url"),
        email=gh.get("email"),
    )

    return {
        "id": user_row.get("id"),
        "github_id": gh.get("id"),
        "login": gh.get("login"),
        "name": gh.get("name"),
        "email": gh.get("email"),
        "avatar_url": gh.get("avatar_url"),
    }


@router.post("/logout")
async def github_logout():
    """Clear the auth cookie. Frontend should also clear its localStorage cache."""
    resp = JSONResponse({"status": "ok"})
    resp.delete_cookie(
        key=COOKIE_NAME,
        domain=_cookie_domain(),
        path="/",
    )
    return resp
