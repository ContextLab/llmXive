import pytest
import pandas as pd
import json
from pathlib import Path
from code.data.download import DataLoader
from llmxive_toolkit import paths


class TestDataLoader:
    """Unit tests for DataLoader class."""
    
    def test_target_column_exists(self):
        """Test that the loaded dataset contains the required target column."""
        loader = DataLoader()
        
        # Mock a simple dataframe with required columns
        test_df = pd.DataFrame({
            'smiles': ['CC', 'CCO', 'CCOC'],
            'logP': [0.5, -0.31, 0.07]
        })
        
        # Validate should not raise
        loader.target_column = 'logP'
        loader.smiles_column = 'smiles'
        loader.validate_target(test_df)
        
        # Should pass without exception
        assert 'logP' in test_df.columns
    
    def test_target_column_missing_raises(self):
        """Test that missing target column raises RuntimeError."""
        loader = DataLoader()
        
        test_df = pd.DataFrame({
            'smiles': ['CC', 'CCO'],
            'other_col': [1, 2]
        })
        
        loader.target_column = 'logP'
        loader.smiles_column = 'smiles'
        
        with pytest.raises(RuntimeError, match="Required target column"):
            loader.validate_target(test_df)
    
    def test_smiles_column_missing_raises(self):
        """Test that missing SMILES column raises RuntimeError."""
        loader = DataLoader()
        
        test_df = pd.DataFrame({
            'logP': [0.5, -0.31],
            'other_col': [1, 2]
        })
        
        loader.target_column = 'logP'
        loader.smiles_column = 'smiles'
        
        with pytest.raises(RuntimeError, match="Required SMILES column"):
            loader.validate_target(test_df)
    
    def test_checksum_computation(self):
        """Test that checksums are computed correctly."""
        loader = DataLoader()
        
        # Create a temporary test file
        test_file = paths.data("raw", "test_checksum.csv")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        test_content = "a,b,c\n1,2,3\n4,5,6\n"
        test_file.write_text(test_content)
        
        # Compute checksum
        checksum = loader.compute_checksum(test_file)
        
        # Verify it's a valid hex string of length 64 (SHA-256)
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)
        
        # Clean up
        test_file.unlink()
    
    def test_checksums_json_written(self):
        """Test that checksums.json is written correctly."""
        loader = DataLoader()
        
        # Create a test file
        test_file = paths.data("raw", "test_data.csv")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("a,b\n1,2\n")
        
        checksum = loader.compute_checksum(test_file)
        checksum_path = test_file.parent / "checksums.json"
        
        loader.write_checksums({"test_data.csv": checksum}, checksum_path)
        
        # Verify file was written
        assert checksum_path.exists()
        
        # Verify content
        with open(checksum_path, 'r') as f:
            data = json.load(f)
        
        assert "test_data.csv" in data
        assert data["test_data.csv"] == checksum
        
        # Clean up
        test_file.unlink()
        checksum_path.unlink()