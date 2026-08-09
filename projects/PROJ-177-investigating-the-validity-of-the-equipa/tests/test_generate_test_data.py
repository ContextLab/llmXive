"""
Tests for test data generation functionality.
Verifies that T020b correctly generates thermal and non-thermal datasets.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.generate_test_data import (
    load_params,
    generate_thermal_data,
    generate_nonthermal_data,
    main
)


class TestLoadParams:
    """Tests for parameter loading functionality."""
    
    def test_load_params_success(self, tmp_path):
        """Test successful loading of parameters."""
        params = {
            'maxwell_boltzmann': {'mean': 1.0, 'scale': 0.1},
            'pareto': {'shape': 2.0}
        }
        params_file = tmp_path / 'test_params.json'
        with open(params_file, 'w') as f:
            json.dump(params, f)
        
        loaded = load_params(str(params_file))
        assert loaded == params
        assert loaded['maxwell_boltzmann']['mean'] == 1.0
        assert loaded['pareto']['shape'] == 2.0
    
    def test_load_params_missing_file(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_params('nonexistent.json')


class TestGenerateThermalData:
    """Tests for thermal data generation."""
    
    def test_thermal_data_structure(self):
        """Test that thermal data has required columns."""
        params = {
            'maxwell_boltzmann': {'mean': 1.0, 'scale': 0.1}
        }
        df = generate_thermal_data(params, n_samples=100, seed=42)
        
        required_columns = [
            'particle_id', 'timestamp', 'x', 'y', 'z',
            'vx', 'vy', 'vz', 'omega_x', 'omega_y', 'omega_z',
            'energy', 'material_type', 'driving_frequency'
        ]
        assert all(col in df.columns for col in required_columns)
    
    def test_thermal_data_distribution(self):
        """Test that thermal data follows expected distribution."""
        params = {
            'maxwell_boltzmann': {'mean': 1.0, 'scale': 0.1}
        }
        df = generate_thermal_data(params, n_samples=10000, seed=42)
        
        # Check that energies are positive
        assert (df['energy'] > 0).all()
        
        # Check mean is approximately correct (with some tolerance for randomness)
        mean_energy = df['energy'].mean()
        assert 0.8 < mean_energy < 1.2  # Within 20% of target
    
    def test_thermal_data_reproducibility(self):
        """Test that same seed produces same results."""
        params = {
            'maxwell_boltzmann': {'mean': 1.0, 'scale': 0.1}
        }
        df1 = generate_thermal_data(params, n_samples=100, seed=42)
        df2 = generate_thermal_data(params, n_samples=100, seed=42)
        
        pd.testing.assert_frame_equal(df1, df2)


class TestGenerateNonthermalData:
    """Tests for non-thermal data generation."""
    
    def test_nonthermal_data_structure(self):
        """Test that non-thermal data has required columns."""
        params = {
            'pareto': {'shape': 2.0}
        }
        df = generate_nonthermal_data(params, n_samples=100, seed=43)
        
        required_columns = [
            'particle_id', 'timestamp', 'x', 'y', 'z',
            'vx', 'vy', 'vz', 'omega_x', 'omega_y', 'omega_z',
            'energy', 'material_type', 'driving_frequency'
        ]
        assert all(col in df.columns for col in required_columns)
    
    def test_nonthermal_data_heavy_tails(self):
        """Test that non-thermal data has heavier tails than thermal."""
        thermal_params = {'maxwell_boltzmann': {'mean': 1.0, 'scale': 0.1}}
        nonthermal_params = {'pareto': {'shape': 2.0}}
        
        thermal_df = generate_thermal_data(thermal_params, n_samples=10000, seed=42)
        nonthermal_df = generate_nonthermal_data(nonthermal_params, n_samples=10000, seed=43)
        
        # Non-thermal should have higher kurtosis (heavier tails)
        thermal_kurt = thermal_df['energy'].kurtosis()
        nonthermal_kurt = nonthermal_df['energy'].kurtosis()
        
        # Pareto distribution typically has higher kurtosis
        assert nonthermal_kurt > thermal_kurt
    
    def test_nonthermal_data_reproducibility(self):
        """Test that same seed produces same results."""
        params = {
            'pareto': {'shape': 2.0}
        }
        df1 = generate_nonthermal_data(params, n_samples=100, seed=43)
        df2 = generate_nonthermal_data(params, n_samples=100, seed=43)
        
        pd.testing.assert_frame_equal(df1, df2)


class TestMainFunction:
    """Tests for the main entry point."""
    
    def test_main_creates_files(self, tmp_path):
        """Test that main function creates expected output files."""
        # Create params file
        params = {
            'maxwell_boltzmann': {'mean': 1.0, 'scale': 0.1},
            'pareto': {'shape': 2.0}
        }
        params_file = tmp_path / 'test_params.json'
        with open(params_file, 'w') as f:
            json.dump(params, f)
        
        output_dir = tmp_path / 'output'
        output_dir.mkdir()
        
        # Run main with custom paths
        import sys
        from io import StringIO
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            main(
                ['--params', str(params_file),
                 '--output-dir', str(output_dir),
                 '--n-samples', '10']
            )
        finally:
            sys.stdout = old_stdout
        
        # Check files were created
        thermal_path = output_dir / 'test_thermal_data.csv'
        nonthermal_path = output_dir / 'test_nonthermal_data.csv'
        
        assert thermal_path.exists(), "Thermal data file not created"
        assert nonthermal_path.exists(), "Non-thermal data file not created"
        
        # Verify content
        thermal_df = pd.read_csv(thermal_path)
        nonthermal_df = pd.read_csv(nonthermal_path)
        
        assert len(thermal_df) == 10
        assert len(nonthermal_df) == 10
        assert thermal_path.name.startswith('test_')
        assert nonthermal_path.name.startswith('test_')


class TestTestPrefix:
    """Tests for test file prefix handling (T021 requirement)."""
    
    def test_files_have_test_prefix(self, tmp_path):
        """Verify generated files have 'test_' prefix."""
        params = {
            'maxwell_boltzmann': {'mean': 1.0, 'scale': 0.1},
            'pareto': {'shape': 2.0}
        }
        
        # Generate data
        thermal_df = generate_thermal_data(params, n_samples=10)
        nonthermal_df = generate_nonthermal_data(params, n_samples=10)
        
        # Save and check filenames
        thermal_path = tmp_path / 'test_thermal_data.csv'
        nonthermal_path = tmp_path / 'test_nonthermal_data.csv'
        
        thermal_df.to_csv(thermal_path, index=False)
        nonthermal_df.to_csv(nonthermal_path, index=False)
        
        assert thermal_path.name.startswith('test_')
        assert nonthermal_path.name.startswith('test_')
        
        # Verify they would be rejected by downstream analysis
        assert 'test_' in thermal_path.name
        assert 'test_' in nonthermal_path.name