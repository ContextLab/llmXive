"""
Unit tests for T033: summary_table.py
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.summary_table import generate_summary_table, load_chip_overlap_stats

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        data_processed = tmpdir / "data" / "processed"
        data_processed.mkdir(parents=True)
        
        # Create mock enrichment matrix
        enrichment_data = {
            'motif_id': ['MA0001.1', 'MA0002.1', 'MA0003.1'],
            'cell_type': ['GM', 'GM', 'GM'],
            'p_value_raw': [1e-10, 1e-5, 1e-3],
            'q_value_adj': [0.001, 0.05, 0.2],
            'log2_odds': [5.0, 3.0, 1.0]
        }
        enrichment_df = pd.DataFrame(enrichment_data)
        enrichment_path = data_processed / "enrichment_matrix.csv"
        enrichment_df.to_csv(enrichment_path, index=False)
        
        # Create mock validation report
        validation_data = {
            'timestamp': '2023-10-27T10:00:00Z',
            'motif_overlap_stats': {
                'MA0001.1': 85.5,
                'MA0002.1': 60.0
                # MA0003.1 missing to test fillna
            }
        }
        validation_path = data_processed / "validation_report.json"
        with open(validation_path, 'w') as f:
            json.dump(validation_data, f)
        
        output_path = data_processed / "summary_table.csv"
        
        yield {
            'enrichment_path': enrichment_path,
            'validation_path': validation_path,
            'output_path': output_path
        }

def test_generate_summary_table(temp_dirs):
    """Test that summary table is generated correctly with merged data."""
    result = generate_summary_table(
        temp_dirs['enrichment_path'],
        temp_dirs['validation_path'],
        temp_dirs['output_path']
    )
    
    # Check file exists
    assert temp_dirs['output_path'].exists(), "Output file was not created."
    
    # Check columns
    expected_cols = ['motif_id', 'p_value_raw', 'q_value_adj', 'chip_overlap_pct']
    assert list(result.columns) == expected_cols, f"Columns mismatch: {result.columns}"
    
    # Check row count
    assert len(result) == 3, f"Expected 3 rows, got {len(result)}"
    
    # Check data values
    assert result.loc[0, 'motif_id'] == 'MA0001.1'
    assert result.loc[0, 'chip_overlap_pct'] == 85.5
    
    # Check fillna for missing overlap
    assert result.loc[2, 'chip_overlap_pct'] == 0.0

def test_load_chip_overlap_stats(temp_dirs):
    """Test loading overlap stats from validation report."""
    stats = load_chip_overlap_stats(temp_dirs['validation_path'])
    
    assert 'MA0001.1' in stats
    assert stats['MA0001.1'] == 85.5
    assert 'MA0003.1' not in stats # Should not be in the source map

def test_missing_validation_report():
    """Test that FileNotFoundError is raised if validation report is missing."""
    with pytest.raises(FileNotFoundError):
        load_chip_overlap_stats(Path("/nonexistent/report.json"))

def test_missing_enrichment_matrix(temp_dirs):
    """Test that FileNotFoundError is raised if enrichment matrix is missing."""
    with pytest.raises(FileNotFoundError):
        generate_summary_table(
            Path("/nonexistent/matrix.csv"),
            temp_dirs['validation_path'],
            temp_dirs['output_path']
        )