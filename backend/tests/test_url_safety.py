import socket

import pytest

from app.services.url_safety import (
    UnsafeURLError,
    normalize_github_url,
    parse_github_repo,
    validate_public_http_url,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("https://github.com/octocat/Hello-World", ("octocat", "Hello-World")),
        ("https://github.com/octocat/Hello-World.git", ("octocat", "Hello-World")),
        ("https://github.com/octocat/Hello-World/tree/main/src", ("octocat", "Hello-World")),
        ("github.com/octocat/hello_world.py", ("octocat", "hello_world.py")),
        ("octocat/Hello-World", ("octocat", "Hello-World")),
        ("  https://www.github.com/a/b/  ", ("a", "b")),
    ],
)
def test_parse_github_repo_accepts_github_forms(value, expected):
    assert parse_github_repo(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "file:///etc/passwd",
        "/etc",
        "C:\\Windows",
        "git@github.com:octocat/repo.git",
        "http://github.com/octocat/repo",          # not https
        "https://gitlab.com/octocat/repo",
        "https://github.com.evil.com/octocat/repo",
        "https://user:pass@github.com/octocat/repo",
        "https://github.com:8443/octocat/repo",
        "https://github.com/octocat",               # no repo
        "../../etc/passwd",
        "octocat/re po",
    ],
)
def test_parse_github_repo_rejects_everything_else(value):
    with pytest.raises(UnsafeURLError):
        parse_github_repo(value)


def test_normalize_github_url_is_canonical():
    assert normalize_github_url("github.com/a/b.git") == "https://github.com/a/b"


@pytest.mark.parametrize(
    "ip",
    ["127.0.0.1", "10.0.0.5", "192.168.1.10", "172.16.0.1", "169.254.169.254", "0.0.0.0", "::1"],
)
def test_probe_rejects_private_and_internal_addresses(monkeypatch, ip):
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(family, 1, 6, "", (ip, 0))])
    with pytest.raises(UnsafeURLError):
        validate_public_http_url("https://internal.example")


def test_probe_rejects_host_with_any_private_record(monkeypatch):
    # DNS returning one public and one private address must still be refused.
    records = [
        (socket.AF_INET, 1, 6, "", ("93.184.216.34", 0)),
        (socket.AF_INET, 1, 6, "", ("10.0.0.1", 0)),
    ]
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: records)
    with pytest.raises(UnsafeURLError):
        validate_public_http_url("https://mixed.example")


@pytest.mark.parametrize(
    "url",
    ["ftp://example.com", "https://user:pw@example.com", "https://example.com:6379", "javascript:alert(1)"],
)
def test_probe_rejects_bad_schemes_ports_and_credentials(public_dns, url):
    with pytest.raises(UnsafeURLError):
        validate_public_http_url(url)


def test_probe_accepts_public_url_and_adds_scheme(public_dns):
    assert validate_public_http_url("example.com/") == "https://example.com"
    assert validate_public_http_url("http://example.com:80/app") == "http://example.com:80/app"
