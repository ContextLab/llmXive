import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

# Import the function to test
from preprocessing import process_subject, check_time_point_completeness

class TestAALAtlasFailureHandling:
    """
    Tests for T014: Ensure AAL atlas failures are handled gracefully without crashing.
    """

    def test_process_subject_skips_on_atlas_file_not_found(self, caplog):
        """
        Verify that if the AAL atlas file is missing (FileNotFoundError),
        the subject is skipped (returns None) and an error is logged,
        without raising an unhandled exception.
        """
        caplog.set_level(logging.ERROR)
        
        subject_id = "sub_test_001"
        subject_data = {
            'acute': [Path("/fake/path/acute.nii.gz")],
            'chronic': [Path("/fake/path/chronic.nii.gz")]
        }
        # Simulate a path that doesn't exist or a mock that raises
        atlas_path = Path("/non_existent_atlas.nii.gz")

        # Mock the internal functions to simulate the failure
        with patch('preprocessing.download_atlas_if_needed', side_effect=FileNotFoundError("AAL atlas not found")):
            # Note: In the real code, download_atlas_if_needed is called in run_preprocessing_pipeline.
            # Here we test the logic inside process_subject which assumes atlas_path is valid.
            # We need to mock the specific step inside process_subject that uses the atlas.
            pass

        # Actually, the test needs to target the specific exception handling in preprocess_fmri
        # Let's mock the NiftiLabelsMasker to raise a FileNotFoundError simulating atlas failure
        with patch('preprocessing.NiftiLabelsMasker') as MockMasker:
            mock_instance = MagicMock()
            mock_instance.fit_transform.side_effect = FileNotFoundError("AAL atlas file not found")
            MockMasker.return_value = mock_instance

            result = process_subject(subject_id, subject_data, atlas_path)

            assert result is None, "Subject should be skipped (None) when AAL atlas fails"
            assert "AAL atlas failure" in caplog.text or "Skipping entire subject" in caplog.text

    def test_process_subject_skips_on_general_preprocessing_error(self, caplog):
        """
        Verify that if any other error occurs during preprocessing (e.g., data mismatch),
        the subject is skipped and logged, without crashing.
        """
        caplog.set_level(logging.ERROR)
        
        subject_id = "sub_test_002"
        subject_data = {
            'acute': [Path("/fake/path/acute.nii.gz")],
            'chronic': [Path("/fake/path/chronic.nii.gz")]
        }
        atlas_path = Path("/fake/atlas.nii.gz")

        with patch('preprocessing.NiftiLabelsMasker') as MockMasker:
            mock_instance = MagicMock()
            mock_instance.fit_transform.side_effect = Exception("Unexpected processing error")
            MockMasker.return_value = mock_instance

            result = process_subject(subject_id, subject_data, atlas_path)

            assert result is None, "Subject should be skipped on general error"
            assert "Skipping entire subject" in caplog.text

    def test_process_subject_success_when_no_errors(self):
        """
        Verify that if preprocessing succeeds, a Subject object is returned.
        """
        subject_id = "sub_test_003"
        subject_data = {
            'acute': [Path("/fake/path/acute.nii.gz")],
            'chronic': [Path("/fake/path/chronic.nii.gz")]
        }
        atlas_path = Path("/fake/atlas.nii.gz")

        # Mock successful preprocessing
        with patch('preprocessing.NiftiLabelsMasker') as MockMasker:
            mock_instance = MagicMock()
            # Return a fake time series (n_regions=90, n_timepoints=100)
            fake_ts = np.random.rand(90, 100)
            mock_instance.fit_transform.return_value = fake_ts.T # Transpose to match expected output
            MockMasker.return_value = mock_instance

            with patch('preprocessing.compute_connectivity_matrix', return_value=np.eye(90)):
                result = process_subject(subject_id, subject_data, atlas_path)

                assert result is not None, "Subject should be processed successfully"
                assert result.subject_id == subject_id
                assert 'acute' in result.matrices
                assert 'chronic' in result.matrices

class TestTimePointCompleteness:
    """
    Tests for T013 logic (missing time points) to ensure it works as expected.
    """
    def test_check_time_point_completeness_missing_chronic(self):
        data = {'acute': [Path("file.nii")]}
        is_complete, missing = check_time_point_completeness(data)
        assert not is_complete
        assert 'chronic' in missing

    def test_check_time_point_completeness_complete(self):
        data = {'acute': [Path("file.nii")], 'chronic': [Path("file.nii")]}
        is_complete, missing = check_time_point_completeness(data)
        assert is_complete
        assert len(missing) == 0
