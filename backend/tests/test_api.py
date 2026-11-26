"""HTTP-level tests for the main endpoints (no network, no LLM, no workers)."""
import pytest


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


@pytest.mark.parametrize(
    "url",
    ["file:///etc/passwd", "https://gitlab.com/a/b", "/etc", "https://github.com/onlyowner"],
)
def test_analyze_rejects_non_github_urls(client, url):
    res = client.post("/api/repos/analyze-url", json={"github_url": url})
    assert res.status_code == 422


def test_analyze_queues_scan_and_dedupes(client, monkeypatch):
    queued = []
    from app.api import repos

    monkeypatch.setattr(repos, "is_url_scanning", lambda url: None)
    monkeypatch.setattr(repos, "enqueue_scan", lambda scan_id, url, fn: queued.append((scan_id, url)))

    res = client.post("/api/repos/analyze-url", json={"github_url": "github.com/octocat/Hello-World.git"})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "processing"
    # URL was normalised before being queued
    assert queued == [(body["scan_id"], "https://github.com/octocat/Hello-World")]

    poll = client.get(f"/api/repos/jobs/{body['scan_id']}")
    assert poll.status_code == 200
    assert poll.json()["status"] in ("queued", "processing")


def test_unknown_scan_is_404(client):
    assert client.get("/api/repos/jobs/does-not-exist").status_code == 404


def test_failed_scan_surfaces_error_message(client):
    from app.database import create_scan, track_repo, update_scan_status

    repo = track_repo(None, "https://github.com/a/err", "err", "a/err")
    scan = create_scan(repo["id"])
    update_scan_status(scan["id"], "error", error="The AI service is busy")

    body = client.get(f"/api/repos/jobs/{scan['id']}").json()
    assert body == {"status": "error", "error": "The AI service is busy"}


@pytest.mark.parametrize("url", ["http://localhost", "http://127.0.0.1:8000", "http://169.254.169.254/latest"])
def test_probe_refuses_internal_targets(client, url):
    res = client.post("/api/probe/start", json={"url": url})
    assert res.status_code == 422


def test_autofix_requires_sign_in(client):
    res = client.post(
        "/api/repos/autofix",
        json={"repo_name": "octocat/Hello-World", "vulnerabilities": [{"title": "x", "file": "a.py"}]},
    )
    assert res.status_code == 401


def test_payment_routes_are_gone(client):
    assert client.get("/api/payments/plan").status_code == 404
    assert client.post("/api/stripe/webhook").status_code == 404


def test_oauth_callback_rejects_missing_state(client, monkeypatch):
    from app.auth import github

    monkeypatch.setattr(github, "GITHUB_CLIENT_SECRET", "secret")
    res = client.get("/auth/github/callback?code=abc&state=forged", follow_redirects=False)
    assert res.status_code in (302, 307)
    assert "error=invalid_state" in res.headers["location"]
    assert "access_token" not in res.headers["location"]


def test_handoff_code_is_single_use(client):
    from app.auth.github import create_handoff

    code = create_handoff("gho_example")
    first = client.post("/auth/github/exchange", json={"handoff": code})
    assert first.status_code == 200
    assert first.json() == {"access_token": "gho_example"}

    second = client.post("/auth/github/exchange", json={"handoff": code})
    assert second.status_code == 400


def test_handoff_code_expires(monkeypatch):
    from app.auth import github

    code = github.create_handoff("gho_example")
    real_time = github.time.time
    monkeypatch.setattr(github.time, "time", lambda: real_time() + github.HANDOFF_TTL_SECONDS + 1)
    assert github.redeem_handoff(code) is None
