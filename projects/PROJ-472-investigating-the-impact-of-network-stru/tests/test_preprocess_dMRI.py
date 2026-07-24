import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.preprocess_dMRI import (
    compute_sha256,
    download_parcellation_file,
    verify_parcellation_file,
    load_tractography,
    generate_connectome_matrix,
    save_connectome_matrix,
    run_preprocessing_for_subject,
    run_pipeline
)
from code.utils.logger import ResearchError, DataLoadError

class TestComputeSha256(unittest.TestCase):
    def test_compute_sha256(self):
        """Test that compute_sha256 returns a valid hex string of correct length."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            temp_path = f.name
        
        try:
            hash_val = compute_sha256(Path(temp_path))
            self.assertEqual(len(hash_val), 64)  # SHA-256 hex length
            self.assertIsInstance(hash_val, str)
        finally:
            os.unlink(temp_path)

class TestDownloadParcellationFile(unittest.TestCase):
    @patch('code.data.preprocess_dMRI.HCP_MMP_FILE_PATH', 'test_parcellation.zip')
    @patch('code.data.preprocess_dMRI.HCP_MMP_URL', 'http://example.com/parcellation.zip')
    @patch('code.data.preprocess_dMRI.get_data_root')
    def test_download_parcellation_file(self, mock_get_data_root):
        """Test that download_parcellation_file creates the file and returns its path."""
        temp_dir = tempfile.mkdtemp()
        mock_get_data_root.return_value = Path(temp_dir)
        
        try:
            # Mock the urllib request
            with patch('code.data.preprocess_dMRI.urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.headers.get.return_value = '100'
                mock_response.read.side_effect = [b'data', b'']
                mock_urlopen.return_value.__enter__.return_value = mock_response
                
                file_path = download_parcellation_file()
                
                self.assertTrue(file_path.exists())
                self.assertEqual(file_path.name, 'test_parcellation.zip')
        finally:
            shutil.rmtree(temp_dir)

class TestVerifyParcellationFile(unittest.TestCase):
    def test_verify_parcellation_file_missing(self):
        """Test that verify_parcellation_file raises FileNotFoundError for missing file."""
        with self.assertRaises(FileNotFoundError):
            verify_parcellation_file(Path("/nonexistent/file.zip"))

    @patch('code.data.preprocess_dMRI.HCP_MMP_HASH', 'PLACEHOLDER_HASH_TO_BE_UPDATED')
    @patch('code.data.preprocess_dMRI.get_data_root')
    def test_verify_parcellation_file_placeholder(self, mock_get_data_root):
        """Test that verify_parcellation_file updates the hash file when placeholder is used."""
        temp_dir = tempfile.mkdtemp()
        processed_dir = Path(temp_dir) / "processed"
        processed_dir.mkdir()
        mock_get_data_root.return_value = Path(temp_dir)
        
        # Create a dummy file
        file_path = Path(temp_dir) / "raw" / "test.zip"
        file_path.parent.mkdir()
        file_path.write_text("dummy")
        
        try:
            result = verify_parcellation_file(file_path)
            self.assertTrue(result)
            
            # Check that hash file was created
            hash_file = processed_dir / "parcellation_hash.json"
            self.assertTrue(hash_file.exists())
            
            with open(hash_file) as f:
                data = json.load(f)
            self.assertIn("hash", data)
        finally:
            shutil.rmtree(temp_dir)

class TestLoadTractography(unittest.TestCase):
    @patch('code.data.preprocess_dMRI.get_data_root')
    def test_load_tractography_missing(self, mock_get_data_root):
        """Test that load_tractography raises FileNotFoundError for missing subject."""
        temp_dir = tempfile.mkdtemp()
        mock_get_data_root.return_value = Path(temp_dir)
        
        try:
            with self.assertRaises(FileNotFoundError):
                load_tractography("sub-01")
        finally:
            shutil.rmtree(temp_dir)

class TestRunPreprocessingForSubject(unittest.TestCase):
    @patch('code.data.preprocess_dMRI.download_parcellation_file')
    @patch('code.data.preprocess_dMRI.verify_parcellation_file')
    @patch('code.data.preprocess_dMRI.load_tractography')
    @patch('code.data.preprocess_dMRI.generate_connectome_matrix')
    @patch('code.data.preprocess_dMRI.save_connectome_matrix')
    @patch('code.data.preprocess_dMRI.get_data_root')
    def test_run_preprocessing_for_subject(
        self, mock_get_data_root, mock_save, mock_gen, mock_load, mock_verify, mock_download
    ):
        """Test the full preprocessing flow for a subject."""
        temp_dir = tempfile.mkdtemp()
        mock_get_data_root.return_value = Path(temp_dir)
        
        mock_download.return_value = Path(temp_dir) / "parcellation.zip"
        mock_load.return_value = Path(temp_dir) / "tracks.tck"
        mock_gen.return_value = Path(temp_dir) / "connectome.tsv"
        mock_save.return_value = {"subject_id": "sub-01", "success": True}
        
        try:
            result = run_preprocessing_for_subject("sub-01")
            self.assertEqual(result["subject_id"], "sub-01")
            self.assertTrue(result["success"])
        finally:
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    unittest.main()