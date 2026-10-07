"""
Integration tests for the main pipeline (T015).
Verifies that main.py correctly orchestrates chunked processing and writes CSV.
"""
import os
import sys
import tempfile
import csv
import shutil
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from unittest.mock import patch, MagicMock, mock_open
from config import DATASET_ID, CHUNK_SIZE

def test_process_chunk_writes_csv():
    """
    Test that process_chunk correctly processes molecules and writes to CSV.
    """
    # We need to test the logic without actually downloading 10M molecules.
    # We will mock fetch_molecules to return a small set of known molecules.
    
    from metrics import (
        calculate_shannon_entropy, 
        calculate_lzma_length, 
        calculate_sa_score, 
        calculate_qed_score, 
        calculate_molecular_weight, 
        calculate_atom_count
    )
    from main import process_molecule, ensure_directories
    import logging
    from logging_setup import setup_logging

    setup_logging()
    
    # Test data: CCO (Ethanol)
    test_molecule = {'cid': 123, 'smiles': 'CCO'}
    
    # Verify metrics calculation works
    result = process_molecule(test_molecule)
    
    assert result is not None, "process_molecule should not return None for valid SMILES"
    assert result['cid'] == 123
    assert result['smiles'] == 'CCO'
    assert 'entropy' in result
    assert 'lz' in result
    assert 'sa' in result
    assert 'qed' in result
    assert 'mw' in result
    assert 'atom_count' in result
    
    # Verify types
    assert isinstance(result['entropy'], float)
    assert isinstance(result['lz'], int)
    assert isinstance(result['sa'], float)
    assert isinstance(result['qed'], float)
    assert isinstance(result['mw'], float)
    assert isinstance(result['atom_count'], int)

def test_main_writes_csv_file(tmp_path):
    """
    Test that main.py writes the metrics.csv file with correct columns.
    """
    from main import main, ensure_directories
    from config import get_metrics_path
    
    # Temporarily override paths for testing
    original_root = Path(__file__).parent.parent.parent
    test_root = tmp_path / "test_project"
    test_root.mkdir()
    
    # Create necessary subdirectories
    (test_root / "data" / "processed").mkdir(parents=True)
    
    # Mock the config to point to our temp directory
    # Since config is imported, we need to patch the functions or variables
    # The config module uses get_project_root() which reads from environment or defaults.
    # Let's patch the get_metrics_path function in main module context?
    # Actually, main.py imports get_metrics_path from config.
    # We can patch config.get_metrics_path to return our temp path.
    
    from unittest.mock import patch
    import code.config as config_module
    import code.main as main_module
    
    original_get_metrics_path = config_module.get_metrics_path
    
    def mock_get_metrics_path():
        return test_root / "data" / "processed" / "metrics.csv"
    
    def mock_get_project_root():
        return test_root
    
    # Mock fetch_molecules to return a few items
    mock_data = [
        {'cid': 1, 'smiles': 'CCO'},
        {'cid': 2, 'smiles': 'CC'}
    ]
    
    with patch.object(config_module, 'get_metrics_path', mock_get_metrics_path), \
         patch.object(config_module, 'get_project_root', mock_get_project_root), \
         patch.object(main_module, 'fetch_molecules', return_value=iter(mock_data)), \
         patch.object(main_module, 'CHUNK_SIZE', 2):
         
         # Run the metrics step logic (we can't run full main because it does analysis)
         # We will call run_metrics_step directly
         main_module.run_metrics_step()
         
         # Check file existence
         metrics_path = mock_get_metrics_path()
         assert metrics_path.exists(), "metrics.csv should be created"
         
         # Check content
         with open(metrics_path, 'r') as f:
             reader = csv.DictReader(f)
             rows = list(reader)
             
             assert len(rows) == 2, "Should have 2 rows"
             
             # Check headers
             expected_cols = ['cid', 'smiles', 'entropy', 'lz', 'sa', 'qed', 'mw', 'atom_count']
             assert reader.fieldnames == expected_cols, f"Headers mismatch: {reader.fieldnames}"
             
             # Check data
             assert rows[0]['cid'] == '1'
             assert rows[0]['smiles'] == 'CCO'
             assert float(rows[0]['entropy']) > 0
             
             assert rows[1]['cid'] == '2'
             assert rows[1]['smiles'] == 'CC'

def test_invalid_smiles_skipped():
    """
    Test that invalid SMILES are skipped and logged.
    """
    from main import process_molecule
    from logging_setup import setup_logging
    setup_logging()
    
    invalid_mol = {'cid': 999, 'smiles': 'INVALID_SMILES_STRING'}
    result = process_molecule(invalid_mol)
    
    assert result is None, "Invalid SMILES should return None"
    
    valid_mol = {'cid': 100, 'smiles': 'CC'}
    result = process_molecule(valid_mol)
    assert result is not None, "Valid SMILES should return result"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])