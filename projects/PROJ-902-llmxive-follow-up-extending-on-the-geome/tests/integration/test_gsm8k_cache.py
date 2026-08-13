"""Integration test for GSM8K download caching.

This test verifies that running the GSM8K download script a second time
does not modify the cached dataset files. It does so by comparing the
SHA‑256 checksums of all files under ``data/gsm8k`` before and after the
second invocation.
"""

import shutil
from pathlib import Path

import pytest

# Import the download script's public API
from src.data.download_gsm8k import main, compute_sha256

# Project‑relative path to the GSM8K cache directory
GSM8K_DIR = Path(__file__).resolve().parents[2] / "data" / "gsm8k"


def _collect_file_hashes(directory: Path) -> dict[Path, str]:
    """Return a mapping of relative file paths to their SHA‑256 hashes."""
    hashes: dict[Path, str] = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(directory)
            hashes[rel_path] = compute_sha256(file_path)
    return hashes


@pytest.mark.integration
def test_gsm8k_download_uses_cache():
    """Run the download script twice and ensure the cache is hit.

    The test proceeds as follows:

    1. Remove any existing ``data/gsm8k`` directory to start from a clean
       state.
    2. Invoke ``src.data.download_gsm8k.main()`` – this should download the
       dataset and populate the cache.
    3. Record SHA‑256 hashes of every file in the cache.
    4. Invoke ``main()`` a second time – this call should hit the local
       cache and **not** rewrite any files.
    5. Record the hashes again and assert they are identical.
    """
    # Ensure a clean slate – delete the cache if it already exists.
    if GSM8K_DIR.exists():
        shutil.rmtree(GSM8K_DIR)

    # First download – this populates the cache.
    main()

    # Verify that the directory now exists and contains files.
    assert GSM8K_DIR.is_dir(), "GSM8K cache directory was not created."
    files_after_first = list(GSM8K_DIR.rglob("*"))
    assert any(p.is_file() for p in files_after_first), "No files were downloaded."

    # Record hashes after the first run.
    hashes_first = _collect_file_hashes(GSM8K_DIR)

    # Second download – should use the cache.
    main()

    # Record hashes after the second run.
    hashes_second = _collect_file_hashes(GSM8K_DIR)

    # The two hash dictionaries must be identical.
    assert hashes_first == hashes_second, (
        "Cache was not reused; file contents changed between runs."
    )