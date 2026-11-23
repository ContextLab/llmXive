"""
Unit tests for T030: Calculate Cross-Cohort Replication Rate.
"""
import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Ensure src is in path for imports
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analysis.replication_rate import (
    load_replication_status,
    calculate_replication_rate,
    write_replication_rate_report,
    run_replication_rate_analysis
)


@pytest.fixture
def temp_replication_file(tmp_path):
    """Create a temporary replication_status.tsv file."""
    file_path = tmp_path / "replication_status.tsv"
    data = {
        'taxon': ['taxon_A', 'taxon_B', 'taxon_C', 'taxon_D'],
        'method': ['MaAsLin2', 'MaAsLin2', 'ANCOM', 'DESeq2'],
        'agp_q_value': [0.01, 0.04, 0.03, 0.02],
        'ukbb_q_value': [0.02, 0.05, 0.04, 0.01],
        'agp_effect_size': [0.5, -0.3, 0.2, 0.4],
        'ukbb_effect_size': [0.4, -0.2, 0.1, -0.3],
        'replication_status': ['replicated', 'replicated', 'cohort-specific', 'non-replicable']
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, sep='\t', index=False)
    return file_path


@pytest.fixture
def temp_empty_file(tmp_path):
    """Create an empty temporary file."""
    file_path = tmp_path / "empty.tsv"
    file_path.touch()
    return file_path


@pytest.fixture
def temp_missing_col_file(tmp_path):
    """Create a file missing the required column."""
    file_path = tmp_path / "missing_col.tsv"
    data = {
        'taxon': ['taxon_A'],
        'method': ['MaAsLin2']
    }
    pd.DataFrame(data).to_csv(file_path, sep='\t', index=False)
    return file_path


def test_load_replication_status_success(temp_replication_file):
    """Test successful loading of replication status file."""
    df = load_replication_status(temp_replication_file)
    assert not df.empty
    assert 'replication_status' in df.columns
    assert len(df) == 4


def test_load_replication_status_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_replication_status(Path("non_existent_path.tsv"))


def test_load_replication_status_empty_file(temp_empty_file):
    """Test that ValueError is raised for empty file."""
    with pytest.raises(ValueError):
        load_replication_status(temp_empty_file)


def test_load_replication_status_missing_columns(temp_missing_col_file):
    """Test that ValueError is raised for missing required columns."""
    with pytest.raises(ValueError):
        load_replication_status(temp_missing_col_file)


def test_calculate_replication_rate_basic(temp_replication_file):
    """Test basic calculation of replication rate."""
    df = load_replication_status(temp_replication_file)
    metrics = calculate_replication_rate(df)
    
    assert metrics['total_significant_taxa'] == 4
    assert metrics['replicated_count'] == 2
    # 2 out of 4 is 50%
    assert metrics['replication_rate'] == 50.0


def test_calculate_replication_rate_all_replicated(tmp_path):
    """Test case where all taxa are replicated."""
    file_path = tmp_path / "all_rep.tsv"
    data = {
        'taxon': ['A', 'B'],
        'replication_status': ['replicated', 'replicated']
    }
    pd.DataFrame(data).to_csv(file_path, sep='\t', index=False)
    
    df = load_replication_status(file_path)
    metrics = calculate_replication_rate(df)
    
    assert metrics['replicated_count'] == 2
    assert metrics['replication_rate'] == 100.0


def test_calculate_replication_rate_none_replicated(tmp_path):
    """Test case where no taxa are replicated."""
    file_path = tmp_path / "none_rep.tsv"
    data = {
        'taxon': ['A', 'B'],
        'replication_status': ['non-replicable', 'cohort-specific']
    }
    pd.DataFrame(data).to_csv(file_path, sep='\t', index=False)
    
    df = load_replication_status(file_path)
    metrics = calculate_replication_rate(df)
    
    assert metrics['replicated_count'] == 0
    assert metrics['replication_rate'] == 0.0


def test_calculate_replication_rate_empty_df(tmp_path):
    """Test calculation on an empty dataframe."""
    file_path = tmp_path / "empty_data.tsv"
    data = {
        'taxon': [],
        'replication_status': []
    }
    pd.DataFrame(data).to_csv(file_path, sep='\t', index=False)
    
    df = load_replication_status(file_path)
    metrics = calculate_replication_rate(df)
    
    assert metrics['total_significant_taxa'] == 0
    assert metrics['replicated_count'] == 0
    assert metrics['replication_rate'] == 0.0


def test_write_replication_rate_report(tmp_path):
    """Test writing the report to a file."""
    metrics = {
        'total_significant_taxa': 10,
        'replicated_count': 5,
        'replication_rate': 50.0
    }
    output_path = tmp_path / "output.tsv"
    
    write_replication_rate_report(metrics, output_path)
    
    assert output_path.exists()
    df_out = pd.read_csv(output_path, sep='\t')
    assert len(df_out) == 1
    assert df_out['total_significant_taxa'].iloc[0] == 10
    assert df_out['replication_rate'].iloc[0] == 50.0


def test_run_replication_rate_analysis_integration(temp_replication_file, tmp_path):
    """Test the full pipeline execution."""
    output_path = tmp_path / "final_output.tsv"
    
    run_replication_rate_analysis(
        input_path=temp_replication_file,
        output_path=output_path
    )
    
    assert output_path.exists()
    df_out = pd.read_csv(output_path, sep='\t')
    assert 'replication_rate' in df_out.columns
    assert df_out['replication_rate'].iloc[0] == 50.0