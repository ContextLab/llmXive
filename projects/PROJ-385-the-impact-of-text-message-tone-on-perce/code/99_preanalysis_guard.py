"""
Pre‑analysis guard for the LMM script.

This guard ensures that ``code/04_fit_lmm.py`` reads data exclusively from
``data/processed/anonymised_ratings.csv`` and does not reference any raw
data files (e.g., paths containing ``data/raw/``). It is intended to be run
as part of CI; the script exits with status 0 when the guard passes and
with status 1 (and an explanatory message) when it fails.
"""

import sys
import re
from pathlib import Path

# Relative path to the LMM script we need to inspect
LMM_SCRIPT_RELATIVE = Path(__file__).parent / "04_fit_lmm.py"

# Expected processed data file (absolute path will be resolved at runtime)
EXPECTED_PROCESSED_PATH = Path("data/processed/anonymised_ratings.csv").as_posix()


def _read_lmm_source() -> str:
    """Read the source code of the LMM script."""
    if not LMM_SCRIPT_RELATIVE.is_file():
        sys.stderr.write(f"Guard error: LMM script not found at {LMM_SCRIPT_RELATIVE}\\n")
        sys.exit(1)

    return LMM_SCRIPT_RELATIVE.read_text(encoding="utf-8")


def _contains_raw_path(source: str) -> bool:
    """
    Detect any string literals or path constructions that reference the raw
    data directory. A simple regex looks for ``data/raw/`` within quotes or
    as a raw string.
    """
    raw_pattern = re.compile(r"""['"]([^'"]*data/raw/[^'"]*)['"]""")
    return bool(raw_pattern.search(source))


def _contains_expected_processed_path(source: str) -> bool:
    """
    Verify that the expected processed file path appears in the source.
    This is a lightweight check; the script could construct the path
    programmatically, but the literal must be present somewhere.
    """
    return EXPECTED_PROCESSED_PATH in source


def check_lmm_script() -> None:
    """
    Perform the guard checks.

    * Fail if the LMM script references any raw data files.
    * Fail if the LMM script does not reference the expected processed file.
    """
    source = _read_lmm_source()

    if _contains_raw_path(source):
        sys.stderr.write(
            "Guard failure: LMM script attempts to load raw data files (data/raw/).\\n"
        )
        sys.exit(1)

    if not _contains_expected_processed_path(source):
        sys.stderr.write(
            f"Guard failure: LMM script does not reference the expected processed file "
            f"'{EXPECTED_PROCESSED_PATH}'.\\n"
        )
        sys.exit(1)

    # All checks passed
    print("Pre‑analysis guard passed: LMM script loads only processed data.")
    sys.exit(0)


def main():
    """CLI entry point."""
    check_lmm_script()


if __name__ == "__main__":
    main()
