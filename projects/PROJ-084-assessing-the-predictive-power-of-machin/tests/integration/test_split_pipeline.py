"""
Integration test for T022b: Perform Strict Scaffold-Based Split.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.modeling.split import (
    create_train_val_test_split,
    validate_split_consistency,
    load_stratified_groups,
    load_excluded_scaffolds,
    run_split_pipeline
)

@pytest.fixture
def sample_scaffold_data():
    """Create a mock scaffold_groups.parquet and batched_reactions.parquet for testing."""
    # Mock data
    data = {
        'scaffold_id': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'],
        'reaction_class': ['A', 'A', 'B', 'A', 'B', 'C']
    }
    df_scaffolds = pd.DataFrame(data)

    # Mock reactions with scaffold_id and yield
    reactions_data = {
        'scaffold_id': ['S1', 'S1', 'S2', 'S2', 'S3', 'S3', 'S4', 'S5', 'S6'],
        'smiles': ['SMI1', 'SMI2', 'SMI3', 'SMI4', 'SMI5', 'SMI6', 'SMI7', 'SMI8', 'SMI9'],
        'yield': [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0],
        'reaction_class': ['A', 'A', 'A', 'A', 'B', 'B', 'A', 'B', 'C']
    }
    df_reactions = pd.DataFrame(reactions_data)

    return df_scaffolds, df_reactions

@pytest.fixture
def temp_dirs(sample_scaffold_data, tmp_path):
    """Setup temporary directories and files."""
    df_scaffolds, df_reactions = sample_scaffold_data

    # Write mock files
    scaffold_path = tmp_path / "scaffold_groups.parquet"
    reactions_path = tmp_path / "batched_reactions.parquet"
    cross_class_path = tmp_path / "cross_class_scaffolds.json"

    df_scaffolds.to_parquet(scaffold_path)
    df_reactions.to_parquet(reactions_path)

    # Mock cross-class scaffolds (S1 appears in A and B? No, S1 is A. Let's say S2 is cross-class)
    # In our mock, S2 is A. Let's make S2 cross-class by adding a row with B?
    # Actually, the mock data has S2 as A. Let's just say S2 is cross-class for the test.
    cross_class_data = {'cross_class_scaffold_ids': ['S2']}
    with open(cross_class_path, 'w') as f:
        json.dump(cross_class_data, f)

    return {
        'scaffold_path': scaffold_path,
        'reactions_path': reactions_path,
        'cross_class_path': cross_class_path,
        'tmp_path': tmp_path
    }

def test_validate_split_consistency(temp_dirs):
    """Test that split consistency validation works."""
    # Create a valid split
    df_scaffolds, df_reactions = temp_dirs['scaffold_path'].load(), temp_dirs['reactions_path'].load() # Pseudo-code for loading
    # Actually, let's just test the function with a mock df
    df = pd.DataFrame({
        'scaffold_id': ['S1', 'S1', 'S2', 'S2'],
        'split': ['train', 'train', 'val', 'val'],
        'reaction_class': ['A', 'A', 'B', 'B']
    })
    assert validate_split_consistency(df) is True

    # Create an invalid split
    df_invalid = pd.DataFrame({
        'scaffold_id': ['S1', 'S1'],
        'split': ['train', 'val'],
        'reaction_class': ['A', 'A']
    })
    assert validate_split_consistency(df_invalid) is False

def test_create_train_val_test_split(temp_dirs):
    """Test the split creation logic."""
    # Mock data
    df = pd.DataFrame({
        'scaffold_id': ['S1', 'S1', 'S2', 'S2', 'S3', 'S3', 'S4', 'S5', 'S6'],
        'smiles': ['SMI1', 'SMI2', 'SMI3', 'SMI4', 'SMI5', 'SMI6', 'SMI7', 'SMI8', 'SMI9'],
        'yield': [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0],
        'reaction_class': ['A', 'A', 'A', 'A', 'B', 'B', 'A', 'B', 'C']
    })
    cross_class = ['S2']

    # Run split
    df_split, log_data, sc003_indices = create_train_val_test_split(
        df, cross_class, train_ratio=0.5, val_ratio=0.3, test_ratio=0.2
    )

    # Check consistency
    assert validate_split_consistency(df_split) is True

    # Check that all scaffolds are assigned
    assert df_split['split'].notna().all()

    # Check SC003 indices are a subset of val indices
    val_indices = df_split[df_split['split'] == 'val'].index.tolist()
    for idx in sc003_indices:
        assert idx in val_indices

def test_run_split_pipeline_integration(temp_dirs, monkeypatch):
    """Integration test for the full pipeline."""
    # Monkeypatch paths to use temp dirs
    from code.modeling import split as split_module
    original_scaffold_path = split_module.SCAFFOLD_GROUPS_PATH
    original_reactions_path = split_module.BATCHED_REACTIONS_PATH
    original_cross_class_path = split_module.CROSS_CLASS_SCAFFOLDS_PATH
    original_output_dir = split_module.OUTPUT_DIR
    original_results_dir = split_module.RESULTS_DIR

    split_module.SCAFFOLD_GROUPS_PATH = temp_dirs['scaffold_path']
    split_module.BATCHED_REACTIONS_PATH = temp_dirs['reactions_path']
    split_module.CROSS_CLASS_SCAFFOLDS_PATH = temp_dirs['cross_class_path']
    split_module.OUTPUT_DIR = temp_dirs['tmp_path']
    split_module.RESULTS_DIR = temp_dirs['tmp_path']

    try:
        run_split_pipeline()

        # Check output files exist
        assert (temp_dirs['tmp_path'] / "stratified_groups.csv").exists()
        assert (temp_dirs['tmp_path'] / "split_log.json").exists()
        assert (temp_dirs['tmp_path'] / "train_indices.csv").exists()
        assert (temp_dirs['tmp_path'] / "validation_indices.csv").exists()
        assert (temp_dirs['tmp_path'] / "held_out_test_indices.csv").exists()
        assert (temp_dirs['tmp_path'] / "sc003_val_indices.csv").exists()
        assert (temp_dirs['tmp_path'] / "split_ratios_final.json").exists()
    finally:
        # Restore original paths
        split_module.SCAFFOLD_GROUPS_PATH = original_scaffold_path
        split_module.BATCHED_REACTIONS_PATH = original_reactions_path
        split_module.CROSS_CLASS_SCAFFOLDS_PATH = original_cross_class_path
        split_module.OUTPUT_DIR = original_output_dir
        split_module.RESULTS_DIR = original_results_dir