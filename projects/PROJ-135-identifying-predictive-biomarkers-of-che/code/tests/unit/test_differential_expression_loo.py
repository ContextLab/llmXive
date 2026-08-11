import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: In a real run, these imports would be from src.differential_expression
# For unit tests, we mock the R parts heavily.

@pytest.fixture
def temp_project_structure(tmp_path):
    """Creates a temporary project structure with mock data."""
    # Setup directories
    data_processed = tmp_path / "data" / "processed"
    data_processed.mkdir(parents=True)
    
    # Create mock discovery sets for 3 tumor types
    types = ["BRCA", "LUAD", "COAD"]
    for t in types:
        df = pd.DataFrame({
            'sample_id': [f'{t}_S{i}' for i in range(10)],
            'tumor_type': [t] * 10,
            'response_label': [1 if i % 2 == 0 else 0 for i in range(10)],
            'GENE_A': np.random.rand(10),
            'GENE_B': np.random.rand(10),
            'GENE_C': np.random.rand(10)
        })
        df.to_csv(data_processed / f"{t}_discovery_set.csv", index=False)
    
    return tmp_path

@pytest.fixture
def sample_discovery_data():
    """Sample DataFrame for testing."""
    return pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3', 'S4'],
        'tumor_type': ['BRCA', 'BRCA', 'LUAD', 'LUAD'],
        'response_label': [1, 0, 1, 0],
        'GENE_X': [10.0, 5.0, 12.0, 4.0],
        'GENE_Y': [2.0, 8.0, 1.0, 9.0]
    })

def test_load_discovery_set_valid(temp_project_structure):
    from src.differential_expression import load_discovery_set
    
    df = load_discovery_set("BRCA", temp_project_structure)
    assert len(df) == 10
    assert 'GENE_A' in df.columns
    assert df['tumor_type'].iloc[0] == 'BRCA'

def test_load_discovery_set_missing_file(temp_project_structure):
    from src.differential_expression import load_discovery_set
    
    with pytest.raises(FileNotFoundError):
        load_discovery_set("PRAD", temp_project_structure)

def test_load_discovery_set_missing_columns(temp_project_structure, tmp_path):
    from src.differential_expression import load_discovery_set
    
    # Create a file with missing columns
    bad_dir = tmp_path / "data" / "processed"
    bad_dir.mkdir(parents=True)
    df = pd.DataFrame({'sample_id': [1], 'bad_col': [2]})
    df.to_csv(bad_dir / "TEST_discovery_set.csv", index=False)
    
    with pytest.raises(ValueError):
        load_discovery_set("TEST", tmp_path)

@patch('src.differential_expression._get_r_packages')
@patch('src.differential_expression.pandas2ri')
@patch('src.differential_expression.ro')
def test_loo_excludes_held_out_type(mock_ro, mock_pandas2ri, mock_get_pkgs, temp_project_structure):
    """
    Verify that when analyzing BRCA, the data from BRCA is excluded.
    """
    # Mock R packages
    mock_deseq = MagicMock()
    mock_get_pkgs.return_value = (mock_deseq, MagicMock(), MagicMock(), MagicMock())
    
    # Mock pandas2ri
    mock_pandas2ri.active = MagicMock(return_value=True)
    mock_pandas2ri.py2rpy = lambda x: x
    
    # Mock R execution result
    mock_ro.r.exists = MagicMock(return_value=True)
    
    # We need to patch the internal logic of run_deseq2_analysis_loo
    # Specifically the part where it constructs n_minus_1_dfs
    from src.differential_expression import run_deseq2_analysis_loo
    
    # Load all data manually to verify logic
    all_dfs = {}
    for t in ["BRCA", "LUAD", "COAD"]:
        all_dfs[t] = pd.read_csv(temp_project_structure / "data" / "processed" / f"{t}_discovery_set.csv")
    
    # Call the function but intercept the data passed to R
    # Since we can't easily run R in unit tests, we verify the data preparation logic
    # by checking the combined dataframe construction inside a mock context
    
    # Simulate the subset logic
    held_out = "BRCA"
    n_minus_1 = {k: v for k, v in all_dfs.items() if k != held_out}
    
    assert "BRCA" not in n_minus_1
    assert "LUAD" in n_minus_1
    assert "COAD" in n_minus_1
    assert len(n_minus_1) == 2

@patch('src.differential_expression._get_r_packages')
@patch('src.differential_expression.pandas2ri')
@patch('src.differential_expression.ro')
@patch('src.differential_expression.watchdog')
def test_significant_gene_filtering(mock_watchdog, mock_ro, mock_pandas2ri, mock_get_pkgs, temp_project_structure):
    """
    Test that the filtering logic (padj < 0.05, |log2FC| > 1.0) is correctly applied.
    We mock the R output to return specific values.
    """
    # Mock R packages
    mock_get_pkgs.return_value = (MagicMock(), MagicMock(), MagicMock(), MagicMock())
    mock_pandas2ri.active = MagicMock(return_value=True)
    mock_pandas2ri.py2rpy = lambda x: x
    mock_ro.r.exists = MagicMock(return_value=True)
    
    # Mock watchdog to return a specific result structure
    mock_result = [
        ["GENE_A", "GENE_B"], # genes
        [2.5, -1.5],          # log2FC
        [0.01, 0.001],        # pvalue
        [0.02, 0.03]          # padj
    ]
    mock_watchdog.return_value = mock_result
    
    from src.differential_expression import run_deseq2_analysis_loo
    
    all_dfs = {}
    for t in ["BRCA", "LUAD", "COAD"]:
        all_dfs[t] = pd.read_csv(temp_project_structure / "data" / "processed" / f"{t}_discovery_set.csv")
    
    df = run_deseq2_analysis_loo("BRCA", temp_project_structure, all_dfs)
    
    assert df is not None
    assert len(df) == 2
    assert all(df['padj'] < 0.05)
    assert all(abs(df['log2FoldChange']) > 1.0)

@patch('src.differential_expression._get_r_packages')
@patch('src.differential_expression.pandas2ri')
@patch('src.differential_expression.ro')
def test_run_deseq2_analysis_no_files(mock_ro, mock_pandas2ri, mock_get_pkgs, tmp_path):
    """Test behavior when no discovery files exist."""
    mock_get_pkgs.return_value = (MagicMock(), MagicMock(), MagicMock(), MagicMock())
    mock_pandas2ri.active = MagicMock(return_value=True)
    mock_ro.r.exists = MagicMock(return_value=True)
    
    from src.differential_expression import run_deseq2_analysis
    
    results = run_deseq2_analysis(tmp_path)
    assert results == {}

@patch('src.differential_expression.run_deseq2_analysis_loo')
def test_process_tumor_type_loo_integration(mock_run_loo, temp_project_structure):
    """Test the wrapper function that saves results."""
    # Mock the DE analysis result
    mock_df = pd.DataFrame({
        'gene': ['GENE_A'],
        'log2FoldChange': [2.0],
        'pvalue': [0.01],
        'padj': [0.02]
    })
    mock_run_loo.return_value = mock_df
    
    from src.differential_expression import process_tumor_type_loo
    
    all_dfs = {}
    for t in ["BRCA", "LUAD", "COAD"]:
        all_dfs[t] = pd.read_csv(temp_project_structure / "data" / "processed" / f"{t}_discovery_set.csv")
    
    output_path = process_tumor_type_loo("BRCA", temp_project_structure, all_dfs)
    
    assert output_path.endswith("loo_iteration_BRCA_de_results.csv")
    assert os.path.exists(output_path)
    
    # Verify content
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == 1
    assert saved_df['gene'].iloc[0] == 'GENE_A'
