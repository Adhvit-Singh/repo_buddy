# repo_buddy backend — container image (deployed on Render; works on any Docker host).
FROM python:3.12-slim

# git is needed to clone the repositories being scanned
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Run as an unprivileged user
RUN useradd --create-home --uid 1000 app
WORKDIR /home/app/backend

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . .
USER app

ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DATABASE_PATH=/home/app/data/repo_buddy.db \
    REPO_STORAGE_PATH=/tmp/repo_buddy_repos
RUN mkdir -p /home/app/data

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
