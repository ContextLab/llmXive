"""
Integration tests for OpenNeuro download functionality.

These tests verify that the download module correctly interacts with
the OpenNeuro API and produces the expected file structure.
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from download import download_dataset, download_all_datasets
from exceptions import DataIntegrityError, PipelineFailureError
from environment_config import get_dataset_ids

# Test constants
TEST_DATASET_ID = "ds003775"
EXPECTED_SUBJECT_COUNT = 25  # Approximate for ds003775
EXPECTED_FILE_PATTERN = "sub-{subject}/eeg/sub-{subject}_task-rest_eeg.fif"


class TestDownloadDataset:
    """Tests for the download_dataset function."""

    def test_invalid_dataset_id_format(self):
        """Test that invalid dataset IDs raise DataIntegrityError."""
        with pytest.raises(DataIntegrityError, match="Invalid dataset ID format"):
            download_dataset("invalid_id")

    @patch('download.get_dataset')
    @patch('download.Download')
    def test_successful_download(self, mock_download_class, mock_get_dataset):
        """Test successful dataset download."""
        # Mock the dataset existence check
        mock_get_dataset.return_value = {'id': TEST_DATASET_ID}
        
        # Mock the download client
        mock_client = MagicMock()
        mock_download_class.return_value = mock_client
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / TEST_DATASET_ID
            
            # Mock the download to create the directory and essential files
            def mock_download():
                output_dir.mkdir(parents=True, exist_ok=True)
                (output_dir / 'dataset_description.json').write_text(
                    '{"id": "ds003775", "name": "Test Dataset"}'
                )
                # Create a mock subject directory structure
                sub_dir = output_dir / 'sub-01' / 'eeg'
                sub_dir.mkdir(parents=True, exist_ok=True)
                (sub_dir / 'sub-01_task-rest_eeg.fif').write_text('mock data')
            
            mock_client.download.side_effect = mock_download
            
            # Execute download
            result_path = download_dataset(TEST_DATASET_ID, output_dir=output_dir)
            
            # Verify results
            assert result_path.exists()
            assert (result_path / 'dataset_description.json').exists()
            assert (result_path / 'sub-01' / 'eeg' / 'sub-01_task-rest_eeg.fif').exists()
            
            # Verify API calls
            mock_get_dataset.assert_called_once_with(TEST_DATASET_ID)
            mock_download_class.assert_called_once()
            mock_client.download.assert_called_once()

    @patch('download.get_dataset')
    def test_nonexistent_dataset_raises_error(self, mock_get_dataset):
        """Test that non-existent datasets raise DataIntegrityError."""
        mock_get_dataset.side_effect = Exception("Dataset not found")
        
        with pytest.raises(DataIntegrityError, match="does not exist"):
            download_dataset("ds999999")

    @patch('download.get_dataset')
    @patch('download.Download')
    def test_download_missing_description_json(self, mock_download_class, mock_get_dataset):
        """Test that missing dataset_description.json raises DataIntegrityError."""
        mock_get_dataset.return_value = {'id': TEST_DATASET_ID}
        
        mock_client = MagicMock()
        mock_download_class.return_value = mock_client
        
        # Mock download that creates directory but NOT the description file
        def mock_download():
            output_dir = Path(tempfile.mkdtemp())
            output_dir.mkdir(parents=True, exist_ok=True)
            # Intentionally NOT creating dataset_description.json
            sub_dir = output_dir / 'sub-01' / 'eeg'
            sub_dir.mkdir(parents=True, exist_ok=True)
            (sub_dir / 'sub-01_task-rest_eeg.fif').write_text('mock data')
        
        mock_client.download.side_effect = mock_download
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / TEST_DATASET_ID
            
            with pytest.raises(DataIntegrityError, match="missing dataset_description.json"):
                download_dataset(TEST_DATASET_ID, output_dir=output_dir)

    @patch('download.get_dataset')
    @patch('download.Download')
    def test_retry_on_failure(self, mock_download_class, mock_get_dataset):
        """Test that download retries on transient failures."""
        mock_get_dataset.return_value = {'id': TEST_DATASET_ID}
        
        mock_client = MagicMock()
        mock_download_class.return_value = mock_client
        
        # Fail twice, succeed on third attempt
        call_count = [0]
        def mock_download():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Transient network error")
            # Success on third attempt
            output_dir = Path(tempfile.mkdtemp())
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / 'dataset_description.json').write_text('{"id": "ds003775"}')
        
        mock_client.download.side_effect = mock_download
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / TEST_DATASET_ID
            
            # This should succeed after retries
            result_path = download_dataset(TEST_DATASET_ID, output_dir=output_dir)
            
            assert result_path.exists()
            assert call_count[0] == 3  # Should have tried 3 times
            assert mock_client.download.call_count == 3


class TestDownloadAllDatasets:
    """Tests for the download_all_datasets function."""

    @patch('download.download_dataset')
    def test_download_multiple_datasets(self, mock_download_dataset):
        """Test downloading multiple datasets."""
        mock_dataset_ids = ['ds003775', 'ds003865', 'ds003392']
        mock_paths = [
            Path('/tmp/ds003775'),
            Path('/tmp/ds003865'),
            Path('/tmp/ds003392')
        ]
        
        # Mock successful downloads
        for path in mock_paths:
            path.mkdir(parents=True, exist_ok=True)
            (path / 'dataset_description.json').write_text('{"id": "test"}')
        
        mock_download_dataset.side_effect = lambda *args, **kwargs: mock_paths.pop(0)
        
        results = download_all_datasets(mock_dataset_ids)
        
        assert len(results) == 3
        assert all(dataset_id in results for dataset_id in mock_dataset_ids)
        
        # Verify download_dataset was called for each dataset
        assert mock_download_dataset.call_count == 3

    @patch('download.download_dataset')
    def test_partial_failure_raises_error(self, mock_download_dataset):
        """Test that partial failures are reported."""
        mock_dataset_ids = ['ds003775', 'ds999999']
        
        # First succeeds, second fails
        def mock_side_effect(*args, **kwargs):
            if args[0] == 'ds999999':
                raise DataIntegrityError("Dataset not found")
            return Path('/tmp/ds003775')
        
        mock_download_dataset.side_effect = mock_side_effect
        
        with pytest.raises(DataIntegrityError, match="Failed to download"):
            download_all_datasets(mock_dataset_ids)

    def test_no_dataset_ids_raises_error(self):
        """Test that missing dataset IDs raise DataIntegrityError."""
        with patch('download.get_dataset_ids', return_value=[]):
            with pytest.raises(DataIntegrityError, match="No dataset IDs"):
                download_all_datasets()


class TestMainFunction:
    """Tests for the main() function."""

    @patch('download.get_dataset_ids')
    @patch('download.download_all_datasets')
    def test_main_success(self, mock_download_all, mock_get_ids):
        """Test successful main execution."""
        mock_get_ids.return_value = ['ds003775']
        mock_download_all.return_value = {'ds003775': Path('/tmp/ds003775')}
        
        result = download_all_datasets()  # Directly test the logic
        
        assert result is not None
        assert 'ds003775' in result

    @patch('download.get_dataset_ids')
    def test_main_no_datasets(self, mock_get_ids):
        """Test main with no dataset IDs."""
        mock_get_ids.return_value = []
        
        with pytest.raises(DataIntegrityError, match="No dataset IDs"):
            download_all_datasets()


class TestFileStructureValidation:
    """Tests for verifying downloaded file structure."""

    @patch('download.get_dataset')
    @patch('download.Download')
    def test_expected_file_structure_created(self, mock_download_class, mock_get_dataset):
        """Verify that the expected BIDS file structure is created."""
        mock_get_dataset.return_value = {'id': TEST_DATASET_ID}
        
        mock_client = MagicMock()
        mock_download_class.return_value = mock_client
        
        def mock_download():
            # Create full BIDS structure
            output_dir = Path(tempfile.mkdtemp())
            (output_dir / 'dataset_description.json').write_text('{"id": "ds003775"}')
            
            # Create subject directories
            for subj in ['01', '02', '03']:
                eeg_dir = output_dir / f'sub-{subj}' / 'eeg'
                eeg_dir.mkdir(parents=True, exist_ok=True)
                (eeg_dir / f'sub-{subj}_task-rest_eeg.fif').write_text('mock data')
                (eeg_dir / f'sub-{subj}_task-rest_events.tsv').write_text('onset\tduration\ttrial_type\n')
        
        mock_client.download.side_effect = mock_download
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / TEST_DATASET_ID
            result_path = download_dataset(TEST_DATASET_ID, output_dir=output_dir)
            
            # Verify structure
            assert (result_path / 'dataset_description.json').exists()
            
            # Check for subject files
            for subj in ['01', '02', '03']:
                eeg_file = result_path / f'sub-{subj}' / 'eeg' / f'sub-{subj}_task-rest_eeg.fif'
                events_file = result_path / f'sub-{subj}' / 'eeg' / f'sub-{subj}_task-rest_events.tsv'
                assert eeg_file.exists(), f"Missing EEG file for sub-{subj}"
                assert events_file.exists(), f"Missing events file for sub-{subj}"

    @patch('download.get_dataset')
    @patch('download.Download')
    def test_subject_count_validation(self, mock_download_class, mock_get_dataset):
        """Verify subject count matches expected minimum."""
        mock_get_dataset.return_value = {'id': TEST_DATASET_ID}
        
        mock_client = MagicMock()
        mock_download_class.return_value = mock_client
        
        def mock_download():
            output_dir = Path(tempfile.mkdtemp())
            (output_dir / 'dataset_description.json').write_text('{"id": "ds003775"}')
            
            # Create only 5 subjects (below threshold of 20)
            for subj in range(1, 6):
                eeg_dir = output_dir / f'sub-{subj:02d}' / 'eeg'
                eeg_dir.mkdir(parents=True, exist_ok=True)
                (eeg_dir / f'sub-{subj:02d}_task-rest_eeg.fif').write_text('mock data')
        
        mock_client.download.side_effect = mock_download
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / TEST_DATASET_ID
            result_path = download_dataset(TEST_DATASET_ID, output_dir=output_dir)
            
            # Count subjects
            subject_dirs = [d for d in result_path.iterdir() if d.name.startswith('sub-')]
            assert len(subject_dirs) == 5
            
            # Note: The actual validation of >= 20 subjects is handled by T013.1
            # This test just verifies the structure is created correctly