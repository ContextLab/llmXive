"""
Unit tests for data retrieval and filtering logic (T011).

This module verifies the filtering logic and pass rate calculation
implemented in code/data/preprocessing.py (T010), which depends on
the retrieval logic from code/data/retrieval.py (T009).

Tests verify:
1. Filtering logic correctly removes records with NULL SMILES or logPapp
2. Pass rate calculation is accurate
3. Excluded records are properly categorized
"""

import os
import sys
import tempfile
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.preprocessing import load_raw_data, preprocess_data, write_clean_data

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test fixtures
def create_sample_raw_csv(filepath: Path, records: List[Dict[str, Any]]) -> None:
    """Create a sample raw CSV file with test data."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['smiles', 'logPapp', 'mw', 'psa', 'assay_id', 'standard_value', 'standard_units']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def test_filtering_logic_removes_null_smiles():
    """Test that records with NULL/empty SMILES are filtered out."""
    logger.info("Testing filtering logic for NULL SMILES...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        raw_csv = tmpdir_path / "raw_data.csv"
        clean_csv = tmpdir_path / "clean_data.csv"
        
        # Create sample data with some NULL SMILES
        records = [
            {'smiles': 'CCO', 'logPapp': -5.5, 'mw': 46.07, 'psa': 20.23, 'assay_id': 'A1', 'standard_value': '5.5e-6', 'standard_units': 'cm/s'},
            {'smiles': '', 'logPapp': -6.0, 'mw': 100.0, 'psa': 30.0, 'assay_id': 'A2', 'standard_value': '1.0e-6', 'standard_units': 'cm/s'},
            {'smiles': None, 'logPapp': -5.8, 'mw': 120.0, 'psa': 25.0, 'assay_id': 'A3', 'standard_value': '2.0e-6', 'standard_units': 'cm/s'},
            {'smiles': 'CCC', 'logPapp': -5.2, 'mw': 44.09, 'psa': 0.0, 'assay_id': 'A4', 'standard_value': '6.3e-6', 'standard_units': 'cm/s'},
        ]
        
        create_sample_raw_csv(raw_csv, records)
        
        # Load and preprocess
        raw_data = load_raw_data(raw_csv)
        clean_data, excluded_records, pass_rate = preprocess_data(raw_data)
        
        # Verify filtering
        assert len(clean_data) == 2, f"Expected 2 valid records, got {len(clean_data)}"
        assert all(record['smiles'] for record in clean_data), "All records should have non-NULL SMILES"
        
        # Verify excluded records
        assert len(excluded_records) == 2, f"Expected 2 excluded records, got {len(excluded_records)}"
        excluded_smiles = [r for r in excluded_records if r.get('reason') == 'null_smiles']
        assert len(excluded_smiles) == 2, "Both excluded records should be due to null SMILES"
        
        # Verify pass rate
        expected_pass_rate = 2 / 4 * 100  # 50%
        assert abs(pass_rate - expected_pass_rate) < 0.01, f"Expected pass rate {expected_pass_rate}%, got {pass_rate}%"
        
        logger.info("✓ Filtering logic for NULL SMILES passed")

def test_filtering_logic_removes_null_logpapp():
    """Test that records with NULL/empty logPapp are filtered out."""
    logger.info("Testing filtering logic for NULL logPapp...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        raw_csv = tmpdir_path / "raw_data.csv"
        clean_csv = tmpdir_path / "clean_data.csv"
        
        # Create sample data with some NULL logPapp
        records = [
            {'smiles': 'CCO', 'logPapp': -5.5, 'mw': 46.07, 'psa': 20.23, 'assay_id': 'A1', 'standard_value': '5.5e-6', 'standard_units': 'cm/s'},
            {'smiles': 'CC', 'logPapp': None, 'mw': 30.0, 'psa': 0.0, 'assay_id': 'A2', 'standard_value': '1.0e-6', 'standard_units': 'cm/s'},
            {'smiles': 'CCC', 'logPapp': '', 'mw': 44.09, 'psa': 0.0, 'assay_id': 'A3', 'standard_value': '2.0e-6', 'standard_units': 'cm/s'},
            {'smiles': 'CCCC', 'logPapp': -4.8, 'mw': 58.12, 'psa': 0.0, 'assay_id': 'A4', 'standard_value': '3.2e-6', 'standard_units': 'cm/s'},
        ]
        
        create_sample_raw_csv(raw_csv, records)
        
        # Load and preprocess
        raw_data = load_raw_data(raw_csv)
        clean_data, excluded_records, pass_rate = preprocess_data(raw_data)
        
        # Verify filtering
        assert len(clean_data) == 2, f"Expected 2 valid records, got {len(clean_data)}"
        assert all(record['logPapp'] is not None and record['logPapp'] != '' for record in clean_data), "All records should have non-NULL logPapp"
        
        # Verify excluded records
        assert len(excluded_records) == 2, f"Expected 2 excluded records, got {len(excluded_records)}"
        excluded_logpapp = [r for r in excluded_records if r.get('reason') == 'null_logpapp']
        assert len(excluded_logpapp) == 2, "Both excluded records should be due to null logPapp"
        
        # Verify pass rate
        expected_pass_rate = 2 / 4 * 100  # 50%
        assert abs(pass_rate - expected_pass_rate) < 0.01, f"Expected pass rate {expected_pass_rate}%, got {pass_rate}%"
        
        logger.info("✓ Filtering logic for NULL logPapp passed")

def test_pass_rate_calculation():
    """Test that pass rate is calculated correctly."""
    logger.info("Testing pass rate calculation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        raw_csv = tmpdir_path / "raw_data.csv"
        clean_csv = tmpdir_path / "clean_data.csv"
        
        # Create sample data: 10 records, 7 valid, 3 invalid
        records = [
            {'smiles': f'MOL{i}', 'logPapp': -5.0 - i * 0.1, 'mw': 100.0 + i, 'psa': 20.0, 'assay_id': f'A{i}', 'standard_value': '1.0e-6', 'standard_units': 'cm/s'}
            for i in range(7)
        ] + [
            {'smiles': '', 'logPapp': -5.0, 'mw': 100.0, 'psa': 20.0, 'assay_id': f'A{i}', 'standard_value': '1.0e-6', 'standard_units': 'cm/s'}
            for i in range(7, 8)
        ] + [
            {'smiles': f'MOL{i}', 'logPapp': None, 'mw': 100.0 + i, 'psa': 20.0, 'assay_id': f'A{i}', 'standard_value': '1.0e-6', 'standard_units': 'cm/s'}
            for i in range(8, 10)
        ]
        
        create_sample_raw_csv(raw_csv, records)
        
        # Load and preprocess
        raw_data = load_raw_data(raw_csv)
        clean_data, excluded_records, pass_rate = preprocess_data(raw_data)
        
        # Verify pass rate
        expected_pass_rate = 7 / 10 * 100  # 70%
        assert abs(pass_rate - expected_pass_rate) < 0.01, f"Expected pass rate {expected_pass_rate}%, got {pass_rate}%"
        
        # Verify counts
        assert len(clean_data) == 7, f"Expected 7 valid records, got {len(clean_data)}"
        assert len(excluded_records) == 3, f"Expected 3 excluded records, got {len(excluded_records)}"
        
        logger.info("✓ Pass rate calculation passed")

def test_filtering_logic_handles_mixed_invalid():
    """Test filtering with a mix of NULL SMILES and NULL logPapp."""
    logger.info("Testing filtering logic with mixed invalid records...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        raw_csv = tmpdir_path / "raw_data.csv"
        clean_csv = tmpdir_path / "clean_data.csv"
        
        # Create sample data with mixed invalid records
        records = [
            # Valid records
            {'smiles': 'CCO', 'logPapp': -5.5, 'mw': 46.07, 'psa': 20.23, 'assay_id': 'A1', 'standard_value': '5.5e-6', 'standard_units': 'cm/s'},
            {'smiles': 'CCC', 'logPapp': -5.2, 'mw': 44.09, 'psa': 0.0, 'assay_id': 'A2', 'standard_value': '6.3e-6', 'standard_units': 'cm/s'},
            {'smiles': 'CCCC', 'logPapp': -4.8, 'mw': 58.12, 'psa': 0.0, 'assay_id': 'A3', 'standard_value': '3.2e-6', 'standard_units': 'cm/s'},
            # Invalid: NULL SMILES
            {'smiles': '', 'logPapp': -6.0, 'mw': 100.0, 'psa': 30.0, 'assay_id': 'A4', 'standard_value': '1.0e-6', 'standard_units': 'cm/s'},
            {'smiles': None, 'logPapp': -5.8, 'mw': 120.0, 'psa': 25.0, 'assay_id': 'A5', 'standard_value': '2.0e-6', 'standard_units': 'cm/s'},
            # Invalid: NULL logPapp
            {'smiles': 'CC', 'logPapp': None, 'mw': 30.0, 'psa': 0.0, 'assay_id': 'A6', 'standard_value': '1.0e-6', 'standard_units': 'cm/s'},
            {'smiles': 'CC', 'logPapp': '', 'mw': 30.0, 'psa': 0.0, 'assay_id': 'A7', 'standard_value': '1.0e-6', 'standard_units': 'cm/s'},
            # Invalid: Both NULL
            {'smiles': '', 'logPapp': None, 'mw': 100.0, 'psa': 20.0, 'assay_id': 'A8', 'standard_value': '1.0e-6', 'standard_units': 'cm/s'},
        ]
        
        create_sample_raw_csv(raw_csv, records)
        
        # Load and preprocess
        raw_data = load_raw_data(raw_csv)
        clean_data, excluded_records, pass_rate = preprocess_data(raw_data)
        
        # Verify filtering
        assert len(clean_data) == 3, f"Expected 3 valid records, got {len(clean_data)}"
        assert all(record['smiles'] for record in clean_data), "All records should have non-NULL SMILES"
        assert all(record['logPapp'] is not None and record['logPapp'] != '' for record in clean_data), "All records should have non-NULL logPapp"
        
        # Verify excluded records
        assert len(excluded_records) == 5, f"Expected 5 excluded records, got {len(excluded_records)}"
        
        # Categorize excluded records
        null_smiles = [r for r in excluded_records if r.get('reason') == 'null_smiles']
        null_logpapp = [r for r in excluded_records if r.get('reason') == 'null_logpapp']
        
        # At least 3 should be due to null SMILES (A4, A5, A8)
        assert len(null_smiles) >= 3, f"Expected at least 3 null SMILES exclusions, got {len(null_smiles)}"
        # At least 2 should be due to null logPapp (A6, A7, A8)
        assert len(null_logpapp) >= 2, f"Expected at least 2 null logPapp exclusions, got {len(null_logpapp)}"
        
        # Verify pass rate
        expected_pass_rate = 3 / 8 * 100  # 37.5%
        assert abs(pass_rate - expected_pass_rate) < 0.01, f"Expected pass rate {expected_pass_rate}%, got {pass_rate}%"
        
        logger.info("✓ Filtering logic with mixed invalid records passed")

def test_write_clean_data_creates_file():
    """Test that write_clean_data creates the output file correctly."""
    logger.info("Testing write_clean_data file creation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        clean_csv = tmpdir_path / "clean_data.csv"
        
        clean_data = [
            {'smiles': 'CCO', 'logPapp': -5.5, 'mw': 46.07, 'psa': 20.23, 'assay_id': 'A1'},
            {'smiles': 'CCC', 'logPapp': -5.2, 'mw': 44.09, 'psa': 0.0, 'assay_id': 'A2'},
        ]
        
        write_clean_data(clean_data, clean_csv)
        
        # Verify file exists
        assert clean_csv.exists(), "Output file should exist"
        
        # Verify content
        with open(clean_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2, f"Expected 2 rows in output, got {len(rows)}"
        assert all('smiles' in row and 'logPapp' in row for row in rows), "All rows should have required fields"
        
        logger.info("✓ write_clean_data file creation passed")

def test_empty_input_handling():
    """Test handling of empty input data."""
    logger.info("Testing empty input handling...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        raw_csv = tmpdir_path / "raw_data.csv"
        clean_csv = tmpdir_path / "clean_data.csv"
        
        # Create empty CSV with headers only
        records = []
        create_sample_raw_csv(raw_csv, records)
        
        # Load and preprocess
        raw_data = load_raw_data(raw_csv)
        clean_data, excluded_records, pass_rate = preprocess_data(raw_data)
        
        # Verify results
        assert len(clean_data) == 0, "Empty input should produce empty output"
        assert len(excluded_records) == 0, "Empty input should have no excluded records"
        assert pass_rate == 0.0, "Pass rate for empty input should be 0%"
        
        logger.info("✓ Empty input handling passed")

if __name__ == '__main__':
    logger.info("Running data filtering unit tests...")
    
    test_filtering_logic_removes_null_smiles()
    test_filtering_logic_removes_null_logpapp()
    test_pass_rate_calculation()
    test_filtering_logic_handles_mixed_invalid()
    test_write_clean_data_creates_file()
    test_empty_input_handling()
    
    logger.info("All data filtering unit tests passed successfully!")