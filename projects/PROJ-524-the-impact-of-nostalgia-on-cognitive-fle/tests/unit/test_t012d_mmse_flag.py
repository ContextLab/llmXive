"""
Unit tests for Task T012d: MMSE Flag Generation

Tests the logic of validating MMSE presence in the raw dataset
and generating the corresponding flag file.
"""

import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Import the functions to test
from code.task_t012d_mmse_flag import validate_mmse_presence, save_mmse_flag


class TestValidateMMSEPresence:
    """Tests for the validate_mmse_presence function"""
    
    def test_mmse_column_missing(self):
        """Test when MMSE column is not present in the dataframe"""
        df = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'age': [65, 70, 75],
            'stimulus_type': ['nostalgia', 'control', 'nostalgia']
        })
        
        result = validate_mmse_presence(df)
        assert result is False
    
    def test_mmse_column_all_null(self):
        """Test when MMSE column exists but all values are null"""
        df = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'age': [65, 70, 75],
            'MMSE': [None, None, None]
        })
        
        result = validate_mmse_presence(df)
        assert result is False
    
    def test_mmse_column_has_values(self):
        """Test when MMSE column exists and has at least one non-null value"""
        df = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'age': [65, 70, 75],
            'MMSE': [28, None, 26]
        })
        
        result = validate_mmse_presence(df)
        assert result is True
    
    def test_mmse_column_all_values(self):
        """Test when MMSE column exists and all values are non-null"""
        df = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'age': [65, 70, 75],
            'MMSE': [28, 27, 26]
        })
        
        result = validate_mmse_presence(df)
        assert result is True
    
    def test_mmse_column_with_zero_values(self):
        """Test when MMSE column has valid numeric values including zero"""
        df = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'age': [65, 70, 75],
            'MMSE': [0, 15, 30]
        })
        
        result = validate_mmse_presence(df)
        assert result is True

class TestSaveMMSEFlag:
    """Tests for the save_mmse_flag function"""
    
    def test_save_true_flag(self):
        """Test saving has_mmse=True"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mmse_flag.json"
            save_mmse_flag(True, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data['has_mmse'] is True
            assert 'timestamp' in data
            assert data['task_id'] == 'T012d'
    
    def test_save_false_flag(self):
        """Test saving has_mmse=False"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mmse_flag.json"
            save_mmse_flag(False, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data['has_mmse'] is False
            assert 'timestamp' in data
            assert data['task_id'] == 'T012d'
    
    def test_creates_directory(self):
        """Test that the function creates parent directories if they don't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "mmse_flag.json"
            save_mmse_flag(True, output_path)
            
            assert output_path.exists()