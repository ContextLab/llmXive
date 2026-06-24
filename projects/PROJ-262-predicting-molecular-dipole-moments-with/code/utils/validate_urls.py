"""Validate that all literature URLs cited in the project specification are accessible.

This script scans the specification Markdown file for URLs, performs an HTTP HEAD
request for each, and writes a CSV report summarising the status of each URL.

The output CSV is written to ``data/validation/urls_report.csv`` relative to the
project root.  The script can be executed directly::

    python code/utils/validate_urls.py

Optional command‑line arguments allow overriding the specification file location
and the output report path.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import List, Tuple

import requests

URL_REGEX = re.compile(
    r"""(?i)\b((?:https?://|www\d{0,3}[.]|doi\.org/)[^\s<>"]+?)"""
)


def extract_urls(text: str) -> List[str]:
    """Return a list of unique URLs found in *text*."""
    urls = set(match.group(0) for match in URL_REGEX.finditer(text))
    # Normalise URLs that start with "www." to include the scheme.
    normalised = {
        url if url.startswith(("http://", "https://")) else f"https://{url}"
        for url in urls
    }
    return sorted(normalised)


def check_url(url: str, timeout: float = 10.0) -> Tuple[str, str]:
    """Perform a HEAD request for *url*.

    Returns a tuple ``(status, detail)`` where *status* is ``OK`` if the request
    succeeded (status code < 400) and ``FAIL`` otherwise. *detail* contains the
    HTTP status code or the exception message.
    """
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        if response.status_code < 400:
            return "OK", str(response.status_code)
        else:
            return "FAIL", str(response.status_code)
    except Exception as exc:  # pragma: no cover – network failures are environment‑specific
        return "FAIL", str(exc)


def validate_spec_urls(
    spec_path: Path, output_path: Path
) -> None:
    """Validate URLs in *spec_path* and write a CSV report to *output_path*."""
    if not spec_path.is_file():
        sys.stderr.write(f"Specification file not found: {spec_path}\\n")
        sys.exit(1)

    text = spec_path.read_text(encoding="utf-8")
    urls = extract_urls(text)

    if not urls:
        sys.stderr.write("No URLs found in the specification.\\n")
        sys.exit(0)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["url", "status", "detail"])
        for url in urls:
            status, detail = check_url(url)
            writer.writerow([url, status, detail])

    print(f"URL validation report written to: {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate literature URLs cited in the project specification."
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "specs"
        / "001-predicting-molecular-dipole-moments"
        / "spec.md",
        help="Path to the specification Markdown file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "data"
        / "validation"
        / "urls_report.csv",
        help="Path where the CSV report will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validate_spec_urls(args.spec, args.output)


if __name__ == "__main__":
    main()
