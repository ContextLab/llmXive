import pytest
import pandas as pd
import os
import sys
import tempfile
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from dataset.loader import (
    filter_progressive_constraints,
    save_filtered_dataset,
    DatasetBlockedException
)

class TestConstraintCountCalculation:
    """Tests for T013: Verify constraint_count calculation and filtering logic."""

    def test_constraint_count_calculation(self):
        """Verify that constraint_count is correctly calculated as len(progressive_constraints)."""
        # Create a mock dataframe with known constraint lists
        data = {
            'task_id': ['task1', 'task2', 'task3', 'task4'],
            'raw_prompt': ['prompt1', 'prompt2', 'prompt3', 'prompt4'],
            'progressive_constraints': [
                ['c1', 'c2', 'c3', 'c4', 'c5'],  # 5 constraints
                ['c1', 'c2', 'c3'],               # 3 constraints
                ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7'], # 7 constraints
                []                                # 0 constraints
            ]
        }
        df = pd.DataFrame(data)

        # Apply filter with min_constraints=5
        filtered_df = filter_progressive_constraints(df, min_constraints=5)

        # Verify constraint_count column exists
        assert 'constraint_count' in filtered_df.columns, "constraint_count column missing"

        # Verify constraint_count values match len(progressive_constraints)
        for idx, row in filtered_df.iterrows():
            expected_count = len(row['progressive_constraints'])
            assert row['constraint_count'] == expected_count, \
                f"constraint_count mismatch for task {row['task_id']}: expected {expected_count}, got {row['constraint_count']}"

        # Verify only tasks with >= 5 constraints are included
        assert len(filtered_df) == 2, f"Expected 2 tasks with >= 5 constraints, got {len(filtered_df)}"
        
        # Verify the specific tasks included
        task_ids = set(filtered_df['task_id'].tolist())
        assert task_ids == {'task1', 'task3'}, f"Unexpected tasks: {task_ids}"

    def test_output_schema_columns(self):
        """Verify the output CSV includes all required columns per T013 spec."""
        data = {
            'task_id': ['task1'],
            'raw_prompt': ['prompt1'],
            'progressive_constraints': [['c1', 'c2', 'c3', 'c4', 'c5']]
        }
        df = pd.DataFrame(data)

        filtered_df = filter_progressive_constraints(df, min_constraints=5)

        required_columns = ['task_id', 'raw_prompt', 'progressive_constraints', 'constraint_count']
        for col in required_columns:
            assert col in filtered_df.columns, f"Required column '{col}' missing from output"

    def test_save_filtered_dataset_writes_file(self):
        """Verify that save_filtered_dataset writes a non-empty CSV file."""
        data = {
            'task_id': ['task1'],
            'raw_prompt': ['prompt1'],
            'progressive_constraints': [['c1', 'c2', 'c3', 'c4', 'c5']],
            'constraint_count': [5]
        }
        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_output.csv')
            save_filtered_dataset(df, output_path)

            # Verify file exists
            assert os.path.exists(output_path), "Output file was not created"

            # Verify file is not empty
            assert os.path.getsize(output_path) > 0, "Output file is empty"

            # Verify CSV can be read back
            read_df = pd.read_csv(output_path)
            assert len(read_df) == 1, "Read back failed to load data"
            assert list(read_df.columns) == ['task_id', 'raw_prompt', 'progressive_constraints', 'constraint_count']

    def test_filter_handles_null_constraints(self):
        """Verify filtering handles null/NaN progressive_constraints gracefully."""
        data = {
            'task_id': ['task1', 'task2', 'task3'],
            'raw_prompt': ['p1', 'p2', 'p3'],
            'progressive_constraints': [
                ['c1', 'c2', 'c3', 'c4', 'c5'],
                None,  # Null value
                ['c1', 'c2']
            ]
        }
        df = pd.DataFrame(data)

        # Should not raise an error
        filtered_df = filter_progressive_constraints(df, min_constraints=5)

        # Only task1 should be included (task2 has None -> count=0, task3 has 2)
        assert len(filtered_df) == 1
        assert filtered_df.iloc[0]['task_id'] == 'task1'

    def test_filter_min_constraints_parameter(self):
        """Verify the min_constraints parameter works correctly."""
        data = {
            'task_id': ['t1', 't2', 't3', 't4'],
            'raw_prompt': ['p1', 'p2', 'p3', 'p4'],
            'progressive_constraints': [
                ['c1', 'c2', 'c3', 'c4', 'c5'],  # 5
                ['c1', 'c2', 'c3', 'c4', 'c5', 'c6'], # 6
                ['c1', 'c2', 'c3'],                # 3
                ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8'] # 8
            ]
        }
        df = pd.DataFrame(data)

        # Test with min=5
        filtered_5 = filter_progressive_constraints(df, min_constraints=5)
        assert len(filtered_5) == 3  # t1, t2, t4

        # Test with min=6
        filtered_6 = filter_progressive_constraints(df, min_constraints=6)
        assert len(filtered_6) == 2  # t2, t4

        # Test with min=7
        filtered_7 = filter_progressive_constraints(df, min_constraints=7)
        assert len(filtered_7) == 1  # t4

        # Test with min=9 (none should pass)
        filtered_9 = filter_progressive_constraints(df, min_constraints=9)
        assert len(filtered_9) == 0