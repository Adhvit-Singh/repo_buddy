# Deploying repo_buddy (free tiers)

| Part | Host | Notes |
|---|---|---|
| Backend (FastAPI, Docker) | Render — free web service | Built from `backend/Dockerfile` via the `render.yaml` blueprint |
| Frontend (Next.js) | Netlify — free tier | Built from `frontend/` via `netlify.toml` |

(Hugging Face Spaces was the first choice, but Docker Spaces now need a paid plan.)

## 1. Backend → Render

1. Sign up at <https://render.com> with your GitHub account.
2. **New → Blueprint** → connect this repository → branch `main`. Render reads `render.yaml`
   and proposes a free web service named `repo-buddy-api`.
3. Fill in the prompted environment variables:
   - `GEMINI_API_KEY` — your key from <https://aistudio.google.com/apikey>
   - `BACKEND_URL` — `https://repo-buddy-api.onrender.com` (or whatever URL Render shows)
   - `FRONTEND_URL` — your Netlify URL from step 2 (you can fill this in afterwards)
   - `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` — leave empty unless you set up sign-in (step 3)
4. **Apply**. The first build takes a few minutes. Check that `<BACKEND_URL>/health` returns `{"status":"healthy",...}`.

Every push to `main` redeploys automatically.

Free-plan notes:
- The service sleeps after ~15 minutes without traffic. The next request takes about a minute to wake it.
- The disk isn't persistent, so the SQLite database resets on every deploy or restart. That's fine for a demo.

## 2. Frontend → Netlify

1. Netlify → **Add new project → Import an existing project → GitHub** → pick this repo.
   `netlify.toml` already sets the base directory (`frontend`) and the build command.
2. **Project configuration → Environment variables**: `NEXT_PUBLIC_API_URL` = the Render URL.
3. Deploy. Then set `FRONTEND_URL` on Render to the Netlify URL, which allows CORS.

## 3. Optional: GitHub sign-in

Needed only for the dashboard and auto-fix PRs.

1. <https://github.com/settings/developers> → **New OAuth App**
   - Homepage URL: the Netlify URL
   - Callback URL: `<BACKEND_URL>/auth/github/callback`
2. Put `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` into the Render service's environment.

## Free-tier limits to know

- Gemini's free tier has per-minute and per-day request limits, and Google sometimes returns
  "high demand" errors. The backend retries and falls back across models, and every endpoint
  is rate-limited per IP, but a busy day can still make scans slow or make them fail with a clear message.
- Don't enable billing on the Gemini key if you want it to stay free.
