"""
Real‑Data‑Only Audit Script

Scans all Python files in `src/ingest/` for prohibited patterns that would
generate synthetic data (e.g., `generate_synthetic_` or `mock_` calls).
Exits with code 0 if none are found, otherwise exits with code 1.

Usage:
    python code/scripts/real_data_audit.py
"""
import sys
import re
from pathlib import Path
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# Patterns that indicate synthetic data generation or mocking
PROHIBITED_PATTERNS = [
    re.compile(r"generate_synthetic_"),
    re.compile(r"\bmock_"),
]

def file_contains_prohibited_pattern(file_path: Path) -> bool:
    """Return True if any prohibited pattern is found in the file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        log.error(f"Failed to read {file_path}: {e}")
        return True  # Treat unreadable file as failure

    for pattern in PROHIBITED_PATTERNS:
        if pattern.search(content):
            log.error(f"Prohibited pattern '{pattern.pattern}' found in {file_path}")
            return True
    return False

def main() -> int:
    """
    Scan all .py files under the project's `src/ingest/` directory.
    Returns exit code 0 if clean, 1 otherwise.
    """
    ingest_dir = Path(__file__).resolve().parents[2] / "src" / "ingest"
    if not ingest_dir.is_dir():
        log.error(f"Ingest directory not found: {ingest_dir}")
        return 1

    problematic_files = []

    for py_file in ingest_dir.rglob("*.py"):
        if file_contains_prohibited_pattern(py_file):
            problematic_files.append(py_file)

    if problematic_files:
        log.error(
            "Real‑data‑only audit failed. Prohibited patterns detected in the following files:"
        )
        for p in problematic_files:
            log.error(f"  - {p}")
        return 1

    log.info("Real‑data‑only audit passed: no prohibited patterns found.")
    return 0

if __name__ == "__main__":
    sys.exit(main())