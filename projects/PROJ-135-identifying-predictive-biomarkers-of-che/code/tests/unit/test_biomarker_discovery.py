import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from src.biomarker_discovery import load_discovery_set, process_tumor_type, aggregate_results

@pytest.fixture
def temp_project_dir():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create directory structure
        (project_root / "data" / "processed").mkdir(parents=True)
        (project_root / "results").mkdir(parents=True)
        (project_root / "results" / "meta_analysis").mkdir(parents=True)
        
        # Create mock discovery set files
        for tumor_type in ['BRCA', 'LUAD', 'COAD']:
            df = pd.DataFrame({
                'gene_id': ['GENE1', 'GENE2', 'GENE3', 'GENE4', 'GENE5'],
                'sample1': [10, 5, 20, 15, 8],
                'sample2': [12, 6, 22, 14, 9],
                'sample3': [11, 5, 21, 16, 7],
                'sample4': [13, 7, 23, 15, 10],
                'sample5': [14, 8, 24, 17, 11],
                'sample6': [15, 9, 25, 18, 12],
                'sample7': [16, 10, 26, 19, 13],
                'sample8': [17, 11, 27, 20, 14],
                'sample9': [18, 12, 28, 21, 15],
                'sample10': [19, 13, 29, 22, 16],
                'sample11': [20, 14, 30, 23, 17],
                'sample12': [21, 15, 31, 24, 18],
                'response_label': ['Responder', 'Responder', 'NonResponder', 'NonResponder', 
                                  'Responder', 'Responder', 'NonResponder', 'NonResponder',
                                  'Responder', 'Responder', 'NonResponder', 'NonResponder']
            })
            df.to_csv(project_root / "data" / "processed" / f"{tumor_type}_discovery_set.csv", index=False)
        
        yield project_root

def test_load_discovery_set_valid(temp_project_dir):
    """Test loading a valid discovery set."""
    df = load_discovery_set('BRCA', temp_project_dir)
    
    assert 'gene_id' in df.columns
    assert 'response_label' in df.columns
    assert len(df) == 5  # 5 genes
    assert df['response_label'].nunique() == 2  # 2 classes

def test_load_discovery_set_missing_file(temp_project_dir):
    """Test loading a non-existent discovery set."""
    with pytest.raises(FileNotFoundError):
        load_discovery_set('NONEXISTENT', temp_project_dir)

def test_load_discovery_set_missing_columns(temp_project_dir):
    """Test loading a discovery set missing required columns."""
    # Create a file without response_label
    df = pd.DataFrame({
        'gene_id': ['GENE1', 'GENE2'],
        'sample1': [10, 5],
        'sample2': [12, 6]
    })
    df.to_csv(temp_project_dir / "data" / "processed" / "TEST_discovery_set.csv", index=False)
    
    with pytest.raises(ValueError):
        load_discovery_set('TEST', temp_project_dir)

def test_process_tumor_type_small_sample(temp_project_dir):
    """Test processing a tumor type with too few samples."""
    # Create a file with only 5 samples
    df = pd.DataFrame({
        'gene_id': ['GENE1', 'GENE2', 'GENE3'],
        'sample1': [10, 5, 20],
        'sample2': [12, 6, 22],
        'sample3': [11, 5, 21],
        'sample4': [13, 7, 23],
        'sample5': [14, 8, 24],
        'response_label': ['Responder', 'Responder', 'NonResponder', 'NonResponder', 'Responder']
    })
    df.to_csv(temp_project_dir / "data" / "processed" / "SMALL_discovery_set.csv", index=False)
    
    # Mock the DESeq2 analysis to avoid R dependency
    with patch('src.biomarker_discovery.run_deseq2_analysis') as mock_deseq:
        mock_deseq.return_value = pd.DataFrame({
            'gene_id': ['GENE1'],
            'log2FoldChange': [1.5],
            'pvalue': [0.01],
            'padj': [0.02]
        })
        
        result = process_tumor_type('SMALL', temp_project_dir)
        
        # Should be skipped due to < 10 samples
        assert result['status'] == 'skipped'
        assert 'insufficient_samples' in result['reason']

def test_aggregate_results(temp_project_dir):
    """Test aggregating DE results from multiple tumor types."""
    # Create mock DE result files
    for tumor_type in ['BRCA', 'LUAD', 'COAD']:
        df = pd.DataFrame({
            'gene_id': ['GENE1', 'GENE2'],
            'log2FoldChange': [1.5, -1.2],
            'pvalue': [0.01, 0.02],
            'padj': [0.02, 0.03]
        })
        df.to_csv(temp_project_dir / "data" / "processed" / f"{tumor_type}_de_results.csv", index=False)
    
    aggregate_results(temp_project_dir)
    
    # Check aggregated file exists
    agg_file = temp_project_dir / "data" / "processed" / "static_aggregated_results.csv"
    assert agg_file.exists()
    
    # Check content
    agg_df = pd.read_csv(agg_file)
    assert len(agg_df) == 6  # 3 tumor types * 2 genes
    assert 'tumor_type' in agg_df.columns
    assert agg_df['tumor_type'].nunique() == 3

def test_aggregate_results_empty(temp_project_dir):
    """Test aggregating when no DE result files exist."""
    aggregate_results(temp_project_dir)
    
    agg_file = temp_project_dir / "data" / "processed" / "static_aggregated_results.csv"
    assert agg_file.exists()
    
    agg_df = pd.read_csv(agg_file)
    assert len(agg_df) == 0
    assert list(agg_df.columns) == ['gene_id', 'log2FoldChange', 'pvalue', 'padj', 'tumor_type']