import json
from pathlib import Path

from llmxive_toolkit import paths

def test_power_analysis_outputs():
    """
    Verify that the power analysis script creates the expected JSON files
    and that the JSON contains the required keys with finite numeric values.
    """
    # Run the script (the test runner will have executed the script already
    # because it is marked with `execute: true` in the artifact above).
    power_path = paths.data("processed", "power_analysis.json")
    metadata_path = paths.data("raw", "metadata.json")

    # Both files must exist
    assert power_path.is_file(), f"{power_path} does not exist"
    assert metadata_path.is_file(), f"{metadata_path} does not exist"

    # Load and validate JSON structure
    with open(power_path, "r", encoding="utf-8") as f:
        power_json = json.load(f)

    required_keys = {
        "dataset_version",
        "source_url",
        "sha256",
        "analytic_min_detectable_dipole_mag",
        "empirical_power",
        "min_detectable_dipole_mag",
    }
    missing = required_keys - power_json.keys()
    assert not missing, f"Missing keys in power_analysis.json: {missing}"

    # Ensure numeric fields are finite
    for key in [
        "analytic_min_detectable_dipole_mag",
        "empirical_power",
        "min_detectable_dipole_mag",
    ]:
        value = power_json[key]
        assert isinstance(value, (int, float)), f"{key} is not numeric"
        assert not (value != value), f"{key} is NaN"
        assert value != float("inf"), f"{key} is infinite"

    # Verify empirical power is within a reasonable range (0–1)
    assert 0.0 <= power_json["empirical_power"] <= 1.0

    # Load metadata and cross‑check checksum
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta_json = json.load(f)
    assert meta_json["sha256"] == power_json["sha256"], "Checksum mismatch between metadata and power analysis"

# The test module is automatically discovered by pytest. No additional
# test runner code is required.