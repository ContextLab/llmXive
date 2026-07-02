"""
Tests for the configuration management module.

These tests verify that configuration files are loaded correctly
and that the merging logic works as expected.
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
import yaml

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_manager import (
    load_yaml_config,
    load_lambdacdm_config,
    load_anomaly_config,
    get_combined_config,
    ensure_config_exists,
    CONFIG_DIR
)

class TestConfigLoading:
    """Test basic configuration loading functionality."""
    
    def setup_method(self):
        """Create a temporary config directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_dir = Path(self.temp_dir) / "config"
        self.test_config_dir.mkdir()
        
        # Create test config files
        self.lcdm_path = self.test_config_dir / "lambdacdm.yaml"
        self.anomaly_path = self.test_config_dir / "anomaly.yaml"
        
        self.lcdm_content = {
            "cosmology": {
                "H0": 70.0,
                "Omega_m": 0.3
            },
            "simulation": {
                "box_size": 100.0
            }
        }
        
        self.anomaly_content = {
            "anomaly_type": "test",
            "cold_spot": {
                "phase_modulation": 0.1
            }
        }
        
        with open(self.lcdm_path, 'w') as f:
            yaml.dump(self.lcdm_content, f)
            
        with open(self.anomaly_path, 'w') as f:
            yaml.dump(self.anomaly_content, f)
            
        # Temporarily override CONFIG_DIR
        self.original_config_dir = CONFIG_DIR
        import utils.config_manager as cm
        cm.CONFIG_DIR = self.test_config_dir
    
    def teardown_method(self):
        """Clean up temporary directory."""
        import utils.config_manager as cm
        cm.CONFIG_DIR = self.original_config_dir
        shutil.rmtree(self.temp_dir)
    
    def test_load_yaml_config_success(self):
        """Test successful loading of a YAML file."""
        result = load_yaml_config("lambdacdm.yaml")
        assert result == self.lcdm_content
        assert result["cosmology"]["H0"] == 70.0
    
    def test_load_yaml_config_missing_not_required(self):
        """Test loading a missing file when required=False."""
        result = load_yaml_config("nonexistent.yaml", required=False)
        assert result == {}
    
    def test_load_yaml_config_missing_required(self):
        """Test that missing required file raises error."""
        with pytest.raises(FileNotFoundError):
            load_yaml_config("nonexistent.yaml", required=True)
    
    def test_load_lambdacdm_config(self):
        """Test loading LambdaCDM config specifically."""
        result = load_lambdacdm_config()
        assert "cosmology" in result
        assert result["cosmology"]["H0"] == 70.0
    
    def test_load_anomaly_config(self):
        """Test loading anomaly config specifically."""
        result = load_anomaly_config()
        assert "anomaly_type" in result
        assert result["anomaly_type"] == "test"
    
    def test_get_combined_config(self):
        """Test merging of configurations."""
        combined = get_combined_config()
        
        # Should have keys from both
        assert "cosmology" in combined
        assert "anomaly_type" in combined
        
        # Anomaly values should not override unrelated LambdaCDM values
        assert combined["cosmology"]["H0"] == 70.0
        assert combined["anomaly_type"] == "test"
        
        # Nested merge test
        assert "cold_spot" in combined
        assert combined["cold_spot"]["phase_modulation"] == 0.1
    
    def test_ensure_config_exists_true(self):
        """Test ensure_config_exists when files exist."""
        assert ensure_config_exists() is True
    
    def test_ensure_config_exists_false(self):
        """Test ensure_config_exists when files missing."""
        # Remove one file
        self.lcdm_path.unlink()
        assert ensure_config_exists() is False

class TestConfigIntegration:
    """Integration tests with real project config files if they exist."""
    
    def test_real_config_structure(self):
        """Test that real config files have expected structure."""
        if not (Path("config") / "lambdacdm.yaml").exists():
            pytest.skip("Real config files not available in test environment")
        
        lcdm = load_lambdacdm_config()
        anomaly = load_anomaly_config()
        
        # Verify LambdaCDM has required keys
        assert "cosmology" in lcdm
        assert "simulation" in lcdm
        
        # Verify anomaly has required keys
        assert "anomaly_type" in anomaly
        assert "cold_spot" in anomaly
        
        # Verify combined config works
        combined = get_combined_config()
        assert len(combined) > 0
        
        # Verify specific anomaly parameters
        assert "phase_modulation" in combined["cold_spot"]
        assert isinstance(combined["cold_spot"]["phase_modulation"], float)
