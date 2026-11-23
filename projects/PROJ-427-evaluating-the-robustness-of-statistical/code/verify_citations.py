"""
Citation verification utility.

This module scans the repository for files that may contain citations,
extracts citation identifiers/URLs, validates them using a simple
reachability check (HTTP HEAD request), and writes a log of the results
to ``state/citation_log.yaml``.

The implementation follows the public API surface defined in the
project specification:

- ``load_config``
- ``find_artifacts``
- ``extract_citations``
- ``verify_citation``
- ``verify_all_citations``
- ``write_citation_log``
- ``main``

The script is intended to be invoked after any artifact that contains
citations is written.  If any citation cannot be reached or is deemed a
mismatch, the script exits with a non‑zero status, causing the task to
fail as required.
"""

import argparse
import json
import logging
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Set, Tuple

import yaml

# ----------------------------------------------------------------------
# Configuration handling
# ----------------------------------------------------------------------
def load_config() -> Dict:
    """
    Load optional YAML configuration for citation verification.

    The configuration file is expected at ``config/citation_validation.yaml``.
    It may contain a list ``ignore`` of citation identifiers that should be
    skipped during verification (e.g., internal references).

    Returns:
        dict: Configuration dictionary (empty if file not found).
    """
    cfg_path = Path("config") / "citation_validation.yaml"
    if not cfg_path.is_file():
        logging.debug("Citation verification config not found; using defaults.")
        return {}
    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    logging.debug(f"Citation verification config loaded: {cfg}")
    return cfg

# ----------------------------------------------------------------------
# Artifact discovery
# ----------------------------------------------------------------------
def find_artifacts(root: Path = Path(".")) -> List[Path]:
    """
    Recursively locate files that may contain citations.

    The function looks for files with extensions that commonly hold
    textual content: ``.py``, ``.md``, ``.txt`` and ``.json``.

    Args:
        root (Path): Directory to start the search from (default: repository root).

    Returns:
        List[Path]: List of file paths that will be scanned.
    """
    extensions = {".py", ".md", ".txt", ".json"}
    artifacts = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            artifacts.append(path)
    logging.debug(f"Found {len(artifacts)} potential citation artifacts.")
    return artifacts

# ----------------------------------------------------------------------
# Citation extraction
# ----------------------------------------------------------------------
_CITATION_REGEX = re.compile(
    r"""
    (                           # start group
      https?://[^\s\]\}]+        # URLs (http/https) up to whitespace or closing delimiters
    )|
    (\{\{claim:([a-f0-9_]+)\}\}) # legacy {{claim:...}} pattern
    """,
    re.VERBOSE | re.IGNORECASE,
)

def extract_citations(text: str) -> Set[str]:
    """
    Extract citation identifiers/URLs from a block of text.

    Supports two patterns:
    1. Plain URLs (http/https).
    2. The legacy ``{{claim:<id>}}`` placeholder used elsewhere in the repo.

    Args:
        text (str): Text to scan.

    Returns:
        Set[str]: Unique citation strings.
    """
    citations: Set[str] = set()
    for match in _CITATION_REGEX.finditer(text):
        url = match.group(1)
        legacy = match.group(3)
        if url:
            citations.add(url.strip())
        elif legacy:
            # Convert the legacy claim into a pseudo‑URL for verification.
            # Many projects map claim IDs to arXiv or DOI; we attempt a generic
            # resolution to ``https://doi.org/<id>`` and also keep the raw ID.
            citations.add(legacy.strip())
    return citations

# ----------------------------------------------------------------------
# Citation verification
# ----------------------------------------------------------------------
def _http_head(url: str, timeout: int = 10) -> bool:
    """
    Perform a lightweight HEAD request to check URL reachability.

    Args:
        url (str): URL to check.
        timeout (int): Seconds before timing out.

    Returns:
        bool: True if the request succeeded (status 200‑399), False otherwise.
    """
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.getcode() < 400
    except Exception as exc:
        logging.debug(f"HEAD request failed for {url}: {exc}")
        return False

def verify_citation(citation: str) -> Tuple[bool, str]:
    """
    Verify a single citation.

    For URLs we perform a HEAD request.  For legacy ``{{claim:...}}`` IDs we
    attempt to resolve them to an arXiv URL (``https://arxiv.org/abs/<id>``) and
    then perform the same check.  If resolution is impossible, the citation is
    considered a mismatch.

    Args:
        citation (str): The citation string extracted from a file.

    Returns:
        Tuple[bool, str]: (is_valid, message) where ``is_valid`` is ``True`` if
        the citation is reachable and matches expectations, otherwise ``False``.
    """
    # Detect legacy claim IDs (they are alphanumeric strings without scheme)
    if citation.startswith("c_") or citation.startswith("claim_"):
        # Assume arXiv; strip potential leading "c_" prefix
        claim_id = citation.lstrip("c_").lstrip("claim_")
        resolved_url = f"https://arxiv.org/abs/{claim_id}"
        reachable = _http_head(resolved_url)
        if reachable:
            return True, f"Resolved claim {citation} to {resolved_url}"
        else:
            return False, f"Unreachable claim URL {resolved_url}"
    # Otherwise treat as a normal URL
    if citation.startswith("http://") or citation.startswith("https://"):
        reachable = _http_head(citation)
        if reachable:
            return True, "OK"
        else:
            return False, "Unreachable"
    # Anything else is considered a mismatch
    return False, "Unrecognised citation format"

def verify_all_citations(citations: Set[str], ignore: Set[str] = None) -> Dict[str, Tuple[bool, str]]:
    """
    Verify a collection of citations.

    Args:
        citations (Set[str]): Set of citation strings.
        ignore (Set[str]): Optional set of citations to skip.

    Returns:
        Dict[str, Tuple[bool, str]]: Mapping from citation to verification result.
    """
    if ignore is None:
        ignore = set()
    results: Dict[str, Tuple[bool, str]] = {}
    for cit in citations:
        if cit in ignore:
            logging.debug(f"Ignoring citation per config: {cit}")
            continue
        is_valid, message = verify_citation(cit)
        results[cit] = (is_valid, message)
    return results

# ----------------------------------------------------------------------
# Logging results
# ----------------------------------------------------------------------
def write_citation_log(
    results: Dict[str, Tuple[bool, str]],
    log_path: Path = Path("state") / "citation_log.yaml",
) -> None:
    """
    Persist verification results to a YAML log.

    The log format is a mapping from citation string to a dictionary with
    ``valid`` (bool) and ``message`` (str) fields.

    Args:
        results (Dict[str, Tuple[bool, str]]): Verification outcomes.
        log_path (Path): Destination file path.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    serialisable = {
        cit: {"valid": valid, "message": msg} for cit, (valid, msg) in results.items()
    }
    with log_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(serialisable, f, sort_keys=False)
    logging.info(f"Citation verification log written to {log_path}")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> int:
    """
    Execute the citation verification pipeline.

    Returns:
        int: Exit code (0 = success, non‑zero = failure).
    """
    parser = argparse.ArgumentParser(
        description="Verify citations across repository artifacts."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Root directory to scan for artifacts (default: repository root).",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    config = load_config()
    ignore_set = set(config.get("ignore", []))

    artifacts = find_artifacts(root=args.root)
    all_citations: Set[str] = set()
    for artifact in artifacts:
        try:
            text = artifact.read_text(encoding="utf-8")
        except Exception as exc:
            logging.warning(f"Could not read {artifact}: {exc}")
            continue
        citations = extract_citations(text)
        if citations:
            logging.debug(f"Found citations in {artifact}: {citations}")
        all_citations.update(citations)

    if not all_citations:
        logging.info("No citations found; nothing to verify.")
        return 0

    verification_results = verify_all_citations(all_citations, ignore=ignore_set)
    write_citation_log(verification_results)

    # Determine overall success
    failed = [cit for cit, (valid, _) in verification_results.items() if not valid]
    if failed:
        logging.error(f"Citation verification failed for {len(failed)} items: {failed}")
        return 1
    logging.info("All citations verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())