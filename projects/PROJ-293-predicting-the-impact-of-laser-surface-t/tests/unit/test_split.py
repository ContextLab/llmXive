import os
import json
import tempfile
import shutil
import pandas as pd
import pytest
from pathlib import Path

# Add parent to path for imports if running from tests/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest import split_dataset

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_split_summary(temp_data_dir):
    """
    Verify that split_dataset correctly splits the data and produces the summary JSON
    with the correct schema: {normalized_count, raw_count, total_count}.
    """
    input_path = os.path.join(temp_data_dir, "aggregated_clean.csv")
    output_norm = os.path.join(temp_data_dir, "normalized_only.csv")
    output_raw = os.path.join(temp_data_dir, "raw_only.csv")
    summary_path = os.path.join(temp_data_dir, "split_summary.json")

    # Create mock data
    data = {
        'pulse_duration': [10, 20, 30, 40, 50],
        'power': [100, 200, 300, 400, 500],
        'normalization_method': ['normalized', 'normalized', 'raw', 'normalized', 'raw']
    }
    df = pd.DataFrame(data)
    df.to_csv(input_path, index=False)

    # Run split
    df_norm, df_raw, summary = split_dataset(
        input_path=input_path,
        output_normalized=output_norm,
        output_raw=output_raw,
        summary_path=summary_path
    )

    # Verify file existence
    assert os.path.exists(output_norm), "Normalized output file not created"
    assert os.path.exists(output_raw), "Raw output file not created"
    assert os.path.exists(summary_path), "Summary JSON not created"

    # Verify summary schema and values
    assert 'normalized_count' in summary, "Missing normalized_count in summary"
    assert 'raw_count' in summary, "Missing raw_count in summary"
    assert 'total_count' in summary, "Missing total_count in summary"

    assert summary['normalized_count'] == 3, f"Expected 3 normalized, got {summary['normalized_count']}"
    assert summary['raw_count'] == 2, f"Expected 2 raw, got {summary['raw_count']}"
    assert summary['total_count'] == 5, f"Expected 5 total, got {summary['total_count']}"

    # Verify DataFrame contents
    assert len(df_norm) == 3
    assert len(df_raw) == 2
    assert all(df_norm['normalization_method'] == 'normalized')
    assert all(df_raw['normalization_method'] == 'raw')

def test_split_handles_missing_column(temp_data_dir):
    """Verify that split_dataset raises ValueError if normalization_method is missing."""
    input_path = os.path.join(temp_data_dir, "bad_data.csv")
    
    # Create data without the required column
    data = {'pulse_duration': [10, 20], 'power': [100, 200]}
    pd.DataFrame(data).to_csv(input_path, index=False)

    with pytest.raises(ValueError) as excinfo:
        split_dataset(
            input_path=input_path,
            output_normalized=os.path.join(temp_data_dir, "norm.csv"),
            output_raw=os.path.join(temp_data_dir, "raw.csv"),
            summary_path=os.path.join(temp_data_dir, "summary.json")
        )
    
    assert "normalization_method" in str(excinfo.value)

def test_split_handles_missing_file(temp_data_dir):
    """Verify that split_dataset raises FileNotFoundError if input is missing."""
    with pytest.raises(FileNotFoundError):
        split_dataset(
            input_path=os.path.join(temp_data_dir, "non_existent.csv"),
            output_normalized=os.path.join(temp_data_dir, "norm.csv"),
            output_raw=os.path.join(temp_data_dir, "raw.csv"),
            summary_path=os.path.join(temp_data_dir, "summary.json")
        )
