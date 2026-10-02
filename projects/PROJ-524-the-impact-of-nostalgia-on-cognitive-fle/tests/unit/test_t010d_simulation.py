"""
Unit tests for T010d: Simulation Data Generation
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from task_t010d_generate_simulation import generate_synthetic_wcst_data, save_simulation_metadata

class TestSimulationDataGeneration:
    
    def test_generation_creates_dataframe(self):
        """Test that the function returns a valid DataFrame"""
        df = generate_synthetic_wcst_data(n_participants=50, seed=42)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 50

    def test_required_columns_present(self):
        """Test that all required schema columns are present"""
        df = generate_synthetic_wcst_data(n_participants=50, seed=42)
        required_cols = [
            'participant_id', 
            'stimulus_type', 
            'age', 
            'perseverative_errors', 
            'categories_completed'
        ]
        for col in required_cols:
            assert col in df.columns, f"Missing required column: {col}"

    def test_age_constraint(self):
        """Test that all ages are >= 65"""
        df = generate_synthetic_wcst_data(n_participants=100, seed=42)
        assert df['age'].min() >= 65, f"Min age {df['age'].min()} is less than 65"

    def test_stimulus_types_valid(self):
        """Test that stimulus types are only 'nostalgia' or 'control'"""
        df = generate_synthetic_wcst_data(n_participants=100, seed=42)
        valid_types = {'nostalgia', 'control'}
        assert set(df['stimulus_type'].unique()).issubset(valid_types)

    def test_metrics_non_negative(self):
        """Test that cognitive metrics are non-negative"""
        df = generate_synthetic_wcst_data(n_participants=100, seed=42)
        assert (df['perseverative_errors'] >= 0).all()
        assert (df['categories_completed'] >= 0).all()

    def test_effect_size_direction(self):
        """
        Test that the generated effect size is in the expected direction.
        Nostalgia group should have fewer errors than control group.
        """
        df = generate_synthetic_wcst_data(n_participants=200, effect_size=0.5, seed=42)
        
        nostalgia_pe = df[df['stimulus_type'] == 'nostalgia']['perseverative_errors'].mean()
        control_pe = df[df['stimulus_type'] == 'control']['perseverative_errors'].mean()
        
        # Nostalgia should have fewer errors (lower mean)
        assert nostalgia_pe < control_pe, \
            f"Expected nostalgia errors ({nostalgia_pe}) < control errors ({control_pe})"

    def test_metadata_structure(self, tmp_path):
        """Test that metadata file is created with correct structure"""
        metadata_path = tmp_path / "metadata.json"
        save_simulation_metadata(metadata_path)
        
        assert metadata_path.exists()
        with open(metadata_path, 'r') as f:
            meta = json.load(f)
        
        assert meta['simulation_mode'] is True
        assert meta['dataset_source'] is not None
        assert 'simulation_parameters' in meta
        assert meta['validation_study_doi'] is None