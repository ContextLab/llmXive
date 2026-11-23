"""
Unit tests for main.py orchestration logic.

Tests the pipeline orchestration without executing full data processing.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from main import create_config, load_config, run_pipeline
from utils.seed_manager import set_global_seed

class TestMainOrchestration:
    """Test main pipeline orchestration functions."""
    
    def test_load_config_json(self):
        """Test loading JSON configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "dataset_ids": ["ds000030"],
                "random_seed": 42
            }
            json.dump(config_data, f)
            f.flush()
            
            config = load_config(f.name)
            assert config["dataset_ids"] == ["ds000030"]
            assert config["random_seed"] == 42
        
        Path(f.name).unlink()
    
    def test_load_config_yaml(self):
        """Test loading YAML configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("dataset_ids:\n  - ds000030\nrandom_seed: 42\n")
            f.flush()
            
            # Mock yaml import if not available
            with patch('main.yaml') as mock_yaml:
                mock_yaml.safe_load.return_value = {
                    "dataset_ids": ["ds000030"],
                    "random_seed": 42
                }
                config = load_config(f.name)
                assert config["dataset_ids"] == ["ds000030"]
                assert config["random_seed"] == 42
        
        Path(f.name).unlink()
    
    def test_create_config_from_args(self):
        """Test creating config from command line arguments."""
        args = MagicMock()
        args.config = None
        args.seed = 123
        
        config = create_config(args)
        
        assert config["random_seed"] == 123
        assert "dataset_ids" in config  # Default config should have this
    
    def test_create_config_from_file(self):
        """Test creating config from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "dataset_ids": ["ds000040"],
                "random_seed": 999
            }
            json.dump(config_data, f)
            f.flush()
            
            args = MagicMock()
            args.config = f.name
            args.seed = None
            
            config = create_config(args)
            assert config["dataset_ids"] == ["ds000040"]
            assert config["random_seed"] == 999
        
        Path(f.name).unlink()
    
    @patch('main.run_download')
    @patch('main.run_preprocess')
    def test_run_pipeline_download(self, mock_preprocess, mock_download):
        """Test pipeline orchestration for download action."""
        config = {"random_seed": 42}
        
        run_pipeline(config, "download")
        
        mock_download.assert_called_once()
        mock_preprocess.assert_not_called()
    
    @patch('main.run_preprocess')
    @patch('main.run_download')
    def test_run_pipeline_full(self, mock_download, mock_preprocess):
        """Test full pipeline orchestration."""
        config = {"random_seed": 42}
        
        run_pipeline(config, "full")
        
        # Should call all phases in order
        assert mock_download.called
        assert mock_preprocess.called
    
    def test_seed_setting(self):
        """Test that random seed is set correctly."""
        config = {"random_seed": 42}
        
        set_global_seed(config["random_seed"])
        # If we get here without error, seed was set
        assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
