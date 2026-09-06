"""
Unit tests for the utils/config.py module.
"""
import os
import sys
import unittest
from pathlib import Path
import tempfile
import shutil

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config import (
    get_project_root,
    get_code_root,
    get_data_dir,
    get_raw_data_dir,
    get_processed_dir,
    get_models_dir,
    get_viz_dir,
    get_figures_dir,
    ensure_directories,
    get_seed,
    set_seed,
    get_model_params,
    get_cv_params,
    get_permutation_params,
    get_data_thresholds,
    get_file_paths,
    get_file_path
)

class TestConfig(unittest.TestCase):
    """Test cases for configuration functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = get_project_root()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_get_project_root_returns_path(self):
        """Test that get_project_root returns a Path object."""
        root = get_project_root()
        self.assertIsInstance(root, Path)
        self.assertTrue(root.exists())

    def test_get_code_root_returns_path(self):
        """Test that get_code_root returns a Path object."""
        code_root = get_code_root()
        self.assertIsInstance(code_root, Path)
        self.assertTrue(code_root.exists())

    def test_get_data_dir_returns_path(self):
        """Test that get_data_dir returns a Path object."""
        data_dir = get_data_dir()
        self.assertIsInstance(data_dir, Path)
        # The data dir might not exist yet, but the path should be correct

    def test_get_raw_data_dir_returns_path(self):
        """Test that get_raw_data_dir returns a Path object."""
        raw_dir = get_raw_data_dir()
        self.assertIsInstance(raw_dir, Path)

    def test_get_processed_dir_returns_path(self):
        """Test that get_processed_dir returns a Path object."""
        processed_dir = get_processed_dir()
        self.assertIsInstance(processed_dir, Path)

    def test_get_models_dir_returns_path(self):
        """Test that get_models_dir returns a Path object."""
        models_dir = get_models_dir()
        self.assertIsInstance(models_dir, Path)

    def test_get_viz_dir_returns_path(self):
        """Test that get_viz_dir returns a Path object."""
        viz_dir = get_viz_dir()
        self.assertIsInstance(viz_dir, Path)

    def test_get_figures_dir_returns_path(self):
        """Test that get_figures_dir returns a Path object."""
        figures_dir = get_figures_dir()
        self.assertIsInstance(figures_dir, Path)

    def test_ensure_directories_creates_folders(self):
        """Test that ensure_directories creates the required directories."""
        # Temporarily override the get_data_dir function to use a temp dir
        # This is a bit tricky, so we'll just test that it doesn't raise an error
        # and that the directories exist after calling it.
        ensure_directories()
        self.assertTrue(get_raw_data_dir().exists())
        self.assertTrue(get_processed_dir().exists())
        self.assertTrue(get_models_dir().exists())

    def test_get_seed_returns_int(self):
        """Test that get_seed returns an integer."""
        seed = get_seed()
        self.assertIsInstance(seed, int)

    def test_set_seed_sets_random_state(self):
        """Test that set_seed sets the random state."""
        set_seed(123)
        import random
        val1 = random.random()
        
        set_seed(123)
        val2 = random.random()
        
        self.assertEqual(val1, val2)

    def test_get_model_params_returns_dict(self):
        """Test that get_model_params returns a dictionary."""
        params = get_model_params()
        self.assertIsInstance(params, dict)
        self.assertIn("n_estimators", params)
        self.assertIn("random_state", params)

    def test_get_cv_params_returns_dict(self):
        """Test that get_cv_params returns a dictionary."""
        params = get_cv_params()
        self.assertIsInstance(params, dict)
        self.assertIn("n_splits", params)

    def test_get_permutation_params_returns_dict(self):
        """Test that get_permutation_params returns a dictionary."""
        params = get_permutation_params()
        self.assertIsInstance(params, dict)
        self.assertIn("n_permutations", params)

    def test_get_data_thresholds_returns_dict(self):
        """Test that get_data_thresholds returns a dictionary."""
        thresholds = get_data_thresholds()
        self.assertIsInstance(thresholds, dict)
        self.assertIn("min_observations", thresholds)
        self.assertIn("top_n_species", thresholds)

    def test_get_file_paths_returns_dict(self):
        """Test that get_file_paths returns a dictionary of Path objects."""
        paths = get_file_paths()
        self.assertIsInstance(paths, dict)
        for key, path in paths.items():
            self.assertIsInstance(path, Path)

    def test_get_file_path_valid_key(self):
        """Test that get_file_path returns a Path for a valid key."""
        path = get_file_path("metadata")
        self.assertIsInstance(path, Path)

    def test_get_file_path_invalid_key(self):
        """Test that get_file_path raises KeyError for an invalid key."""
        with self.assertRaises(KeyError):
            get_file_path("invalid_key")

if __name__ == "__main__":
    unittest.main()
