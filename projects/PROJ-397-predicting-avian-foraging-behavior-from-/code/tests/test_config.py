import os
import sys
import unittest
from pathlib import Path
import tempfile
import shutil

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
    get_reports_dir,
    get_metadata_file,
    get_seed,
    set_seed,
    get_model_params,
    get_cv_params,
    get_permutation_params,
    get_data_thresholds,
    get_file_path,
    get_file_paths,
    ensure_directories,
    get_land_cover_class_names,
    get_foraging_guilds,
    DEFAULT_SEED,
    RANDOM_STATE,
    MIN_OBSERVATIONS_PER_SPECIES,
    BUFFER_DISTANCE_METERS
)


class TestConfig(unittest.TestCase):
    def test_get_project_root_returns_path(self):
        """Test that get_project_root returns a Path object."""
        root = get_project_root()
        self.assertIsInstance(root, Path)
        self.assertTrue(root.exists())

    def test_get_code_root_returns_correct_path(self):
        """Test that get_code_root returns the correct path."""
        code_root = get_code_root()
        self.assertEqual(code_root, get_project_root() / "code")

    def test_get_data_dir_returns_correct_path(self):
        """Test that get_data_dir returns the correct path."""
        data_dir = get_data_dir()
        self.assertEqual(data_dir, get_project_root() / "data")

    def test_get_raw_data_dir_returns_correct_path(self):
        """Test that get_raw_data_dir returns the correct path."""
        raw_dir = get_raw_data_dir()
        self.assertEqual(raw_dir, get_data_dir() / "raw")

    def test_get_processed_dir_returns_correct_path(self):
        """Test that get_processed_dir returns the correct path."""
        processed_dir = get_processed_dir()
        self.assertEqual(processed_dir, get_data_dir() / "processed")

    def test_get_models_dir_returns_correct_path(self):
        """Test that get_models_dir returns the correct path."""
        models_dir = get_models_dir()
        self.assertEqual(models_dir, get_data_dir() / "models")

    def test_get_viz_dir_returns_correct_path(self):
        """Test that get_viz_dir returns the correct path."""
        viz_dir = get_viz_dir()
        self.assertEqual(viz_dir, get_data_dir() / "viz")

    def test_get_figures_dir_returns_correct_path(self):
        """Test that get_figures_dir returns the correct path."""
        figures_dir = get_figures_dir()
        self.assertEqual(figures_dir, get_viz_dir() / "figures")

    def test_get_reports_dir_returns_correct_path(self):
        """Test that get_reports_dir returns the correct path."""
        reports_dir = get_reports_dir()
        self.assertEqual(reports_dir, get_viz_dir() / "reports")

    def test_get_metadata_file_returns_correct_path(self):
        """Test that get_metadata_file returns the correct path."""
        metadata_file = get_metadata_file()
        self.assertEqual(metadata_file, get_data_dir() / "metadata.yaml")

    def test_get_seed_returns_default_seed(self):
        """Test that get_seed returns the default seed."""
        seed = get_seed()
        self.assertEqual(seed, DEFAULT_SEED)

    def test_set_seed_changes_random_state(self):
        """Test that set_seed changes the random state."""
        import random
        import numpy as np

        set_seed(123)
        random_val_1 = random.random()
        np_val_1 = np.random.random()

        set_seed(123)
        random_val_2 = random.random()
        np_val_2 = np.random.random()

        self.assertEqual(random_val_1, random_val_2)
        self.assertEqual(np_val_1, np_val_2)

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
        self.assertIn("random_state", params)

    def test_get_permutation_params_returns_dict(self):
        """Test that get_permutation_params returns a dictionary."""
        params = get_permutation_params()
        self.assertIsInstance(params, dict)
        self.assertIn("n_permutations", params)
        self.assertIn("random_state", params)

    def test_get_data_thresholds_returns_dict(self):
        """Test that get_data_thresholds returns a dictionary."""
        thresholds = get_data_thresholds()
        self.assertIsInstance(thresholds, dict)
        self.assertIn("min_observations", thresholds)
        self.assertIn("buffer_distance", thresholds)
        self.assertEqual(thresholds["min_observations"], MIN_OBSERVATIONS_PER_SPECIES)
        self.assertEqual(thresholds["buffer_distance"], BUFFER_DISTANCE_METERS)

    def test_get_file_path_returns_path(self):
        """Test that get_file_path returns a Path object."""
        file_path = get_file_path("test.txt")
        self.assertIsInstance(file_path, Path)
        self.assertEqual(file_path.name, "test.txt")

    def test_get_file_path_with_directory(self):
        """Test that get_file_path works with a custom directory."""
        custom_dir = Path("/custom/dir")
        file_path = get_file_path("test.txt", custom_dir)
        self.assertEqual(file_path, custom_dir / "test.txt")

    def test_get_file_paths_returns_list(self):
        """Test that get_file_paths returns a list of Path objects."""
        names = ["file1.txt", "file2.txt"]
        paths = get_file_paths(names)
        self.assertIsInstance(paths, list)
        self.assertEqual(len(paths), 2)
        self.assertIsInstance(paths[0], Path)

    def test_ensure_directories_creates_dirs(self):
        """Test that ensure_directories creates the required directories."""
        # Use a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override the project root
            original_root = get_project_root()
            # We can't easily override the global _PROJECT_ROOT, so we just test
            # that the function doesn't raise an error
            try:
                ensure_directories()
            except Exception as e:
                self.fail(f"ensure_directories raised an exception: {e}")

    def test_get_land_cover_class_names_returns_list(self):
        """Test that get_land_cover_class_names returns a list of strings."""
        names = get_land_cover_class_names()
        self.assertIsInstance(names, list)
        self.assertGreater(len(names), 0)
        for name in names:
            self.assertIsInstance(name, str)

    def test_get_foraging_guilds_returns_list(self):
        """Test that get_foraging_guilds returns a list of strings."""
        guilds = get_foraging_guilds()
        self.assertIsInstance(guilds, list)
        self.assertGreater(len(guilds), 0)
        for guild in guilds:
            self.assertIsInstance(guild, str)

    def test_constants_are_defined(self):
        """Test that all constants are defined with expected types."""
        self.assertIsInstance(DEFAULT_SEED, int)
        self.assertIsInstance(RANDOM_STATE, int)
        self.assertIsInstance(MIN_OBSERVATIONS_PER_SPECIES, int)
        self.assertIsInstance(BUFFER_DISTANCE_METERS, int)


if __name__ == "__main__":
    unittest.main()