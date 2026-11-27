import threading

import pytest

from app import queue
from app.services import autofix_service
from app.services.autofix_service import AutoFixError, generate_and_apply_fix


def test_queue_dedupes_same_url_while_running():
    release = threading.Event()
    ran = []

    def slow_task(scan_id, url):
        ran.append(scan_id)
        release.wait(timeout=5)

    url = "https://github.com/a/dedupe"
    first = queue.enqueue_scan("scan-1", url, slow_task)
    second = queue.enqueue_scan("scan-2", url, slow_task)
    assert first == second == "scan-1"
    assert queue.is_url_scanning(url) == "scan-1"

    release.set()
    queue._executor.submit(lambda: None).result(timeout=5)  # let the worker drain
    for _ in range(50):
        if queue.is_url_scanning(url) is None:
            break
        threading.Event().wait(0.05)
    assert queue.is_url_scanning(url) is None
    assert ran == ["scan-1"]


def test_autofix_needs_user_token():
    with pytest.raises(AutoFixError) as exc:
        generate_and_apply_fix("octocat/Hello-World", [{"title": "x", "file": "a.py"}], None)
    assert exc.value.status_code == 401


def test_autofix_needs_llm_key():
    with pytest.raises(AutoFixError) as exc:
        generate_and_apply_fix("octocat/Hello-World", [{"title": "x", "file": "a.py"}], "gho_token")
    assert exc.value.status_code == 503


def test_autofix_rejects_non_github_repo():
    from app.services.url_safety import UnsafeURLError

    with pytest.raises(UnsafeURLError):
        generate_and_apply_fix("https://evil.example/a/b", [{"title": "x"}], "gho_token")


def test_autofix_only_writes_files_it_was_given(monkeypatch):
    """The model may not add or overwrite files outside the affected set."""
    written = {}

    class FakeContent:
        decoded_content = b"old"

    class FakeRepo:
        default_branch = "main"

        def get_contents(self, path):
            return FakeContent()

        def get_git_ref(self, ref):
            return type("Ref", (), {"object": type("O", (), {"sha": "base"})()})()

        def get_git_commit(self, sha):
            return "base-commit"

        def create_git_blob(self, content, enc):
            return type("B", (), {"sha": f"blob-{len(written)}"})()

        def get_git_tree(self, sha):
            return "base-tree"

        def create_git_tree(self, elements, base):
            for e in elements:
                written[e._InputGitTreeElement__path] = True
            return "tree"

        def create_git_commit(self, msg, tree, parents):
            return type("C", (), {"sha": "new"})()

        def create_git_ref(self, ref, sha):
            pass

        def create_pull(self, **kw):
            return type("PR", (), {"html_url": "https://github.com/o/r/pull/1"})()

    class FakeGithub:
        def __init__(self, auth):
            pass

        def get_repo(self, name):
            return FakeRepo()

    import github

    monkeypatch.setattr(github, "Github", FakeGithub)
    monkeypatch.setattr(autofix_service, "active_provider", lambda: "gemini")
    monkeypatch.setattr(
        autofix_service,
        "llm_json",
        lambda prompt, **kw: {"app.py": "fixed", ".github/workflows/evil.yml": "pwned"},
    )

    url = generate_and_apply_fix("o/r", [{"title": "x", "file": "app.py"}], "gho_token")
    assert url == "https://github.com/o/r/pull/1"
    assert list(written) == ["app.py"]
