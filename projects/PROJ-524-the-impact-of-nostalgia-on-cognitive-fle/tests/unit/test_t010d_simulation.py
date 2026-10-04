import os
import json
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function to test
from task_t010d_generate_simulation import generate_synthetic_wcst_data, save_simulation_metadata

class TestSimulationDataGeneration:
    
    def test_generate_synthetic_wcst_data_age_range(self):
        """Test that generated ages are strictly within 65-85."""
        df = generate_synthetic_wcst_data(n_participants=100, seed=42)
        
        assert 'age' in df.columns
        assert df['age'].min() >= 65
        assert df['age'].max() <= 85
        
    def test_generate_synthetic_wcst_data_columns(self):
        """Test that all required columns are present."""
        df = generate_synthetic_wcst_data(n_participants=50, seed=123)
        
        required_cols = [
            'participant_id', 
            'age', 
            'stimulus_type', 
            'perseverative_errors', 
            'categories_completed'
        ]
        assert all(col in df.columns for col in required_cols)
        
    def test_generate_synthetic_wcst_data_stimulus_types(self):
        """Test that stimulus_type only contains valid values."""
        df = generate_synthetic_wcst_data(n_participants=50, seed=456)
        
        valid_types = {'nostalgia', 'control'}
        assert set(df['stimulus_type'].unique()).issubset(valid_types)
        
    def test_generate_synthetic_wcst_data_non_null_metrics(self):
        """Test that cognitive metrics are not null."""
        df = generate_synthetic_wcst_data(n_participants=50, seed=789)
        
        assert not df['perseverative_errors'].isnull().any()
        assert not df['categories_completed'].isnull().any()
        
    def test_save_simulation_metadata(self, tmp_path):
        """Test that metadata is saved correctly as JSON."""
        metadata = {
            "simulation_mode": True,
            "source": "test",
            "count": 10
        }
        output_file = tmp_path / "test_metadata.json"
        
        save_simulation_metadata(metadata, str(output_file))
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = json.load(f)
            
        assert loaded == metadata