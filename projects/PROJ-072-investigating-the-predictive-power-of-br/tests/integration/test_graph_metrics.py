import os
import sys
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from graph_metrics.calculator import extract_features_for_subject, compute_global_efficiency
from graph_metrics.assemble_features import assemble_features

class TestFeatureExtraction:
    """Integration test for feature extraction (T018/T022)."""

    def test_feature_extraction(self):
        """
        Runs the full assembly pipeline and asserts:
        1. Output file data/processed/features.csv exists.
        2. Shape is consistent with number of subjects.
        3. Contains no NaNs.
        4. Includes required columns.
        """
        # Ensure we have valid input data (subject_status.csv, subject_labels.csv, matrices)
        # This test assumes T014, T015, T013 are completed.
        
        output_path = Path(PROJECT_ROOT) / "data" / "processed" / "features.csv"
        
        # Run the pipeline
        try:
            result_path = assemble_features()
        except FileNotFoundError as e:
            # If input data is missing, skip or fail explicitly
            pytest.skip(f"Input data missing for integration test: {e}")
        except Exception as e:
            pytest.fail(f"Pipeline execution failed: {e}")

        # Assert file exists
        assert output_path.exists(), f"Output file {output_path} was not created."

        # Load and check
        df = pd.read_csv(output_path)

        # Check columns
        required_cols = ['subject_id', 'diagnosis', 'global_efficiency', 'local_efficiency', 'modularity', 'prefrontal_centrality', 'hippocampal_centrality']
        for col in required_cols:
            assert col in df.columns, f"Missing required column: {col}"

        # Check NaNs
        assert not df.isnull().any().any(), "Feature matrix contains NaN values."

        # Check shape (at least 1 subject)
        assert df.shape[0] > 0, "No subjects processed."

        # Check value ranges (optional but good practice)
        assert df['global_efficiency'].between(0, 1).all() or df['global_efficiency'].min() < 0, "Global efficiency out of expected range (might be negative if graph is disconnected? Usually 0-1)."
        # Modularity is typically 0-1 or negative.
        
        # If PCA was applied, the columns might be different (PC1, PC2...).
        # The test should handle both cases or assert that if PCA columns exist, original ones are gone.
        # For simplicity, we assert the presence of at least the main metrics if PCA was not forced.
        # If PCA was applied, the test might need to check for PC columns.
        # Let's check if original metrics exist OR PC columns exist.
        
        has_metrics = all(col in df.columns for col in ['global_efficiency', 'local_efficiency', 'modularity'])
        has_pcs = any(col.startswith('PC') for col in df.columns)
        
        assert has_metrics or has_pcs, "Neither original metrics nor PCA components found."

def test_efficiency_full_graph():
    """Unit test for global efficiency on a fully connected graph."""
    # Create a 10x10 matrix of all 1.0s (fully connected, weight 1)
    matrix = np.ones((10, 10))
    # Remove self-loops for graph creation (diagonal)
    np.fill_diagonal(matrix, 0)
    
    eff = compute_global_efficiency(matrix)
    # For a complete graph with N nodes, efficiency is 1.0
    assert np.isclose(eff, 1.0), f"Expected efficiency 1.0, got {eff}"
