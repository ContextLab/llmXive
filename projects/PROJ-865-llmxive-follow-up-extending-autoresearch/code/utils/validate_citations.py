"""validate_citations.py
Reference-Validator Script

This script extracts citation identifiers (DOIs and HuggingFace dataset IDs)
from one or more markdown files, fetches primary source metadata, and
verifies that each citation is reachable. It produces a JSON report at the
specified output location with the following schema:

{
    "status": "PASS" | "FAIL",
    "citations": [
        {
            "id": "<citation identifier>",
            "status": "PASS" | "FAIL",
            "mismatch_reason": "<string | null>",
            "source_metadata": {
                "title": "<string>",
                "authors": ["<author>", ...],
                "year": <int | null>
            }
        },
        ...
    ]
}

The script implements exponential back‑off for transient HTTP errors and
fails loudly if a citation cannot be resolved.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

DOI_REGEX = re.compile(r'\b10\.\d{4,9}/[^\s\]\)]+', re.IGNORECASE)
# Simple heuristic for HuggingFace dataset identifiers: <namespace>/<repo>
HF_DATASET_REGEX = re.compile(r'(?<![\w/])([A-Za-z0-9_-]+/[A-Za-z0-9_-]+)(?![\w/])')


def extract_citations(text: str) -> list[str]:
    """
    Return a list of unique citation identifiers found in ``text``.
    Identifiers include:
    * DOIs (e.g. 10.1000/xyz123)
    * HuggingFace dataset IDs (e.g. claw-ai-lab/arc-bench)
    """
    dois = DOI_REGEX.findall(text)
    hf_ids = HF_DATASET_REGEX.findall(text)
    # Deduplicate while preserving order
    seen = set()
    citations: list[str] = []
    for cid in dois + hf_ids:
        if cid not in seen:
            seen.add(cid)
            citations.append(cid)
    return citations


def fetch_doi_metadata(doi: str) -> dict:
    """
    Query Crossref for ``doi`` and return a dict with ``title``, ``authors``,
    and ``year``. Raises on failure.
    """
    url = f"https://api.crossref.org/works/{doi}"
    for attempt in range(5):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()["message"]
                title = data.get("title", [""])[0]
                authors = [
                    f"{a.get('given', '').strip()} {a.get('family', '').strip()}".strip()
                    for a in data.get("author", [])
                ]
                year = None
                # Prefer printed date, fall back to online date
                if "published-print" in data and "date-parts" in data["published-print"]:
                    year = data["published-print"]["date-parts"][0][0]
                elif "published-online" in data and "date-parts" in data["published-online"]:
                    year = data["published-online"]["date-parts"][0][0]
                return {"title": title, "authors": authors, "year": year}
            elif resp.status_code == 404:
                raise ValueError(f"DOI not found: {doi}")
            else:
                # Treat other status codes as transient
                raise RuntimeError(f"Unexpected status {resp.status_code}")
        except Exception as exc:
            if attempt < 4:
                backoff = 2 ** attempt
                time.sleep(backoff)
            else:
                raise RuntimeError(f"Failed to fetch DOI {doi}: {exc}") from exc


def fetch_hf_metadata(dataset_id: str) -> dict:
    """
    Query the HuggingFace Hub for ``dataset_id`` (e.g. ``claw-ai-lab/arc-bench``)
    and return a dict with ``title``, ``authors`` and ``year`` (derived from
    the last‑modified timestamp). Raises on failure.
    """
    url = f"https://huggingface.co/api/datasets/{dataset_id}"
    for attempt in range(5):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # ``cardData`` often contains a human‑readable title
                title = data.get("cardData", {}).get("title") or data.get("id", "")
                # Author information is not consistently structured; we fall back
                # to ``author`` if present.
                raw_authors = data.get("author")
                if isinstance(raw_authors, list):
                    authors = [str(a) for a in raw_authors]
                elif isinstance(raw_authors, str):
                    authors = [raw_authors]
                else:
                    authors = []
                # Derive year from ``lastModified`` timestamp (ISO 8601)
                year = None
                if "lastModified" in data:
                    try:
                        year = int(data["lastModified"][:4])
                    except Exception:
                        pass
                return {"title": title, "authors": authors, "year": year}
            elif resp.status_code == 404:
                raise ValueError(f"HuggingFace dataset not found: {dataset_id}")
            else:
                raise RuntimeError(f"Unexpected status {resp.status_code}")
        except Exception as exc:
            if attempt < 4:
                backoff = 2 ** attempt
                time.sleep(backoff)
            else:
                raise RuntimeError(f"Failed to fetch HuggingFace dataset {dataset_id}: {exc}") from exc


def resolve_citation(citation_id: str) -> tuple[bool, dict | None, str | None]:
    """
    Resolve ``citation_id`` (DOI or HF dataset) and return a tuple:
    (is_successful, source_metadata, mismatch_reason)
    """
    try:
        if citation_id.lower().startswith("10."):
            metadata = fetch_doi_metadata(citation_id)
        else:
            metadata = fetch_hf_metadata(citation_id)
        return True, metadata, None
    except Exception as exc:
        return False, None, str(exc)


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------

def build_report(citation_ids: list[str]) -> dict:
    """
    For each identifier in ``citation_ids`` attempt to fetch metadata.
    Returns the full report dictionary matching the required schema.
    """
    citations_report = []
    all_pass = True

    for cid in citation_ids:
        success, meta, reason = resolve_citation(cid)
        citation_entry = {
            "id": cid,
            "status": "PASS" if success else "FAIL",
            "mismatch_reason": None if success else reason,
            "source_metadata": meta if meta else {"title": "", "authors": [], "year": None},
        }
        citations_report.append(citation_entry)
        if not success:
            all_pass = False

    return {
        "status": "PASS" if all_pass else "FAIL",
        "citations": citations_report,
    }


def parse_arguments() -> argparse.Namespace:
    """
    Parse CLI arguments. Defaults are provided so the script can be run
    without explicit arguments (useful for automated verification).
    """
    parser = argparse.ArgumentParser(
        description="Validate citations in markdown files against primary sources."
    )
    parser.add_argument(
        "--input",
        action="append",
        help=(
            "Path to a markdown file containing citations. Can be used multiple times. "
            "If omitted, defaults to the project's plan and spec files."
        ),
    )
    parser.add_argument(
        "--output",
        help=(
            "Path to write the JSON citation validation report. "
            "If omitted, defaults to data/artifacts/citation_validation_report.json"
        ),
    )
    args = parser.parse_args()

    # Apply sensible defaults when arguments are missing
    if not args.input:
        # Default to the two specification markdown files
        args.input = [
            str(Path("specs/001-llmxive-follow-up-extending-autoresearch/plan.md")),
            str(Path("specs/001-llmxive-follow-up-extending-autoresearch/spec.md")),
        ]
    if not args.output:
        args.output = str(Path("data/artifacts/citation_validation_report.json"))

    return args


def main() -> int:
    args = parse_arguments()

    # Aggregate all citation identifiers from all input files
    all_citations: list[str] = []
    for in_path_str in args.input:
        in_path = Path(in_path_str)
        if not in_path.is_file():
            print(f"[ERROR] Input file not found: {in_path}", file=sys.stderr)
            return 1
        text = in_path.read_text(encoding="utf-8")
        all_citations.extend(extract_citations(text))

    # De‑duplicate while preserving order
    seen = set()
    unique_citations: list[str] = []
    for cid in all_citations:
        if cid not in seen:
            seen.add(cid)
            unique_citations.append(cid)

    report = build_report(unique_citations)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Citation validation report written to {out_path}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())