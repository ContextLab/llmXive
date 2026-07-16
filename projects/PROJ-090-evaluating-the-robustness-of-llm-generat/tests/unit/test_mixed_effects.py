import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.statistics import run_mixed_effects_logistic_regression, MixedEffectsResult

def test_mixed_effects_logistic_regression_structure():
    """
    Test that the mixed-effects logistic regression function produces the expected output structure.
    """
    # Create a temporary directory for test outputs
    with tempfile.TemporaryDirectory() as tmpdir:
        results_path = os.path.join(tmpdir, "execution_results.json")
        output_path = os.path.join(tmpdir, "mixed_effects_results.json")

        # Create mock data
        # Simulate 10 tasks, 3 perturbation types (original, synonym, typo), with binary pass/fail
        np.random.seed(42)
        n_tasks = 10
        n_per_task = 3  # original, synonym, typo
        task_ids = [f"task_{i}" for i in range(n_tasks)]

        data = []
        for task_id in task_ids:
            for p_type in ['original', 'synonym', 'typo']:
                # Random pass/fail with some structure
                pass_status = 1 if np.random.rand() > 0.3 else 0
                data.append({
                    "task_id": task_id,
                    "perturbation_type": p_type,
                    "pass_status": pass_status
                })

        # Write mock data
        with open(results_path, 'w') as f:
            json.dump(data, f)

        # Run the function
        result = run_mixed_effects_logistic_regression(results_path, output_path)

        # Verify output file exists
        assert os.path.exists(output_path), "Output file should be created"

        # Verify result object structure
        assert isinstance(result, MixedEffectsResult), "Result should be a MixedEffectsResult object"
        assert result.variance_component_task >= 0, "Variance component should be non-negative"
        assert result.std_dev_task >= 0, "Standard deviation should be non-negative"
        assert len(result.fixed_effects) > 0, "Should have fixed effects"
        assert len(result.p_values) > 0, "Should have p-values"
        assert result.n_obs == n_tasks * n_per_task, f"Should have {n_tasks * n_per_task} observations"
        assert result.n_groups == n_tasks, f"Should have {n_tasks} groups"

        # Verify output JSON structure
        with open(output_path, 'r') as f:
            output_data = json.load(f)

        assert 'formula' in output_data
        assert 'variance_component_task' in output_data
        assert 'std_dev_task' in output_data
        assert 'fixed_effects' in output_data
        assert 'p_values' in output_data
        assert 'n_observations' in output_data
        assert 'n_groups' in output_data

def test_mixed_effects_with_realistic_data():
    """
    Test mixed-effects model with data that has a clear perturbation effect.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        results_path = os.path.join(tmpdir, "execution_results.json")
        output_path = os.path.join(tmpdir, "mixed_effects_results.json")

        # Create data where original has high pass rate, perturbations lower
        n_tasks = 20
        data = []
        for i in range(n_tasks):
            task_id = f"task_{i}"
            # Original: 90% pass
            data.append({"task_id": task_id, "perturbation_type": "original", "pass_status": 1 if np.random.rand() < 0.9 else 0})
            # Synonym: 70% pass
            data.append({"task_id": task_id, "perturbation_type": "synonym", "pass_status": 1 if np.random.rand() < 0.7 else 0})
            # Typo: 60% pass
            data.append({"task_id": task_id, "perturbation_type": "typo", "pass_status": 1 if np.random.rand() < 0.6 else 0})

        with open(results_path, 'w') as f:
            json.dump(data, f)

        result = run_mixed_effects_logistic_regression(results_path, output_path)

        # Should detect some variance due to task
        assert result.n_groups == n_tasks
        assert result.n_obs == n_tasks * 3

        # Load and check the JSON output
        with open(output_path, 'r') as f:
            output_data = json.load(f)

        # The variance component should be present and non-negative
        assert output_data['variance_component_task'] >= 0
        assert output_data['std_dev_task'] >= 0
        assert 'synonym' in output_data['fixed_effects'] or 'typo' in output_data['fixed_effects'], \
            "Should have coefficients for perturbation types"

def test_mixed_effects_single_task():
    """
    Test behavior with minimal data (single task) - should handle gracefully.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        results_path = os.path.join(tmpdir, "execution_results.json")
        output_path = os.path.join(tmpdir, "mixed_effects_results.json")

        # Only one task
        data = [
            {"task_id": "task_0", "perturbation_type": "original", "pass_status": 1},
            {"task_id": "task_0", "perturbation_type": "synonym", "pass_status": 0},
            {"task_id": "task_0", "perturbation_type": "typo", "pass_status": 0}
        ]

        with open(results_path, 'w') as f:
            json.dump(data, f)

        # This might fail due to insufficient groups for random effects,
        # but we test that it either works or raises a clear error.
        try:
            result = run_mixed_effects_logistic_regression(results_path, output_path)
            # If it succeeds, verify structure
            assert result.n_groups == 1
        except Exception as e:
            # Expected: MixedLM may fail with only 1 group
            assert "Could not fit" in str(e) or "singular" in str(e).lower(), \
                f"Expected fit error for single group, got: {e}"
