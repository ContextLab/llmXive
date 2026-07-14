"""
Integration test for material-level data splitting (T019).

This test verifies that the material-level split logic ensures no material_id
exists in both the training and test sets, satisfying FR-003.
"""

import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add the project root to the path to allow imports from code/
# Assuming this file is run from the project root or via pytest with proper configuration
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.synthetic_gen import generate_synthetic_data
from data.preprocess import preprocess_pipeline
from models.train import material_level_split


def test_material_level_split_no_overlap():
    """
    Integration test: Verify that material_level_split guarantees
    no material_id overlap between train and test sets.
    """
    # 1. Generate a synthetic dataset
    # We use a temporary directory for this test to avoid cluttering the data/ folder
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        raw_csv_path = tmp_path / "raw_synthetic.csv"
        processed_csv_path = tmp_path / "processed_data.csv"

        # Generate synthetic data (N=5000)
        generate_synthetic_data(output_path=str(raw_csv_path))

        # Preprocess the data to get a clean dataframe with material_ids
        # We pass the raw path directly to the pipeline logic or simulate it
        # Since preprocess_pipeline expects to read from data/raw/ usually, we adapt
        df_raw = pd.read_csv(raw_csv_path)
        
        # Simulate preprocessing steps that are relevant for the split (filtering, etc)
        # For this specific test, we need a dataframe with 'material_id' and other features.
        # The synthetic generator creates 'material_id'.
        # We assume the preprocess_pipeline logic would clean this, but for the split test
        # we just need a valid dataframe with material_ids.
        
        # Ensure we have enough unique materials to split
        unique_materials = df_raw['material_id'].nunique()
        assert unique_materials > 20, "Generated synthetic data must have enough unique materials for a split test."

        # 2. Perform the material-level split
        # We assume train_size=0.8
        train_df, test_df = material_level_split(df_raw, test_size=0.2, random_state=42)

        # 3. Assertions
        train_materials = set(train_df['material_id'].unique())
        test_materials = set(test_df['material_id'].unique())

        # Check for overlap
        overlap = train_materials.intersection(test_materials)
        
        assert len(overlap) == 0, (
            f"FR-003 Violation: Found {len(overlap)} material_ids present in both "
            f"train and test sets: {overlap}"
        )

        # Verify that the split is roughly correct (allowing for some variance due to grouping)
        total_materials = unique_materials
        train_material_count = len(train_materials)
        test_material_count = len(test_materials)

        # The split should be close to 80/20 of the materials, not necessarily rows
        # But since we split by material, the row distribution follows.
        expected_train_ratio = 0.8
        actual_train_ratio = train_material_count / total_materials

        assert 0.7 <= actual_train_ratio <= 0.9, (
            f"Split ratio is too far from 0.8. Got {actual_train_ratio:.2f} "
            f"({train_material_count}/{total_materials})"
        )

        # Verify no empty splits
        assert len(train_df) > 0, "Training set is empty."
        assert len(test_df) > 0, "Test set is empty."

def test_material_level_split_consistency():
    """
    Integration test: Verify that running the split with the same random_state
    produces the same result.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        raw_csv_path = tmp_path / "raw_synthetic.csv"
        
        generate_synthetic_data(output_path=str(raw_csv_path))
        df_raw = pd.read_csv(raw_csv_path)

        # Run split twice with same seed
        train1, test1 = material_level_split(df_raw, test_size=0.2, random_state=123)
        train2, test2 = material_level_split(df_raw, test_size=0.2, random_state=123)

        # Compare material sets
        set1_train = set(train1['material_id'].unique())
        set2_train = set(train2['material_id'].unique())
        
        assert set1_train == set2_train, "Material split is not deterministic with the same random_state."

        set1_test = set(test1['material_id'].unique())
        set2_test = set(test2['material_id'].unique())
        
        assert set1_test == set2_test, "Material split is not deterministic with the same random_state."

    # Also verify no overlap in the second run
    assert set1_train.intersection(set1_test) == set(), "Overlap detected in deterministic run."

def test_material_level_split_handles_single_material_group():
    """
    Edge case: Ensure the split handles cases where a material_id has multiple rows correctly.
    All rows for a given material_id must go to the same set.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        raw_csv_path = tmp_path / "raw_synthetic.csv"
        
        generate_synthetic_data(output_path=str(raw_csv_path))
        df_raw = pd.read_csv(raw_csv_path)

        # Select a specific material_id that exists
        sample_material_id = df_raw['material_id'].iloc[0]
        material_rows = df_raw[df_raw['material_id'] == sample_material_id]
        
        # Perform split
        train_df, test_df = material_level_split(df_raw, test_size=0.2, random_state=999)

        # Check if this specific material is in train
        if sample_material_id in train_df['material_id'].values:
            # Then it must NOT be in test
            assert sample_material_id not in test_df['material_id'].values, (
                f"Material {sample_material_id} found in both train and test."
            )
            # And ALL rows for this material must be in train
            rows_in_train = train_df[train_df['material_id'] == sample_material_id]
            assert len(rows_in_train) == len(material_rows), (
                f"Only {len(rows_in_train)} of {len(material_rows)} rows for {sample_material_id} "
                f"are in the training set."
            )
        elif sample_material_id in test_df['material_id'].values:
            # Then it must NOT be in train
            assert sample_material_id not in train_df['material_id'].values, (
                f"Material {sample_material_id} found in both train and test."
            )
            # And ALL rows for this material must be in test
            rows_in_test = test_df[test_df['material_id'] == sample_material_id]
            assert len(rows_in_test) == len(material_rows), (
                f"Only {len(rows_in_test)} of {len(material_rows)} rows for {sample_material_id} "
                f"are in the test set."
            )
        else:
            # It might be excluded if the split logic drops some groups, but typically it should be in one.
            # Given standard groupby split, it should be in one.
            pass