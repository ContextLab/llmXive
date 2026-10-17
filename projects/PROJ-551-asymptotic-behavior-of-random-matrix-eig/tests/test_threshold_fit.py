import json
from pathlib import Path

def test_threshold_statistical_file_exists():
    """Simple sanity test that the statistical JSON file is produced."""
    out_path = Path("data/processed/threshold_statistical.json")
    assert out_path.exists(), "threshold_statistical.json was not created"

    # Verify that the JSON can be loaded and contains the expected top‑level keys
    with out_path.open() as f:
        data = json.load(f)

    assert "generated_at" in data, "Missing timestamp"
    assert "threshold_estimates" in data, "Missing threshold_estimates list"
    # At least one entry should be present after a successful run
    assert isinstance(data["threshold_estimates"], list)
    assert len(data["threshold_estimates"]) > 0, "No threshold estimates were written"