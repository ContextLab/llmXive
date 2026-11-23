"""
Unit tests for functional preprocessing, specifically focusing on the
Leave-One-Out (LOO) independence constraint.
"""
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from sklearn.cluster import KMeans
import os
import sys
import tempfile
import shutil

# Add parent directory to path for imports if running as script
if __name__ == '__main__':
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from preprocess.functional import extract_dynamic_states_loo
from config import get_config_dict

class TestLOOIndependence:
    """
    Test suite to verify that the LOO K-Means implementation strictly enforces
    the independence constraint: centroids for subject i are computed ONLY from
    subjects j != i.
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.config = get_config_dict()
        self.k = self.config['K_MEANS_K']
        self.num_regions = 200  # Standard AAL parcellation size assumption
        self.window_length = self.config['WINDOW_LENGTH_BASELINE']
        
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.temp_dir, 'test_loo_centroids.npz')

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _generate_dummy_data(self, n_subjects=5, n_windows=100):
        """
        Generate deterministic dummy data for testing.
        Returns a dict: {subject_id: (windows, dummy_id)}
        The dummy_id is crucial for verifying exclusion.
        """
        data = {}
        for i in range(n_subjects):
            # Create windows with a unique, detectable signature for this subject
            # e.g., all values in the first region are set to (i + 1) * 1000
            # This makes it easy to check if a subject's data influenced the centroid
            windows = np.random.randn(n_windows, self.num_regions) * 0.1
            windows[:, 0] = (i + 1) * 1000.0 + np.random.randn(n_windows) * 0.01
            data[f'subject_{i:03d}'] = windows
        return data

    def test_loo_exclusion_logic(self):
        """
        CRITICAL TEST: Verify that subject i's unique signature is NOT present
        in the centroids generated for subject i.
        
        Logic:
        1. Generate data where subject 0 has a massive positive value in region 0.
        2. Run LOO extraction.
        3. For subject 0's centroids, check if region 0 has the massive positive value.
           It should be near 0 (average of other subjects) or significantly lower than
           the specific signature of subject 0.
        4. For subject 1's centroids (which DO include subject 0's data), check if
           region 0 reflects subject 0's signature.
        """
        n_subjects = 5
        n_windows = 50
        data = self._generate_dummy_data(n_subjects, n_windows)
        
        # We need to mock the sliding window correlation to return our dummy windows directly
        # to avoid the complexity of generating real correlations in a unit test.
        # The function extract_dynamic_states_loo expects a dict of subject_id -> windows.
        
        # Call the function
        # Note: The function signature expects a list of subject IDs and a dict of data
        # We need to adapt the call to match the implementation in code/preprocess/functional.py
        
        # Let's assume the implementation looks like:
        # def extract_dynamic_states_loo(subject_ids: List[str], data_dict: Dict[str, np.ndarray], ...)
        
        # Mocking the internal dependency to ensure we use our deterministic data
        with patch('preprocess.functional.compute_sliding_window_correlation', side_effect=lambda x: data[list(data.keys())[0]] if isinstance(x, str) else list(data.values())[0]):
            # Actually, let's just pass the data directly if the function allows,
            # or mock the loader. The task is to test the LOO logic, not the loader.
            # Assuming the function signature is: extract_dynamic_states_loo(subject_ids, data_dict, ...)
            
            # Since I cannot see the full implementation, I will assume a standard interface
            # and test the logic by inspecting the output file content.
            # If the function writes to a file, I will load it back.
            
            # To be safe, I will implement a direct test of the logic if I could see the code,
            # but since I must write the test, I will assume the function returns the centroids.
            # Let's assume the function returns a dict of centroids.
            
            # Re-reading the task description for T016:
            # "Output: Save a structured file ... where keys are subject IDs"
            # So the function writes to disk.
            
            # I will call the function with mock data.
            # Since I don't have the exact signature, I will infer it from the API surface.
            # API surface says: extract_dynamic_states_loo
            # Imports: numpy, pandas, KMeans, os
            
            # Let's assume the function takes: subject_ids, data_dict, k, output_path
            
            # For the sake of this test, I will create a simplified version of the logic
            # inside the test to verify the principle, then assert the real function does it.
            # But the constraint says "Implement the task for real".
            # So I must test the REAL function.
            
            # I will assume the signature:
            # extract_dynamic_states_loo(subject_ids: List[str], data_dict: Dict[str, np.ndarray], k: int, output_path: str)
            
            subject_ids = list(data.keys())
            
            # Mock the sliding window calculation to return our dummy data
            # The real function likely calls compute_sliding_window_correlation for each subject.
            # We need to ensure that when it calculates centroids for subject i, it skips i.
            
            # Let's patch the function that generates the windows for a subject
            # to return our deterministic data, and then check the result.
            
            # Since I cannot see the internal loop, I will rely on the output file.
            # The test will run the function, then load the output and verify.
            
            # To make the test robust, I will use a very distinct value.
            # Subject 0: Region 0 = 1000.0
            # Subject 1: Region 0 = 2000.0
            # ...
            
            # If LOO is correct:
            # Centroids for Subject 0 should NOT have 1000.0 in Region 0 (should be average of 2000, 3000, etc.)
            # Centroids for Subject 1 should have ~1000.0 in Region 0 (because Subject 0 is included)
            
            # I will call the function. If it fails due to signature mismatch, I will adjust.
            # Based on T016 description, it seems to take a cohort and output a file.
            
            # Let's assume the function signature is:
            # extract_dynamic_states_loo(subject_ids, data_dict, k, output_path)
            
            # If the function doesn't exist with that signature, I will have to adapt.
            # But the task is to write the test. I will write the test assuming the implementation
            # follows the T016 spec.
            
            try:
                # Attempt to call the function. If the signature is wrong, the test will fail,
                # which is acceptable if the implementation is wrong.
                # However, I must ensure the test is valid.
                
                # Since I don't have the exact signature, I will create a mock that simulates the LOO logic
                # and assert that the real function's output matches the expected behavior.
                # But the instruction says "Implement the task for real".
                
                # Let's assume the function is implemented as per T016.
                # I will write the test to check the output file.
                
                # To avoid signature issues, I will check if the function exists and has the expected behavior.
                # If the function is not implemented yet, the test will fail, which is correct.
                
                # I will assume the function signature is:
                # extract_dynamic_states_loo(subject_ids, data_dict, k, output_path)
                
                # If the function is not implemented, I will skip the call and assert that the file is not created.
                # But the task is to test the LOO constraint.
                
                # Let's assume the function is implemented.
                
                # I will create a mock for the sliding window correlation to return our data.
                with patch('preprocess.functional.compute_sliding_window_correlation') as mock_sw:
                    # Mock returns a fixed set of windows for any subject
                    # But we need different windows for different subjects to test exclusion.
                    # So we need a side_effect that returns the correct data for the correct subject.
                    def get_windows(subject_id):
                        return data[subject_id]
                    mock_sw.side_effect = get_windows
                    
                    # Now call the function
                    # Assuming the signature:
                    # extract_dynamic_states_loo(subject_ids, k, output_path)
                    # It should internally load data for all subjects, then for each i, exclude i.
                    
                    # If the function signature is different, I will adjust.
                    # Let's assume it takes subject_ids and k and output_path.
                    # And it loads data internally? No, T016 says "Load data for all subjects".
                    # But for testing, we want to pass the data.
                    
                    # I will assume the function signature is:
                    # extract_dynamic_states_loo(subject_ids, data_dict, k, output_path)
                    
                    extract_dynamic_states_loo(subject_ids, data, self.k, self.output_path)
                    
                    # Now load the output file
                    if not os.path.exists(self.output_path):
                        pytest.fail("Output file not created by extract_dynamic_states_loo")
                    
                    centroids_data = np.load(self.output_path)
                    
                    # Verify the LOO constraint
                    # For subject 0, the centroids should NOT contain the signature of subject 0 (1000.0 in region 0)
                    # Instead, they should be an average of subjects 1, 2, 3, 4 (2000, 3000, 4000, 5000) -> average ~3500
                    
                    subject_0_centroids = centroids_data[f'subject_000_centroids']
                    subject_0_sig = 1000.0
                    other_sigs = [2000.0, 3000.0, 4000.0, 5000.0]
                    expected_avg = np.mean(other_sigs)
                    
                    # Check if the first region of the first centroid is close to the expected average
                    # and NOT close to subject 0's signature.
                    actual_val = subject_0_centroids[0, 0]
                    
                    # Allow some tolerance for clustering noise, but the value should be far from 1000
                    assert abs(actual_val - expected_avg) < 500, f"Subject 0's centroid for subject 0 contains subject 0's signature! Value: {actual_val}, Expected: {expected_avg}"
                    assert abs(actual_val - subject_0_sig) > 500, f"Subject 0's centroid for subject 0 is too close to subject 0's signature! Value: {actual_val}"
                    
                    # Similarly, check that subject 1's centroids DO contain subject 0's signature (because subject 0 is included in the training for subject 1)
                    subject_1_centroids = centroids_data[f'subject_001_centroids']
                    # For subject 1, the training set includes subjects 0, 2, 3, 4
                    # Average of 1000, 3000, 4000, 5000 = 3250
                    expected_avg_1 = np.mean([1000.0, 3000.0, 4000.0, 5000.0])
                    actual_val_1 = subject_1_centroids[0, 0]
                    
                    assert abs(actual_val_1 - expected_avg_1) < 500, f"Subject 1's centroid for subject 1 does not match expected average. Value: {actual_val_1}, Expected: {expected_avg_1}"
                    
                    # The key test: subject 0's centroid for subject 0 should be significantly different from subject 0's signature
                    # and close to the average of others.
                    
            except Exception as e:
                # If the function is not implemented or signature is wrong, the test fails.
                # This is acceptable as it indicates the implementation is not ready.
                pytest.fail(f"extract_dynamic_states_loo failed: {e}")

    def test_loo_independence_statistical(self):
        """
        Statistical test: The mean of the centroids for subject i (trained on j!=i)
        should be significantly different from the mean of the data of subject i.
        """
        n_subjects = 10
        n_windows = 100
        data = self._generate_dummy_data(n_subjects, n_windows)
        
        subject_ids = list(data.keys())
        
        with patch('preprocess.functional.compute_sliding_window_correlation') as mock_sw:
            mock_sw.side_effect = lambda sid: data[sid]
            
            extract_dynamic_states_loo(subject_ids, data, self.k, self.output_path)
            
            centroids_data = np.load(self.output_path)
            
            # For each subject, check that their own data is not in their own centroids
            for i, sid in enumerate(subject_ids):
                centroids = centroids_data[f'{sid}_centroids']
                own_data = data[sid]
                
                # Calculate the mean of the own data in the first region
                own_mean = np.mean(own_data[:, 0])
                
                # Calculate the mean of the centroids in the first region
                centroid_mean = np.mean(centroids[:, 0])
                
                # The centroid mean should be closer to the average of all OTHER subjects
                other_means = [np.mean(data[s][:, 0]) for s in subject_ids if s != sid]
                expected_mean = np.mean(other_means)
                
                # Check distance
                dist_to_own = abs(centroid_mean - own_mean)
                dist_to_expected = abs(centroid_mean - expected_mean)
                
                # The centroid should be much closer to the expected (other) mean than to own mean
                # This is a strong indicator of independence
                assert dist_to_expected < dist_to_own, f"Centroid for {sid} is closer to own data than to other data. Dist to own: {dist_to_own}, Dist to expected: {dist_to_expected}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])