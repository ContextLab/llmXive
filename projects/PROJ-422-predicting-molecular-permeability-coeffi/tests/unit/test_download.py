import pandas as pd
from pathlib import Path
from code.data.download import DataLoader, VERIFIED_DATASET_CONFIG

def test_download_creates_files(tmp_path):
    """
    End‑to‑end test that the DataLoader writes the raw CSV and checksum
    files and that the required target column is present.
    """
    # Use a temporary directory for output
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True)

    # Override paths to point to the temporary location
    # The llmxive toolkit's `paths` helper cannot be monkey‑patched easily,
    # so we pass an explicit save_path.
    save_path = raw_dir / "permeability_data.csv"

    loader = DataLoader(config=VERIFIED_DATASET_CONFIG)
    df = loader.process(save_path=save_path)

    # Verify CSV exists and contains the expected columns
    assert save_path.is_file()
    loaded = pd.read_csv(save_path)
    for col in VERIFIED_DATASET_CONFIG["expected_columns"]:
        assert col in loaded.columns

    # Verify checksum file
    checksum_path = raw_dir / "checksums.json"
    assert checksum_path.is_file()
    checksums = pd.read_json(checksum_path, typ="series")
    assert save_path.name in checksums.index
    # Simple sanity: checksum should be a 64‑character hex string
    assert len(checksums[save_path.name]) == 64