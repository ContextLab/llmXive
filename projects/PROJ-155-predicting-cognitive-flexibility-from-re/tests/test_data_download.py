"""
Unit test for the data download module (T002).
The test checks that:
1. The download function creates the expected directory layout.
2. A checksum file is written.
3. The manifest records exactly one subject.
"""
import os
import json

from code.data.download import download_hcp_subset
from code.data.paths import get_raw_path, ensure_dir


def test_download_creates_expected_structure(tmp_path, monkeypatch):
    """
    Run the download in a temporary directory and verify the artefacts.
    """
    # Redirect the project's root to the temporary directory for isolation.
    # ``paths.root`` is a Path object defined by llmxive_toolkit; we monkeypatch it.
    import llmxive_toolkit
    monkeypatch.setattr(llmxive_toolkit.paths, "root", tmp_path)

    # Ensure the raw data directory points inside the temporary root.
    raw_root = get_raw_path() / "HCP_1200"
    ensure_dir(raw_root)

    # Execute the download.
    result_path = download_hcp_subset()

    # 1️⃣  Verify the function returned the correct path.
    assert result_path == raw_root

    # 2️⃣  Check that the subject folder exists with the expected files.
    subj_dir = raw_root / "sub-0001"
    assert subj_dir.is_dir()
    assert (subj_dir / "sub-0001_REST.nii.gz").exists()
    assert (subj_dir / "confounds.tsv").exists()

    # 3️⃣  Verify phenotypic / behavioural CSVs.
    assert (raw_root / "phenotypic.csv").exists()
    assert (raw_root / "behavioral_scores.csv").exists()

    # 4️⃣  Manifest must contain exactly one subject.
    manifest_path = raw_root / "manifest.json"
    assert manifest_path.is_file()
    with manifest_path.open() as f:
        manifest = json.load(f)
    assert manifest["total_count"] == 1
    assert manifest["subjects"] == ["sub-0001"]

    # 5️⃣  Checksums file must exist and contain at least one line.
    checksums_path = raw_root.parent.parent / "checksums.txt"
    # ``paths.data`` creates ``<project>/data``; the checksum file lives there.
    assert checksums_path.is_file()
    with checksums_path.open() as f:
        lines = f.readlines()
    assert len(lines) > 0