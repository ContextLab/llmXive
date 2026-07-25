"""
Tests for data ingestion module.
"""
import pytest
import pandas as pd
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import numpy as np

# Import the module
import sys
sys.path.insert(0, 'code')
from data_ingestion import (
    verify_checksum,
    calculate_partial_charges_internal_only,
    engineer_features,
    merge_consistency_artifacts,
    extract_structures_from_data,
    DataIngestionError
)

@pytest.fixture
def sample_df():
    """Create a sample dataframe for testing."""
    return pd.DataFrame({
        'cation_id': ['C001', 'C002'],
        'anion_id': ['A001', 'A002'],
        'smiles_cation': ['CCO', 'CN(C)C'],
        'smiles_anion': ['[Cl-]', '[Br-]'],
        'structural_family': ['alcohol', 'amine']
    })

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

def test_verify_checksum():
    """Test checksum verification."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        temp_path = f.name
    
    try:
        # Calculate actual hash
        import hashlib
        sha256_hash = hashlib.sha256(b"test data").hexdigest()
        
        # Test correct hash
        assert verify_checksum(temp_path, sha256_hash) == True
        
        # Test incorrect hash
        assert verify_checksum(temp_path, "wrong_hash") == False
        
    finally:
        os.unlink(temp_path)

def test_calculate_partial_charges_internal_only(sample_df, temp_dir):
    """Test partial charge calculation."""
    # Mock the output path
    original_path = "data/processed/internal_consistency_checks.parquet"
    test_path = os.path.join(temp_dir, "test_consistency.parquet")
    
    with patch('data_ingestion.os.makedirs'), \
         patch('data_ingestion.logger'), \
         patch('data_ingestion.pd.DataFrame.to_parquet') as mock_to_parquet:
        
        result = calculate_partial_charges_internal_only(sample_df)
        
        # Verify partial_charge column was added
        assert 'partial_charge' in result.columns
        assert len(result) == len(sample_df)
        
        # Verify to_parquet was called
        mock_to_parquet.assert_called_once()

def test_engineer_features(sample_df, temp_dir):
    """Test feature engineering."""
    with patch('data_ingestion.calculate_partial_charges_internal_only') as mock_calc, \
         patch('data_ingestion.os.makedirs'), \
         patch('data_ingestion.logger'), \
         patch('data_ingestion.pd.DataFrame.to_parquet') as mock_to_parquet:
        
        # Mock the partial charge calculation to return a simple dataframe
        mock_calc.return_value = sample_df.copy()
        
        result = engineer_features(sample_df)
        
        # Verify expected columns were added
        expected_cols = ['cation_tpsa', 'anion_tpsa', 'total_tpsa', 
                       'cation_surface_area', 'anion_surface_area', 'total_surface_area',
                       'cation_hbond_count', 'anion_hbond_count', 'total_hbond_count']
        
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"

def test_merge_consistency_artifacts(temp_dir):
    """Test merging consistency artifacts."""
    # Create test data
    unified_df = pd.DataFrame({
        'cation_id': ['C001', 'C002'],
        'anion_id': ['A001', 'A002'],
        'smiles_cation': ['CCO', 'CN(C)C'],
        'smiles_anion': ['[Cl-]', '[Br-]'],
        'structural_family': ['alcohol', 'amine']
    })
    
    consistency_df = pd.DataFrame({
        'cation_id': ['C001', 'C002'],
        'anion_id': ['A001', 'A002'],
        'partial_charge': [0.5, 0.6]
    })
    
    # Save test files
    os.makedirs(os.path.join(temp_dir, 'processed'), exist_ok=True)
    unified_path = os.path.join(temp_dir, 'processed', 'unified_dataset.parquet')
    consistency_path = os.path.join(temp_dir, 'processed', 'internal_consistency_checks.parquet')
    
    unified_df.to_parquet(unified_path)
    consistency_df.to_parquet(consistency_path)
    
    # Patch paths
    with patch('data_ingestion.os.path.exists', side_effect=lambda x: True if x in [consistency_path, unified_path] else False), \
         patch('data_ingestion.pd.read_parquet', side_effect=[consistency_df, unified_df]), \
         patch('data_ingestion.os.path.dirname', return_value=os.path.join(temp_dir, 'processed')), \
         patch('data_ingestion.os.makedirs'), \
         patch('data_ingestion.logger'), \
         patch('data_ingestion.pd.DataFrame.to_parquet') as mock_to_parquet:
        
        result = merge_consistency_artifacts()
        
        # Verify partial_charge is in result
        assert 'partial_charge' in result.columns
        assert len(result) == 2

def test_extract_structures_from_data(temp_dir):
    """Test structure extraction."""
    # Create a sample parquet file
    sample_df = pd.DataFrame({
        'cation_id': ['C001', 'C002'],
        'anion_id': ['A001', 'A002'],
        'smiles_cation': ['CCO', 'CN(C)C'],
        'smiles_anion': ['[Cl-]', '[Br-]'],
        'structural_family': ['alcohol', 'amine']
    })
    
    os.makedirs(os.path.join(temp_dir, 'raw'), exist_ok=True)
    spice_path = os.path.join(temp_dir, 'raw', 'spice.parquet')
    sample_df.to_parquet(spice_path)
    
    with patch('data_ingestion.os.path.exists', side_effect=lambda x: x == spice_path), \
         patch('data_ingestion.pd.read_parquet', return_value=sample_df), \
         patch('data_ingestion.os.path.dirname', return_value=os.path.join(temp_dir, 'raw')), \
         patch('data_ingestion.os.makedirs'), \
         patch('data_ingestion.logger'), \
         patch('builtins.open', MagicMock()) as mock_open:
        
        extract_structures_from_data()
        
        # Verify file was written
        mock_open.assert_called()
