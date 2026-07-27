import pytest
import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path

# Add the code root to the path so imports work during testing
# The test is run from the project root, so we go up one level from tests/unit
code_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(code_root))

from src.analysis.logistic_model import fit_mixed_effects_model, analyze_entropy_validity_relationship


class TestLogisticModelZeroEntropy:
    """
    Unit tests for the logistic regression model's handling of near-zero entropy values.
    Specifically verifies the model does not crash when input entropy values are near zero
    (representing high confidence error cases).
    """

    def test_handles_zero_entropy(self):
        """
        Verify that the logistic regression model does not crash when input entropy values
        are exactly zero or extremely close to zero.
        
        This simulates a high-confidence prediction scenario where the model is very sure
        (low entropy), which could be an error case if the prediction is wrong.
        """
        # Create a synthetic dataset with zero and near-zero entropy values
        # This mimics the edge case described in the task
        n_samples = 100
        
        # Mix of zero, near-zero, and normal entropy values
        entropy_values = np.concatenate([
            np.zeros(30),  # Exactly zero entropy (perfect confidence)
            np.full(30, 1e-10),  # Near-zero entropy
            np.random.uniform(0.1, 2.0, 40)  # Normal entropy range
        ])
        
        # Create corresponding validity labels (binary)
        # In a real scenario, zero entropy could be either valid or invalid
        # We'll create a mix to ensure the model can handle both cases
        validity_labels = np.concatenate([
            np.ones(15),   # Zero entropy, valid
            np.zeros(15),  # Zero entropy, invalid (high confidence error)
            np.ones(15),   # Near-zero entropy, valid
            np.zeros(15),  # Near-zero entropy, invalid
            np.random.randint(0, 2, 40)  # Random for normal entropy
        ])
        
        # Create task type labels for stratification (GSM8K vs MiniGrid)
        task_types = np.array(['gsm8k'] * 50 + ['minigrid'] * 50)
        
        # Create sequence IDs for random intercepts
        sequence_ids = np.array([f'seq_{i % 10}' for i in range(100)])
        
        # Create a DataFrame
        df = pd.DataFrame({
            'entropy': entropy_values,
            'validity': validity_labels,
            'task_type': task_types,
            'sequence_id': sequence_ids
        })
        
        # This should NOT raise an exception even with zero entropy values
        # The model should handle this gracefully
        try:
            result = fit_mixed_effects_model(
                df,
                entropy_col='entropy',
                validity_col='validity',
                task_col='task_type',
                sequence_col='sequence_id'
            )
            
            # Verify the result is not None and has expected attributes
            assert result is not None, "Model fit should return a result object"
            assert hasattr(result, 'coefficients'), "Result should have coefficients"
            assert hasattr(result, 'p_values'), "Result should have p_values"
            assert hasattr(result, 'auc_roc'), "Result should have auc_roc"
            
            # The model should have successfully fitted without crashing
            # Even if the fit is not perfect, it should not raise an exception
            assert result.coefficients is not None, "Coefficients should be computed"
            
        except Exception as e:
            pytest.fail(f"Model crashed on zero entropy input: {type(e).__name__}: {e}")

    def test_handles_extremely_small_entropy(self):
        """
        Test with entropy values at the limit of floating point precision.
        """
        # Create data with entropy at machine epsilon level
        entropy_values = np.full(50, 1e-15)
        validity_labels = np.random.randint(0, 2, 50)
        task_types = np.array(['gsm8k'] * 25 + ['minigrid'] * 25)
        sequence_ids = np.array([f'seq_{i % 5}' for i in range(50)])
        
        df = pd.DataFrame({
            'entropy': entropy_values,
            'validity': validity_labels,
            'task_type': task_types,
            'sequence_id': sequence_ids
        })
        
        # Should not crash
        try:
            result = fit_mixed_effects_model(
                df,
                entropy_col='entropy',
                validity_col='validity',
                task_col='task_type',
                sequence_col='sequence_id'
            )
            assert result is not None
        except Exception as e:
            pytest.fail(f"Model crashed on extremely small entropy: {type(e).__name__}: {e}")

    def test_mixed_zero_and_normal_entropy(self):
        """
        Test with a realistic mix of zero, near-zero, and normal entropy values.
        """
        # Create a more realistic distribution
        entropy_values = np.concatenate([
            np.zeros(20),  # 20% zero entropy
            np.random.uniform(0.001, 0.1, 30),  # 30% very low entropy
            np.random.uniform(0.1, 3.0, 50)  # 50% normal entropy
        ])
        
        validity_labels = np.random.randint(0, 2, 100)
        task_types = np.array(['gsm8k'] * 50 + ['minigrid'] * 50)
        sequence_ids = np.array([f'seq_{i % 10}' for i in range(100)])
        
        df = pd.DataFrame({
            'entropy': entropy_values,
            'validity': validity_labels,
            'task_type': task_types,
            'sequence_id': sequence_ids
        })
        
        # Should complete without error
        try:
            result = fit_mixed_effects_model(
                df,
                entropy_col='entropy',
                validity_col='validity',
                task_col='task_type',
                sequence_col='sequence_id'
            )
            
            # Verify we got a valid result
            assert result is not None
            assert result.coefficients is not None
            assert isinstance(result.auc_roc, (int, float))
            
        except Exception as e:
            pytest.fail(f"Model failed on mixed entropy distribution: {type(e).__name__}: {e}")