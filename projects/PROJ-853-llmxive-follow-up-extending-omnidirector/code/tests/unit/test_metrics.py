import pytest
import numpy as np
import json
import tempfile
from pathlib import Path
import os

# Adjust import based on project structure
# Assuming tests are run from code/ directory or PYTHONPATH is set
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.metrics import (
    calculate_reconstruction_error,
    calculate_pearson_correlation,
    calculate_camera_motion_complexity,
    calculate_all_reconstruction_errors,
    run_correlation_analysis
)

class TestReconstructionError:
    def test_exact_match(self):
        est = {'dimensions': [10.0, 20.0, 30.0]}
        gt = {'dimensions': [10.0, 20.0, 30.0]}
        assert calculate_reconstruction_error(est, gt) == 0.0

    def test_mismatch(self):
        est = {'dimensions': [10.0, 20.0, 30.0]}
        gt = {'dimensions': [11.0, 20.0, 30.0]}
        # L2 norm of [1, 0, 0] is 1.0
        assert calculate_reconstruction_error(est, gt) == 1.0

    def test_multi_dimension_mismatch(self):
        est = {'dimensions': [10.0, 20.0, 30.0]}
        gt = {'dimensions': [11.0, 21.0, 30.0]}
        # L2 norm of [1, 1, 0] is sqrt(2)
        assert np.isclose(calculate_reconstruction_error(est, gt), np.sqrt(2))

    def test_zero_gt(self):
        est = {'dimensions': [10.0, 20.0, 30.0]}
        gt = {'dimensions': [0.0, 0.0, 0.0]}
        assert calculate_reconstruction_error(est, gt) == 0.0

class TestPearsonCorrelation:
    def test_perfect_positive(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        r, p = calculate_pearson_correlation(x, y)
        assert np.isclose(r, 1.0)
        assert p == 0.0 # p-value might be 0.0 or very small

    def test_perfect_negative(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 4.0, 3.0, 2.0, 1.0]
        r, p = calculate_pearson_correlation(x, y)
        assert np.isclose(r, -1.0)

    def test_no_correlation(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 1.0, 4.0, 2.0, 3.0] # Random permutation
        r, p = calculate_pearson_correlation(x, y)
        # Should be close to 0, but not exactly 0 due to small sample
        assert abs(r) < 0.5

    def test_insufficient_data(self):
        r, p = calculate_pearson_correlation([1.0], [2.0])
        assert r == 0.0
        assert p == 1.0

    def test_with_nan(self):
        x = [1.0, 2.0, np.nan, 4.0]
        y = [2.0, 4.0, 6.0, 8.0]
        r, p = calculate_pearson_correlation(x, y)
        # Should ignore NaN and calculate on remaining
        assert not np.isnan(r)

class TestComplexityCalculation:
    def test_pre_calculated_complexity(self):
        data = [
            {'sequence_id': 's1', 'complexity': 5.5},
            {'sequence_id': 's2', 'complexity': 10.2}
        ]
        results = calculate_camera_motion_complexity(data)
        assert results[0]['complexity'] == 5.5
        assert results[1]['complexity'] == 10.2

    def test_derived_complexity_from_poses(self):
        # Mock data with poses but no complexity
        data = [
            {
                'sequence_id': 's1',
                'poses': [
                    {'t_vector': [1.0, 0.0, 0.0], 'R_matrix': [[1,0,0],[0,1,0],[0,0,1]]},
                    {'t_vector': [0.0, 1.0, 0.0], 'R_matrix': [[1,0,0],[0,1,0],[0,0,1]]}
                ]
            }
        ]
        results = calculate_camera_motion_complexity(data)
        assert len(results) == 1
        assert results[0]['sequence_id'] == 's1'
        # Should have calculated a non-zero complexity
        assert results[0]['complexity'] > 0.0

class TestCorrelationAnalysisPipeline:
    def test_run_correlation_analysis(self):
        # Create temp input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = [
                {'sequence_id': 's1', 'complexity': 1.0, 'estimated': {'dimensions': [10,10,10]}, 'ground_truth': {'dimensions': [10,10,10]}},
                {'sequence_id': 's2', 'complexity': 2.0, 'estimated': {'dimensions': [12,10,10]}, 'ground_truth': {'dimensions': [10,10,10]}},
                {'sequence_id': 's3', 'complexity': 3.0, 'estimated': {'dimensions': [14,10,10]}, 'ground_truth': {'dimensions': [10,10,10]}}
            ]
            json.dump(data, f)
            input_path = Path(f.name)

        output_path = input_path.parent / "output_correlation.json"

        try:
            results = run_correlation_analysis(input_path, output_path)
            
            assert 'pearson_r' in results
            assert 'p_value' in results
            assert results['sequence_count'] == 3
            
            # Check file was written
            assert output_path.exists()
            
            # Read back and verify
            with open(output_path) as f:
                saved = json.load(f)
            assert saved['pearson_r'] == results['pearson_r']
            
        finally:
            input_path.unlink()
            if output_path.exists():
                output_path.unlink()