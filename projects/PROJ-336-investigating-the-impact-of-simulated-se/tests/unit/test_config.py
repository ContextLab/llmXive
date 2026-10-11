import unittest
from pathlib import Path
import src.config as config

class TestConfig(unittest.TestCase):
    def test_constants_exist_and_types(self):
        # Path constants
        self.assertIsInstance(config.DATA_ROOT, Path, "DATA_ROOT should be a pathlib.Path")
        self.assertIsInstance(config.RAW_DIR, Path, "RAW_DIR should be a pathlib.Path")
        self.assertIsInstance(config.PREPROC_DIR, Path, "PREPROC_DIR should be a pathlib.Path")
        self.assertIsInstance(config.QUALITY_DIR, Path, "QUALITY_DIR should be a pathlib.Path")
        self.assertIsInstance(config.CONNECTIVITY_DIR, Path, "CONNECTIVITY_DIR should be a pathlib.Path")
        self.assertIsInstance(config.RESULTS_DIR, Path, "RESULTS_DIR should be a pathlib.Path")

        # Quality‑control thresholds
        self.assertEqual(config.FD_THRESHOLD, 0.5, "FD_THRESHOLD should be 0.5")
        self.assertAlmostEqual(config.FD_VOLUME_PCT, 0.10, places=5, msg="FD_VOLUME_PCT should be 0.10")

        # Dataset and analysis parameters
        self.assertIsInstance(config.DATASET_IDS, list, "DATASET_IDS should be a list")
        self.assertListEqual(config.DATASET_IDS, ["ds001770", "ds003820"], "DATASET_IDS list mismatch")
        self.assertIsInstance(config.ATLAS_URL, str, "ATLAS_URL should be a string")
        self.assertTrue(config.ATLAS_URL.startswith("https://"), "ATLAS_URL should start with https://")
        self.assertEqual(config.MAX_SUBJECTS, 24, "MAX_SUBJECTS should be 24")
        self.assertEqual(config.PERMUTATIONS, 1000, "PERMUTATIONS should be 1000")
        self.assertEqual(config.RANDOM_SEED, 42, "RANDOM_SEED should be 42")

if __name__ == '__main__':
    unittest.main()