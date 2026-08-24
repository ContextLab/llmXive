import os
import sys
import pytest
import pandas as pd
import hashlib
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path so we can import from analysis
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.write_dataset import calculate_file_checksum, write_processed_dataset

class TestWriteDataset:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        data = {
            'sample_id': ['S1', 'S2', 'S3'],
            'age': [25, 40, 60],
            'sex': ['M', 'F', 'M'],
            'population': ['EUR', 'AFR', 'EAS'],
            'haplogroup': ['H1', 'L2', 'D4'],
            'burden': [0.001, 0.005, 0.012]
        }
        return pd.DataFrame(data)

    def test_calculate_file_checksum(self, temp_dir, sample_dataframe):
        """Test that checksum calculation works correctly."""
        file_path = temp_dir / "test.csv"
        sample_dataframe.to_csv(file_path, index=False)
        
        checksum = calculate_file_checksum(file_path)
        
        assert isinstance(checksum, str)
        assert len(checksum) == 32  # MD5 hex digest length
        
        # Verify it matches the expected MD5
        with open(file_path, 'rb') as f:
            expected_checksum = hashlib.md5(f.read()).hexdigest()
        
        assert checksum == expected_checksum

    def test_calculate_file_checksum_file_not_found(self, temp_dir):
        """Test that FileNotFoundError is raised for missing file."""
        non_existent_path = temp_dir / "non_existent.csv"
        
        with pytest.raises(FileNotFoundError):
            calculate_file_checksum(non_existent_path)

    def test_write_processed_dataset(self, temp_dir, sample_dataframe):
        """Test that write_processed_dataset creates the file and returns checksum."""
        output_path = temp_dir / "output.csv"
        
        checksum = write_processed_dataset(sample_dataframe, output_path)
        
        # Check file exists
        assert output_path.exists()
        
        # Check file is not empty
        assert output_path.stat().st_size > 0
        
        # Check returned checksum matches file
        with open(output_path, 'rb') as f:
            expected_checksum = hashlib.md5(f.read()).hexdigest()
        
        assert checksum == expected_checksum

    def test_write_processed_dataset_creates_directory(self, temp_dir, sample_dataframe):
        """Test that write_processed_dataset creates parent directories."""
        nested_path = temp_dir / "subdir" / "output.csv"
        
        checksum = write_processed_dataset(sample_dataframe, nested_path)
        
        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_write_processed_dataset_empty_dataframe(self, temp_dir):
        """Test handling of an empty DataFrame."""
        empty_df = pd.DataFrame()
        output_path = temp_dir / "empty.csv"
        
        checksum = write_processed_dataset(empty_df, output_path)
        
        assert output_path.exists()
        # File should exist but might be empty or just headers
        assert output_path.stat().st_size >= 0