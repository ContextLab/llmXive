import json
from pathlib import Path

def test_dataset_and_stats_exist():
    """Verify that the ground‑truth generation script produced the required artefacts."""
    parquet_path = Path("data/processed/training_sample.parquet")
    stats_path = Path("data/processed/dataset_stats.json")
    assert parquet_path.is_file(), f"Parquet file missing: {parquet_path}"
    assert stats_path.is_file(), f"Stats JSON missing: {stats_path}"

    # Basic sanity check on the JSON structure
    with open(stats_path, "r", encoding="utf-8") as f:
        stats = json.load(f)
    assert "per_level_statistics" in stats, "Missing per_level_statistics key"
    assert isinstance(stats["per_level_statistics"], dict), "per_level_statistics should be a dict"