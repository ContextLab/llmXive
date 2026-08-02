"""
Integration test for feature extraction (US2).

This test verifies that the graph metrics calculator can:
1. Load connectivity matrices from disk (produced by T013).
2. Extract features using the pipeline from code/graph_metrics/calculator.py.
3. Save the output to data/processed/features.csv.
4. Validate the output file exists, has correct shape, no NaNs, and required columns.
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Add parent to path for imports if running standalone, though pytest handles this via conftest
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.graph_metrics.calculator import extract_features_pipeline
from code.graph_metrics.assemble_features import assemble_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_feature_extraction():
    """
    Integration test: Run feature extraction on available matrices and validate output.
    
    Expected behavior:
    - Runs extract_features_pipeline on matrices in data/processed/
    - Produces data/processed/features.csv
    - Output has columns: 'global_efficiency', 'local_efficiency', 'modularity', 
      'prefrontal_centrality', 'hippocampal_centrality'
    - No NaNs in numeric columns
    - Shape is (N_subjects, N_features)
    """
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data" / "processed"
    output_path = data_dir / "features.csv"
    
    # Ensure data directory exists (should have been created by T001)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if there are any connectivity matrices to process
    # T013 should have generated files like sub-*_matrix.npy
    matrix_files = list(data_dir.glob("*_matrix.npy"))
    
    if not matrix_files:
        logger.warning("No connectivity matrices found in data/processed/. "
                     "This test requires T013 to have run successfully. "
                     "Skipping feature extraction test.")
        # We cannot proceed without input data. In a real CI, this might be a failure 
        # if data generation is expected to have happened before this test.
        # For now, we assert that the output path exists or create a minimal valid state 
        # if the test is expected to run in isolation (which contradicts "Integration").
        # However, per strict integration test rules, if input is missing, we fail loudly.
        raise FileNotFoundError(
            f"Integration test failed: No input matrices found in {data_dir}. "
            "Prerequisite tasks (T013) must be completed and executed to generate input data."
        )

    logger.info(f"Found {len(matrix_files)} connectivity matrices to process.")

    # Run the feature extraction pipeline
    # This function is expected to load all matrices, compute metrics, and save to CSV
    try:
        extract_features_pipeline()
    except Exception as e:
        logger.error(f"Feature extraction pipeline failed: {e}")
        raise

    # Assertions
    assert output_path.exists(), f"Output file {output_path} was not created."

    df = pd.read_csv(output_path)

    # Check required columns
    required_columns = [
        'global_efficiency', 
        'local_efficiency', 
        'modularity', 
        'prefrontal_centrality', 
        'hippocampal_centrality'
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    assert not missing_cols, f"Output missing required columns: {missing_cols}"

    # Check for NaNs in numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    nan_counts = df[numeric_cols].isna().sum()
    assert nan_counts.sum() == 0, f"Output contains NaNs: {nan_counts[nan_counts > 0]}"

    # Check shape consistency
    # Shape should be (number_of_subjects, number_of_features)
    # We verify that the number of rows matches the number of input matrices
    n_subjects = len(matrix_files)
    assert len(df) == n_subjects, (
        f"Row count mismatch: Expected {n_subjects} rows (one per matrix), "
        f"got {len(df)}."
    )

    # Verify expected dimensionality (5 specific metrics + subject ID)
    # The test description says "expected feature dimensionality".
    # Based on the columns list, we expect at least these 5 metrics.
    # If assemble_features adds more, that's fine, but we check the minimum.
    assert len(df.columns) >= len(required_columns), (
        f"Expected at least {len(required_columns)} feature columns, got {len(df.columns)}"
    )

    logger.info("Integration test passed: features.csv created with valid shape, no NaNs, and required columns.")

if __name__ == "__main__":
    test_feature_extraction()
    print("SUCCESS: test_feature_extraction passed.")