"""
Unit tests for generate_ground_truth.py (T090)
"""

import pytest
import os
import sys
import json
import yaml
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.errors import ConfigurationError, ValidationError

class TestGenerateGroundTruth:
    """Test suite for ground truth generation."""

    @pytest.fixture
    def temp_config(self, tmp_path):
        """Create temporary synthetic config file."""
        config = {
            'random_seed': 42,
            'interaction_coefficients': {
                'beta_CrMo': 0.05,
                'beta_CrV': 0.03
            },
            'base_energy_eV': 0.1,
            'noise_std': 0.02,
            'temperatures': [500, 600, 700],
            'alloy_systems': ['Fe-Cr-Mo', 'Fe-Cr-V']
        }
        config_path = tmp_path / 'synthetic_ground_truth.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        return config_path

    @pytest.fixture
    def temp_calphad(self, tmp_path):
        """Create temporary CALPHAD params file."""
        calphad = {
            'database': 'TCFE9',
            'parameters': {'Fe-Cr': 0.1, 'Fe-Mo': 0.2}
        }
        calphad_path = tmp_path / 'calphad_params.json'
        with open(calphad_path, 'w') as f:
            json.dump(calphad, f)
        return calphad_path

    def test_load_synthetic_config_valid(self, temp_config):
        """Test loading valid synthetic config."""
        from data.generate_ground_truth import load_synthetic_config
        
        config = load_synthetic_config(temp_config)
        
        assert config is not None
        assert 'random_seed' in config
        assert 'interaction_coefficients' in config
        assert len(config['interaction_coefficients']) > 0

    def test_load_synthetic_config_missing(self, tmp_path):
        """Test loading missing synthetic config."""
        from data.generate_ground_truth import load_synthetic_config
        
        with pytest.raises(ConfigurationError):
            load_synthetic_config(tmp_path / 'nonexistent.yaml')

    def test_load_synthetic_config_empty(self, tmp_path):
        """Test loading empty synthetic config."""
        from data.generate_ground_truth import load_synthetic_config
        
        empty_config = tmp_path / 'empty.yaml'
        empty_config.write_text('')
        
        with pytest.raises(ConfigurationError):
            load_synthetic_config(empty_config)

    def test_load_calphad_params_valid(self, temp_calphad):
        """Test loading valid CALPHAD params."""
        from data.generate_ground_truth import load_calphad_params
        
        params = load_calphad_params(temp_calphad)
        
        assert params is not None
        assert 'database' in params
        assert 'parameters' in params

    def test_load_calphad_params_missing(self, tmp_path):
        """Test loading missing CALPHAD params."""
        from data.generate_ground_truth import load_calphad_params
        
        with pytest.raises(ConfigurationError):
            load_calphad_params(tmp_path / 'nonexistent.json')

    def test_generate_ground_truth_structure(self, temp_config, temp_calphad, tmp_path):
        """Test that generated ground truth has correct structure."""
        from data.generate_ground_truth import generate_ground_truth
        
        synthetic_config = yaml.safe_load(open(temp_config))
        calphad_params = json.load(open(temp_calphad))
        
        output_path = tmp_path / 'ground_truth.csv'
        df = generate_ground_truth(calphad_params, synthetic_config, output_path)
        
        assert df is not None
        assert len(df) > 0
        
        # Check required columns
        required_cols = [
            'system', 'temperature_K', 'bulk_concentration_1', 
            'bulk_concentration_2', 'segregation_energy_eV',
            'equilibrium_concentration', 'is_saturated',
            'interaction_coefficient_beta', 'random_seed'
        ]
        
        for col in required_cols:
            assert col in df.columns

    def test_generate_ground_truth_reproducibility(self, temp_config, temp_calphad, tmp_path):
        """Test that generation is reproducible with same seed."""
        from data.generate_ground_truth import generate_ground_truth
        
        synthetic_config = yaml.safe_load(open(temp_config))
        calphad_params = json.load(open(temp_calphad))
        
        output1 = tmp_path / 'ground_truth1.csv'
        output2 = tmp_path / 'ground_truth2.csv'
        
        df1 = generate_ground_truth(calphad_params, synthetic_config, output1)
        df2 = generate_ground_truth(calphad_params, synthetic_config, output2)
        
        # Should be identical with same seed
        pd.testing.assert_frame_equal(df1, df2)

    def test_generate_ground_truth_no_coefficients(self, tmp_path):
        """Test generation fails with no interaction coefficients."""
        from data.generate_ground_truth import generate_ground_truth
        
        config = {
            'random_seed': 42,
            'interaction_coefficients': {},
            'base_energy_eV': 0.1,
            'temperatures': [500],
            'alloy_systems': ['Fe-Cr-Mo']
        }
        
        with pytest.raises(ConfigurationError):
            generate_ground_truth({}, config, tmp_path / 'output.csv')

    def test_generate_ground_truth_invalid_system(self, temp_config, temp_calphad, tmp_path):
        """Test handling of invalid system format."""
        from data.generate_ground_truth import generate_ground_truth
        
        synthetic_config = yaml.safe_load(open(temp_config))
        synthetic_config['alloy_systems'].append('Invalid-System')
        
        calphad_params = json.load(open(temp_calphad))
        
        output_path = tmp_path / 'ground_truth.csv'
        df = generate_ground_truth(calphad_params, synthetic_config, output_path)
        
        # Should still generate data for valid systems
        assert len(df) > 0
        assert 'Invalid-System' not in df['system'].values

    def test_mclean_concentration_bounds(self, temp_config, temp_calphad, tmp_path):
        """Test that equilibrium concentrations are within valid bounds."""
        from data.generate_ground_truth import generate_ground_truth
        
        synthetic_config = yaml.safe_load(open(temp_config))
        calphad_params = json.load(open(temp_calphad))
        
        output_path = tmp_path / 'ground_truth.csv'
        df = generate_ground_truth(calphad_params, synthetic_config, output_path)
        
        # Concentrations should be between 0 and 1
        assert (df['equilibrium_concentration'] >= 0).all()
        assert (df['equilibrium_concentration'] <= 1).all()

    def test_saturated_flag_logic(self, temp_config, temp_calphad, tmp_path):
        """Test that saturation flag is set correctly."""
        from data.generate_ground_truth import generate_ground_truth
        
        synthetic_config = yaml.safe_load(open(temp_config))
        calphad_params = json.load(open(temp_calphad))
        
        output_path = tmp_path / 'ground_truth.csv'
        df = generate_ground_truth(calphad_params, synthetic_config, output_path)
        
        # is_saturated should be boolean
        assert df['is_saturated'].dtype == bool