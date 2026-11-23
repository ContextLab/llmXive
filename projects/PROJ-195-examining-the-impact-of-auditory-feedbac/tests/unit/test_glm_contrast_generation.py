"""
Unit tests for T020: Contrast map generation.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

import numpy as np
import nibabel as nib
from nilearn.glm.first_level import FirstLevelModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from glm_contrast_generation import (
    load_valid_subjects,
    get_first_level_model_path,
    compute_and_save_contrast,
    main
)


class TestContrastGeneration(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.processed_dir = Path(self.temp_dir) / "data" / "processed"
        self.glm_results_dir = self.processed_dir / "glm_results"
        
        self.processed_dir.mkdir(parents=True)
        self.glm_results_dir.mkdir(parents=True)
        
        # Mock valid_subjects.txt
        self.valid_subjects_file = self.processed_dir / "valid_subjects.txt"
        with open(self.valid_subjects_file, 'w') as f:
            f.write("sub-01\n")
            f.write("sub-02\n")
        
        # Mock a fake FirstLevelModel pickle
        # Since we can't easily instantiate a real FirstLevelModel without data,
        # we will mock the load and compute_contrast behavior in the tests.
        self.mock_model_path = self.glm_results_dir / "sub-01_first_level.pkl"
        
        # Create a dummy file to represent the pickle (we will mock the load)
        with open(self.mock_model_path, 'w') as f:
            f.write("dummy_pickle_content")

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    @patch('glm_contrast_generation.PROCESSED_DIR')
    @patch('glm_contrast_generation.VALID_SUBJECTS_FILE')
    def test_load_valid_subjects(self, mock_valid_file, mock_processed_dir):
        """Test loading valid subjects."""
        mock_valid_file.exists.return_value = True
        mock_valid_file.read_text.return_value = "sub-01\nsub-02\n"
        
        # We need to patch the file reading logic
        with patch('builtins.open', unittest.mock.mock_open(read_data="sub-01\nsub-02\n")):
            subjects = load_valid_subjects()
            self.assertEqual(subjects, ["sub-01", "sub-02"])

    def test_get_first_level_model_path(self):
        """Test locating the model path."""
        # The path should exist because we created it in setUp
        path = get_first_level_model_path("sub-01")
        self.assertEqual(path, self.mock_model_path)

        # Test non-existent subject
        path = get_first_level_model_path("sub-99")
        self.assertIsNone(path)

    @patch('glm_contrast_generation.PROCESSED_DIR')
    def test_compute_and_save_contrast(self, mock_processed_dir):
        """Test contrast computation and saving."""
        # Create a mock model
        mock_model = MagicMock(spec=FirstLevelModel)
        mock_z_map = MagicMock()
        mock_z_map.to_filename = MagicMock()
        
        mock_model.compute_contrast.return_value = mock_z_map
        
        # Mock the output path
        output_path = Path(self.temp_dir) / "test_contrast.nii.gz"
        mock_processed_dir.__truediv__.return_value = output_path.parent
        mock_processed_dir.__truediv__.return_value.__truediv__.return_value = output_path
        
        # Actually, let's just test the logic without full path mocking complexity
        # We'll patch the save method
        with patch('glm_contrast_generation.PROCESSED_DIR') as mock_dir:
            mock_dir.__truediv__.return_value.__truediv__.return_value = output_path
            mock_dir.__truediv__.return_value.__truediv__.return_value.mkdir = MagicMock()
            
            # We need to mock the actual file saving to avoid nibabel errors
            with patch('nibabel.save') as mock_save:
                result = compute_and_save_contrast(
                    mock_model, 
                    "sub-01", 
                    "perturbed", 
                    [0, 1, 1]
                )
                
                # Verify compute_contrast was called
                mock_model.compute_contrast.assert_called_once()
                # Verify save was called
                mock_z_map.to_filename.assert_called_once()
                self.assertIsNotNone(result)

    def test_main_execution(self):
        """Test the main function execution flow."""
        # We need to mock the entire pipeline to avoid real data dependencies
        with patch('glm_contrast_generation.load_valid_subjects') as mock_load:
            mock_load.return_value = ["sub-01"]
            
            with patch('glm_contrast_generation.get_first_level_model_path') as mock_get_path:
                mock_get_path.return_value = self.mock_model_path
                
                with patch('builtins.open', unittest.mock.mock_open(read_data="dummy")):
                    with patch('pickle.load') as mock_pickle_load:
                        mock_model = MagicMock()
                        mock_model.compute_contrast.return_value = MagicMock(to_filename=MagicMock())
                        mock_pickle_load.return_value = mock_model
                        
                        with patch('glm_contrast_generation.compute_and_save_contrast') as mock_compute:
                            mock_compute.return_value = Path("dummy.nii.gz")
                            
                            # Run main
                            main()
                            
                            # Verify functions were called
                            mock_load.assert_called_once()
                            mock_compute.assert_called_once()


if __name__ == '__main__':
    unittest.main()