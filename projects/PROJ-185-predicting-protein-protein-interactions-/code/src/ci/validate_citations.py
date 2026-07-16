#!/usr/bin/env python
"""
Citation verification script for CI.

Scans the repository for Markdown (*.md) and Python (*.py) files,
extracts HTTP/HTTPS URLs, and verifies that they are reachable.
If any URL cannot be reached (status >= 400 or request error),
the script exits with a non‑zero status, causing the CI job to fail.

The script is deliberately lightweight and uses only the standard
library plus the ``requests`` package (declared in ``requirements.txt``).
"""

import argparse
import pathlib
import re
import sys
from typing import List, Tuple

import requests

URL_REGEX = re.compile(r"https?://[^\s\)\]\}\'\"]+")


def find_target_files(root: pathlib.Path) -> List[pathlib.Path]:
    """
    Recursively find all ``.md`` and ``.py`` files under *root*.

    Parameters
    ----------
    root: pathlib.Path
        Directory to start the search from.

    Returns
    -------
    List[pathlib.Path]
        List of file paths matching the required extensions.
    """
    return [
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in {".md", ".py"}
    ]


def extract_urls(text: str) -> List[str]:
    """
    Return a list of URLs found in *text* using a simple regular expression.
    """
    return URL_REGEX.findall(text)


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Check that *url* is reachable.

    First tries a ``HEAD`` request; if that fails or returns a
    status >= 400, falls back to a ``GET`` request.

    Returns
    -------
    (bool, str)
        ``True`` if the URL is reachable, ``False`` otherwise.
        The second element contains either the HTTP status code or
        the exception message.
    """
    try:
        # Prefer HEAD to minimise bandwidth
        response = requests.head(url, allow_redirects=True, timeout=5)
        if response.status_code >= 400:
            # Some servers do not support HEAD; try GET
            response = requests.get(url, stream=True, timeout=5)
            if response.status_code >= 400:
                return False, f"HTTP {response.status_code}"
        return True, f"HTTP {response.status_code}"
    except Exception as exc:  # pragma: no cover – exercised in CI failures
        return False, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate citations (HTTP/HTTPS URLs) in markdown and python files."
    )
    parser.add_argument(
        "--path",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parents[2],
        help="Root directory to scan (default: project root).",
    )
    args = parser.parse_args()

    root = args.path.resolve()
    if not root.is_dir():
        print(f"Error: provided path '{root}' is not a directory.", file=sys.stderr)
        return 1

    failures: List[str] = []

    for file_path in find_target_files(root):
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:  # pragma: no cover
            failures.append(f"{file_path}: cannot read file ({exc})")
            continue

        for url in extract_urls(content):
            ok, info = validate_url(url)
            if not ok:
                failures.append(f"{file_path}:{url} -> {info}")

    if failures:
        print("Citation validation failures:", file=sys.stderr)
        for line in failures:
            print(line, file=sys.stderr)
        return 1

    print("All citations validated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
