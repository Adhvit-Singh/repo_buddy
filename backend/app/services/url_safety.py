"""
repo_buddy — URL safety checks

The backend takes URLs from anonymous users and then (a) runs `git clone` on
them and (b) sends HTTP requests to them. Both are dangerous without checks:

- Cloning an arbitrary URL lets a caller make the server clone local paths
  (`/etc`, `file://...`) or internal git hosts and ship the contents to an LLM.
- Probing an arbitrary URL is SSRF: the caller could make the server hit
  `localhost`, cloud metadata (169.254.169.254) or the private network.
"""
import ipaddress
import re
import socket
from urllib.parse import urlparse

_GITHUB_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")


class UnsafeURLError(ValueError):
    """The URL was rejected; the message is safe to show to the user."""


def parse_github_repo(value: str) -> tuple[str, str]:
    """
    Accept `https://github.com/owner/repo`, `github.com/owner/repo` or
    `owner/repo` and return (owner, repo). Raise UnsafeURLError otherwise.
    """
    value = (value or "").strip()
    if not value:
        raise UnsafeURLError("Please enter a GitHub repository URL.")

    if "://" in value:
        parsed = urlparse(value)
        if parsed.scheme != "https" or parsed.hostname not in ("github.com", "www.github.com"):
            raise UnsafeURLError("Only public https://github.com repositories can be scanned.")
        if parsed.username or parsed.password or parsed.port:
            raise UnsafeURLError("Repository URLs can't contain credentials or ports.")
        path = parsed.path
    else:
        path = re.sub(r"^(www\.)?github\.com/", "", value)

    parts = [p for p in path.strip("/").split("/") if p]
    if len(parts) < 2:
        raise UnsafeURLError("Use the form https://github.com/owner/repo.")
    owner, repo = parts[0], parts[1].removesuffix(".git")
    if not (_GITHUB_NAME.match(owner) and _GITHUB_NAME.match(repo)) or ".." in owner + repo:
        raise UnsafeURLError("That doesn't look like a valid GitHub owner/repo name.")
    return owner, repo


def normalize_github_url(value: str) -> str:
    """Return the canonical clone URL `https://github.com/owner/repo`."""
    owner, repo = parse_github_repo(value)
    return f"https://github.com/{owner}/{repo}"


def _is_public_ip(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    return addr.is_global and not addr.is_multicast


def validate_public_http_url(value: str) -> str:
    """
    Allow only http(s) URLs whose host resolves exclusively to public IPs.
    Returns the cleaned URL. Raise UnsafeURLError otherwise.
    """
    value = (value or "").strip()
    if not value:
        raise UnsafeURLError("Please enter the URL of your live app.")
    if "://" not in value:
        value = "https://" + value

    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise UnsafeURLError("Only http:// or https:// URLs can be probed.")
    if parsed.username or parsed.password:
        raise UnsafeURLError("URLs can't contain credentials.")
    if parsed.port not in (None, 80, 443):
        raise UnsafeURLError("Only standard web ports (80/443) can be probed.")

    host = parsed.hostname
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise UnsafeURLError(f"Couldn't resolve {host}.")
    ips = {info[4][0] for info in infos}
    if not ips or not all(_is_public_ip(ip) for ip in ips):
        raise UnsafeURLError("That address points to a private or internal network and can't be probed.")
    return value.rstrip("/")
