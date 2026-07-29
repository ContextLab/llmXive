"""
Integration test for the full data harmonization pipeline.
Verifies end-to-end execution and output integrity.
"""
import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from code.ingestion import run_dgp_pipeline
from code.config import get_project_root

def test_full_pipeline_execution():
    """
    Executes the full DGP pipeline and verifies output artifacts exist
    and contain required columns.
    """
    # Run the pipeline
    # Note: This might take a moment
    try:
        result_df = run_dgp_pipeline()
    except SystemExit as e:
        pytest.fail(f"Pipeline failed with SystemExit: {e}")
    
    # Verify required columns
    required_cols = [
        'discount_rate_k', 'procrastination_score', 
        'wm_accuracy', 'wm_rt', 'participant_id'
    ]
    
    for col in required_cols:
        assert col in result_df.columns, f"Missing required column: {col}"
    
    # Verify no nulls in key columns (assuming pipeline handles this or we check here)
    # The spec says "after imputation or filtering", so we check the final result
    for col in required_cols:
        if col != 'participant_id': # ID might be int, but check anyway
            assert result_df[col].isnull().sum() == 0, f"Nulls found in {col}"
    
    # Verify file existence on disk
    project_root = get_project_root()
    processed_path = os.path.join(project_root, "data", "processed", "harmonized_dataset.parquet")
    assert os.path.exists(processed_path), "Processed dataset file not created"
    
    # Load and verify
    loaded_df = pd.read_parquet(processed_path)
    assert len(loaded_df) == len(result_df)
    
    # Verify state file update
    state_path = os.path.join(project_root, "state", "projects", "PROJ-196-the-role-of-temporal-discounting-in-proc.yaml")
    assert os.path.exists(state_path), "State file not created"
    
    import yaml
    with open(state_path, 'r') as f:
        state = yaml.safe_load(f)
    
    assert "artifact_hashes" in state
    assert "data/processed/harmonized_dataset.parquet" in state["artifact_hashes"]