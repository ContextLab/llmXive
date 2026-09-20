import os
import sys
import unittest
from pathlib import Path
import tempfile
import shutil

# Add the project root to the path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import (
    get_project_root, get_code_root, get_data_dir, get_raw_data_dir,
    get_processed_dir, get_models_dir, get_viz_dir, get_figures_dir,
    get_reports_dir, get_metadata_file, ensure_directories, get_seed,
    set_seed, get_model_params, get_cv_params, get_permutation_params,
    get_data_thresholds, get_file_paths, get_file_path
)

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory structure for testing if needed
        # However, since config.py relies on the actual file structure,
        # we test the logic assuming the standard layout exists or is created.
        self.original_cwd = os.getcwd()
        # We assume the tests are run from the project root or code directory
        # The config module calculates paths relative to itself.
        pass

    def tearDown(self):
        os.chdir(self.original_cwd)

    def test_get_project_root(self):
        root = get_project_root()
        self.assertIsInstance(root, Path)
        self.assertTrue(root.exists())
        # Check that 'code' is a child of root
        self.assertTrue((root / "code").exists())

    def test_get_code_root(self):
        code_root = get_code_root()
        self.assertIsInstance(code_root, Path)
        self.assertTrue(code_root.exists())
        self.assertTrue((code_root / "utils").exists())

    def test_get_data_dir(self):
        data_dir = get_data_dir()
        self.assertIsInstance(data_dir, Path)
        # The directory might not exist yet, but the path should be correct
        expected = get_project_root() / "data"
        self.assertEqual(data_dir, expected)

    def test_get_sub_directories(self):
        raw = get_raw_data_dir()
        proc = get_processed_dir()
        mod = get_models_dir()
        viz = get_viz_dir()
        fig = get_figures_dir()
        rep = get_reports_dir()

        self.assertEqual(raw, get_data_dir() / "raw")
        self.assertEqual(proc, get_data_dir() / "processed")
        self.assertEqual(mod, get_project_root() / "models")
        self.assertEqual(viz, get_project_root() / "viz")
        self.assertEqual(fig, get_viz_dir() / "figures")
        self.assertEqual(rep, get_viz_dir() / "reports")

    def test_ensure_directories(self):
        # Create a temp dir to simulate a clean environment if needed,
        # but ensure_directories creates dirs if missing.
        # We just verify it doesn't raise an exception.
        ensure_directories()
        # Verify the main directories now exist
        self.assertTrue(get_data_dir().exists())
        self.assertTrue(get_raw_data_dir().exists())
        self.assertTrue(get_processed_dir().exists())
        self.assertTrue(get_models_dir().exists())
        self.assertTrue(get_viz_dir().exists())
        self.assertTrue(get_figures_dir().exists())
        self.assertTrue(get_reports_dir().exists())

    def test_get_seed(self):
        seed = get_seed()
        self.assertIsInstance(seed, int)
        self.assertEqual(seed, 42)

    def test_set_seed(self):
        set_seed(123)
        self.assertEqual(get_seed(), 123)
        set_seed(42) # Reset to default

    def test_get_model_params(self):
        params = get_model_params()
        self.assertIn("n_estimators", params)
        self.assertIn("random_state", params)
        self.assertEqual(params["random_state"], 42)

    def test_get_cv_params(self):
        params = get_cv_params()
        self.assertIn("n_splits", params)
        self.assertIn("shuffle", params)
        self.assertTrue(params["shuffle"])

    def test_get_permutation_params(self):
        params = get_permutation_params()
        self.assertIn("n_permutations", params)
        self.assertIn("alpha", params)
        self.assertEqual(params["alpha"], 0.05)

    def test_get_data_thresholds(self):
        thresholds = get_data_thresholds()
        self.assertIn("min_observations_per_species", thresholds)
        self.assertEqual(thresholds["min_observations_per_species"], 50)
        self.assertIn("buffer_radius_meters", thresholds)
        self.assertEqual(thresholds["buffer_radius_meters"], 100)

    def test_get_file_path(self):
        path = get_file_path("data/raw/test.csv")
        expected = get_project_root() / "data" / "raw" / "test.csv"
        self.assertEqual(path, expected)

    def test_get_file_paths(self):
        paths = get_file_paths()
        self.assertIn("metadata", paths)
        self.assertIn("model", paths)
        self.assertIsInstance(paths["metadata"], Path)

if __name__ == "__main__":
    unittest.main()