import json
from pathlib import Path

import pytest
from llmxive_toolkit import paths

# Import the script's main function
from code.download_pantheon import main as download_main

@pytest.fixture
def clean_raw_dir(tmp_path):
    """Create a temporary raw data directory and point the paths helper to it."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    # Monkey‑patch the llmxive_toolkit.paths.data function to use the temp dir
    original_data = paths.data

    def temp_data(*parts):
        return raw_dir.joinpath(*parts)

    paths.data = temp_data
    yield raw_dir
    # Restore original function after test
    paths.data = original_data

def test_download_and_metadata_creation(clean_raw_dir, caplog):
    """
    End‑to‑end test that the download script:
    * Retrieves the real Pantheon+ FITS file.
    * Writes the file to data/raw/pantheon_plus.fits.
    * Generates a valid metadata.json with required fields.
    * Updates the project state YAML with the checksum.
    """
    # Run the script (no arguments -> default URL)
    download_main()

    fits_path = clean_raw_dir / "pantheon_plus.fits"
    metadata_path = clean_raw_dir / "metadata.json"
    state_path = Path(__file__).parents[3] / "state" / "projects" / "PROJ-753-testing-the-isotropy-of-cosmic-expansion.yaml"

    # Verify files exist
    assert fits_path.is_file(), "FITS file was not created"
    assert metadata_path.is_file(), "metadata.json was not created"
    assert state_path.is_file(), "State YAML was not created"

    # Verify metadata content
    metadata = json.loads(metadata_path.read_text())
    required_keys = {"dataset_version", "source_url", "sha256", "citation_verified"}
    assert required_keys.issubset(metadata.keys()), "Missing keys in metadata.json"
    assert metadata["citation_verified"] is False

    # Verify checksum matches the file's actual hash
    from code.download_pantheon import compute_sha256
    actual_hash = compute_sha256(fits_path)
    assert metadata["sha256"] == actual_hash, "Checksum mismatch in metadata"

    # Verify state YAML contains the same checksum
    import yaml
    state = yaml.safe_load(state_path.read_text())
    assert state.get("artifact_hashes", {}).get("pantheon_plus.fits") == actual_hash

    # Ensure the logger reported success
    assert any("Pantheon+ dataset download and verification completed successfully." in rec.message for rec in caplog.records)