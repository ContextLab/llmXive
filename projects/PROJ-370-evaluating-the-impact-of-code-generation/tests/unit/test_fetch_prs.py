import json
from pathlib import Path

from code.config.settings import get_paths
from src.extraction.fetch_prs import main as fetch_prs_main

def test_fetch_prs_creates_output_files(tmp_path, monkeypatch):
    """
    Basic sanity test that the fetch_prs script creates the expected
    output files. This test does NOT require a real GitHub token; it
    runs the script with a very small ``max_prs`` value (1) by monkey‑
    patching the hyper‑parameters.
    """
    # Patch the hyper‑parameters to fetch at most one PR per repo
    from code.config import settings as cfg
    cfg.HYPERPARAMS["max_prs"] = 1

    # Ensure the script writes into a temporary data directory
    paths = get_paths()
    raw_dir = Path(paths["data_raw"])
    # Redirect to the temporary directory for the duration of the test
    monkeypatch.setattr(cfg, "PATHS", {
        **cfg.PATHS,
        "data_raw": tmp_path / "data_raw",
    })
    # Run the script
    fetch_prs_main()

    # Verify files exist
    prs_file = tmp_path / "data_raw" / "prs.json"
    checksums_file = tmp_path / "data_raw" / "checksums.json"
    assert prs_file.is_file(), "prs.json was not created"
    assert checksums_file.is_file(), "checksums.json was not created"

    # Load and perform minimal sanity checks
    prs = json.loads(prs_file.read_text())
    checksums = json.loads(checksums_file.read_text())
    assert isinstance(prs, list)
    assert isinstance(checksums, dict)
    # If real data was fetched, lengths should match
    if prs:
        assert len(prs) == len(checksums)