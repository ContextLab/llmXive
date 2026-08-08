"""
Contract tests for meta-analysis output schema compliance.

Verifies that the gene panel output conforms to the expected schema.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.meta_analysis import save_gene_panel


class TestGenePanelSchema:
    """Tests for gene panel schema compliance."""
    
    def test_gene_panel_required_fields(self):
        """Test that all required fields are present in the gene panel."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'gene_panel.json'
            
            save_gene_panel(
                genes=['GENE_A', 'GENE_B', 'GENE_C'],
                method='intersection',
                output_path=output_path
            )
            
            with open(output_path, 'r') as f:
                panel_data = json.load(f)
            
            # Check required fields
            assert 'selected' in panel_data
            assert 'panel_size' in panel_data
            assert 'selection_method' in panel_data
            assert 'created_at' in panel_data
            assert 'gene_list' in panel_data
            
            # Validate field types
            assert isinstance(panel_data['selected'], list)
            assert isinstance(panel_data['panel_size'], int)
            assert isinstance(panel_data['selection_method'], str)
            assert isinstance(panel_data['created_at'], str)
            assert isinstance(panel_data['gene_list'], list)
    
    def test_gene_panel_consistency(self):
        """Test that panel_size matches the length of selected genes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'gene_panel.json'
            genes = ['GENE_A', 'GENE_B', 'GENE_C', 'GENE_D']
            
            save_gene_panel(
                genes=genes,
                method='intersection',
                output_path=output_path
            )
            
            with open(output_path, 'r') as f:
                panel_data = json.load(f)
            
            assert panel_data['panel_size'] == len(genes)
            assert len(panel_data['selected']) == len(genes)
            assert len(panel_data['gene_list']) == len(genes)
    
    def test_gene_panel_sorted_list(self):
        """Test that gene_list is alphabetically sorted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'gene_panel.json'
            genes = ['ZEBRA', 'APPLE', 'MANGO', 'BANANA']
            
            save_gene_panel(
                genes=genes,
                method='intersection',
                output_path=output_path
            )
            
            with open(output_path, 'r') as f:
                panel_data = json.load(f)
            
            expected_sorted = sorted(genes)
            assert panel_data['gene_list'] == expected_sorted
            assert panel_data['gene_list'] == sorted(panel_data['gene_list'])
    
    def test_gene_panel_with_meta_analysis(self):
        """Test gene panel with meta-analysis summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'gene_panel.json'
            genes = ['GENE_A', 'GENE_B']
            
            meta_results = {
                'GENE_A': {
                    'combined_pvalue': 0.001,
                    'combined_zscore': 3.5,
                    'num_studies': 3
                },
                'GENE_B': {
                    'combined_pvalue': 0.005,
                    'combined_zscore': 2.8,
                    'num_studies': 3
                }
            }
            
            save_gene_panel(
                genes=genes,
                method='stouffer',
                meta_analysis_results=meta_results,
                output_path=output_path
            )
            
            with open(output_path, 'r') as f:
                panel_data = json.load(f)
            
            assert 'meta_analysis_summary' in panel_data
            assert 'GENE_A' in panel_data['meta_analysis_summary']
            assert 'combined_pvalue' in panel_data['meta_analysis_summary']['GENE_A']
            assert 'combined_zscore' in panel_data['meta_analysis_summary']['GENE_A']
            assert 'num_studies' in panel_data['meta_analysis_summary']['GENE_A']
    
    def test_gene_panel_with_fallback_reason(self):
        """Test gene panel with fallback reason."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'gene_panel.json'
            
            save_gene_panel(
                genes=['GENE_A', 'GENE_B'],
                method='union_top_ranked',
                fallback_reason='intersection_empty',
                output_path=output_path
            )
            
            with open(output_path, 'r') as f:
                panel_data = json.load(f)
            
            assert 'fallback_reason' in panel_data
            assert panel_data['fallback_reason'] == 'intersection_empty'
            assert panel_data['selection_method'] == 'union_top_ranked'
    
    def test_gene_panel_empty_genes_raises_error(self):
        """Test that saving an empty gene panel raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'gene_panel.json'
            
            with pytest.raises(ValueError, match="Cannot save empty gene panel"):
                save_gene_panel(
                    genes=[],
                    method='intersection',
                    output_path=output_path
                )
