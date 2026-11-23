"""
Unit test for sensitivity analysis sweep (T027).

This test validates that the sensitivity analysis correctly:
1. Sweeps the anomaly cutoff over a range of multiples of sigma (σ).
2. Calculates p-values and effect sizes for each cutoff.
3. Handles edge cases (e.g., empty subsets).

Dependencies:
- code/analysis.py (run_sensitivity_analysis)
- code/config.py (get_random_seed)
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis import run_sensitivity_analysis
from config import get_random_seed


class TestSensitivityAnalysis:
    """Tests for the sensitivity analysis sweep functionality."""

    @pytest.fixture
    def mock_master_dataset(self):
        """Create a mock master dataset for testing sensitivity analysis."""
        np.random.seed(42)
        n_samples = 1000
        
        # Create synthetic data that mimics the structure of master_dataset.csv
        data = {
            'event_id': [f'USGS_{i:06d}' for i in range(n_samples)],
            'magnitude': np.random.uniform(4.0, 7.0, n_samples),
            'lat': np.random.uniform(50.0, 65.0, n_samples),
            'lon': np.random.uniform(-160.0, -130.0, n_samples),
            'depth_km': np.random.uniform(5.0, 70.0, n_samples),
            'pressure_anomaly': np.random.normal(0.0, 1.0, n_samples),
            'is_event': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
            'region': np.random.choice(['Pacific Ring of Fire', 'Other'], n_samples)
        }
        
        df = pd.DataFrame(data)
        return df

    @pytest.fixture
    def mock_results_path(self, tmp_path):
        """Create a temporary path for results."""
        output_dir = tmp_path / "data" / "processed"
        output_dir.mkdir(parents=True)
        return output_dir

    def test_sensitivity_sweep_executes(self, mock_master_dataset, mock_results_path):
        """Test that sensitivity analysis executes without errors."""
        cutoff_range = [0.5, 1.0, 1.5, 2.0]
        seed = get_random_seed()
        
        # Run sensitivity analysis
        results = run_sensitivity_analysis(
            mock_master_dataset, 
            cutoff_range, 
            output_path=mock_results_path / "sensitivity_test.json",
            random_seed=seed
        )
        
        # Verify results structure
        assert results is not None
        assert 'sensitivity_sweep' in results
        assert len(results['sensitivity_sweep']) == len(cutoff_range)
        
        # Verify each result has required fields
        for result in results['sensitivity_sweep']:
            assert 'cutoff_sigma' in result
            assert 'p_value' in result
            assert 'effect_size' in result
            assert 'n_events' in result
            assert 'n_controls' in result
            assert 'significant' in result

    def test_sensitivity_sweep_correct_cutoffs(self, mock_master_dataset, mock_results_path):
        """Test that sensitivity analysis uses the correct cutoff values."""
        cutoff_range = [0.5, 1.0, 1.5, 2.0]
        seed = get_random_seed()
        
        results = run_sensitivity_analysis(
            mock_master_dataset, 
            cutoff_range, 
            output_path=mock_results_path / "sensitivity_test.json",
            random_seed=seed
        )
        
        # Extract cutoffs from results
        result_cutoffs = [r['cutoff_sigma'] for r in results['sensitivity_sweep']]
        
        # Verify all expected cutoffs are present
        for cutoff in cutoff_range:
            assert cutoff in result_cutoffs, f"Cutoff {cutoff} not found in results"
        
        # Verify no unexpected cutoffs
        assert len(result_cutoffs) == len(cutoff_range)

    def test_sensitivity_sweep_empty_subset_handling(self, mock_results_path):
        """Test that sensitivity analysis handles empty subsets gracefully."""
        # Create dataset with very few events
        np.random.seed(123)
        n_samples = 100
        data = {
            'event_id': [f'USGS_{i:06d}' for i in range(n_samples)],
            'magnitude': np.random.uniform(4.0, 7.0, n_samples),
            'lat': np.random.uniform(50.0, 65.0, n_samples),
            'lon': np.random.uniform(-160.0, -130.0, n_samples),
            'depth_km': np.random.uniform(5.0, 70.0, n_samples),
            'pressure_anomaly': np.random.normal(0.0, 1.0, n_samples),
            'is_event': np.zeros(n_samples, dtype=int),  # No events
            'region': np.random.choice(['Pacific Ring of Fire', 'Other'], n_samples)
        }
        
        df = pd.DataFrame(data)
        cutoff_range = [0.5, 1.0, 2.0]
        seed = get_random_seed()
        
        # This should handle the empty event subset without crashing
        results = run_sensitivity_analysis(
            df, 
            cutoff_range, 
            output_path=mock_results_path / "empty_test.json",
            random_seed=seed
        )
        
        # Verify results are still generated (with NaN or 0 for empty subsets)
        assert results is not None
        assert 'sensitivity_sweep' in results
        
        # Check that results contain expected structure even with empty data
        for result in results['sensitivity_sweep']:
            assert 'cutoff_sigma' in result
            # n_events should be 0
            assert result['n_events'] == 0

    def test_sensitivity_sweep_p_value_range(self, mock_master_dataset, mock_results_path):
        """Test that calculated p-values are in valid range [0, 1]."""
        cutoff_range = [0.5, 1.0, 1.5, 2.0]
        seed = get_random_seed()
        
        results = run_sensitivity_analysis(
            mock_master_dataset, 
            cutoff_range, 
            output_path=mock_results_path / "p_value_test.json",
            random_seed=seed
        )
        
        for result in results['sensitivity_sweep']:
            p_value = result['p_value']
            assert 0.0 <= p_value <= 1.0, f"P-value {p_value} out of range [0, 1]"

    def test_sensitivity_sweep_effect_size_range(self, mock_master_dataset, mock_results_path):
        """Test that effect sizes are reasonable (not infinite or NaN)."""
        cutoff_range = [0.5, 1.0, 1.5, 2.0]
        seed = get_random_seed()
        
        results = run_sensitivity_analysis(
            mock_master_dataset, 
            cutoff_range, 
            output_path=mock_results_path / "effect_size_test.json",
            random_seed=seed
        )
        
        for result in results['sensitivity_sweep']:
            effect_size = result['effect_size']
            # Effect size should be a finite number (can be negative)
            assert np.isfinite(effect_size), f"Effect size {effect_size} is not finite"

    def test_sensitivity_sweep_output_file_created(self, mock_master_dataset, mock_results_path):
        """Test that sensitivity analysis creates the output JSON file."""
        cutoff_range = [0.5, 1.0, 1.5, 2.0]
        output_file = mock_results_path / "sensitivity_output.json"
        seed = get_random_seed()
        
        results = run_sensitivity_analysis(
            mock_master_dataset, 
            cutoff_range, 
            output_path=output_file,
            random_seed=seed
        )
        
        # Verify file was created
        assert output_file.exists(), f"Output file {output_file} was not created"
        
        # Verify file is not empty
        assert output_file.stat().st_size > 0, f"Output file {output_file} is empty"

    def test_sensitivity_sweep_significance_flag(self, mock_master_dataset, mock_results_path):
        """Test that significance flag is correctly set based on p-value threshold."""
        cutoff_range = [0.5, 1.0, 1.5, 2.0]
        seed = get_random_seed()
        
        results = run_sensitivity_analysis(
            mock_master_dataset, 
            cutoff_range, 
            output_path=mock_results_path / "significance_test.json",
            random_seed=seed
        )
        
        for result in results['sensitivity_sweep']:
            p_value = result['p_value']
            significant = result['significant']
            
            # Verify significance flag matches p-value threshold (0.05)
            expected_significant = p_value < 0.05
            assert significant == expected_significant, \
                f"Significance flag mismatch: p={p_value}, significant={significant}, expected={expected_significant}"

    def test_sensitivity_sweep_multiple_runs_reproducible(self, mock_master_dataset, mock_results_path):
        """Test that sensitivity analysis is reproducible with the same seed."""
        cutoff_range = [0.5, 1.0, 1.5, 2.0]
        seed = 42
        output_file1 = mock_results_path / "repro_test1.json"
        output_file2 = mock_results_path / "repro_test2.json"
        
        # Run twice with same seed
        results1 = run_sensitivity_analysis(
            mock_master_dataset, 
            cutoff_range, 
            output_path=output_file1,
            random_seed=seed
        )
        
        results2 = run_sensitivity_analysis(
            mock_master_dataset, 
            cutoff_range, 
            output_path=output_file2,
            random_seed=seed
        )
        
        # Compare results
        assert len(results1['sensitivity_sweep']) == len(results2['sensitivity_sweep'])
        
        for r1, r2 in zip(results1['sensitivity_sweep'], results2['sensitivity_sweep']):
            assert r1['cutoff_sigma'] == r2['cutoff_sigma']
            assert r1['p_value'] == r2['p_value']
            assert r1['effect_size'] == r2['effect_size']
            assert r1['n_events'] == r2['n_events']
            assert r1['n_controls'] == r2['n_controls']
            assert r1['significant'] == r2['significant']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])