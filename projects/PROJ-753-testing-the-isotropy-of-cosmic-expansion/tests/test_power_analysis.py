"""Tests for the power analysis script.

The test ensures that the required output files are created and contain
the expected top‑level keys.
"""
import json
from pathlib import Path

def test_power_analysis_outputs():
    metadata_path = Path("data/raw/metadata.json")
    power_path = Path("data/processed/power_analysis.json")

    assert metadata_path.is_file(), f"Missing {metadata_path}"
    assert power_path.is_file(), f"Missing {power_path}"

    # Verify required fields in metadata
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    required_meta = {"dataset_version", "source_url", "sha256"}
    assert required_meta.issubset(meta), "metadata.json missing required fields"

    # Verify required fields in power analysis result
    with open(power_path, "r", encoding="utf-8") as f:
        power = json.load(f)
    required_power = {
        "analytic_min_detectable_dipole_mag",
        "empirical_power",
        "min_detectable_dipole_mag",
        "num_supernovae",
    }
    assert required_power.issubset(power), "power_analysis.json missing required fields"