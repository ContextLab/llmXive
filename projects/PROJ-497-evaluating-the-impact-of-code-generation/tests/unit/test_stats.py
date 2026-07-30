import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from stats import aggregate_analysis_dataset, calculate_per_sample_stats


@pytest.fixture
def mock_raw_counts_csv(tmp_path):
    """
    Creates a mock raw_vulnerability_counts.csv file for testing.
    """
    data = {
        'task_id': ['HUMAN-EVAL-001', 'HUMAN-EVAL-001', 'HUMAN-EVAL-001', 
                    'HUMAN-EVAL-002', 'HUMAN-EVAL-002',
                    'MBPP-001', 'MBPP-001'],
        'source_type': ['LLM', 'LLM', 'Human', 'LLM', 'Human', 'LLM', 'Human'],
        'file_path': [
            'data/generated/StarCoder/HumanEval/HUMAN-EVAL-001/samples/s1.py',
            'data/generated/StarCoder/HumanEval/HUMAN-EVAL-001/samples/s2.py',
            'data/human/HumanEval/HUMAN-EVAL-001/s1.py',
            'data/generated/StarCoder/HumanEval/HUMAN-EVAL-002/samples/s1.py',
            'data/human/HumanEval/HUMAN-EVAL-002/s1.py',
            'data/generated/StarCoder/MBPP/MBPP-001/samples/s1.py',
            'data/human/MBPP/MBPP-001/s1.py'
        ],
        'lines_of_code': [10, 12, 11, 20, 22, 5, 6],
        'vulnerability_count': [1, 2, 0, 3, 1, 0, 0]
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / 'raw_vulnerability_counts.csv'
    df.to_csv(csv_path, index=False)
    return csv_path


def test_aggregate_analysis_dataset(mock_raw_counts_csv, tmp_path):
    """
    Tests T015: Aggregation logic.
    Verifies grouping by task_id and source_type and calculating means.
    """
    output_path = tmp_path / 'aggregated_analysis_dataset.csv'
    
    result_df = aggregate_analysis_dataset(str(mock_raw_counts_csv), str(output_path))
    
    # Check file exists
    assert output_path.exists(), "Output CSV was not created."
    
    # Check shape: We have 3 unique tasks, but HUMAN-EVAL-001 has 2 source types (LLM, Human).
    # HUMAN-EVAL-002 has 2 source types.
    # MBPP-001 has 2 source types.
    # Total groups = 2 + 2 + 2 = 6 rows.
    assert result_df.shape[0] == 6, f"Expected 6 rows, got {result_df.shape[0]}"
    
    # Check columns
    expected_cols = {'task_id', 'source_type', 'benchmark', 'lines_of_code', 'vulnerability_count', 'is_valid'}
    assert set(result_df.columns) == expected_cols, f"Columns mismatch: {result_df.columns}"
    
    # Verify aggregation logic for HUMAN-EVAL-001 / LLM
    # Input: LOC [10, 12] -> Mean 11. Vuln [1, 2] -> Mean 1.5
    row = result_df[(result_df['task_id'] == 'HUMAN-EVAL-001') & (result_df['source_type'] == 'LLM')]
    assert len(row) == 1
    assert row['lines_of_code'].values[0] == 11.0
    assert row['vulnerability_count'].values[0] == 1.5
    
    # Verify Human row for HUMAN-EVAL-001
    # Input: LOC [11] -> Mean 11. Vuln [0] -> Mean 0.0
    row = result_df[(result_df['task_id'] == 'HUMAN-EVAL-001') & (result_df['source_type'] == 'Human')]
    assert row['lines_of_code'].values[0] == 11.0
    assert row['vulnerability_count'].values[0] == 0.0
    
    # Verify benchmark inference
    assert result_df[result_df['task_id'] == 'HUMAN-EVAL-001']['benchmark'].iloc[0] == 'HumanEval'
    assert result_df[result_df['task_id'] == 'MBPP-001']['benchmark'].iloc[0] == 'MBPP'
    
    # Verify is_valid is True
    assert all(result_df['is_valid'] == True)


def test_missing_input_file(tmp_path):
    """
    Tests that the function fails loudly if input file is missing.
    """
    output_path = tmp_path / 'output.csv'
    input_path = tmp_path / 'nonexistent.csv'
    
    with pytest.raises(FileNotFoundError):
        aggregate_analysis_dataset(str(input_path), str(output_path))
