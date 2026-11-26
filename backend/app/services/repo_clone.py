import os
import subprocess
import uuid
from app.config import REPO_STORAGE_PATH
from app.services.url_safety import normalize_github_url

def clone_repo(repo_url: str) -> str:
    """
    Shallow-clones a public GitHub repo into a unique local directory and
    returns its path. Only https://github.com/owner/repo URLs are accepted,
    so callers can't make the server clone local paths or internal hosts.
    """
    repo_url = normalize_github_url(repo_url)
    # Unique folder per clone
    repo_id = str(uuid.uuid4())[:8]
    repo_path = os.path.join(REPO_STORAGE_PATH, repo_id)

    os.makedirs(repo_path, exist_ok=True)

    result = subprocess.run(
        ["git", "-c", "protocol.file.allow=never", "clone", "--depth", "1", "--", repo_url, repo_path],
        capture_output=True,
        text=True,
        timeout=180,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )

    if result.returncode != 0:
        raise Exception(f"Git clone failed: {result.stderr}")

    return repo_path


def cleanup_repo(repo_path: str):
    """Remove a cloned repo to free disk space."""
    import shutil
    if os.path.exists(repo_path) and REPO_STORAGE_PATH in repo_path:
        shutil.rmtree(repo_path, ignore_errors=True)
