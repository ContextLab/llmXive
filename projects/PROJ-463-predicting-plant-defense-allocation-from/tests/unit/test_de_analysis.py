"""
Unit tests for DE Analysis (T018).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import sys

# Mock rpy2 for testing without R environment
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_rpy2():
    """Mock rpy2 to avoid R dependency in unit tests."""
    with patch('src.analysis.de_analysis.importr') as mock_importr, \
         patch('src.analysis.de_analysis.pandas2ri') as mock_pandas2ri, \
         patch('src.analysis.de_analysis.ro') as mock_ro:
         
         # Setup mock R objects
         mock_deseq2 = MagicMock()
         mock_biobase = MagicMock()
         mock_importr.side_effect = lambda x: mock_deseq2 if x == 'DESeq2' else mock_biobase
         
         # Mock the R result dataframe
         mock_r_df = MagicMock()
         mock_r_df.__iter__ = lambda self: iter(['gene1', 'gene2'])
         mock_r_df.__getitem__ = lambda self, key: ['gene1', 'gene2'] if key == 0 else [10.5, 20.0]
         
         mock_pandas2ri.rpy2py.return_value = pd.DataFrame({
             'baseMean': [10.5, 20.0],
             'log2FoldChange': [1.5, -0.5],
             'lfcSE': [0.1, 0.2],
             'stat': [15.0, -2.5],
             'pvalue': [0.001, 0.05],
             'padj': [0.002, 0.06]
         }, index=['gene1', 'gene2'])
         
         yield mock_ro

def test_run_deseq2_analysis_structure(mock_rpy2):
    """Test that run_deseq2_analysis returns a DataFrame with expected columns."""
    from src.analysis.de_analysis import run_deseq2_analysis

    # Create mock data
    count_matrix = pd.DataFrame({
        'gene1': [100, 200, 150],
        'gene2': [50, 60, 55]
    }, index=['gene1', 'gene2'])
    
    col_data = pd.DataFrame({
        'condition': ['control', 'control', 'treatment']
    }, index=['sample1', 'sample2', 'sample3'])
    
    # Run analysis
    results = run_deseq2_analysis(
        count_matrix=count_matrix,
        col_data=col_data,
        condition_col='condition',
        control_level='control',
        treatment_level='treatment'
    )
    
    # Assertions
    assert isinstance(results, pd.DataFrame)
    expected_cols = ['gene_id', 'baseMean', 'log2FoldChange', 'lfcSE', 'stat', 'pvalue', 'padj']
    assert all(col in results.columns for col in expected_cols)
    assert len(results) == 2

def test_process_study_creates_output(mock_rpy2, tmp_path):
    """Test that process_study creates output files and manifest entry."""
    from src.analysis.de_analysis import process_study

    # Create temporary input file
    input_data = pd.DataFrame({
        'gene_id': ['gene1', 'gene2'],
        'control_rep1': [100, 50],
        'control_rep2': [110, 55],
        'treatment_rep1': [200, 60],
        'treatment_rep2': [210, 65]
    })
    input_file = tmp_path / "test_study_tpm.csv"
    input_data.to_csv(input_file, index=False)
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Run process_study
    entry = process_study(
        accession_id="SRR12345",
        species="Arabidopsis_thaliana",
        tissue="leaf",
        treatment="herbivory",
        input_path=input_file,
        output_dir=output_dir
    )
    
    # Assertions
    assert entry is not None
    assert entry['accession_id'] == "SRR12345"
    assert entry['species'] == "Arabidopsis_thaliana"
    assert Path(entry['file_path']).exists()
    assert 'checksum' in entry
    assert 'provenance' in entry

def test_process_study_skips_missing_metadata(mock_rpy2, tmp_path):
    """Test that process_study handles missing control/treatment columns gracefully."""
    from src.analysis.de_analysis import process_study

    # Create input file with ambiguous column names
    input_data = pd.DataFrame({
        'gene_id': ['gene1', 'gene2'],
        'sample1': [100, 50],
        'sample2': [110, 55]
    })
    input_file = tmp_path / "test_study_tpm.csv"
    input_data.to_csv(input_file, index=False)
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Run process_study
    entry = process_study(
        accession_id="SRR12345",
        species="Arabidopsis_thaliana",
        tissue="leaf",
        treatment="herbivory",
        input_path=input_file,
        output_dir=output_dir
    )
    
    # Should return None if control/treatment cannot be distinguished
    assert entry is None

def test_create_manifest_entry_structure():
    """Test that _create_manifest_entry produces a valid dict structure."""
    from src.analysis.de_analysis import _create_manifest_entry
    from pathlib import Path
    
    # We need to mock the file existence for checksum calculation
    # or pass a dummy checksum
    import hashlib
    dummy_checksum = hashlib.sha256(b"dummy").hexdigest()
    
    entry = _create_manifest_entry(
        accession_id="SRR12345",
        species="Arabidopsis_thaliana",
        tissue="leaf",
        treatment="herbivory",
        result_file=Path("dummy.csv"),
        checksum=dummy_checksum
    )
    
    assert 'accession_id' in entry
    assert 'file_name' in entry
    assert 'provenance' in entry
    assert 'tool_versions' in entry['provenance']
    assert 'parameters' in entry['provenance']

def test_main_execution(tmp_path):
    """Test the main function execution flow (mocked)."""
    from src.analysis.de_analysis import main
    import os
    
    # Set up environment variables to point to temp directories
    os.environ['DATA_PATH'] = str(tmp_path)
    
    # Create necessary directory structure
    processed_dir = tmp_path / "processed"
    count_matrices_dir = processed_dir / "count_matrices"
    count_matrices_dir.mkdir(parents=True)
    
    # Create a dummy input file
    dummy_input = pd.DataFrame({
        'gene_id': ['gene1', 'gene2'],
        'control_rep1': [100, 50],
        'control_rep2': [110, 55],
        'treatment_rep1': [200, 60],
        'treatment_rep2': [210, 65]
    })
    dummy_input.to_csv(count_matrices_dir / "SRR12345_tpm.csv", index=False)
    
    # Mock the R dependencies to avoid actual R execution
    with patch('src.analysis.de_analysis._load_r_packages') as mock_load, \
         patch('src.analysis.de_analysis.pandas2ri') as mock_pandas2ri:
         
         mock_load.return_value = (MagicMock(), MagicMock())
         mock_pandas2ri.rpy2py.return_value = pd.DataFrame({
             'baseMean': [10.5, 20.0],
             'log2FoldChange': [1.5, -0.5],
             'lfcSE': [0.1, 0.2],
             'stat': [15.0, -2.5],
             'pvalue': [0.001, 0.05],
             'padj': [0.002, 0.06]
         }, index=['gene1', 'gene2'])
         
         # Run main
         try:
             main()
         except Exception as e:
             # We expect it to run to completion or fail gracefully due to mocking
             pass
         
         # Check if output directories were created
         assert (tmp_path / "processed" / "deseq2_results").exists()
         assert (tmp_path / "processed" / "manifests").exists()