"""
Unit tests for T006: create_paired_samples_index.py

These tests verify that the PairedSampleIndex artifact is created correctly
by extracting valid samples from the intersection of expression and metabolite
data, excluding mismatches logged in the pairing log.
"""
import csv
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module
import code.create_paired_samples_index as module

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create necessary directories
        (root / "data" / "raw").mkdir(parents=True)
        (root / "logs").mkdir(parents=True)
        (root / "data" / "processed").mkdir(parents=True)
        yield root

@pytest.fixture
def mock_raw_files(temp_project_root):
    """Create mock raw data files with biosample_id columns."""
    expr_path = temp_project_root / "data" / "raw" / "geo_expression_matrix.csv"
    metab_path = temp_project_root / "data" / "raw" / "metabolite_matrix.csv"
    
    # Mock expression data
    # S1, S2, S3, S4
    with open(expr_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['gene_id', 'biosample_id', 'sample_1', 'sample_2'])
        writer.writerow(['GENE1', 'S1', '10.5', '20.0'])
        writer.writerow(['GENE2', 'S2', '15.0', '25.0'])
        writer.writerow(['GENE3', 'S3', '12.0', '22.0'])
        writer.writerow(['GENE4', 'S4', '18.0', '28.0'])
    
    # Mock metabolite data
    # S1, S2, S3, S5 (S5 not in expression)
    with open(metab_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['metabolite_id', 'biosample_id', 'sample_1', 'sample_2'])
        writer.writerow(['MET1', 'S1', '0.5', '0.6'])
        writer.writerow(['MET2', 'S2', '0.7', '0.8'])
        writer.writerow(['MET3', 'S3', '0.9', '1.0'])
        writer.writerow(['MET4', 'S5', '1.1', '1.2'])
    
    return expr_path, metab_path

@pytest.fixture
def mock_pairing_log(temp_project_root):
    """Create a mock pairing log with one mismatch (S3)."""
    log_path = temp_project_root / "logs" / "data_pairing.json"
    log_data = [
        {"sample_id": "S3", "reason": "biosample_id mismatch in metadata"}
    ]
    with open(log_path, 'w') as f:
        json.dump(log_data, f)
    return log_path

def test_load_pairing_log_success(mock_pairing_log):
    """Test loading a valid pairing log."""
    log_data = module.load_pairing_log(mock_pairing_log)
    assert isinstance(log_data, list)
    assert len(log_data) == 1
    assert log_data[0]["sample_id"] == "S3"

def test_load_pairing_log_not_found(temp_project_root):
    """Test loading a non-existent pairing log."""
    fake_path = temp_project_root / "logs" / "non_existent.json"
    with pytest.raises(FileNotFoundError):
        module.load_pairing_log(fake_path)

def test_get_biosample_ids_from_csv(temp_project_root):
    """Test extracting biosample IDs from a CSV."""
    expr_path = temp_project_root / "data" / "raw" / "geo_expression_matrix.csv"
    # Create a test file
    with open(expr_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['gene_id', 'biosample_id'])
        writer.writerow(['G1', 'A'])
        writer.writerow(['G2', 'B'])
        writer.writerow(['G3', 'A'])
    
    ids = module.get_biosample_ids_from_csv(expr_path)
    assert ids == {'A', 'B'}

def test_extract_valid_samples_logic(temp_project_root, mock_raw_files, mock_pairing_log):
    """
    Test the logic of extracting valid samples.
    
    Expression: S1, S2, S3, S4
    Metabolite: S1, S2, S3, S5
    Intersection: S1, S2, S3
    Mismatches: S3
    Expected Valid: S1, S2
    """
    # We need to patch the global paths in the module to point to our temp root
    original_root = module.PROJECT_ROOT
    original_log = module.PAIRING_LOG_PATH
    original_expr = module.RAW_EXPR_PATH
    original_metab = module.RAW_METAB_PATH
    
    try:
        module.PROJECT_ROOT = temp_project_root
        module.PAIRING_LOG_PATH = mock_pairing_log
        module.RAW_EXPR_PATH = mock_raw_files[0]
        module.RAW_METAB_PATH = mock_raw_files[1]
        
        log_data = module.load_pairing_log(mock_pairing_log)
        valid_samples = module.extract_valid_samples(log_data)
        
        assert valid_samples == {'S1', 'S2'}
    finally:
        # Restore
        module.PROJECT_ROOT = original_root
        module.PAIRING_LOG_PATH = original_log
        module.RAW_EXPR_PATH = original_expr
        module.RAW_METAB_PATH = original_metab

def test_save_paired_samples_index(temp_project_root):
    """Test saving the paired samples index."""
    output_path = temp_project_root / "data" / "processed" / "test_output.csv"
    samples = {"S1", "S2", "S3"}
    
    module.save_paired_samples_index(samples, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ['sample_id']
        rows = list(reader)
        assert len(rows) == 3
        ids = {row[0] for row in rows}
        assert ids == samples

def test_main_integration(temp_project_root, mock_raw_files, mock_pairing_log):
    """
    Integration test for the main function.
    """
    # Patch the global paths
    original_root = module.PROJECT_ROOT
    original_log = module.PAIRING_LOG_PATH
    original_expr = module.RAW_EXPR_PATH
    original_metab = module.RAW_METAB_PATH
    original_out = module.OUTPUT_PATH
    
    try:
        module.PROJECT_ROOT = temp_project_root
        module.PAIRING_LOG_PATH = mock_pairing_log
        module.RAW_EXPR_PATH = mock_raw_files[0]
        module.RAW_METAB_PATH = mock_raw_files[1]
        module.OUTPUT_PATH = temp_project_root / "data" / "processed" / "paired_samples.csv"
        
        # Run main
        module.main()
        
        # Verify output
        assert module.OUTPUT_PATH.exists()
        with open(module.OUTPUT_PATH, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ['sample_id']
            rows = list(reader)
            ids = {row[0] for row in rows}
            # Expected: S1, S2 (S3 is mismatch, S4/S5 not in intersection)
            assert ids == {"S1", "S2"}
    finally:
        # Restore
        module.PROJECT_ROOT = original_root
        module.PAIRING_LOG_PATH = original_log
        module.RAW_EXPR_PATH = original_expr
        module.RAW_METAB_PATH = original_metab
        module.OUTPUT_PATH = original_out