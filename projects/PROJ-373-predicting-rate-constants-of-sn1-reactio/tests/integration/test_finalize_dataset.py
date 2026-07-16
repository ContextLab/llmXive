import os
import sys
import tempfile
import csv
from pathlib import Path
import pandas as pd
import pytest

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from data.finalize_dataset import load_split_datasets, save_final_dataset, save_checksum
from utils.checksum import verify_file_checksum

@pytest.fixture
def temp_split_dir():
    """Create a temporary directory with dummy train, val, test CSVs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create dummy data
        dummy_data = {
            'smiles': ['CC(C)CBr', 'CC(Br)C', 'CC(C)(C)Br'],
            'rate_constant': [1.0, 2.0, 3.0],
            'substrate_class': ['secondary', 'secondary', 'tertiary']
        }
        
        for split_name in ['train', 'val', 'test']:
            df = pd.DataFrame(dummy_data)
            # Add some noise to make them distinct but valid
            if split_name == 'val':
                df['rate_constant'] = [4.0, 5.0, 6.0]
            elif split_name == 'test':
                df['rate_constant'] = [7.0, 8.0, 9.0]
            
            df.to_csv(tmpdir_path / f"{split_name}.csv", index=False)
        
        yield tmpdir_path

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_split_datasets(temp_split_dir):
    """Test that load_split_datasets correctly concatenates train, val, test."""
    df = load_split_datasets(temp_split_dir)
    
    # We have 3 rows in each of 3 splits
    assert len(df) == 9
    assert 'smiles' in df.columns
    assert 'rate_constant' in df.columns
    assert 'substrate_class' in df.columns

def test_save_final_dataset(temp_split_dir, temp_output_dir):
    """Test saving the final dataset."""
    df = load_split_datasets(temp_split_dir)
    output_file = temp_output_dir / "cleaned_sn1.csv"
    
    save_final_dataset(df, output_file)
    
    assert output_file.exists()
    
    # Verify content
    loaded_df = pd.read_csv(output_file)
    assert len(loaded_df) == 9
    assert list(loaded_df.columns) == ['smiles', 'rate_constant', 'substrate_class']

def test_save_and_verify_checksum(temp_split_dir, temp_output_dir):
    """Test saving and verifying the checksum."""
    df = load_split_datasets(temp_split_dir)
    output_file = temp_output_dir / "cleaned_sn1.csv"
    checksum_file = temp_output_dir / "cleaned_sn1.csv.sha256"
    
    save_final_dataset(df, output_file)
    save_checksum(output_file, checksum_file)
    
    assert checksum_file.exists()
    
    # Verify checksum
    is_valid = verify_file_checksum(output_file, checksum_file)
    assert is_valid, "Checksum verification failed"

def test_full_pipeline(temp_split_dir, temp_output_dir):
    """Test the full pipeline: load, save, checksum, verify."""
    df = load_split_datasets(temp_split_dir)
    output_file = temp_output_dir / "cleaned_sn1.csv"
    checksum_file = temp_output_dir / "cleaned_sn1.csv.sha256"
    
    save_final_dataset(df, output_file)
    save_checksum(output_file, checksum_file)
    
    # Verify file exists
    assert output_file.exists()
    assert checksum_file.exists()
    
    # Verify checksum
    is_valid = verify_file_checksum(output_file, checksum_file)
    assert is_valid
    
    # Verify data integrity
    loaded_df = pd.read_csv(output_file)
    assert len(loaded_df) == 9
    assert not loaded_df.isnull().any().any()