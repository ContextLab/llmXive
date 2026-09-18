import os
import json
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.analysis.power_simulation import (
    load_synthetic_baseline_data,
    simulate_post_intervention,
    run_power_simulation_iteration,
    run_power_simulation,
    main
)
from code.utils.random_seed import set_global_seed, get_rng


class TestPowerSimulation:
    """Tests for power simulation functionality."""

    def test_load_synthetic_baseline_data(self):
        """Test loading synthetic baseline data."""
        set_global_seed(42)
        data = load_synthetic_baseline_data(n_participants=10, seed=42)
        
        assert len(data) > 0
        assert all('participant_id' in record for record in data)
        assert all('metric_type' in record for record in data)
        assert all('value' in record for record in data)

    def test_simulate_post_intervention(self):
        """Test post-intervention simulation with effect size."""
        set_global_seed(42)
        baseline_data = load_synthetic_baseline_data(n_participants=10, seed=42)
        rng = get_rng()
        
        post_data = simulate_post_intervention(baseline_data, effect_size=0.5, rng=rng)
        
        assert len(post_data) > 0
        assert all('participant_id' in record for record in post_data)
        assert all('metric_type' in record for record in post_data)
        assert all('value' in record for record in post_data)
        
        # Check that post values are different from baseline (effect applied)
        baseline_values = {(r['participant_id'], r['metric_type']): r['value'] 
                         for r in baseline_data}
        post_values = {(r['participant_id'], r['metric_type']): r['value'] 
                     for r in post_data}
        
        # At least some values should be different
        diffs = [abs(baseline_values[k] - post_values[k]) 
                for k in baseline_values.keys() 
                if k in post_values]
        assert any(d > 0.01 for d in diffs), "Effect size should create differences"

    def test_run_power_simulation_iteration(self):
        """Test single iteration of power simulation."""
        set_global_seed(42)
        baseline_data = load_synthetic_baseline_data(n_participants=20, seed=42)
        rng = get_rng()
        
        result = run_power_simulation_iteration(
            baseline_data, 
            effect_size=0.5, 
            alpha=0.05, 
            rng=rng
        )
        
        assert 'p_values' in result
        assert 'significant' in result
        assert 'n_participants' in result
        assert result['n_participants'] == 20
        
        # Check that p-values are valid
        for metric, p_val in result['p_values'].items():
            assert 0 <= p_val <= 1, f"Invalid p-value for {metric}: {p_val}"

    def test_run_power_simulation_full(self):
        """Test full power simulation with multiple iterations."""
        set_global_seed(42)
        
        # Use fewer iterations for testing
        results = run_power_simulation(
            n_iterations=10,
            n_participants=20,
            effect_size=0.5,
            alpha=0.05,
            seed=42
        )
        
        assert 'total_iterations' in results
        assert 'power_by_metric' in results
        assert 'overall_power' in results
        assert results['total_iterations'] == 10
        assert results['n_participants'] == 20
        assert results['effect_size'] == 0.5
        
        # Check power results structure
        for metric, power_data in results['power_by_metric'].items():
            assert 'estimated_power' in power_data
            assert 'mean_p_value' in power_data
            assert 'corrected_p_value' in power_data
            assert 'significant' in power_data
            assert 0 <= power_data['estimated_power'] <= 1

    def test_holm_bonferroni_correction_applied(self):
        """Test that Holm-Bonferroni correction is applied."""
        set_global_seed(42)
        
        results = run_power_simulation(
            n_iterations=5,
            n_participants=20,
            effect_size=0.5,
            alpha=0.05,
            seed=42
        )
        
        # Check that correction method is recorded
        assert results['correction_method'] == 'holm_bonferroni'
        
        # Check that corrected p-values are different from raw p-values
        for metric, power_data in results['power_by_metric'].items():
            assert power_data['corrected_p_value'] >= power_data['mean_p_value'], \
                "Holm-Bonferroni should increase p-values (or keep same)"

    def test_main_writes_output_file(self):
        """Test that main() writes the expected output file."""
        import tempfile
        import shutil
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the get_path function to use temp directory
            with patch('code.analysis.power_simulation.get_path') as mock_get_path:
                output_file = Path(tmpdir) / 'power_analysis.json'
                mock_get_path.return_value = str(output_file)
                
                # Run main
                main()
                
                # Check that file was created
                assert output_file.exists(), "Output file should be created"
                
                # Check file content
                with open(output_file, 'r') as f:
                    data = json.load(f)
                
                assert 'total_iterations' in data
                assert 'power_by_metric' in data

    def test_effect_size_detection(self):
        """Test that larger effect sizes produce higher power."""
        set_global_seed(42)
        
        # Test with small effect size
        results_small = run_power_simulation(
            n_iterations=10,
            n_participants=20,
            effect_size=0.2,
            alpha=0.05,
            seed=42
        )
        
        # Test with large effect size
        results_large = run_power_simulation(
            n_iterations=10,
            n_participants=20,
            effect_size=0.8,
            alpha=0.05,
            seed=42
        )
        
        # Large effect should have higher power
        assert results_large['overall_power'] >= results_small['overall_power'], \
            "Larger effect size should yield higher power"

    def test_sample_size_impact(self):
        """Test that larger sample sizes produce higher power."""
        set_global_seed(42)
        
        # Test with small sample
        results_small_n = run_power_simulation(
            n_iterations=10,
            n_participants=10,
            effect_size=0.5,
            alpha=0.05,
            seed=42
        )
        
        # Test with large sample
        results_large_n = run_power_simulation(
            n_iterations=10,
            n_participants=50,
            effect_size=0.5,
            alpha=0.05,
            seed=42
        )
        
        # Larger sample should have higher power
        assert results_large_n['overall_power'] >= results_small_n['overall_power'], \
            "Larger sample size should yield higher power"