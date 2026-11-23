"""
Unit tests for the Power Analysis module (T021).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
from src.analysis.power import (
    load_dependencies_data,
    calculate_effect_size,
    calculate_power,
    run_power_analysis
)

class TestPowerAnalysis:
    
    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Creates a temporary CSV file with valid data for testing."""
        data = {
            'age_in_days': [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
            'vulnerability_count': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'name': [f'pkg_{i}' for i in range(10)]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "test_data.csv"
        df.to_csv(file_path, index=False)
        return str(file_path)

    def test_calculate_effect_size_valid(self):
        """Test Fisher's z transformation for a valid rho."""
        rho = 0.5
        z = calculate_effect_size(rho)
        # Expected: 0.5 * ln(1.5/0.5) = 0.5 * ln(3) ≈ 0.5493
        expected = 0.5 * np.log(3)
        assert abs(z - expected) < 1e-5

    def test_calculate_effect_size_invalid(self):
        """Test that rho >= 1 raises ValueError."""
        with pytest.raises(ValueError):
            calculate_effect_size(1.0)
        with pytest.raises(ValueError):
            calculate_effect_size(-1.0)

    def test_calculate_power_small_sample(self):
        """Test power calculation with a small sample size."""
        # With N=5, effect=0.2, alpha=0.05, power should be very low
        z_effect = calculate_effect_size(0.2)
        power = calculate_power(5, z_effect)
        assert 0.0 <= power <= 1.0
        assert power < 0.2  # Expect low power

    def test_calculate_power_large_sample(self):
        """Test power calculation with a large sample size."""
        # With N=200, effect=0.2, alpha=0.05, power should be high
        z_effect = calculate_effect_size(0.2)
        power = calculate_power(200, z_effect)
        assert 0.0 <= power <= 1.0
        assert power > 0.8  # Expect high power

    def test_run_power_analysis_creates_file(self, sample_csv, tmp_path):
        """Test that run_power_analysis creates the output JSON file."""
        output_file = tmp_path / "power_results.json"
        
        results = run_power_analysis(
            input_path=sample_csv,
            output_path=str(output_file)
        )
        
        assert output_file.exists()
        
        # Verify JSON structure
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        
        assert 'effect_size' in loaded
        assert 'alpha' in loaded
        assert 'sample_size' in loaded
        assert 'actual_power' in loaded
        assert 'meets_target' in loaded
        assert loaded['sample_size'] == 10  # From fixture

    def test_run_power_analysis_no_data(self, tmp_path):
        """Test that run_power_analysis fails if input file is missing."""
        fake_path = str(tmp_path / "nonexistent.csv")
        with pytest.raises(FileNotFoundError):
            run_power_analysis(input_path=fake_path)

    def test_run_power_analysis_empty_after_filter(self, tmp_path):
        """Test behavior when data has only nulls in required columns."""
        data = {
            'age_in_days': [np.nan, np.nan],
            'vulnerability_count': [np.nan, np.nan],
            'name': ['a', 'b']
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "empty_data.csv"
        df.to_csv(file_path, index=False)
        
        with pytest.raises(ValueError, match="No valid data points found"):
            run_power_analysis(input_path=str(file_path))