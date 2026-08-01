import pytest
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from dataset.loader import filter_progressive_constraints, save_filtered_dataset, DatasetBlockedException
from config import get_paths

@pytest.fixture
def sample_dataset():
    """Create a sample dataset for testing."""
    data = {
        'task_id': ['task_1', 'task_2', 'task_3', 'task_4', 'task_5'],
        'raw_prompt': [
            'Prompt 1',
            'Prompt 2',
            'Prompt 3',
            'Prompt 4',
            'Prompt 5'
        ],
        'progressive_constraints': [
            ['c1', 'c2', 'c3', 'c4', 'c5'],  # 5 constraints
            ['c1', 'c2', 'c3', 'c4'],        # 4 constraints
            ['c1', 'c2', 'c3', 'c4', 'c5', 'c6'], # 6 constraints
            ['c1', 'c2'],                    # 2 constraints
            ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7'] # 7 constraints
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def output_path(tmp_path):
    """Create a temporary output path."""
    return str(tmp_path / "filtered_tasks.csv")

def test_constraint_count_calculation(sample_dataset):
    """Test that constraint_count is correctly calculated as len(progressive_constraints)."""
    filtered_df = filter_progressive_constraints(sample_dataset, min_constraints=5)
    
    # Check that constraint_count column exists
    assert 'constraint_count' in filtered_df.columns
    
    # Check that the values are correct
    expected_counts = [5, 6, 7]  # Only tasks with >= 5 constraints
    actual_counts = sorted(filtered_df['constraint_count'].tolist())
    
    assert actual_counts == sorted(expected_counts), \
        f"Expected constraint counts {sorted(expected_counts)}, got {actual_counts}"

def test_filtering_logic(sample_dataset):
    """Test that filtering correctly excludes tasks with < 5 constraints."""
    filtered_df = filter_progressive_constraints(sample_dataset, min_constraints=5)
    
    # Should have 3 tasks (5, 6, and 7 constraints)
    assert len(filtered_df) == 3
    
    # Verify all constraint counts are >= 5
    assert all(filtered_df['constraint_count'] >= 5)

def test_filtering_with_different_threshold(sample_dataset):
    """Test filtering with a different threshold."""
    filtered_df = filter_progressive_constraints(sample_dataset, min_constraints=3)
    
    # Should have 4 tasks (3, 4, 5, 6, 7 -> only 2 is excluded)
    # Wait, let's recount: 5, 4, 6, 2, 7 -> >= 3: 5, 4, 6, 7 = 4 tasks
    assert len(filtered_df) == 4
    
    # Verify all constraint counts are >= 3
    assert all(filtered_df['constraint_count'] >= 3)

def test_output_schema(sample_dataset, output_path):
    """Test that the output CSV has the correct schema."""
    filtered_df = filter_progressive_constraints(sample_dataset, min_constraints=5)
    save_filtered_dataset(filtered_df, output_path)
    
    # Read the CSV back
    result_df = pd.read_csv(output_path)
    
    # Check required columns
    required_cols = ['task_id', 'raw_prompt', 'progressive_constraints', 'constraint_count']
    for col in required_cols:
        assert col in result_df.columns, f"Missing required column: {col}"
    
    # Check that progressive_constraints is stored as a JSON string
    for constraints_str in result_df['progressive_constraints']:
        # Should be able to parse it as JSON
        parsed = json.loads(constraints_str)
        assert isinstance(parsed, list)

def test_empty_result(sample_dataset, output_path):
    """Test filtering when no tasks match the criteria."""
    # Use a threshold that excludes all tasks
    filtered_df = filter_progressive_constraints(sample_dataset, min_constraints=100)
    
    assert len(filtered_df) == 0
    
    # Should still be able to save
    save_filtered_dataset(filtered_df, output_path)
    
    # Read back and verify
    result_df = pd.read_csv(output_path)
    assert len(result_df) == 0

def test_missing_columns_raises_exception():
    """Test that missing required columns raises DatasetBlockedException."""
    # Create a dataset missing 'task_id'
    incomplete_data = {
        'raw_prompt': ['Prompt 1'],
        'progressive_constraints': [['c1', 'c2', 'c3', 'c4', 'c5']]
    }
    df = pd.DataFrame(incomplete_data)
    
    with pytest.raises(DatasetBlockedException) as exc_info:
        filter_progressive_constraints(df, min_constraints=5)
    
    assert "task_id" in str(exc_info.value)