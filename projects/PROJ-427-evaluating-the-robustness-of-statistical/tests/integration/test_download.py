"""
Integration test for the download pipeline.

The test patches ``download.load_config`` so that only a tiny, publicly‑available
CSV file (the Iris dataset from the seaborn repository) is processed.  This keeps
the test fast, deterministic and independent of the large list of UCI URLs that
the full pipeline normally handles.

The test verifies that:
  1. The pipeline runs without raising an exception.
  2. At least one cleaned CSV file is written to ``data/raw/cleaned``.
  3. A checksum record file ``state/dataset_checksums.yaml`` is created and
     contains an entry for the downloaded file.
  4. The diversity verification step succeeds (i.e. the dataset is recognised as
     either numerical‑only, categorical‑only or mixed and the required minimum
     counts are met).
"""

import pathlib
import yaml

import pytest

# The modules live at the repository root (e.g. ``code/download.py`` is importable as ``download``)
from download import main as download_main
from verify_diversity import verify_dataset_diversity


@pytest.fixture(scope="function")
def clean_environment(tmp_path, monkeypatch):
    """
    Ensure a clean state before each test run.

    The fixture does not delete the real ``data/`` and ``state/`` directories
    because the production code writes to those fixed paths.  It only patches
    the configuration loader so that the pipeline processes a single tiny file.
    """
    # Minimal configuration containing a single, small CSV file.
    sample_config = {
        "datasets": [
            {
                "name": "iris",
                "url": "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv",
                "type": "numerical",
            }
        ]
    }

    # Patch the ``load_config`` function used by ``download`` to return our sample config.
    monkeypatch.setattr("download.load_config", lambda: sample_config)

    # Ensure any previously generated artefacts are removed so the test starts fresh.
    raw_dir = pathlib.Path("data/raw")
    cleaned_dir = raw_dir / "cleaned"
    checksum_file = pathlib.Path("state/dataset_checksums.yaml")

    for p in (raw_dir, cleaned_dir):
        if p.is_dir():
            for child in p.iterdir():
                child.unlink()
    if checksum_file.is_file():
        checksum_file.unlink()

    # Yield control back to the test.
    yield

    # Cleanup after the test – remove the files we just created.
    for p in (raw_dir, cleaned_dir):
        if p.is_dir():
            for child in p.iterdir():
                child.unlink()
    if checksum_file.is_file():
        checksum_file.unlink()


def test_download_pipeline_runs_and_produces_outputs(clean_environment):
    """
    Run the download pipeline and assert that the expected artefacts exist.
    """
    # Execute the full download‑clean‑checksum pipeline.
    download_main()

    # 1. At least one cleaned CSV file should be present.
    cleaned_dir = pathlib.Path("data/raw/cleaned")
    cleaned_csv_files = list(cleaned_dir.glob("*.csv"))
    assert cleaned_csv_files, "No cleaned CSV files were produced in data/raw/cleaned"

    # 2. The checksum record file must exist and contain an entry for the downloaded file.
    checksum_path = pathlib.Path("state/dataset_checksums.yaml")
    assert checksum_path.is_file(), "Checksum file state/dataset_checksums.yaml was not created"

    with checksum_path.open("r") as f:
        checksums = yaml.safe_load(f) or {}

    # The dictionary should map a filename (or a dataset identifier) to a SHA‑256 hash.
    assert isinstance(checksums, dict) and checksums, "Checksum file is empty or malformed"

    # The entry for the Iris dataset should be present (key may be the original filename).
    # We check that *some* key ends with 'iris.csv' and that its value looks like a SHA‑256 hash.
    matching_keys = [k for k in checksums.keys() if "iris" in k.lower() and k.lower().endswith(".csv")]
    assert matching_keys, "Checksum entry for the Iris dataset not found"
    for key in matching_keys:
        hash_val = checksums[key]
        assert isinstance(hash_val, str) and len(hash_val) == 64, f"Invalid SHA‑256 hash for {key}"

    # 3. Verify dataset diversity constraints are satisfied.
    # The function returns ``True`` on success; otherwise it raises or returns ``False``.
    diversity_ok = verify_dataset_diversity()
    assert diversity_ok, "Dataset diversity verification failed"