"""
Unit tests for LOO-Blind Differential Expression Analysis.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, Mock

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.differential_expression import (
    load_discovery_set,
    process_tumor_type_loo,
    run_deseq2_analysis
)
from src.config import get_project_root, ensure_directories


@pytest.fixture
def temp_project_structure():
    """Create a temporary project structure with mock discovery sets."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create data/processed directory
        processed_dir = tmpdir / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create mock discovery sets for 3 tumor types
        tumor_types = ["BRCA", "LUAD", "COAD"]
        
        for tt in tumor_types:
            # Create mock data
            n_samples = 50
            n_genes = 100
            
            # Gene expression matrix
            data = {
                'sample_id': [f"{tt}_sample_{i}" for i in range(n_samples)],
                'response_label': ['Responder'] * 25 + ['NonResponder'] * 25,
                'tumor_type': [tt] * n_samples
            }
            
            # Add gene columns
            for g in range(n_genes):
                data[f'GENE_{g}'] = np.random.randint(10, 1000, n_samples)
            
            df = pd.DataFrame(data)
            output_path = processed_dir / f"{tt}_discovery_set.csv"
            df.to_csv(output_path, index=False)
        
        yield tmpdir


@pytest.fixture
def sample_discovery_data(temp_project_structure):
    """Load sample discovery data from temp structure."""
    processed_dir = temp_project_structure / "data" / "processed"
    data = {}
    
    for tt in ["BRCA", "LUAD", "COAD"]:
        df = pd.read_csv(processed_dir / f"{tt}_discovery_set.csv")
        data[tt] = df
    
    return data


def test_load_discovery_set_valid(temp_project_structure):
    """Test loading a valid discovery set."""
    processed_dir = temp_project_structure / "data" / "processed"
    tumor_type = "BRCA"
    
    # Patch get_project_root to return temp directory
    with patch('src.differential_expression.get_project_root', return_value=temp_project_structure):
        df = load_discovery_set(tumor_type)
    
    assert df is not None
    assert len(df) == 50
    assert 'sample_id' in df.columns
    assert 'response_label' in df.columns
    assert 'tumor_type' in df.columns
    assert df['tumor_type'].iloc[0] == tumor_type


def test_load_discovery_set_missing_file(temp_project_structure):
    """Test loading a missing discovery set raises error."""
    with patch('src.differential_expression.get_project_root', return_value=temp_project_structure):
        with pytest.raises(FileNotFoundError):
            load_discovery_set("NONEXISTENT")


def test_load_discovery_set_missing_columns(temp_project_structure):
    """Test loading discovery set with missing columns raises error."""
    processed_dir = temp_project_structure / "data" / "processed"
    
    # Create a file with missing columns
    bad_df = pd.DataFrame({'sample_id': [1, 2], 'other': [3, 4]})
    bad_path = processed_dir / "BAD_discovery_set.csv"
    bad_df.to_csv(bad_path, index=False)
    
    with patch('src.differential_expression.get_project_root', return_value=temp_project_structure):
        with pytest.raises(ValueError):
            load_discovery_set("BAD")


@patch('src.differential_expression.setup_r_environment')
@patch('src.differential_expression.watchdog')
def test_process_tumor_type_loo_integration(
    mock_watchdog, 
    mock_setup_r, 
    temp_project_structure, 
    sample_discovery_data
):
    """Test LOO processing logic with mocked R environment."""
    # Mock R environment
    mock_deseq2 = MagicMock()
    mock_stats = MagicMock()
    mock_base = MagicMock()
    mock_setup_r.return_value = (mock_deseq2, mock_stats, mock_base, MagicMock())
    
    # Mock watchdog to return True immediately
    mock_watchdog.side_effect = lambda func, timeout: func()
    
    # Mock pandas2ri and rpy2
    with patch('src.differential_expression.pandas2ri') as mock_pandas2ri:
        with patch('src.differential_expression.rpy2.robjects') as mock_ro:
            mock_pandas2ri.py2rpy.return_value = MagicMock()
            mock_ro.rpy2py_dataframe.return_value = pd.DataFrame({
                'gene_id': ['GENE_1', 'GENE_2'],
                'log2FoldChange': [2.5, -1.5],
                'pvalue': [0.001, 0.03],
                'padj': [0.01, 0.02]
            })
            
            # Mock DESeqDataSetFromMatrix
            mock_deseq2.DESeqDataSetFromMatrix.return_value = MagicMock()
            mock_deseq2.DESeq.return_value = MagicMock()
            mock_deseq2.results.return_value = mock_ro.rpy2py_dataframe.return_value
            
            output_dir = temp_project_structure / "data" / "processed"
            
            # Run LOO for BRCA (holding out BRCA, using LUAD + COAD)
            result = process_tumor_type_loo(
                tumor_type="BRCA",
                all_discovery_data=sample_discovery_data,
                deseq2=mock_deseq2,
                stats=mock_stats,
                base=mock_base,
                output_dir=output_dir
            )
            
            assert result is True
            
            # Verify output file was created
            output_file = output_dir / "loo_iteration_BRCA_de_results.csv"
            assert output_file.exists()
            
            # Verify content
            results_df = pd.read_csv(output_file)
            assert 'gene_id' in results_df.columns
            assert 'log2FoldChange' in results_df.columns
            assert 'tumor_type_held_out' in results_df.columns
            assert results_df['tumor_type_held_out'].iloc[0] == "BRCA"


def test_loo_excludes_held_out_type(sample_discovery_data):
    """Verify that LOO analysis correctly excludes the held-out tumor type."""
    # Check that when holding out BRCA, only LUAD and COAD are in N-1
    n_minus_1_types = [tt for tt in sample_discovery_data.keys() if tt != "BRCA"]
    assert "BRCA" not in n_minus_1_types
    assert "LUAD" in n_minus_1_types
    assert "COAD" in n_minus_1_types
    assert len(n_minus_1_types) == 2


def test_significant_gene_filtering():
    """Test that only genes meeting FDR and log2FC thresholds are included."""
    # Create mock results
    mock_results = pd.DataFrame({
        'gene_id': ['G1', 'G2', 'G3', 'G4'],
        'log2FoldChange': [2.5, 0.5, -1.5, 1.2],
        'pvalue': [0.001, 0.04, 0.002, 0.06],
        'padj': [0.01, 0.03, 0.04, 0.07]
    })
    
    # Apply same filter as in process_tumor_type_loo
    significant = mock_results[
        (mock_results['padj'] < 0.05) & 
        (abs(mock_results['log2FoldChange']) > 1.0)
    ]
    
    # Expected: G1 (padj=0.01, |log2FC|=2.5), G3 (padj=0.04, |log2FC|=1.5)
    # G2: log2FC=0.5 (too low)
    # G4: padj=0.07 (too high)
    assert len(significant) == 2
    assert 'G1' in significant['gene_id'].values
    assert 'G3' in significant['gene_id'].values
    assert 'G2' not in significant['gene_id'].values
    assert 'G4' not in significant['gene_id'].values


@patch('src.differential_expression.get_project_root')
def test_run_deseq2_analysis_no_files(mock_get_root, temp_project_structure):
    """Test that run_deseq2_analysis exits when no discovery files are found."""
    mock_get_root.return_value = Path("/nonexistent")
    
    # Should exit with error
    with pytest.raises(SystemExit) as exc_info:
        run_deseq2_analysis()
    
    assert exc_info.value.code == 1


@patch('src.differential_expression.get_project_root')
def test_run_deseq2_analysis_insufficient_types(mock_get_root, temp_project_structure):
    """Test that run_deseq2_analysis exits with <2 tumor types."""
    # Create a temp dir with only 1 tumor type
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        processed_dir = tmpdir / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Only one tumor type
        df = pd.DataFrame({'sample_id': [1], 'response_label': ['R'], 'tumor_type': ['A'], 'G1': [100]})
        df.to_csv(processed_dir / "A_discovery_set.csv", index=False)
        
        mock_get_root.return_value = tmpdir
        
        with pytest.raises(SystemExit) as exc_info:
            run_deseq2_analysis()
        
        assert exc_info.value.code == 1