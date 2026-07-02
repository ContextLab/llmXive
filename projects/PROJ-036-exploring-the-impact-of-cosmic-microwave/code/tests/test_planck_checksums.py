"""
Tests for T012b: Planck checksums configuration validation.

These tests verify that the planck_checksums.yaml file contains
the required structure and valid checksums for Planck PR3 maps.
"""
import pytest
import yaml
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestPlanckChecksums:
    """Test cases for Planck checksums configuration."""
    
    @pytest.fixture
    def checksums_file(self):
        """Load the planck_checksums.yaml file."""
        config_dir = Path(__file__).parent.parent.parent / "config"
        checksums_file = config_dir / "planck_checksums.yaml"
        
        if not checksums_file.exists():
            pytest.skip("planck_checksums.yaml not found - task T012b not completed")
        
        with open(checksums_file, 'r') as f:
            return yaml.safe_load(f)
    
    def test_file_structure(self, checksums_file):
        """Test that the configuration file has the required structure."""
        assert "description" in checksums_file, "Missing 'description' field"
        assert "source" in checksums_file, "Missing 'source' field"
        assert "last_updated" in checksums_file, "Missing 'last_updated' field"
        assert "maps" in checksums_file, "Missing 'maps' field"
        assert isinstance(checksums_file["maps"], dict), "'maps' must be a dictionary"
    
    def test_required_maps_present(self, checksums_file):
        """Test that both Commander and SMICA maps are present."""
        maps = checksums_file["maps"]
        assert "commander" in maps, "Missing 'commander' map configuration"
        assert "smica" in maps, "Missing 'smica' map configuration"
    
    def test_commander_map_fields(self, checksums_file):
        """Test that Commander map has all required fields."""
        commander = checksums_file["maps"]["commander"]
        
        required_fields = ["name", "sha256", "md5", "source", "url", "description", "nside"]
        for field in required_fields:
            assert field in commander, f"Missing '{field}' field in commander map"
    
    def test_smica_map_fields(self, checksums_file):
        """Test that SMICA map has all required fields."""
        smica = checksums_file["maps"]["smica"]
        
        required_fields = ["name", "sha256", "md5", "source", "url", "description", "nside"]
        for field in required_fields:
            assert field in smica, f"Missing '{field}' field in smica map"
    
    def test_checksum_format(self, checksums_file):
        """Test that checksums are in the correct format."""
        commander = checksums_file["maps"]["commander"]
        smica = checksums_file["maps"]["smica"]
        
        # SHA256 should be 64 hex characters
        assert len(commander["sha256"]) == 64, "Commander SHA256 should be 64 characters"
        assert len(smica["sha256"]) == 64, "SMICA SHA256 should be 64 characters"
        
        # MD5 should be 32 hex characters
        assert len(commander["md5"]) == 32, "Commander MD5 should be 32 characters"
        assert len(smica["md5"]) == 32, "SMICA MD5 should be 32 characters"
        
        # Verify they are valid hex strings
        try:
            int(commander["sha256"], 16)
            int(smica["sha256"], 16)
            int(commander["md5"], 16)
            int(smica["md5"], 16)
        except ValueError:
            pytest.fail("Checksums are not valid hexadecimal strings")
    
    def test_nside_values(self, checksums_file):
        """Test that NSIDE values are valid."""
        commander = checksums_file["maps"]["commander"]
        smica = checksums_file["maps"]["smica"]
        
        assert commander["nside"] >= 256, "Commander NSIDE must be >= 256"
        assert smica["nside"] >= 256, "SMICA NSIDE must be >= 256"
        
        # NSIDE should be a power of 2
        assert commander["nside"] & (commander["nside"] - 1) == 0, "Commander NSIDE must be power of 2"
        assert smica["nside"] & (smica["nside"] - 1) == 0, "SMICA NSIDE must be power of 2"
    
    def test_file_names(self, checksums_file):
        """Test that file names match expected Planck PR3 naming convention."""
        commander = checksums_file["maps"]["commander"]
        smica = checksums_file["maps"]["smica"]
        
        assert commander["name"].endswith(".fits"), "Commander file must be FITS format"
        assert smica["name"].endswith(".fits"), "SMICA file must be FITS format"
        assert "commander" in commander["name"].lower(), "Commander file name should contain 'commander'"
        assert "smica" in smica["name"].lower(), "SMICA file name should contain 'smica'"
        assert "R3.00" in commander["name"], "Commander file should be from Release 3"
        assert "R3.00" in smica["name"], "SMICA file should be from Release 3"
    
    def test_urls_valid(self, checksums_file):
        """Test that URLs are valid ESA PLA URLs."""
        commander = checksums_file["maps"]["commander"]
        smica = checksums_file["maps"]["smica"]
        
        assert commander["url"].startswith("https://pla.esac.esa.int/"), "Commander URL must be from ESA PLA"
        assert smica["url"].startswith("https://pla.esac.esa.int/"), "SMICA URL must be from ESA PLA"