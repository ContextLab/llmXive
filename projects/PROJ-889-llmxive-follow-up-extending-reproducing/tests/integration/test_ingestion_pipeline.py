"""
Integration test for multi-seed aggregation in the ingestion pipeline.
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
    seed1_data = {
        'step': [1, 2, 3],
        'reward_biased': [10.0, 20.0, 30.0],
        'reward_unbiased': [8.0, 15.0, 35.0]
    }
    df1 = pd.DataFrame(seed1_data)
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
    """Test that multiple seeds are correctly aggregated."""
    raw_dir, output_dir = temp_data_dirs
    
    # Run the pipeline
    output_file = process_all_trajectories(raw_dir, output_dir)
    
    # Verify output file exists
    assert output_file.exists(), "Output CSV file was not created"
    
    # Load and verify contents
    result_df = pd.read_csv(output_file)
    
    # Check that we have data from both seeds
    assert len(result_df) == 7, "Expected 7 rows (3 from seed1 + 4 from seed2)"
    
    # Check that required columns exist
    required_cols = ['step', 'reward_biased', 'reward_unbiased', 'G_t', 'dG_t', 'G_t_zscore', 'seed_id']
    for col in required_cols:
        assert col in result_df.columns, f"Missing column: {col}"
    
    # Verify seed_id column is populated
    assert 'seed_001' in result_df['seed_id'].values
    assert 'seed_002' in result_df['seed_id'].values

def test_g_t_calculation_across_seeds(temp_data_dirs):
    """Test that G(t) is correctly calculated for all seeds."""
    raw_dir, output_dir = temp_data_dirs
    
    output_file = process_all_trajectories(raw_dir, output_dir)
    result_df = pd.read_csv(output_file)
    
    # Manually verify a few G_t values
    # Seed 1, step 1: |10 - 8| = 2
    seed1_step1 = result_df[(result_df['seed_id'] == 'seed_001') & (result_df['step'] == 1)]
    assert abs(seed1_step1['G_t'].iloc[0] - 2.0) < 1e-6
    
    # Seed 2, step 4: |42 - 40| = 2
    seed2_step4 = result_df[(result_df['seed_id'] == 'seed_002') & (result_df['step'] == 4)]
    assert abs(seed2_step4['G_t'].iloc[0] - 2.0) < 1e-6