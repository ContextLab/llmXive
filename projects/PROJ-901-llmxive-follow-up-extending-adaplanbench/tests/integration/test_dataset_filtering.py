"""
Integration tests for dataset filtering logic (T013).

Verifies that the filtering logic correctly selects tasks with >= 5 progressive constraints.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.dataset.loader import filter_progressive_constraints, MIN_CONSTRAINT_REVEALS

@pytest.fixture
def sample_raw_data():
    """Create a mock DataFrame simulating the raw dataset structure."""
    # Simulate the structure of AdaPlanBench
    data = {
        "task_id": [f"task_{i}" for i in range(10)],
        "instruction": ["Do something"] * 10,
        "progressive_constraints": [
            [1, 2],           # 2 constraints
            [1, 2, 3],        # 3 constraints
            [1, 2, 3, 4],     # 4 constraints
            [1, 2, 3, 4, 5],  # 5 constraints (should be included)
            [1, 2, 3, 4, 5, 6], # 6 constraints (should be included)
            [1, 2, 3, 4, 5, 6, 7], # 7 constraints (should be included)
            [1],              # 1 constraint
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], # 10 constraints
            [],               # 0 constraints
            [1, 2, 3, 4, 5, 5] # 6 items (duplicates allowed in list?) -> count is 6
        ]
    }
    return pd.DataFrame(data)

def test_filter_logic_includes_correct_tasks(sample_raw_data):
    """
    Verify that filter_progressive_constraints correctly selects tasks with >= 5 constraints.
    """
    # Execute filter
    filtered_df = filter_progressive_constraints(sample_raw_data, min_reveals=MIN_CONSTRAINT_REVEALS)
    
    # Verify count
    # Expected indices: 3, 4, 5, 7, 9 (0-based) -> 5 tasks
    expected_count = 5
    assert len(filtered_df) == expected_count, f"Expected {expected_count} tasks, got {len(filtered_df)}"
    
    # Verify all selected tasks meet the criteria
    for _, row in filtered_df.iterrows():
        count = len(row['progressive_constraints'])
        assert count >= MIN_CONSTRAINT_REVEALS, f"Task {row['task_id']} has {count} constraints, which is < {MIN_CONSTRAINT_REVEALS}"
    
    # Verify specific task IDs are present
    expected_ids = {"task_3", "task_4", "task_5", "task_7", "task_9"}
    actual_ids = set(filtered_df['task_id'].tolist())
    assert actual_ids == expected_ids, f"Expected IDs {expected_ids}, got {actual_ids}"

def test_filter_logic_updates_constraint_count_column(sample_raw_data):
    """
    Verify that the filter function adds/updates the 'constraint_count' column.
    """
    filtered_df = filter_progressive_constraints(sample_raw_data, min_reveals=MIN_CONSTRAINT_REVEALS)
    
    assert 'constraint_count' in filtered_df.columns, "Missing 'constraint_count' column"
    
    # Verify values match list lengths
    for _, row in filtered_df.iterrows():
        expected_count = len(row['progressive_constraints'])
        assert row['constraint_count'] == expected_count, \
            f"Constraint count mismatch for {row['task_id']}: expected {expected_count}, got {row['constraint_count']}"

def test_filter_empty_result():
    """
    Verify behavior when no tasks meet the criteria.
    """
    data = {
        "task_id": ["task_1", "task_2"],
        "progressive_constraints": [[1], [1, 2]]
    }
    df = pd.DataFrame(data)
    
    # Filter for >= 5 constraints
    filtered_df = filter_progressive_constraints(df, min_reveals=5)
    
    assert len(filtered_df) == 0, "Expected empty DataFrame when no tasks meet criteria"
    assert 'constraint_count' in filtered_df.columns or len(filtered_df) == 0, \
        "Constraint count column handling on empty result"
