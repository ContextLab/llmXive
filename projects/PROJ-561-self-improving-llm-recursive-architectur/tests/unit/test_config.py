import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from config import (
    _parse_research_md_for_param_limit,
    get_config,
    set_config,
    get_max_param_increase_percent,
    SafetyConstraints,
    Config,
    Hyperparameters,
    PathConfig
)

class TestConfigDefaults(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.research_md_path = os.path.join(self.test_dir, "research.md")
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        # Reset config to force re-initialization
        import config
        config._config = None

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
        import config
        config._config = None

    def test_parse_research_md_missing(self):
        """Test parsing when research.md does not exist."""
        result = _parse_research_md_for_param_limit(os.path.join(self.test_dir, "nonexistent.md"))
        self.assertIsNone(result)

    def test_parse_research_md_no_methodology(self):
        """Test parsing when research.md exists but lacks methodology section."""
        with open(self.research_md_path, 'w') as f:
            f.write("Some random text\nNo methodology here")
        
        result = _parse_research_md_for_param_limit(self.research_md_path)
        self.assertIsNone(result)

    def test_parse_research_md_deferred(self):
        """Test parsing when value is marked as deferred."""
        content = """
        ## Methodology for Parameter Limit
        The limit is [deferred] until analysis.
        """
        with open(self.research_md_path, 'w') as f:
            f.write(content)
        
        result = _parse_research_md_for_param_limit(self.research_md_path)
        self.assertIsNone(result)

    def test_parse_research_md_valid_ratio(self):
        """Test parsing when a valid ratio is defined."""
        content = """
        ## Methodology for Parameter Limit
        We determined the MAX_PARAM_INCREASE_RATIO is 0.25.
        """
        with open(self.research_md_path, 'w') as f:
            f.write(content)
        
        result = _parse_research_md_for_param_limit(self.research_md_path)
        self.assertEqual(result, 0.25)

    def test_parse_research_md_ratio_variations(self):
        """Test parsing various ratio formats."""
        test_cases = [
            ("ratio: 0.15", 0.15),
            ("limit: 0.30", 0.30),
            ("max_param_increase: 0.20", 0.20),
            ("increase ratio 0.40", 0.40),
        ]
        
        for text, expected in test_cases:
            content = f"## Methodology for Parameter Limit\n{text}"
            with open(self.research_md_path, 'w') as f:
                f.write(content)
            
            result = _parse_research_md_for_param_limit(self.research_md_path)
            self.assertEqual(result, expected, f"Failed for text: {text}")

    def test_config_uses_research_value(self):
        """Test that get_config picks up the value from research.md."""
        content = """
        ## Methodology for Parameter Limit
        The defined ratio is 0.18.
        """
        with open(self.research_md_path, 'w') as f:
            f.write(content)
        
        # Mock the paths to point to our test dir
        with patch('config.PathConfig') as MockPathConfig:
            mock_paths = MagicMock()
            mock_paths.research_md = self.research_md_path
            MockPathConfig.return_value = mock_paths
            
            cfg = get_config()
            self.assertIsNotNone(cfg.safety.max_param_increase_ratio)
            self.assertEqual(cfg.safety.max_param_increase_ratio, 0.18)

    def test_config_deferred_when_missing(self):
        """Test that get_config sets None when research.md is missing or undefined."""
        # Ensure research.md does not exist in test dir
        if os.path.exists(self.research_md_path):
            os.remove(self.research_md_path)
        
        with patch('config.PathConfig') as MockPathConfig:
            mock_paths = MagicMock()
            mock_paths.research_md = self.research_md_path # Points to non-existent file
            MockPathConfig.return_value = mock_paths
            
            cfg = get_config()
            self.assertIsNone(cfg.safety.max_param_increase_ratio)

    def test_hyperparameters_defaults(self):
        """Test default hyperparameter values."""
        cfg = get_config()
        self.assertEqual(cfg.hyperparams.lr, 5e-5)
        self.assertEqual(cfg.hyperparams.batch_size, 4)
        self.assertEqual(cfg.hyperparams.seed, 42)

    def test_getters(self):
        """Test that helper getters return correct values."""
        cfg = get_config()
        self.assertEqual(get_max_param_increase_percent(), cfg.safety.max_param_increase_ratio)
        # Reset seed for test
        import config
        config._config = None
        with open(self.research_md_path, 'w') as f:
            f.write("## Methodology for Parameter Limit\nratio: 0.10")
        with patch('config.PathConfig') as MockPathConfig:
            mock_paths = MagicMock()
            mock_paths.research_md = self.research_md_path
            MockPathConfig.return_value = mock_paths
            cfg = get_config()
            self.assertEqual(get_max_param_increase_percent(), 0.10)

if __name__ == '__main__':
    unittest.main()