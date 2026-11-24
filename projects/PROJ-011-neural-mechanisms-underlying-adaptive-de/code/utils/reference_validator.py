"""
Reference Validator

This module scans the provided markdown/text files for URLs (citations) and
verifies that each URL is reachable (HTTP status 200). It writes a YAML
report to ``state/reference_validation_report.yaml``. The script exits with
status 0 only if **all** citations are reachable; otherwise it exits with
status 1.

The validator is deliberately simple – it checks reachability, which is a
concrete, reproducible property of a citation. More sophisticated
validation (e.g., DOI metadata comparison) could be added later.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import List, Dict

import requests
import yaml

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Regular expression to capture markdown links: [text](url)
_MD_LINK_RE = r'\[.*?\]\((https?://[^)]+)\)'

def extract_urls(file_path: Path) -> List[str]:
    """Extract all HTTP/HTTPS URLs from a markdown/text file."""
    import re

    if not file_path.is_file():
        log.warning(f"File not found or not a regular file: {file_path}")
        return []

    text = file_path.read_text(encoding="utf-8")
    urls = re.findall(_MD_LINK_RE, text)
    return urls

def check_url(url: str, timeout: int = 10) -> bool:
    """Return True if the URL responds with HTTP 200, else False."""
    try:
        # Use HEAD when possible to minimise bandwidth.
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        # Some servers do not support HEAD; fall back to GET.
        if response.status_code == 405:  # Method Not Allowed
            response = requests.get(url, stream=True, timeout=timeout)
        reachable = response.status_code == 200
        if not reachable:
            log.debug(f"URL {url} returned status {response.status_code}")
        return reachable
    except Exception as exc:
        log.debug(f"Exception while checking {url}: {exc}")
        return False

def build_report(file_paths: List[Path]) -> Dict:
    """Create the validation report dictionary."""
    report = {
        "citations": [],
        "summary": {
            "total_citations": 0,
            "reachable": 0,
            "unreachable": 0,
        },
    }

    for fp in file_paths:
        urls = extract_urls(fp)
        for url in urls:
            reachable = check_url(url)
            entry = {
                "file": str(fp),
                "url": url,
                "reachable": reachable,
            }
            report["citations"].append(entry)
            report["summary"]["total_citations"] += 1
            if reachable:
                report["summary"]["reachable"] += 1
            else:
                report["summary"]["unreachable"] += 1

    return report

def write_report(report: Dict, out_path: Path) -> None:
    """Write the YAML report, ensuring the parent directory exists."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(report, f, sort_keys=False)
    log.info(f"Reference‑validation report written to {out_path}")

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate citations in markdown/text files."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Path(s) to files to scan. If omitted, defaults to spec.md, plan.md, README.md at the project root.",
    )
    args = parser.parse_args(argv)

    # Determine which files to validate
    if args.files:
        file_paths = [Path(p).resolve() for p in args.files]
    else:
        root = Path(paths.root).resolve()
        default_names = ["spec.md", "plan.md", "README.md"]
        file_paths = [root / name for name in default_names]

    log.info(f"Validating citations in {len(file_paths)} file(s).")
    report = build_report(file_paths)

    out_path = paths.state("reference_validation_report.yaml")
    write_report(report, out_path)

    # Exit status: 0 if all reachable, else 1
    if report["summary"]["unreachable"] == 0:
        log.info("All citations are reachable.")
        return 0
    else:
        log.error(
            f"{report['summary']['unreachable']} citation(s) could not be reached."
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())