import os
import sys
import csv
import tempfile
import shutil
from pathlib import Path
import pytest
import logging

# Add parent directory to path for imports if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.finalize_dataset import load_split_datasets, save_final_dataset, save_checksum
from config import DataConfig

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    # Create expected subdirectories
    split_dir = Path(temp_dir) / "data" / "split"
    processed_dir = Path(temp_dir) / "data" / "processed"
    split_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    
    # Create dummy split files
    headers = ['smiles', 'rate_constant', 'substrate_class']
    train_data = [
        {'smiles': 'CC(C)Br', 'rate_constant': '1.0', 'substrate_class': 'tertiary'},
        {'smiles': 'CCCBr', 'rate_constant': '0.5', 'substrate_class': 'secondary'}
    ]
    val_data = [
        {'smiles': 'CC(C)(C)Br', 'rate_constant': '2.0', 'substrate_class': 'tertiary'}
    ]
    test_data = [
        {'smiles': 'CCBr', 'rate_constant': '0.1', 'substrate_class': 'secondary'}
    ]

    def write_csv(path, data):
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)

    write_csv(split_dir / "train.csv", train_data)
    write_csv(split_dir / "val.csv", val_data)
    write_csv(split_dir / "test.csv", test_data)

    yield {
        'temp_root': temp_dir,
        'split_dir': split_dir,
        'processed_dir': processed_dir,
        'expected_combined_count': len(train_data) + len(val_data) + len(test_data)
    }

    shutil.rmtree(temp_dir)

def test_load_split_datasets(temp_data_dir):
    """Test loading the split datasets."""
    # Mock config to point to temp directory
    class MockConfig:
        split_dir = temp_data_dir['split_dir']
    
    config = MockConfig()
    data = load_split_datasets(config)
    
    assert 'train' in data
    assert 'val' in data
    assert 'test' in data
    assert len(data['train']) == 2
    assert len(data['val']) == 1
    assert len(data['test']) == 1

def test_save_final_dataset(temp_data_dir):
    """Test saving the combined dataset."""
    class MockConfig:
        split_dir = temp_data_dir['split_dir']
        processed_dir = temp_data_dir['processed_dir']
    
    config = MockConfig()
    data = load_split_datasets(config)
    
    all_rows = []
    all_rows.extend(data['train'])
    all_rows.extend(data['val'])
    all_rows.extend(data['test'])
    
    output_path = temp_data_dir['processed_dir'] / "test_output.csv"
    save_final_dataset(all_rows, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == temp_data_dir['expected_combined_count']
        # Check specific row content
        assert rows[0]['smiles'] == 'CC(C)Br'

def test_save_checksum(temp_data_dir):
    """Test checksum generation."""
    class MockConfig:
        split_dir = temp_data_dir['split_dir']
        processed_dir = temp_data_dir['processed_dir']
    
    config = MockConfig()
    data = load_split_datasets(config)
    
    all_rows = []
    all_rows.extend(data['train'])
    all_rows.extend(data['val'])
    all_rows.extend(data['test'])
    
    output_path = temp_data_dir['processed_dir'] / "test_checksum.csv"
    checksum_path = temp_data_dir['processed_dir'] / "test_checksum.csv.sha256"
    
    save_final_dataset(all_rows, output_path)
    save_checksum(output_path, checksum_path)
    
    assert checksum_path.exists()
    with open(checksum_path, 'r') as f:
        content = f.read()
        assert len(content.split()[0]) == 64 # SHA256 hex length
        assert "test_checksum.csv" in content