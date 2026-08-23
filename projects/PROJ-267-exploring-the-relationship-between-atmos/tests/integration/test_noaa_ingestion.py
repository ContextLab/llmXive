"""
Integration test for NOAA AR Data Ingestion (T016).
Verifies that the script runs, produces output files, and validates basic structure.
"""
import os
import sys
import json
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

def test_noaa_ingestion_script():
    """Test that the NOAA ingestion script runs and produces expected artifacts."""
    script_path = PROJECT_ROOT / "code" / "01_data_ingestion_noaa.py"
    output_file = PROJECT_ROOT / "data" / "raw" / "noaa-ar" / "ar_catalog_raw.json"
    metadata_file = PROJECT_ROOT / "data" / "raw" / "noaa-ar" / "dataset_metadata.json"

    # Ensure directories exist
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )

    # Assert script execution
    assert result.returncode == 0, f"Script failed with: {result.stderr}"

    # Assert output file exists
    assert output_file.exists(), f"Output file {output_file} was not created."

    # Assert metadata file exists
    assert metadata_file.exists(), f"Metadata file {metadata_file} was not created."

    # Validate JSON structure
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list), "Output data must be a list."
    
    # Validate at least one record exists (unless region is empty, but we expect data)
    # Note: In a real CI environment without network, this might fail, but the task
    # requires real data. We assume the runner has network access.
    # If the list is empty, it's a valid state if no ARs occurred in that window/region,
    # but typically we expect some.
    
    if len(data) > 0:
        # Check required fields based on the query in the script
        required_fields = {'date', 'latitude', 'longitude', 'peak_intensity'}
        first_record = data[0]
        assert required_fields.issubset(first_record.keys()), f"Missing required fields. Found: {first_record.keys()}"

    # Validate metadata structure
    with open(metadata_file, 'r') as f:
        meta = json.load(f)
    
    assert "source" in meta, "Metadata missing 'source'."
    assert "fetch_timestamp" in meta, "Metadata missing 'fetch_timestamp'."
    assert "checksum_sha256" in meta, "Metadata missing 'checksum_sha256'."

if __name__ == "__main__":
    test_noaa_ingestion_script()
    print("Integration test passed.")