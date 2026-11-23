"""
Unit tests for the utils/config module.
"""
import os
import sys
import unittest
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path so we can import utils.config
# Assuming the test runner is executed from the project root or code root
# We need to ensure the import path is correct relative to the test file
code_root = Path(__file__).resolve().parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.config import (
    RANDOM_SEED,
    EBD_URL,
    NLCD_URL,
    BUFFER_SIZE,
    N_PERMUTATIONS,
    get_project_root,
    get_code_root,
    get_data_dir,
    get_raw_data_dir,
    get_processed_dir,
    get_models_dir,
    get_viz_dir,
    get_figures_dir,
    get_reports_dir,
    get_metadata_file,
    get_seed,
    set_seed,
    get_land_cover_class_names,
    get_foraging_guilds,
    get_model_params,
    get_cv_params,
    get_permutation_params,
    get_data_thresholds,
    ensure_directories
)


class TestConfig(unittest.TestCase):
    """Test cases for the config module."""

    def test_random_seed_constant(self):
        """Verify that RANDOM_SEED is defined and equals 42."""
        self.assertEqual(RANDOM_SEED, 42)

    def test_seed_function(self):
        """Verify that get_seed returns the correct value."""
        self.assertEqual(get_seed(), 42)

    def test_set_seed(self):
        """Verify that set_seed updates the global seed."""
        original_seed = get_seed()
        set_seed(123)
        self.assertEqual(get_seed(), 123)
        # Reset to original
        set_seed(original_seed)

    def test_ebd_url(self):
        """Verify EBD_URL is a non-empty string."""
        self.assertIsInstance(EBD_URL, str)
        self.assertTrue(len(EBD_URL) > 0)
        self.assertIn("s3", EBD_URL)

    def test_nlcd_url(self):
        """Verify NLCD_URL is a non-empty string."""
        self.assertIsInstance(NLCD_URL, str)
        self.assertTrue(len(NLCD_URL) > 0)
        self.assertIn("usgs", NLCD_URL.lower())

    def test_buffer_size(self):
        """Verify BUFFER_SIZE is 100."""
        self.assertEqual(BUFFER_SIZE, 100)

    def test_n_permutations(self):
        """Verify N_PERMUTATIONS is 1000."""
        self.assertEqual(N_PERMUTATIONS, 1000)

    def test_get_project_root(self):
        """Verify get_project_root returns a Path object."""
        root = get_project_root()
        self.assertIsInstance(root, Path)
        self.assertTrue(root.exists())

    def test_directory_paths(self):
        """Verify all directory getter functions return Path objects."""
        self.assertIsInstance(get_code_root(), Path)
        self.assertIsInstance(get_data_dir(), Path)
        self.assertIsInstance(get_raw_data_dir(), Path)
        self.assertIsInstance(get_processed_dir(), Path)
        self.assertIsInstance(get_models_dir(), Path)
        self.assertIsInstance(get_viz_dir(), Path)
        self.assertIsInstance(get_figures_dir(), Path)
        self.assertIsInstance(get_reports_dir(), Path)

    def test_metadata_file_path(self):
        """Verify get_metadata_file returns a Path to metadata.yaml."""
        meta_path = get_metadata_file()
        self.assertIsInstance(meta_path, Path)
        self.assertEqual(meta_path.name, "metadata.yaml")

    def test_land_cover_class_names(self):
        """Verify land cover class names is a non-empty dict."""
        classes = get_land_cover_class_names()
        self.assertIsInstance(classes, dict)
        self.assertGreater(len(classes), 0)
        self.assertIn(11, classes)  # Water
        self.assertIn(21, classes)  # Forest

    def test_foraging_guilds(self):
        """Verify foraging guilds is a non-empty list."""
        guilds = get_foraging_guilds()
        self.assertIsInstance(guilds, list)
        self.assertGreater(len(guilds), 0)
        self.assertIn("ground", guilds)

    def test_model_params(self):
        """Verify model params is a dict with expected keys."""
        params = get_model_params()
        self.assertIsInstance(params, dict)
        self.assertIn("n_estimators", params)
        self.assertIn("random_state", params)
        self.assertEqual(params["random_state"], 42)

    def test_cv_params(self):
        """Verify CV params is a dict with expected keys."""
        params = get_cv_params()
        self.assertIsInstance(params, dict)
        self.assertIn("n_splits", params)
        self.assertIn("random_state", params)

    def test_permutation_params(self):
        """Verify permutation params returns N_PERMUTATIONS."""
        self.assertEqual(get_permutation_params(), 1000)

    def test_data_thresholds(self):
        """Verify data thresholds is a dict with expected keys."""
        thresholds = get_data_thresholds()
        self.assertIsInstance(thresholds, dict)
        self.assertIn("min_observations_per_species", thresholds)
        self.assertEqual(thresholds["min_observations_per_species"], 50)

    def test_ensure_directories(self):
        """Verify ensure_directories creates necessary folders."""
        # This test assumes we are running in a temp environment or the dirs already exist
        # We just check it doesn't raise an exception
        try:
            ensure_directories()
            # Check if at least one directory exists
            self.assertTrue(get_data_dir().exists())
        except Exception as e:
            self.fail(f"ensure_directories raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()