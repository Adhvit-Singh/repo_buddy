"""
Test setup: isolate every run from real keys, real data and real networks.

Environment variables are set *before* the app is imported, because config
and the database layer read them at import time. Values set here win over a
local backend/.env (python-dotenv never overrides existing variables).
"""
import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp(prefix="repo_buddy_tests_")
os.environ.update(
    {
        "DATABASE_PATH": os.path.join(_tmp, "test.db"),
        "REPO_STORAGE_PATH": os.path.join(_tmp, "repos"),
        "GEMINI_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "GITHUB_CLIENT_ID": "",
        "GITHUB_CLIENT_SECRET": "",
        "RATE_LIMIT_ENABLED": "false",
    }
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402


@pytest.fixture
def client():
    """FastAPI test client without startup hooks (no background workers)."""
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


@pytest.fixture
def public_dns(monkeypatch):
    """Make every hostname resolve to a public IP, so tests need no network."""
    import socket

    def fake_getaddrinfo(host, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
