"""
Unit test for the convergence‑threshold integrity check introduced in T055/T057.
The test mocks the SingleStepSinkhornSolver to force a convergence failure on every call,
then verifies that the synthetic data generation script aborts with a RuntimeError and
does not create the output JSONL file.
"""
import builtins
import importlib
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

# Import the module under test
synthetic_module = importlib.import_module("data_generation.synthetic_attention")

@mock.patch.object(synthetic_module, "SingleStepSinkhornSolver")
def test_convergence_threshold_failure(mock_solver_class, tmp_path):
    # Configure the mocked solver so that its `solve` method always raises
    # SinkhornNonConvergenceError, simulating total failure.
    mock_solver_instance = mock.Mock()
    mock_solver_instance.solve.side_effect = synthetic_module.SinkhornNonConvergenceError()
    mock_solver_class.return_value = mock_solver_instance

    # Patch the output path to a temporary location
    output_path = tmp_path / "synthetic_attention_matrices.jsonl"

    # Run the generation with a tiny number of matrices to keep the test fast
    with pytest.raises(RuntimeError, match="Convergence rate"):
        synthetic_module.generate_static_dataset(
            num_matrices=10,
            matrix_size=8,
            target_sparsity=0.0,
            target_outlier_magnitude=0.0,
            epsilon=1e-4,
            output_path=output_path,
            base_seed=123,
        )

    # Ensure no file was written
    assert not output_path.exists()