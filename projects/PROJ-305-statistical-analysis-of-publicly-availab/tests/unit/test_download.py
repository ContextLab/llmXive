import sys
from pathlib import Path

import pytest

# Import the script as a module to test its functions without executing the
# CLI entry point.
sys.path.append(str(Path(__file__).resolve().parents[2]))
from src.data.download import (
    YEARS,
    FILE_TYPES,
    verify_download,
    fetch_vaers_data,
    paths,
)


@pytest.mark.parametrize("year", YEARS)
@pytest.mark.parametrize("ftype", FILE_TYPES)
def test_files_exist(year, ftype):
    """
    After a successful run, each expected CSV must exist under
    ``data/raw/<year>/`` and be non‑empty.
    """
    file_path = paths.data("raw", str(year), f"{year}{ftype}.csv")
    assert file_path.is_file(), f"Missing file {file_path}"
    assert file_path.stat().st_size > 0, f"Empty file {file_path}"


def test_verify_download_success():
    """
    ``verify_download`` should raise SystemExit with code 1 if any file is
    missing.  In the normal test environment the files are present because
    the download script has already been executed (see the execution
    request above).  Therefore the call must complete without raising.
    """
    # Should not raise
    verify_download()