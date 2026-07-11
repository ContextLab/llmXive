"""
Unit Tests for Image Saver Module (Task T021)

Tests the save_image and save_batch_images functions to ensure
correct directory creation, file naming, and error handling.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import unittest

# Add the project root to the path to allow imports
# Assuming this test file is in tests/unit/, and code is in code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from generation.image_saver import (
    save_image,
    save_batch_images,
    ImageSaveError,
    VALID_GROUPS
)

class TestImageSaver(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for test outputs."""
        self.test_dir = tempfile.mkdtemp()
        self.test_scene_id = "test_scene_123"

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_image_invalid_group(self):
        """Test that saving with an invalid group raises an error."""
        dummy_data = b"fake_image_data"
        with self.assertRaises(ImageSaveError):
            save_image(dummy_data, self.test_scene_id, "InvalidGroup", output_dir=Path(self.test_dir))

    def test_save_image_creates_directory(self):
        """Test that the group subdirectory is created if it doesn't exist."""
        import numpy as np
        dummy_array = np.zeros((100, 100, 3), dtype=np.uint8)
        
        group = "Baseline"
        save_image(dummy_array, self.test_scene_id, group, output_dir=Path(self.test_dir))
        
        expected_path = Path(self.test_dir) / group / f"{self.test_scene_id}.png"
        self.assertTrue(expected_path.exists())

    def test_save_image_correct_naming(self):
        """Test that the image is saved with the correct scene_id and extension."""
        import numpy as np
        dummy_array = np.zeros((100, 100, 3), dtype=np.uint8)
        
        group = "Experimental"
        save_image(dummy_array, self.test_scene_id, group, output_dir=Path(self.test_dir))
        
        expected_path = Path(self.test_dir) / group / f"{self.test_scene_id}.png"
        self.assertTrue(expected_path.exists())
        self.assertEqual(expected_path.suffix, ".png")

    def test_save_batch_images(self):
        """Test saving multiple images for different groups in one call."""
        import numpy as np
        dummy_array = np.zeros((100, 100, 3), dtype=np.uint8)
        
        images = {
            "Baseline": dummy_array,
            "Experimental": dummy_array,
            "Control": dummy_array
        }
        
        groups = ["Baseline", "Experimental", "Control"]
        saved_paths = save_batch_images(images, self.test_scene_id, groups, output_dir=Path(self.test_dir))
        
        self.assertEqual(len(saved_paths), 3)
        
        for group in groups:
            expected_path = Path(self.test_dir) / group / f"{self.test_scene_id}.png"
            self.assertIn(group, saved_paths)
            self.assertEqual(saved_paths[group], expected_path)
            self.assertTrue(expected_path.exists())

    def test_save_batch_images_missing_group(self):
        """Test that missing groups in the input dict are handled gracefully (skipped) but not raising if not all required."""
        import numpy as np
        dummy_array = np.zeros((100, 100, 3), dtype=np.uint8)
        
        images = {
            "Baseline": dummy_array
            # Experimental and Control missing
        }
        
        groups = ["Baseline", "Experimental", "Control"]
        
        # The function should log a warning but not raise an error if the group is missing from the dict
        # unless we modify the logic to require all. Based on current implementation, it logs warning and skips.
        # However, the current implementation of save_batch_images in the artifact raises ImageSaveError 
        # if ANY of the requested groups are missing from the result of the loop? 
        # Let's re-read the artifact logic:
        # It checks `if group not in images`, logs warning, continues.
        # Then it checks `if failed_groups`, raises error.
        # So if a group is missing from 'images' dict, it is skipped and NOT added to failed_groups.
        # Thus, no error is raised if some groups are missing, just warnings.
        # But the task T021 says "Ensure all three groups... are fully generated before marking task complete".
        # This implies the caller (diffusion_runner) must ensure all exist.
        # The saver itself just saves what it gets.
        
        saved_paths = save_batch_images(images, self.test_scene_id, groups, output_dir=Path(self.test_dir))
        
        # Only Baseline should be saved
        self.assertEqual(len(saved_paths), 1)
        self.assertIn("Baseline", saved_paths)

    def test_save_bytes_image(self):
        """Test saving raw bytes."""
        dummy_bytes = b"PNG_HEADER_DATA"
        group = "Control"
        save_image(dummy_bytes, self.test_scene_id, group, output_dir=Path(self.test_dir))
        
        expected_path = Path(self.test_dir) / group / f"{self.test_scene_id}.png"
        self.assertTrue(expected_path.exists())
        with open(expected_path, 'rb') as f:
            self.assertEqual(f.read(), dummy_bytes)


if __name__ == '__main__':
    unittest.main()