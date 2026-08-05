from __future__ import annotations

"""
PII Scanner

Scans every file under the project's ``data`` directory for patterns that may
contain personally identifiable information (PII).  The scanner is driven by
``run_pii_scan`` which is used as the entry‑point for both the command line
interface and the integration test ``tests/integration/test_pii_validation.py``.

The implementation follows the specification for **Constitution Principle III**,
using a set of regular‑expression patterns to locate common PII types such as
email addresses, IP addresses, phone numbers, SSNs, credit‑card numbers, AWS
access keys and GitHub tokens.

The script writes its findings to ``data/pii_findings.csv`` (creating the
file and its parent directories if necessary) and returns a list of dictionaries
describing each finding.

The module is deliberately defensive:

* If ``config.get_data_root`` cannot be imported (e.g. during isolated test
  execution) it falls back to ``Path("data")``.
* Missing directories are created automatically.
* Any unexpected exception while scanning a file is logged but does not abort
  the whole run – this matches the project's “robust logging” policy.
"""

import csv
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# --------------------------------------------------------------------------- #
# Configuration helpers – import from ``code.config`` if available, otherwise
# fall back to a sensible default.  This keeps the module usable in isolation
# (e.g. when the test suite imports it without the full project configuration
# having been loaded first).
# --------------------------------------------------------------------------- #
try:
    from config import get_data_root  # type: ignore
except Exception:  # pragma: no cover – defensive fallback
    def get_data_root() -> Path:  # pylint: disable=function-redefined
        """Fallback ``get_data_root`` returning the conventional data directory."""
        return Path("data")

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# PII regular‑expression patterns (Constitution Principle III)
# --------------------------------------------------------------------------- #
PII_PATTERNS: Dict[str, re.Pattern] = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "ipv4": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
    ),
    "ipv6": re.compile(
        r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
        r"|(?:[0-9a-fA-F]{1,4}:){1,7}:"
        r"|:(?:[0-9a-fA-F]{1,4}:){1,7}"
        r"|(?:(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4})?"
        r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
        r"(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}\b"
    ),
    "phone_us": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|"
        r"3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b"
    ),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github_token": re.compile(r"\bg[hp]_[0-9a-zA-Z]{36}\b"),
}


# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def setup_logging() -> None:
    """Configure module‑level logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("data/pii_scan.log"),
        ],
    )

def should_scan_file(file_path: Path) -> bool:
    """
    Decide whether ``file_path`` should be examined for PII.

    The function accepts typical source‑code and text‑based extensions and
    explicitly rejects binary artefacts.  Unknown extensions are inspected
    heuristically – if the first kilobyte contains a null byte the file is
    considered binary and skipped.
    """
    if not file_path.is_file():
        return False

    # Known text‑based extensions
    text_exts = {".py", ".csv", ".json", ".yaml", ".yml", ".txt", ".md", ".ini"}
    binary_exts = {".png", ".jpg", ".jpeg", ".pdf", ".zip", ".tar", ".gz", ".exe"}

    suffix = file_path.suffix.lower()
    if suffix in text_exts:
        return True
    if suffix in binary_exts:
        return False

    # Heuristic for unknown extensions
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\x00" not in chunk
    except Exception as exc:  # pragma: no cover
        logger.debug(f"Could not inspect {file_path}: {exc}")
        return False


def scan_file_for_pii(file_path: Path) -> List[Dict[str, Any]]:
    """
    Scan a single file for all configured PII patterns.

    Returns a list of dictionaries; each entry records the file path,
    line number, type of PII, the exact matched text and a timestamp.
    """
    findings: List[Dict[str, Any]] = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, start=1):
                for pii_type, pattern in PII_PATTERNS.items():
                    for match in pattern.findall(line):
                        findings.append(
                            {
                                "file_path": str(file_path),
                                "line_number": line_num,
                                "pii_type": pii_type,
                                "matched_text": match,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
    except Exception as exc:  # pragma: no cover
        logger.error(f"Error scanning file {file_path}: {exc}")
    return findings


def scan_directory(base_dir: Path) -> List[Dict[str, Any]]:
    """
    Recursively walk ``base_dir`` and scan every file that ``should_scan_file``
    deems appropriate.
    """
    all_findings: List[Dict[str, Any]] = []
    if not base_dir.exists():
        logger.warning(f"Directory does not exist: {base_dir}")
        return all_findings

    for file_path in base_dir.rglob("*"):
        if should_scan_file(file_path):
            file_findings = scan_file_for_pii(file_path)
            all_findings.extend(file_findings)
            if file_findings:
                logger.warning(
                    f"PII found in {file_path}: {len(file_findings)} instance(s)"
                )
    return all_findings


def write_findings_to_csv(findings: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Persist the list of PII findings to ``output_path`` as a CSV file.

    The CSV always contains a header row; if ``findings`` is empty an empty
    file with only the header is written.
    """
    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "file_path",
        "line_number",
        "pii_type",
        "matched_text",
        "timestamp",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        if findings:
            writer.writerows(findings)

    logger.info(f"PII findings written to {output_path} ({len(findings)} entries)")


def run_pii_scan() -> List[Dict[str, Any]]:
    """
    Orchestrates a full PII scan of the project's data directory.

    Returns the list of findings so callers (tests, notebooks, etc.) can
    programmatically inspect the results.
    """
    logger.info("Starting PII scan on the data directory...")
    data_root = get_data_root()
    findings = scan_directory(data_root)
    output_path = data_root / "pii_findings.csv"
    write_findings_to_csv(findings, output_path)
    return findings


def main() -> None:
    """CLI entry point – configures logging and launches the scan."""
    setup_logging()
    run_pii_scan()


if __name__ == "__main__":
    main()
