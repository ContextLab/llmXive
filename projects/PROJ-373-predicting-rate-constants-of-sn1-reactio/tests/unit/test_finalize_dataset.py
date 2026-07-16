import os
import sys
import csv
import tempfile
import shutil
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.finalize_dataset import load_split_datasets, save_final_dataset, save_checksum

def test_load_split_datasets():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        # Create mock split files
        splits = ['train.csv', 'val.csv', 'test.csv']
        for i, split in enumerate(splits):
            file_path = base_path / split
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['smiles', 'rate_constant'])
                writer.writeheader()
                # Write i+1 rows
                for j in range(i + 1):
                    writer.writerow({'smiles': f'C{j}', 'rate_constant': str(j)})
        
        datasets = load_split_datasets(base_path)
        
        assert len(datasets) == 3
        assert len(datasets[0]) == 1  # train
        assert len(datasets[1]) == 2  # val
        assert len(datasets[2]) == 3  # test

def test_save_final_dataset():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        # Create mock data
        datasets = [
            [{'smiles': 'C1', 'rate_constant': '1.0'}],
            [{'smiles': 'C2', 'rate_constant': '2.0'}, {'smiles': 'C3', 'rate_constant': '3.0'}]
        ]
        
        output_path = base_path / 'final.csv'
        save_final_dataset(datasets, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 3
        assert rows[0]['smiles'] == 'C1'
        assert rows[1]['smiles'] == 'C2'

def test_save_checksum():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / 'test.txt'
        file_path.write_text("test content")
        
        checksum_path = Path(tmpdir) / 'test.txt.sha256'
        save_checksum(file_path, checksum_path)
        
        assert checksum_path.exists()
        checksum_content = checksum_path.read_text().strip()
        assert len(checksum_content) == 64  # SHA256 hex length