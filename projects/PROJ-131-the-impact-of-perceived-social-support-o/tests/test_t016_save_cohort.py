"""
Tests for T016: Save validated synthetic cohort.

These tests verify that the save_cohort script correctly:
1. Loads preprocessed data.
2. Constructs a synthetic cohort.
3. Validates the cohort.
4. Saves the file only if validation passes.

Since the actual data generation depends on previous steps (T013, T014, T015),
we will mock the data and functions to test the logic flow.
"""

import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.save_cohort import main as save_cohort_main

def test_save_cohort_success():
    """Test that the cohort is saved when validation passes."""
    # Create a mock dataframe
    mock_df = pd.DataFrame({
        'age': [25, 30, 35],
        'gender': ['M', 'F', 'M'],
        'social_support': [5, 10, 8],
        'harassment_exposure': [1, 2, 3],
        'depression': [10, 20, 15]
    })
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        output_file = results_dir / "synthetic_cohort.csv"
        
        # Mock the data loading and construction functions
        with patch('code.analysis.save_cohort.load_preprocessed_data', return_value=mock_df), \
             patch('code.analysis.save_cohort.construct_synthetic_cohort', return_value=mock_df), \
             patch('code.analysis.save_cohort.validate_synthetic_cohort', return_value=(True, "All checks passed")), \
             patch('code.analysis.save_cohort.project_root', tmp_path):
            
                success = save_cohort_main()
                
                assert success is True, "Expected save_cohort_main to return True on success"
                assert output_file.exists(), "Output file should exist after successful save"
                
                # Verify content
                saved_df = pd.read_csv(output_file)
                assert len(saved_df) == 3, "Saved dataframe should have 3 rows"
                assert 'age' in saved_df.columns, "Saved dataframe should have 'age' column"

def test_save_cohort_validation_failure():
    """Test that the cohort is NOT saved when validation fails."""
    mock_df = pd.DataFrame({
        'age': [25, 30, 35],
        'social_support': [5, 10, 8],
        'harassment_exposure': [1, 2, 3]
    })
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        output_file = results_dir / "synthetic_cohort.csv"
        
        with patch('code.analysis.save_cohort.load_preprocessed_data', return_value=mock_df), \
             patch('code.analysis.save_cohort.construct_synthetic_cohort', return_value=mock_df), \
             patch('code.analysis.save_cohort.validate_synthetic_cohort', return_value=(False, "Balance check failed")), \
             patch('code.analysis.save_cohort.project_root', tmp_path):
            
                success = save_cohort_main()
                
                assert success is False, "Expected save_cohort_main to return False on validation failure"
                assert not output_file.exists(), "Output file should NOT exist if validation failed"

def test_save_cohort_load_failure():
    """Test that the script handles failure to load preprocessed data."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        with patch('code.analysis.save_cohort.load_preprocessed_data', return_value=None), \
             patch('code.analysis.save_cohort.project_root', tmp_path):
            
                success = save_cohort_main()
                
                assert success is False, "Expected save_cohort_main to return False when data loading fails"

def test_save_cohort_construction_failure():
    """Test that the script handles failure to construct cohort."""
    mock_df = pd.DataFrame({'age': [25]})
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        with patch('code.analysis.save_cohort.load_preprocessed_data', return_value=mock_df), \
             patch('code.analysis.save_cohort.construct_synthetic_cohort', return_value=None), \
             patch('code.analysis.save_cohort.project_root', tmp_path):
            
                success = save_cohort_main()
                
                assert success is False, "Expected save_cohort_main to return False when construction fails"