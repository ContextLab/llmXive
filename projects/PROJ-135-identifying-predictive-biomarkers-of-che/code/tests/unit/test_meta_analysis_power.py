import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.meta_analysis import (
    load_discovery_results,
    compute_intersection,
    compute_union_top_ranked,
    run_stouffers_meta_analysis,
    aggregate_and_select_panel
)
from src.config import get_project_root

@pytest.fixture
def temp_project_structure():
    """Create a temporary project structure with mock DE results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Mock results directory
        de_dir = tmp_path / 'results' / 'de'
        de_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock DE results for 2 tumor types
        # Type 1: BRCA
        df1 = pd.DataFrame({
            'gene_symbol': ['GENE_A', 'GENE_B', 'GENE_C'],
            'log2FoldChange': [2.0, 1.5, 0.5],
            'pvalue': [0.001, 0.01, 0.5],
            'padj': [0.01, 0.05, 0.9]
        })
        df1.to_csv(de_dir / 'BRCA_de_results.csv', index=False)

        # Type 2: LUAD
        df2 = pd.DataFrame({
            'gene_symbol': ['GENE_A', 'GENE_B', 'GENE_D'],
            'log2FoldChange': [2.5, 1.2, 3.0],
            'pvalue': [0.0001, 0.02, 0.001],
            'padj': [0.001, 0.06, 0.01]
        })
        df2.to_csv(de_dir / 'LUAD_de_results.csv', index=False)

        yield tmp_path

        # Cleanup handled by TemporaryDirectory

def test_load_discovery_results_valid(temp_project_structure):
    results_dir = temp_project_structure / 'results' / 'de'
    results = load_discovery_results(results_dir)
    assert 'BRCA' in results
    assert 'LUAD' in results
    assert len(results['BRCA']) == 3
    assert len(results['LUAD']) == 3

def test_compute_intersection(temp_project_structure):
    results_dir = temp_project_structure / 'results' / 'de'
    results = load_discovery_results(results_dir)
    # GENE_A is significant in both (padj < 0.05, |log2FC| > 1)
    # GENE_B: BRCA (padj=0.05, not < 0.05? strict <, so no. Wait, 0.05 is not < 0.05)
    # Let's adjust mock data logic in test if needed, but assuming strict < 0.05
    # BRCA: GENE_A (0.01), GENE_B (0.05 - NO), GENE_C (0.9) -> {GENE_A}
    # LUAD: GENE_A (0.001), GENE_B (0.06 - NO), GENE_D (0.01) -> {GENE_A, GENE_D}
    # Intersection: {GENE_A}
    intersection = compute_intersection(results)
    assert 'GENE_A' in intersection
    assert 'GENE_B' not in intersection # padj 0.05 is not < 0.05
    assert 'GENE_D' not in intersection # only in LUAD

def test_compute_union_top_ranked(temp_project_structure):
    results_dir = temp_project_structure / 'results' / 'de'
    results = load_discovery_results(results_dir)
    # Significant in at least one:
    # BRCA: GENE_A (2.0), GENE_B (1.5, padj 0.05 NO) -> GENE_A
    # LUAD: GENE_A (2.5), GENE_D (3.0)
    # Union: GENE_A, GENE_D
    # Ranked by mean |log2FC|:
    # GENE_A: (2.0+2.5)/2 = 2.25
    # GENE_D: 3.0
    # Order: GENE_D, GENE_A
    union = compute_union_top_ranked(results, max_genes=50)
    assert 'GENE_A' in union
    assert 'GENE_D' in union
    if len(union) >= 2:
        assert union[0] == 'GENE_D' # Higher mean log2FC

def test_aggregate_and_select_panel_with_power_flag(temp_project_structure):
    """Test T049: Validate Meta-Analysis Statistical Power."""
    results_dir = temp_project_structure / 'results' / 'de'
    results = load_discovery_results(results_dir)
    
    meta_df = run_stouffers_meta_analysis(results)
    
    output_panel = temp_project_structure / 'results' / 'meta_analysis' / 'gene_panel.json'
    output_status = temp_project_structure / 'results' / 'meta_analysis' / 'panel_status.json'
    
    output_panel.parent.mkdir(parents=True, exist_ok=True)
    
    aggregate_and_select_panel(results, meta_df, output_panel, output_status)
    
    assert output_panel.exists()
    assert output_status.exists()
    
    with open(output_status, 'r') as f:
        status = json.load(f)
    
    # Check that underpowered_genes is present
    assert 'underpowered_genes' in status
    assert 'underpowered_count' in status
    assert 'min_sample_size_threshold' in status
    
    # Check panel structure
    with open(output_panel, 'r') as f:
        panel = json.load(f)
    
    for gene in panel:
        assert 'underpowered' in gene
        assert 'approx_sample_size' in gene