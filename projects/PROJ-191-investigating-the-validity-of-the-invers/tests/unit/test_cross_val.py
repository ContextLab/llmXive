"""
Unit tests for leave-one-out cross-validation logic.

This module tests the logic for excluding individual experiments from the
harmonized dataset to verify robustness of the results.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import json

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.loaders import HarmonizedDataset
from data.fallback_logic import detect_independent_runs, bootstrap_resample_dataset
from data.state_manager import check_bootstrap_flag, read_state


def create_mock_harmonized_dataset(n_runs=3, n_points=100):
    """Create a mock HarmonizedDataset for testing."""
    runs = []
    for i in range(n_runs):
        # Create synthetic but realistic data structure
        separation = np.linspace(0.0001, 0.001, n_points)  # 0.1 to 1 mm
        force = -1e-15 * (1 / separation**2)  # Newtonian force
        uncertainty = np.abs(force) * 0.01  # 1% uncertainty
        
        run_data = pd.DataFrame({
            'separation': separation,
            'force': force,
            'uncertainty': uncertainty,
            'experiment_id': f'exp_{i}'
        })
        
        runs.append({
            'experiment_id': f'exp_{i}',
            'data': run_data,
            'separation_range': (separation.min(), separation.max()),
            'force_range': (force.min(), force.max()),
            'uncertainty_range': (uncertainty.min(), uncertainty.max())
        })
    
    return HarmonizedDataset(
        runs=runs,
        common_separation_grid=separation,
        covariance_matrix=np.eye(n_points) * (0.01 * np.abs(force[0]))**2
    )


class TestLeaveOneOutLogic:
    """Tests for the leave-one-out cross-validation logic."""
    
    def test_detect_independent_runs_count(self):
        """Test that we can correctly count independent runs."""
        dataset = create_mock_harmonized_dataset(n_runs=3)
        independent_runs = detect_independent_runs(dataset)
        assert len(independent_runs) == 3
        
        dataset_single = create_mock_harmonized_dataset(n_runs=1)
        independent_runs_single = detect_independent_runs(dataset_single)
        assert len(independent_runs_single) == 1
    
    def test_leave_one_out_creates_correct_subset(self):
        """Test that leaving one experiment out creates the correct subset."""
        dataset = create_mock_harmonized_dataset(n_runs=3)
        
        # Test leaving out each experiment
        for i in range(3):
            # Simulate leaving out experiment i
            remaining_runs = [r for idx, r in enumerate(dataset.runs) if idx != i]
            assert len(remaining_runs) == 2
            
            # Verify the correct experiment was excluded
            experiment_ids = [r['experiment_id'] for r in remaining_runs]
            assert f'exp_{i}' not in experiment_ids
            assert len(experiment_ids) == 2
    
    def test_leave_one_out_preserves_data_integrity(self):
        """Test that the remaining data maintains integrity after exclusion."""
        dataset = create_mock_harmonized_dataset(n_runs=3)
        
        # Leave out first experiment
        remaining_runs = dataset.runs[1:]
        
        # Verify all data in remaining runs is intact
        for run in remaining_runs:
            assert 'separation' in run['data'].columns
            assert 'force' in run['data'].columns
            assert 'uncertainty' in run['data'].columns
            assert len(run['data']) > 0
            assert not run['data'].isnull().any().any()
    
    def test_bootstrap_flag_detection(self):
        """Test that bootstrap flag is correctly detected when needed."""
        # Test with single run (should trigger bootstrap)
        dataset_single = create_mock_harmonized_dataset(n_runs=1)
        independent_runs_single = detect_independent_runs(dataset_single)
        assert len(independent_runs_single) < 3
        
        # Test with sufficient runs (should not trigger bootstrap)
        dataset_multiple = create_mock_harmonized_dataset(n_runs=3)
        independent_runs_multiple = detect_independent_runs(dataset_multiple)
        assert len(independent_runs_multiple) >= 3
    
    def test_leave_one_out_with_realistic_data_structure(self):
        """Test leave-one-out logic with a more realistic data structure."""
        # Create dataset with varying point counts per experiment
        runs = []
        for i in range(3):
            n_points = 100 + i * 20  # Varying point counts
            separation = np.linspace(0.0001, 0.001, n_points)
            force = -1e-15 * (1 / separation**2)
            uncertainty = np.abs(force) * 0.01
            
            run_data = pd.DataFrame({
                'separation': separation,
                'force': force,
                'uncertainty': uncertainty,
                'experiment_id': f'exp_{i}'
            })
            
            runs.append({
                'experiment_id': f'exp_{i}',
                'data': run_data,
                'separation_range': (separation.min(), separation.max()),
                'force_range': (force.min(), force.max()),
                'uncertainty_range': (uncertainty.min(), uncertainty.max())
            })
        
        dataset = HarmonizedDataset(
            runs=runs,
            common_separation_grid=np.linspace(0.0001, 0.001, 100),
            covariance_matrix=np.eye(100) * 1e-34
        )
        
        # Test leaving out each experiment
        for i in range(3):
            remaining_runs = [r for idx, r in enumerate(dataset.runs) if idx != i]
            assert len(remaining_runs) == 2
            
            # Verify the remaining experiments have their original data
            for run in remaining_runs:
                assert len(run['data']) > 0
                assert run['data']['separation'].min() >= 0.0001
                assert run['data']['separation'].max() <= 0.001
    
    def test_leave_one_out_edge_case_two_runs(self):
        """Test leave-one-out logic with exactly two runs (edge case)."""
        dataset = create_mock_harmonized_dataset(n_runs=2)
        
        # Should be able to leave out one run and still have one remaining
        for i in range(2):
            remaining_runs = [r for idx, r in enumerate(dataset.runs) if idx != i]
            assert len(remaining_runs) == 1
            
            # Verify the remaining run has data
            assert len(remaining_runs[0]['data']) > 0
    
    def test_bootstrap_resample_integration(self):
        """Test that bootstrap resampling works as a fallback when needed."""
        # Create dataset with insufficient runs
        dataset = create_mock_harmonized_dataset(n_runs=1)
        
        # Bootstrap should be triggered
        independent_runs = detect_independent_runs(dataset)
        assert len(independent_runs) < 3
        
        # Test bootstrap resampling
        bootstrap_samples = bootstrap_resample_dataset(dataset, n_iterations=5)
        assert len(bootstrap_samples) == 5
        
        # Each sample should have the same structure
        for sample in bootstrap_samples:
            assert isinstance(sample, HarmonizedDataset)
            assert len(sample.runs) == 1  # Original had 1 run
            assert len(sample.runs[0]['data']) > 0
    
    def test_state_file_bootstrap_flag_check(self):
        """Test that the bootstrap flag in state file is correctly read."""
        # Create a temporary state file
        temp_dir = Path(__file__).parent.parent.parent / 'data' / 'processed'
        temp_dir.mkdir(parents=True, exist_ok=True)
        state_file = temp_dir / 'state.json'
        
        # Test with bootstrap flag set to True
        state_data = {'USE_BOOTSTRAP': True}
        with open(state_file, 'w') as f:
            json.dump(state_data, f)
        
        assert check_bootstrap_flag() is True
        
        # Test with bootstrap flag set to False
        state_data = {'USE_BOOTSTRAP': False}
        with open(state_file, 'w') as f:
            json.dump(state_data, f)
        
        assert check_bootstrap_flag() is False
        
        # Test with missing flag
        state_data = {'other_key': 'value'}
        with open(state_file, 'w') as f:
            json.dump(state_data, f)
        
        assert check_bootstrap_flag() is False
        
        # Clean up
        state_file.unlink()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])