"""
Tests for Task T016d: Post-Augmentation Save
"""
import os
import sys
import json
import pandas as pd
import pytest
from pathlib import Path
import hashlib

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils import get_project_paths

paths = get_project_paths()

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

class TestT016dSaveAugmented:
    """Tests for the T016d save augmented dataset functionality."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Ensure required directories exist
        paths["processed"].mkdir(parents=True, exist_ok=True)
        paths["state"].mkdir(parents=True, exist_ok=True)
        yield
        # Cleanup after test if needed (optional)

    def test_save_augmented_dataset_exists(self):
        """Test that final_augmented_dataset.csv is created after running T016d."""
        # This test assumes T016d has been run. 
        # In a real CI/CD, this would be run after the script execution.
        output_path = paths["processed"] / "final_augmented_dataset.csv"
        assert output_path.exists(), f"Output file {output_path} was not created"

    def test_save_augmented_dataset_has_content(self):
        """Test that the saved dataset is not empty."""
        output_path = paths["processed"] / "final_augmented_dataset.csv"
        if not output_path.exists():
            pytest.skip("Output file does not exist yet (run T016d first)")
        
        df = pd.read_csv(output_path)
        assert len(df) > 0, "Saved dataset is empty"

    def test_save_augmented_dataset_manifest_exists(self):
        """Test that the manifest file is created."""
        manifest_path = paths["processed"] / "final_augmented_dataset_manifest.json"
        assert manifest_path.exists(), f"Manifest file {manifest_path} was not created"

    def test_save_augmented_dataset_manifest_valid(self):
        """Test that the manifest file contains required fields."""
        manifest_path = paths["processed"] / "final_augmented_dataset_manifest.json"
        if not manifest_path.exists():
            pytest.skip("Manifest file does not exist yet (run T016d first)")
        
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        required_keys = ["file", "checksum_algorithm", "checksum", "record_count", "timestamp"]
        for key in required_keys:
            assert key in manifest, f"Manifest missing required key: {key}"
        
        assert manifest["checksum_algorithm"] == "SHA256"
        assert isinstance(manifest["record_count"], int)
        assert manifest["record_count"] > 0

    def test_save_augmented_dataset_checksum_matches(self):
        """Test that the checksum in the manifest matches the actual file checksum."""
        output_path = paths["processed"] / "final_augmented_dataset.csv"
        manifest_path = paths["processed"] / "final_augmented_dataset_manifest.json"
        
        if not output_path.exists() or not manifest_path.exists():
            pytest.skip("Required files do not exist yet (run T016d first)")
        
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        actual_checksum = compute_file_checksum(output_path)
        manifest_checksum = manifest["checksum"]
        
        assert actual_checksum == manifest_checksum, (
            f"Checksum mismatch: actual={actual_checksum}, manifest={manifest_checksum}"
        )

    def test_save_augmented_dataset_schema(self):
        """Test that the dataset has the expected columns."""
        output_path = paths["processed"] / "final_augmented_dataset.csv"
        if not output_path.exists():
            pytest.skip("Output file does not exist yet (run T016d first)")
        
        df = pd.read_csv(output_path)
        
        # At minimum, we expect SMILES and degradation pathway columns
        # The exact schema depends on the preprocessing, but we check for key fields
        expected_columns = ["smiles", "degradation_pathway"]
        for col in expected_columns:
            assert col in df.columns, f"Missing expected column: {col}"