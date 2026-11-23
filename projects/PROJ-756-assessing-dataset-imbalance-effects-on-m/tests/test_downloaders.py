import os
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Import the module under test
from downloaders import (
    DataFetchError,
    calculate_sha256,
    download_file,
    verify_checksum,
    generate_checksum_file,
    update_state_file,
    load_huggingface_dataset,
    download_oqmd_constitution,
    download_materials_project
)

class TestDownloaders:
    """Test suite for downloader module."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    def test_calculate_sha256(self, temp_dir):
        """Test SHA-256 calculation."""
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        checksum = calculate_sha256(test_file)
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_verify_checksum(self, temp_dir):
        """Test checksum verification."""
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        checksum = calculate_sha256(test_file)
        assert verify_checksum(test_file, checksum) is True
        assert verify_checksum(test_file, "wronghash") is False

    def test_generate_checksum_file(self, temp_dir):
        """Test checksum file generation."""
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        checksum_file = os.path.join(temp_dir, "test.txt.sha256")
        generate_checksum_file(test_file, checksum_file)
        
        assert os.path.exists(checksum_file)
        with open(checksum_file, 'r') as f:
            content = f.read()
            assert len(content.split()[0]) == 64  # checksum length

    def test_update_state_file(self, temp_dir):
        """Test state file update."""
        project_id = "test-project"
        state_path = os.path.join(temp_dir, f"{project_id}.yaml")
        
        # Create state file
        update_state_file(project_id, "test.parquet", "abc123",)
        
        assert os.path.exists(state_path)
        
        # Verify content
        import yaml
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f)
        
        assert state_data["project_id"] == project_id
        assert state_data["artifact_hashes"]["test.parquet"] == "abc123"

    @patch('downloaders.load_dataset')
    def test_load_huggingface_dataset_success(self, mock_load_dataset, temp_dir):
        """Test successful HF dataset loading."""
        # Mock dataset
        mock_df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        mock_dataset = MagicMock()
        mock_dataset.to_pandas.return_value = mock_df
        mock_load_dataset.return_value = mock_dataset
        
        output_path = os.path.join(temp_dir, "test.parquet")
        
        load_huggingface_dataset(
            dataset_name="test/dataset",
            config_name="default",
            split="train",
            output_path=output_path,
            project_id="test-project"
        )
        
        assert os.path.exists(output_path)
        mock_load_dataset.assert_called_once_with("test/dataset", "default", split="train")

    @patch('downloaders.load_dataset')
    def test_load_huggingface_dataset_failure(self, mock_load_dataset, temp_dir):
        """Test HF dataset loading failure raises DataFetchError."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        output_path = os.path.join(temp_dir, "test.parquet")
        
        with pytest.raises(DataFetchError):
            load_huggingface_dataset(
                dataset_name="test/dataset",
                config_name="default",
                split="train",
                output_path=output_path,
                project_id="test-project"
            )

    def test_download_oqmd_constitution_structure(self, temp_dir):
        """Test OQMD download creates correct directory structure."""
        # Change to temp dir for isolation
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create necessary directories
            os.makedirs("data/raw", exist_ok=True)
            os.makedirs("state/projects", exist_ok=True)
            
            # Mock the load_huggingface_dataset function
            with patch('downloaders.load_huggingface_dataset') as mock_load:
                download_oqmd_constitution("test-project")
                
                # Verify directory was created
                assert os.path.exists("data/raw")
                
                # Verify load_huggingface_dataset was called with correct params
                mock_load.assert_called_once()
                args, kwargs = mock_load.call_args
                assert kwargs['dataset_name'] == "oqmd/oqmd"
                assert kwargs['config_name'] == "formation_energy_per_atom"
                assert kwargs['split'] == "train"
                assert kwargs['output_path'] == "data/raw/oqmd.parquet"
        finally:
            os.chdir(original_cwd)

    def test_download_materials_project_no_api_key(self, temp_dir):
        """Test MP download skips when no API key."""
        # Ensure no API key
        if 'MATERIALS_PROJECT_API_KEY' in os.environ:
            del os.environ['MATERIALS_PROJECT_API_KEY']
        
        with patch('downloaders.logger') as mock_logger:
            download_materials_project()
            
            # Verify warning was logged
            mock_logger.warning.assert_called()

    def test_download_materials_project_with_api_key(self, temp_dir):
        """Test MP download proceeds with API key."""
        with patch('downloaders.os.getenv', return_value="fake_api_key"):
            with patch('downloaders.logger') as mock_logger:
                # Should not raise, just log warning about implementation pending
                download_materials_project()
                
                # Verify it didn't crash
                assert True