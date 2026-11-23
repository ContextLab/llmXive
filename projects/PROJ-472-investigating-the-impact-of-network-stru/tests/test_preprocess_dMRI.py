import os
import json
import tempfile
import shutil
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# We need to mock the config and data setup to run tests without real data
# or we run a unit test on the logic that doesn't require MRtrix3.

class TestPreprocessDMRI(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.raw_dir = os.path.join(self.test_dir, "data", "raw")
        self.proc_dir = os.path.join(self.test_dir, "data", "processed")
        os.makedirs(self.raw_dir)
        os.makedirs(self.proc_dir)
        
        # Mock config to point to test dir
        self.config_patcher = patch('code.data.preprocess_dMRI.get_data_root', return_value=Path(self.test_dir))
        self.mock_get_data_root = self.config_patcher.start()
        
        # Create a fake hash file
        self.hash_file = Path(self.proc_dir) / "parcellation_hash.json"
        with open(self.hash_file, 'w') as f:
            json.dump({"hash": "test_hash_123"}, f)

    def tearDown(self):
        self.config_patcher.stop()
        shutil.rmtree(self.test_dir)

    @patch('code.data.preprocess_dMRI.compute_sha256')
    @patch('code.data.preprocess_dMRI.HCP_MMP_FILE_PATH', 'test.zip')
    @patch('code.data.preprocess_dMRI.HCP_MMP_URL', 'http://test.com/test.zip')
    def test_verify_parcellation_hash_update(self, mock_compute_sha256):
        """Test that verify_parcellation_file updates the hash file on mismatch/first run."""
        from code.data.preprocess_dMRI import verify_parcellation_file
        
        # Create a fake zip
        zip_path = Path(self.raw_dir) / "test.zip"
        zip_path.touch()
        
        mock_compute_sha256.return_value = "new_hash_456"
        
        result = verify_parcellation_file(zip_path)
        
        self.assertTrue(result)
        
        # Check if hash file was updated
        with open(self.hash_file, 'r') as f:
            data = json.load(f)
        self.assertEqual(data["hash"], "new_hash_456")

    @patch('code.data.preprocess_dMRI.subprocess.run')
    @patch('code.data.preprocess_dMRI.load_tractography')
    @patch('code.data.preprocess_dMRI.save_connectome_matrix')
    def test_generate_connectome_matrix_calls_mrtrix(self, mock_save, mock_load_tck, mock_subprocess):
        """Test that generate_connectome_matrix calls tck2connectome with correct args."""
        from code.data.preprocess_dMRI import generate_connectome_matrix
        
        mock_tck = Path("/fake/tck.tck")
        mock_nodes = Path("/fake/nodes.mif")
        mock_output = Path("/fake/out.tsv")
        
        mock_load_tck.return_value = mock_tck
        mock_subprocess.return_value = MagicMock(stdout="ok", stderr="")
        mock_save.return_value = mock_output
        
        # We need to mock the existence of tck2connectome
        with patch('code.data.preprocess_dMRI.subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0), # version check
                MagicMock(returncode=0)  # actual run
            ]
            
            result = generate_connectome_matrix(mock_tck, mock_nodes, "sub-001")
            
            # Check that tck2connectome was called
            calls = mock_run.call_args_list
            self.assertTrue(any("tck2connectome" in str(call) for call in calls))

    @patch('code.data.preprocess_dMRI.download_parcellation_file')
    @patch('code.data.preprocess_dMRI.verify_parcellation_file')
    @patch('code.data.preprocess_dMRI.load_tractography')
    def test_run_pipeline_handles_missing_subjects(self, mock_load_tck, mock_verify, mock_download):
        """Test that run_pipeline handles cases where no subjects are found."""
        from code.data.preprocess_dMRI import run_pipeline
        
        mock_download.return_value = Path(self.raw_dir) / "test.zip"
        mock_verify.return_value = True
        mock_load_tck.return_value = None # No tractography for any subject
        
        # Create empty matched_subjects
        subjects_file = Path(self.proc_dir) / "matched_subjects.json"
        with open(subjects_file, 'w') as f:
            json.dump({"subject_ids": []}, f)
        
        # We expect it to raise an error or return empty if no subjects
        # The current implementation raises ResearchError if no subjects found
        with self.assertRaises(Exception): # ResearchError
            run_pipeline()

if __name__ == '__main__':
    unittest.main()