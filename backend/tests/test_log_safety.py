"""Regression: a non-ASCII character in a print() once crashed scans on Windows."""
import re
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
PRINT_WITH_NON_ASCII = re.compile(r"print\(.*[^\x00-\x7F]")


def test_log_lines_are_ascii_only():
    offenders = [
        f"{path.relative_to(APP)}:{n}"
        for path in APP.rglob("*.py")
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if PRINT_WITH_NON_ASCII.search(line)
    ]
    assert offenders == [], f"non-ASCII characters in print(): {offenders}"
