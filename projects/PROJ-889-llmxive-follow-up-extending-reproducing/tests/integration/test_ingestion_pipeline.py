"""
Integration test for multi-seed aggregation in the ingestion pipeline.
Runs the full aggregation pipeline on a small set of mock logs to verify
row counts, seed distribution, and numeric column integrity.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import shutil
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion import process_all_trajectories, load_trajectory_logs, compute_divergence_gap

@pytest.fixture
def temp_data_dirs():
    """Create temporary raw and processed directories with test data."""
    temp_root = Path(tempfile.mkdtemp())
    raw_dir = temp_root / "data" / "raw"
    output_dir = temp_root / "data" / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test data for seed_001
    # Using explicit values to verify G(t) = |biased - unbiased|
    seed1_data = {
        'step': [1, 2, 3],
        'reward_biased': [10.0, 20.0, 30.0],
        'reward_unbiased': [8.0, 15.0, 35.0]
    }
    df1 = pd.DataFrame(seed1_data)
    # Save with seed_id column to simulate real logs if ingestion expects it,
    # or rely on filename parsing. The current ingestion logic in the API
    # description implies filename parsing or explicit column.
    # We will ensure the file has the columns expected by load_trajectory_logs.
    # Assuming load_trajectory_logs expects 'step', 'reward_biased', 'reward_unbiased'.
    df1.to_csv(raw_dir / "seed_001.csv", index=False)
    
    # Create test data for seed_002
    seed2_data = {
        'step': [1, 2, 3, 4],
        'reward_biased': [12.0, 22.0, 32.0, 42.0],
        'reward_unbiased': [10.0, 18.0, 30.0, 40.0]
    }
    df2 = pd.DataFrame(seed2_data)
    df2.to_csv(raw_dir / "seed_002.csv", index=False)
    
    yield raw_dir, output_dir
    
    # Cleanup
    shutil.rmtree(temp_root)

def test_multi_seed_aggregation(temp_data_dirs):
    """
    Integration test: Run the full aggregation pipeline on a small set of mock logs.
    Assertions:
    1. Assert merged CSV has expected row count (3 + 4 = 7).
    2. Assert seed_id distribution matches input (seed_001 and seed_002 present).
    3. Assert G(t) and dG(t) columns exist and are numeric.
    """
    raw_dir, output_dir = temp_data_dirs
    
    # Run the pipeline
    output_file = process_all_trajectories(raw_dir, output_dir)
    
    # Verify output file exists
    assert output_file.exists(), "Output CSV file was not created"
    
    # Load and verify contents
    result_df = pd.read_csv(output_file)
    
    # 1. Check row count
    # seed_001 has 3 rows, seed_002 has 4 rows. Total = 7.
    assert len(result_df) == 7, f"Expected 7 rows (3 from seed1 + 4 from seed2), got {len(result_df)}"
    
    # 2. Check seed_id distribution
    assert 'seed_id' in result_df.columns, "Missing column: seed_id"
    assert 'seed_001' in result_df['seed_id'].values, "seed_001 not found in distribution"
    assert 'seed_002' in result_df['seed_id'].values, "seed_002 not found in distribution"
    
    # Verify counts per seed
    assert result_df[result_df['seed_id'] == 'seed_001'].shape[0] == 3
    assert result_df[result_df['seed_id'] == 'seed_002'].shape[0] == 4

def test_g_t_calculation_across_seeds(temp_data_dirs):
    """
    Verify G(t) and dG(t) columns exist and are numeric.
    Additionally, spot-check G(t) calculation logic.
    """
    raw_dir, output_dir = temp_data_dirs
    
    output_file = process_all_trajectories(raw_dir, output_dir)
    result_df = pd.read_csv(output_file)
    
    # Assert columns exist
    required_cols = ['step', 'reward_biased', 'reward_unbiased', 'G_t', 'dG_t', 'G_t_zscore', 'seed_id']
    for col in required_cols:
        assert col in result_df.columns, f"Missing column: {col}"
    
    # Assert numeric types
    numeric_cols = ['G_t', 'dG_t', 'G_t_zscore']
    for col in numeric_cols:
        assert pd.api.types.is_numeric_dtype(result_df[col]), f"Column {col} is not numeric"
    
    # Manual verification of G(t) = |biased - unbiased|
    # Seed 1, step 1: |10 - 8| = 2
    seed1_step1 = result_df[(result_df['seed_id'] == 'seed_001') & (result_df['step'] == 1)]
    assert len(seed1_step1) == 1, "Expected exactly one row for seed_001 step 1"
    assert abs(seed1_step1['G_t'].iloc[0] - 2.0) < 1e-6, f"G(t) mismatch for seed_001 step 1: {seed1_step1['G_t'].iloc[0]}"
    
    # Seed 2, step 4: |42 - 40| = 2
    seed2_step4 = result_df[(result_df['seed_id'] == 'seed_002') & (result_df['step'] == 4)]
    assert len(seed2_step4) == 1, "Expected exactly one row for seed_002 step 4"
    assert abs(seed2_step4['G_t'].iloc[0] - 2.0) < 1e-6, f"G(t) mismatch for seed_002 step 4: {seed2_step4['G_t'].iloc[0]}"

def test_derivative_and_zscore_existence(temp_data_dirs):
    """
    Ensure dG(t) and z-score columns are populated with numeric values (not NaN everywhere).
    """
    raw_dir, output_dir = temp_data_dirs
    output_file = process_all_trajectories(raw_dir, output_dir)
    result_df = pd.read_csv(output_file)
    
    # Check that dG_t and G_t_zscore are not all NaN
    assert not result_df['dG_t'].isna().all(), "dG_t column is entirely NaN"
    assert not result_df['G_t_zscore'].isna().all(), "G_t_zscore column is entirely NaN"
    
    # Verify there is at least one non-NaN value in dG_t (derivative requires >1 point)
    non_nan_dg = result_df['dG_t'].dropna()
    assert len(non_nan_dg) > 0, "No valid derivative values computed"