"""
Citation validation utility.

This script searches target source files for URLs, verifies that each URL is reachable,
and enforces a minimum title‑token overlap of 0.7 between the HTML title of the
referenced page and the surrounding citation text in the source file.

The original implementation performed only a reachability check.  This extended
version adds the title‑token overlap requirement as required by Constitution II.
"""

import argparse
import pathlib
import re
import sys
from typing import List, Tuple

import requests

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def find_target_files(root: pathlib.Path) -> List[pathlib.Path]:
    """
    Recursively locate files that may contain citations.

    Currently, we consider any file with a recognised source‑code or documentation
    extension.  The set can be extended in the future without affecting callers.

    Parameters
    ----------
    root: pathlib.Path
        Directory to start the recursive search from.

    Returns
    -------
    List[pathlib.Path]
        List of file paths to be inspected.
    """
    # Common extensions that typically contain citations.
    extensions = {".py", ".R", ".md", ".txt", ".rst", ".ipynb"}
    return [
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in extensions
    ]


def extract_urls(line: str) -> List[str]:
    """
    Extract all HTTP/HTTPS URLs from a line of text.

    Parameters
    ----------
    line: str
        A single line from a source file.

    Returns
    -------
    List[str]
        All URLs found on the line (may be empty).
    """
    # Simple regex that captures http(s) URLs.
    url_pattern = re.compile(
        r"https?://[^\s\"\'<>]+", re.IGNORECASE
    )
    return url_pattern.findall(line)


def fetch_title(url: str) -> str:
    """
    Retrieve the HTML title of a web page.

    The function issues a GET request with a short timeout.  If the request
    succeeds but no <title> tag is present, an empty string is returned.

    Parameters
    ----------
    url: str
        The URL to fetch.

    Returns
    -------
    str
        The raw title string (whitespace stripped) or an empty string.
    """
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    html = response.text

    # Extract the <title> tag content.
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if match:
        title = match.group(1)
        # Collapse whitespace and strip surrounding spaces.
        return " ".join(title.split())
    return ""


def tokenize(text: str) -> List[str]:
    """
    Tokenise a string into lower‑cased alphanumeric tokens.

    Non‑alphanumeric characters are treated as delimiters.

    Parameters
    ----------
    text: str
        Input string.

    Returns
    -------
    List[str]
        List of tokens.
    """
    # Replace non‑alphanumeric characters with spaces, split, and lower‑case.
    cleaned = re.sub(r"[^0-9a-zA-Z]+", " ", text)
    return [tok.lower() for tok in cleaned.split() if tok]


def title_token_overlap(title: str, citation: str) -> float:
    """
    Compute the token overlap ratio between a title and a citation line.

    Overlap is defined as the size of the intersection divided by the size of the
    union of the token sets (Jaccard similarity).

    Parameters
    ----------
    title: str
        The HTML title of the referenced page.
    citation: str
        The citation text extracted from the source file (the line containing the URL).

    Returns
    -------
    float
        Overlap ratio in the range [0, 1].
    """
    title_tokens = set(tokenize(title))
    citation_tokens = set(tokenize(citation))

    if not title_tokens and not citation_tokens:
        return 1.0  # Both empty – treat as perfect overlap.

    intersection = title_tokens.intersection(citation_tokens)
    union = title_tokens.union(citation_tokens)
    return len(intersection) / len(union)


def validate_url(url: str, citation_line: str) -> None:
    """
    Validate a single URL.

    The validation comprises two checks:
    1. The URL must be reachable (HTTP 200‑ish response).
    2. The title‑token overlap between the page title and the citation line must be
       at least 0.7.

    If either check fails, a ``ValueError`` is raised with a descriptive message.

    Parameters
    ----------
    url: str
        The URL to validate.
    citation_line: str
        The line from the source file that contains the URL.
    """
    # --- Reachability check -------------------------------------------------
    try:
        # ``head`` is usually sufficient; fall back to ``get`` if not allowed.
        response = requests.head(url, allow_redirects=True, timeout=10)
        if response.status_code >= 400:
            # Some servers do not support HEAD; try GET.
            response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        raise ValueError(f"URL unreachable: {url} ({exc})") from exc

    # --- Title‑token overlap check -----------------------------------------
    title = fetch_title(url)
    overlap = title_token_overlap(title, citation_line)

    if overlap < 0.7:
        raise ValueError(
            f"Title‑token overlap too low for URL {url} (overlap={overlap:.2f} < 0.7). "
            f"Page title: '{title}'. Citation line: '{citation_line.strip()}'"
        )


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate citations in source files."
    )
    parser.add_argument(
        "root",
        type=pathlib.Path,
        nargs="?",
        default=pathlib.Path("."),
        help="Root directory to search for files containing citations.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    """
    Walk the file tree, locate URLs, and validate each.

    The script exits with status code 0 if all citations pass validation;
    otherwise it prints errors to stderr and exits with status code 1.
    """
    args = _parse_args(argv)

    root_path = pathlib.Path(args.root).resolve()
    if not root_path.is_dir():
        print(f"Error: root path '{root_path}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    files = find_target_files(root_path)
    failures: List[Tuple[pathlib.Path, int, str]] = []

    for file_path in files:
        try:
            with file_path.open(encoding="utf-8") as f:
                for line_no, line in enumerate(f, start=1):
                    urls = extract_urls(line)
                    for url in urls:
                        try:
                            validate_url(url, line)
                        except ValueError as err:
                            failures.append((file_path, line_no, str(err)))
        except Exception as e:
            # If a file cannot be read, treat it as a failure.
            failures.append((file_path, 0, f"Unable to read file: {e}"))

    if failures:
        for file_path, line_no, message in failures:
            location = f"{file_path}:{line_no}" if line_no else str(file_path)
            print(f"Citation validation error at {location}: {message}", file=sys.stderr)
        sys.exit(1)

    # All good.
    print("All citations passed validation.")
    sys.exit(0)