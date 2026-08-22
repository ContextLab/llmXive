import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from scipy.stats import norm

from src.meta_analysis import (
    load_discovery_results,
    run_stouffers_meta_analysis,
    save_meta_analysis_results
)

@pytest.fixture
def temp_project_structure():
    """Create a temporary project structure with mock DE results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create discovery set directory
        discovery_dir = tmpdir / "data" / "processed" / "discovery_set"
        discovery_dir.mkdir(parents=True)
        
        # Create mock DE results for 3 tumor types
        tumor_types = ["BRCA", "LUAD", "COAD"]
        
        # Common genes across all types
        common_genes = ["GENE_A", "GENE_B", "GENE_C", "GENE_D", "GENE_E"]
        
        for tumor_type in tumor_types:
            # Create mock data with varying p-values and log2FC
            np.random.seed(42)
            data = {
                'gene_symbol': common_genes + [f"GENE_{tumor_type}_{i}" for i in range(5)],
                'pvalue': np.random.uniform(0.001, 0.5, 10),
                'log2FC': np.random.uniform(-2, 2, 10),
                'padj': np.random.uniform(0.01, 0.5, 10)
            }
            
            df = pd.DataFrame(data)
            output_file = discovery_dir / f"{tumor_type}_de_results.csv"
            df.to_csv(output_file, index=False)
        
        yield tmpdir

@pytest.fixture
def temp_project_empty_results():
    """Create a temporary project structure with no DE results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        discovery_dir = tmpdir / "data" / "processed" / "discovery_set"
        discovery_dir.mkdir(parents=True)
        yield tmpdir

class TestLoadDiscoveryResults:
    def test_load_discovery_results_valid(self, temp_project_structure):
        """Test loading valid DE results."""
        discovery_dir = temp_project_structure / "data" / "processed" / "discovery_set"
        results = load_discovery_results(discovery_dir)
        
        assert len(results) == 3
        assert "BRCA" in results
        assert "LUAD" in results
        assert "COAD" in results
        
        for tumor_type, df in results.items():
            assert 'gene_symbol' in df.columns
            assert 'pvalue' in df.columns
            assert 'log2FC' in df.columns
            assert len(df) == 10

    def test_load_discovery_results_missing_file(self, temp_project_empty_results):
        """Test loading when no DE result files exist."""
        discovery_dir = temp_project_empty_results / "data" / "processed" / "discovery_set"
        
        with pytest.raises(ValueError, match="No DE result files found"):
            load_discovery_results(discovery_dir)

    def test_load_discovery_results_missing_columns(self, temp_project_structure):
        """Test loading when required columns are missing."""
        discovery_dir = temp_project_structure / "data" / "processed" / "discovery_set"
        
        # Remove a required column from one file
        file_path = discovery_dir / "BRCA_de_results.csv"
        df = pd.read_csv(file_path)
        df = df.drop(columns=['pvalue'])
        df.to_csv(file_path, index=False)
        
        with pytest.raises(ValueError, match="missing required columns"):
            load_discovery_results(discovery_dir)

class TestStouffersMetaAnalysis:
    def test_run_stouffers_meta_analysis(self, temp_project_structure):
        """Test Stouffer's meta-analysis with valid data."""
        discovery_dir = temp_project_structure / "data" / "processed" / "discovery_set"
        results = load_discovery_results(discovery_dir)
        
        meta_df = run_stouffers_meta_analysis(results)
        
        # Check output structure
        assert 'gene_symbol' in meta_df.columns
        assert 'meta_pvalue' in meta_df.columns
        assert 'meta_zscore' in meta_df.columns
        assert 'n_studies' in meta_df.columns
        assert 'log2FC_mean' in meta_df.columns
        assert 'bonferroni_adjusted_p' in meta_df.columns
        assert 'significant' in meta_df.columns
        
        # Check that common genes are present
        common_genes = ["GENE_A", "GENE_B", "GENE_C", "GENE_D", "GENE_E"]
        for gene in common_genes:
            assert gene in meta_df['gene_symbol'].values
        
        # Check that n_studies is correct for common genes
        common_gene_rows = meta_df[meta_df['gene_symbol'].isin(common_genes)]
        assert all(common_gene_rows['n_studies'] == 3)
        
        # Check that p-values are in valid range
        assert all((meta_df['meta_pvalue'] >= 0) & (meta_df['meta_pvalue'] <= 1))
        assert all((meta_df['bonferroni_adjusted_p'] >= 0) & (meta_df['bonferroni_adjusted_p'] <= 1))

    def test_run_stouffers_meta_analysis_insufficient_studies(self, temp_project_structure):
        """Test meta-analysis with genes that have insufficient studies."""
        discovery_dir = temp_project_structure / "data" / "processed" / "discovery_set"
        results = load_discovery_results(discovery_dir)
        
        # Filter results to only include one tumor type
        single_type_results = {"BRCA": results["BRCA"]}
        
        # This should skip genes with only 1 study
        meta_df = run_stouffers_meta_analysis(single_type_results)
        
        # Should be empty or have very few genes
        assert len(meta_df) == 0

    def test_run_stouffers_meta_analysis_empty(self, temp_project_empty_results):
        """Test meta-analysis with no results."""
        discovery_dir = temp_project_empty_results / "data" / "processed" / "discovery_set"
        
        with pytest.raises(ValueError, match="No results provided"):
            load_discovery_results(discovery_dir)

class TestSaveMetaAnalysisResults:
    def test_save_meta_analysis_results(self, temp_project_structure):
        """Test saving meta-analysis results."""
        discovery_dir = temp_project_structure / "data" / "processed" / "discovery_set"
        results = load_discovery_results(discovery_dir)
        meta_df = run_stouffers_meta_analysis(results)
        
        output_dir = temp_project_structure / "results" / "meta_analysis"
        output_dir.mkdir(parents=True)
        
        output_csv = output_dir / "stouffer_meta.csv"
        m_meta = len(meta_df)
        
        save_meta_analysis_results(meta_df, output_csv, m_meta)
        
        # Check CSV file exists
        assert output_csv.exists()
        
        # Check JSON file exists
        bonferroni_json = output_dir / "bonferroni_correction.json"
        assert bonferroni_json.exists()
        
        # Verify JSON content
        with open(bonferroni_json, 'r') as f:
            data = json.load(f)
        
        assert data['m_meta'] == m_meta
        assert 'description' in data
        assert data['method'] == "Bonferroni"

    def test_save_meta_analysis_results_creates_directory(self, temp_project_structure):
        """Test that save function creates output directory if it doesn't exist."""
        discovery_dir = temp_project_structure / "data" / "processed" / "discovery_set"
        results = load_discovery_results(discovery_dir)
        meta_df = run_stouffers_meta_analysis(results)
        
        output_dir = temp_project_structure / "results" / "meta_analysis" / "new_subdir"
        output_csv = output_dir / "stouffer_meta.csv"
        m_meta = len(meta_df)
        
        save_meta_analysis_results(meta_df, output_csv, m_meta)
        
        assert output_csv.exists()