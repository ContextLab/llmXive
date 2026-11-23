"""
Integration tests for the batch processing functionality (T021).
Tests that the batch processor correctly handles the full dataset
while respecting memory constraints.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import pandas as pd
import numpy as np

# Import the module to test
import sys
sys.path.insert(0, 'code')
from preprocessing.batch_processor import (
    estimate_dataframe_memory_mb,
    calculate_optimal_batch_size,
    process_in_batches,
    main
)
from utils.io import save_parquet, load_parquet

@pytest.fixture
def temp_parquet_file(tmp_path):
    """Create a temporary parquet file with test data."""
    file_path = tmp_path / "test_data.parquet"
    
    # Create test data
    data = {
        'smiles': ['CCO', 'CC(=O)O', 'c1ccccc1', 'CCOCC', 'CC(=O)OC'],
        'yield': [50.0, 75.5, 90.0, 60.0, 85.0],
        'reaction_class': ['esterification', 'oxidation', 'substitution', 'esterification', 'oxidation'],
        'fingerprint_ecfp': [[True] * 2048 for _ in range(5)],
        'fingerprint_maccs': [[True] * 167 for _ in range(5)]
    }
    
    df = pd.DataFrame(data)
    df.to_parquet(file_path)
    
    return file_path

@pytest.fixture
def large_temp_parquet_file(tmp_path):
    """Create a larger temporary parquet file for batch testing."""
    file_path = tmp_path / "large_test_data.parquet"
    
    # Create larger test data (1000 rows)
    np.random.seed(42)
    n_rows = 1000
    
    data = {
        'smiles': [f'CCO{i}' for i in range(n_rows)],
        'yield': np.random.uniform(0, 100, n_rows),
        'reaction_class': np.random.choice(['esterification', 'oxidation', 'substitution'], n_rows),
        'fingerprint_ecfp': [[True] * 2048 for _ in range(n_rows)],
        'fingerprint_maccs': [[True] * 167 for _ in range(n_rows)]
    }
    
    df = pd.DataFrame(data)
    df.to_parquet(file_path)
    
    return file_path

def test_estimate_dataframe_memory_mb():
    """Test memory estimation function."""
    # Create a small DataFrame
    df = pd.DataFrame({
        'a': [1, 2, 3],
        'b': ['x', 'y', 'z']
    })
    
    mem_mb = estimate_dataframe_memory_mb(df)
    
    # Should return a positive number
    assert mem_mb > 0
    # Should be less than 10 MB for such a small DataFrame
    assert mem_mb < 10

def test_calculate_optimal_batch_size(temp_parquet_file):
    """Test batch size calculation."""
    # Mock the file path
    with patch('preprocessing.batch_processor.INPUT_FILE', temp_parquet_file):
        batch_size = calculate_optimal_batch_size(100)
        
        # Should return a reasonable batch size
        assert batch_size >= 1000
        assert batch_size <= 100000

def test_process_in_batches_small_file(temp_parquet_file, tmp_path):
    """Test batch processing with a small file."""
    output_file = tmp_path / "output.parquet"
    log_file = tmp_path / "log.json"
    
    # Mock file paths
    with patch('preprocessing.batch_processor.INPUT_FILE', temp_parquet_file):
        with patch('preprocessing.batch_processor.OUTPUT_FILE', output_file):
            with patch('preprocessing.batch_processor.LOG_FILE', log_file):
                # Run the processing
                stats = process_in_batches(1000)
                
                # Check results
                assert stats['success'] is True
                assert stats['total_rows_processed'] == 5
                assert stats['total_batches'] == 1
                
                # Check output file exists
                assert output_file.exists()
                
                # Check log file exists
                assert log_file.exists()
                
                # Load and verify log content
                with open(log_file, 'r') as f:
                    log_data = json.load(f)
                
                assert log_data['total_rows_processed'] == 5

def test_process_in_batches_large_file(large_temp_parquet_file, tmp_path):
    """Test batch processing with a larger file."""
    output_file = tmp_path / "output.parquet"
    log_file = tmp_path / "log.json"
    
    # Mock file paths
    with patch('preprocessing.batch_processor.INPUT_FILE', large_temp_parquet_file):
        with patch('preprocessing.batch_processor.OUTPUT_FILE', output_file):
            with patch('preprocessing.batch_processor.LOG_FILE', log_file):
                # Run the processing with a smaller batch size for testing
                stats = process_in_batches(200)
                
                # Check results
                assert stats['success'] is True
                assert stats['total_rows_processed'] == 1000
                assert stats['total_batches'] == 5  # 1000 / 200 = 5
                
                # Check output file exists
                assert output_file.exists()
                
                # Verify output data
                output_df = load_parquet(output_file)
                assert len(output_df) == 1000
                
                # Check log file exists
                assert log_file.exists()
                
                # Load and verify log content
                with open(log_file, 'r') as f:
                    log_data = json.load(f)
                
                assert log_data['total_rows_processed'] == 1000
                assert log_data['total_batches'] == 5

def test_main_function(temp_parquet_file, tmp_path):
    """Test the main function entry point."""
    output_file = tmp_path / "output.parquet"
    log_file = tmp_path / "log.json"
    
    # Mock file paths
    with patch('preprocessing.batch_processor.INPUT_FILE', temp_parquet_file):
        with patch('preprocessing.batch_processor.OUTPUT_FILE', output_file):
            with patch('preprocessing.batch_processor.LOG_FILE', log_file):
                # Run main
                result = main()
                
                # Should return 0 for success
                assert result == 0
                
                # Check output file exists
                assert output_file.exists()
                
                # Check log file exists
                assert log_file.exists()

def test_empty_dataset_handling(tmp_path):
    """Test handling of empty datasets."""
    input_file = tmp_path / "empty.parquet"
    output_file = tmp_path / "output.parquet"
    log_file = tmp_path / "log.json"
    
    # Create empty parquet file
    pd.DataFrame({'smiles': [], 'yield': [], 'reaction_class': []}).to_parquet(input_file)
    
    with patch('preprocessing.batch_processor.INPUT_FILE', input_file):
        with patch('preprocessing.batch_processor.OUTPUT_FILE', output_file):
            with patch('preprocessing.batch_processor.LOG_FILE', log_file):
                stats = process_in_batches(1000)
                
                # Should handle empty dataset gracefully
                assert stats['success'] is True
                assert stats['total_rows_processed'] == 0
                assert stats['total_batches'] == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])