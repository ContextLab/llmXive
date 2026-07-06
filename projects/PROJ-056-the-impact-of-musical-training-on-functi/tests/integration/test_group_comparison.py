"""
Integration test for User Story 2: Group Comparison on Synthetic Data.

This test verifies the end-to-end pipeline for:
1. Loading synthetic subject data (US1 output simulation).
2. Computing functional connectivity matrices.
3. Performing statistical group comparisons (Welch's t-test, FDR).
4. Verifying output artifacts exist and contain expected columns.

Dependencies:
- code/data/synthetic_generator.py (for data generation)
- code/analysis/connectivity.py (for matrix computation)
- code/analysis/stats.py (for statistical testing)
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from data.synthetic_generator import generate_synthetic_dataset
from analysis.connectivity import compute_group_connectivity_stats
from analysis.stats import welch_t_test, fdr_correction, cohen_d, confidence_interval
from utils.logging import get_logger
from utils.memory_monitor import check_memory_limit

logger = get_logger(__name__)

def test_group_comparison_integration():
    """
    Integration test: Generate synthetic data -> Compute Connectivity -> Run Stats -> Verify Outputs.
    
    Expected behavior:
    1. Synthetic data is generated with >= 50 subjects per group.
    2. Connectivity matrices are computed for the group.
    3. Statistical tests (t-test, FDR, Cohen's d) are performed.
    4. Results are written to CSV files in the expected format.
    """
    # 1. Setup: Create temporary directory for outputs
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        data_dir = output_dir / "data" / "processed"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Starting Group Comparison Integration Test")
        
        # 2. Generate Synthetic Data
        # Simulating the output of T019 (subjects_cleaned.csv)
        logger.info("Generating synthetic dataset (N=120, 60 per group)...")
        df_subjects = generate_synthetic_dataset(
            n_subjects=120, 
            n_musician=60, 
            n_non_musician=60,
            random_seed=42
        )
        
        # Validate group sizes (US1 constraint)
        assert len(df_subjects[df_subjects['group'] == 'musician']) >= 50
        assert len(df_subjects[df_subjects['group'] == 'non_musician']) >= 50
        logger.info(f"Generated {len(df_subjects)} subjects. Musicians: {len(df_subjects[df_subjects['group'] == 'musician'])}")

        # 3. Simulate Connectivity Matrices
        # In a real scenario, this would load NIfTI files. 
        # Here we generate dummy connectivity matrices for the test to ensure the pipeline runs.
        # We assume an atlas with 90 regions (AAL standard) -> 90x90 matrix
        n_rois = 90
        n_connections = (n_rois * (n_rois - 1)) // 2  # Upper triangle only
        
        # Create a dummy matrix of correlations for each subject
        # Shape: (n_subjects, n_connections)
        # We inject a small effect size for the test to detect (optional, but good for validation)
        logger.info("Simulating connectivity matrices...")
        connectivity_data = np.random.rand(len(df_subjects), n_connections) * 2 - 1 # Uniform [-1, 1]
        
        # Inject a known effect in the first 10 connections for musicians to ensure non-null result
        musician_idx = df_subjects[df_subjects['group'] == 'musician'].index
        connectivity_data[musician_idx, :10] += 0.3 
        
        # 4. Run Statistical Analysis
        logger.info("Running Welch's t-test and FDR correction...")
        
        # Split data by group
        y_musician = connectivity_data[df_subjects['group'] == 'musician']
        y_non_musician = connectivity_data[df_subjects['group'] == 'non_musician']
        
        # Perform t-test
        t_stats, p_values = welch_t_test(y_musician, y_non_musician)
        
        # Perform FDR correction
        q_values = fdr_correction(p_values)
        
        # Calculate Effect Size (Cohen's d)
        effect_sizes = cohen_d(y_musician, y_non_musician)
        
        # Calculate 95% CI
        ci_lower, ci_upper = confidence_interval(effect_sizes, len(y_musician) + len(y_non_musician))
        
        # 5. Construct Results DataFrame
        connection_ids = [f"ROI_{i:02d}-ROI_{j:02d}" for i in range(n_rois) for j in range(i+1, n_rois)]
        
        results_df = pd.DataFrame({
            "connection_id": connection_ids,
            "t_stat": t_stats,
            "p_value": p_values,
            "q_value": q_values,
            "effect_size": effect_sizes,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper
        })
        
        # 6. Write Output (Simulating T030)
        output_file = data_dir / "connectivity_results.csv"
        results_df.to_csv(output_file, index=False)
        logger.info(f"Results written to {output_file}")
        
        # 7. Verification Assertions
        assert output_file.exists(), "Output file 'connectivity_results.csv' was not created."
        
        loaded_df = pd.read_csv(output_file)
        
        # Check columns
        expected_cols = ["connection_id", "t_stat", "p_value", "q_value", "effect_size", "ci_lower", "ci_upper"]
        assert list(loaded_df.columns) == expected_cols, f"Columns mismatch. Expected {expected_cols}, got {list(loaded_df.columns)}"
        
        # Check row count (should match number of connections)
        assert len(loaded_df) == n_connections, f"Row count mismatch. Expected {n_connections}, got {len(loaded_df)}"
        
        # Check for data validity (no NaNs in critical columns)
        assert not loaded_df["p_value"].isna().any(), "Found NaN p-values"
        assert not loaded_df["q_value"].isna().any(), "Found NaN q-values"
        
        # Verify the injected effect is detectable (statistical sanity check)
        # The first 10 connections should have lower p-values on average than the rest
        p_injected = loaded_df["p_value"].iloc[:10]
        p_rest = loaded_df["p_value"].iloc[10:]
        assert p_injected.mean() < p_rest.mean(), "Injected effect was not detected (mean p-value of injected group is not lower)."
        
        logger.info("Integration test PASSED: Group comparison pipeline executed successfully.")

if __name__ == "__main__":
    test_group_comparison_integration()