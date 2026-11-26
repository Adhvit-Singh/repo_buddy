# Deploying repo_buddy (free tiers)

| Part | Host | Why |
|---|---|---|
| Backend (FastAPI, Docker) | Hugging Face Spaces — free CPU Space | Runs a long-lived Python container with no credit card |
| Frontend (Next.js) | Netlify — free tier | Native Next.js support, builds from this repo |

## 1. Backend → Hugging Face Space

1. Create a free account at <https://huggingface.co>.
2. **New Space** → name it `repo-buddy` → SDK **Docker** → template **Blank** → visibility **Public**.
3. In the Space: **Settings → Variables and secrets**, add:
   - Secret `GEMINI_API_KEY` — your key from <https://aistudio.google.com/apikey>
   - Variable `FRONTEND_URL` — your Netlify URL (step 2), e.g. `https://repo-buddy.netlify.app`
   - Variable `BACKEND_URL` — the Space URL, e.g. `https://<hf-username>-repo-buddy.hf.space`
4. Let GitHub publish the code to the Space:
   - Hugging Face → **Settings → Access Tokens** → new token with **write** access.
   - GitHub repo → **Settings → Secrets and variables → Actions**:
     - secret `HF_TOKEN` = that token
     - variable `HF_SPACE` = `<hf-username>/repo-buddy`
   - GitHub → **Actions → Deploy backend to Hugging Face → Run workflow**.
     After that it redeploys automatically whenever `backend/` changes on `main`.
5. Check `https://<hf-username>-repo-buddy.hf.space/health` returns `{"status":"healthy",...}`.

Notes
- Free Spaces sleep after ~48 h without traffic; the first request then takes a minute to wake it.
- The SQLite database lives in the container and resets when the Space restarts —
  fine for a demo. For persistence, attach Space storage and set `DATABASE_PATH` to `/data/repo_buddy.db`.

## 2. Frontend → Netlify

1. Netlify → **Add new site → Import an existing project → GitHub** → pick this repo.
   `netlify.toml` already sets the base directory (`frontend`) and build command.
2. **Site configuration → Environment variables**: `NEXT_PUBLIC_API_URL` = the Space URL from step 1.
3. Deploy, then put the Netlify URL into the Space's `FRONTEND_URL` variable (CORS).

## 3. Optional: GitHub sign-in

Needed only for the dashboard and auto-fix PRs.

1. <https://github.com/settings/developers> → **New OAuth App**
   - Homepage URL: the Netlify URL
   - Callback URL: `<BACKEND_URL>/auth/github/callback`
2. Add `GITHUB_CLIENT_ID` (variable) and `GITHUB_CLIENT_SECRET` (secret) to the Space.

## Free-tier limits to know

- Gemini's free tier has per-minute and per-day request limits, and Google sometimes returns
  "high demand" errors. The backend retries and falls back across models, and every endpoint
  is rate-limited per IP, but a busy day can still make scans slow or fail with a clear message.
- Don't enable billing on the Gemini key if you want it to stay free.
