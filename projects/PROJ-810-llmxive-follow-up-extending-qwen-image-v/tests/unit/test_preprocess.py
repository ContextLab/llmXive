import sys
import json
from pathlib import Path

import pandas as pd
import pytest

# Ensure the project root is on the PYTHONPATH for imports.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from code.data import preprocess

@pytest.fixture
def sample_parquet(tmp_path):
    """
    Create a minimal but realistic parquet file that mimics the structure
    expected by ``preprocess.extract_ground_truth_labels``.
    """
    data = {
        "region_id": [1, 2, 3, 4],
        # Two text regions, two image regions.
        "modality": ["text", "image", "text", "image"],
        # Simple non‑overlapping boxes.
        "bbox": [
            [0, 0, 10, 10],
            [20, 0, 30, 10],
            [0, 20, 10, 30],
            [20, 20, 30, 30],
        ],
    }
    df = pd.DataFrame(data)
    parquet_path = tmp_path / "sample.parquet"
    df.to_parquet(parquet_path, index=False)
    return parquet_path

def test_t009_ground_truth_extraction(tmp_path, sample_parquet):
    """
    Run the T009 CLI flow against the synthetic sample parquet and verify:
    - ``ground_truth.parquet`` is created under ``data/interim``.
    - The checksum JSON file exists and contains a valid SHA‑256 hash.
    - All retained rows have ``modality`` in {text, image} and ``overlap_ratio`` ≤ 0.1.
    """
    # Place the sample parquet where the script expects it.
    target_input = Path("data/interim/sample.parquet")
    target_input.parent.mkdir(parents=True, exist_ok=True)
    target_input.write_bytes(sample_parquet.read_bytes())

    # Invoke the script's main function as if called from the command line.
    sys.argv = ["preprocess.py", "--task", "T009"]
    preprocess.main()

    # Verify the output parquet exists.
    output_parquet = Path("data/interim/ground_truth.parquet")
    assert output_parquet.exists(), "ground_truth.parquet was not created"

    # Load the output and perform basic validation.
    df_out = pd.read_parquet(output_parquet)
    assert not df_out.empty, "ground_truth.parquet should contain rows"
    assert set(df_out["modality"]).issubset({"text", "image"}), "Unexpected modality present"
    assert all(df_out["overlap_ratio"] <= 0.1), "Overlap ratio exceeds threshold"

    # Verify checksum file.
    checksum_file = Path("data/results/ground_truth_checksum.json")
    assert checksum_file.exists(), "Checksum JSON not created"
    with open(checksum_file, "r") as f:
        checksum_data = json.load(f)
    assert "sha256" in checksum_data, "Checksum JSON missing sha256 field"
    assert checksum_data["file"].endswith("ground_truth.parquet"), "Checksum file path mismatch"