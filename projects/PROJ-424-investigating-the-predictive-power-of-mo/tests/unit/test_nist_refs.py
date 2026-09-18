"""
Unit tests for NIST reference data generation and validation.
"""
import json
import os
import sys
from pathlib import Path
import pytest

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from data.raw.generate_nist_refs import generate_nist_refs, init_manifest, compute_file_hash
from utils.data_fetcher import validate_nist_refs, DataValidationError

PROJECT_ROOT = code_dir.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
NIST_REFS_PATH = DATA_RAW_DIR / "nist_refs.json"
MANIFEST_PATH = DATA_RAW_DIR / "manifest.json"

class TestNistRefsGeneration:
    """Tests for NIST reference file generation."""

    def test_generate_nist_refs_creates_file(self):
        """Test that generate_nist_refs creates the expected file."""
        # Remove file if it exists to test creation
        if NIST_REFS_PATH.exists():
            NIST_REFS_PATH.unlink()
        
        result_path = generate_nist_refs()
        
        assert result_path.exists()
        assert result_path == NIST_REFS_PATH
        
        # Verify it's valid JSON
        with open(result_path, "r") as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "references" in data
        assert "water" in data["references"]
        assert "ethanol" in data["references"]
        assert "acetone" in data["references"]

    def test_nist_refs_has_required_fields(self):
        """Test that generated refs have all required fields."""
        if not NIST_REFS_PATH.exists():
            generate_nist_refs()
        
        with open(NIST_REFS_PATH, "r") as f:
            data = json.load(f)
        
        for solvent in ["water", "ethanol", "acetone"]:
            ref = data["references"][solvent]
            assert "solvent" in ref
            assert "diffusion_coefficient" in ref
            assert "nist_accession_id" in ref
            assert "url" in ref
            assert ref["diffusion_coefficient"] > 0
            assert ref["nist_accession_id"].startswith("TRC-REF-")

    def test_manifest_generation(self):
        """Test that init_manifest creates a valid manifest."""
        # Ensure refs exist first
        if not NIST_REFS_PATH.exists():
            generate_nist_refs()
        
        if MANIFEST_PATH.exists():
            MANIFEST_PATH.unlink()
        
        result_path = init_manifest()
        
        assert result_path.exists()
        assert result_path == MANIFEST_PATH
        
        with open(result_path, "r") as f:
            manifest = json.load(f)
        
        assert "files" in manifest
        assert "nist_refs.json" in manifest["files"]
        assert "sha256" in manifest["files"]["nist_refs.json"]
        assert len(manifest["files"]["nist_refs.json"]["sha256"]) == 64

    def test_checksum_consistency(self):
        """Test that manifest checksum matches actual file hash."""
        if not NIST_REFS_PATH.exists():
            generate_nist_refs()
        
        if not MANIFEST_PATH.exists():
            init_manifest()
        
        # Calculate actual hash
        actual_hash = compute_file_hash(NIST_REFS_PATH)
        
        # Get manifest hash
        with open(MANIFEST_PATH, "r") as f:
            manifest = json.load(f)
        
        manifest_hash = manifest["files"]["nist_refs.json"]["sha256"]
        
        assert actual_hash == manifest_hash

class TestNistRefsValidation:
    """Tests for NIST reference validation."""

    def test_validate_existing_refs(self):
        """Test validation passes for existing, valid refs."""
        if not NIST_REFS_PATH.exists():
            generate_nist_refs()
        
        if not MANIFEST_PATH.exists():
            init_manifest()
        
        # Should not raise
        validate_nist_refs()

    def test_validate_missing_file_raises(self):
        """Test validation raises when file is missing."""
        # Temporarily rename file
        if NIST_REFS_PATH.exists():
            temp_path = NIST_REFS_PATH.with_suffix(".json.bak")
            NIST_REFS_PATH.rename(temp_path)
            
            try:
                with pytest.raises(DataValidationError):
                    validate_nist_refs()
            finally:
                # Restore file
                temp_path.rename(NIST_REFS_PATH)

    def test_validate_checksum_mismatch_raises(self):
        """Test validation raises when checksum doesn't match."""
        if not NIST_REFS_PATH.exists():
            generate_nist_refs()
        
        if not MANIFEST_PATH.exists():
            init_manifest()
        
        # Corrupt manifest hash
        with open(MANIFEST_PATH, "r") as f:
            manifest = json.load(f)
        
        original_hash = manifest["files"]["nist_refs.json"]["sha256"]
        manifest["files"]["nist_refs.json"]["sha256"] = "0" * 64
        
        with open(MANIFEST_PATH, "w") as f:
            json.dump(manifest, f)
        
        try:
            with pytest.raises(DataValidationError):
                validate_nist_refs()
        finally:
            # Restore manifest
            manifest["files"]["nist_refs.json"]["sha256"] = original_hash
            with open(MANIFEST_PATH, "w") as f:
                json.dump(manifest, f)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])