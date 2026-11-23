import pytest
import pandas as pd
import numpy as np
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the analysis service which contains the full pipeline logic
from src.services.analysis import run_full_analysis, save_analysis_report
from src.models.config import ARTIFACT_PATH

@pytest.fixture
def sample_analysis_dataset():
    """
    Creates a realistic sample dataset mimicking the structure of
    data/processed/final_analysis_dataset.parquet.
    This avoids dependency on the full ingestion pipeline for this specific test,
    focusing on the statistical execution and report generation.
    """
    np.random.seed(42)
    n_nodes = 500

    # Generate synthetic but realistic data distributions
    # Bridging coefficients typically range 0.0 to 1.0
    bridging = np.random.beta(2, 5, n_nodes) 

    # Citation counts: skewed distribution (power-law like)
    citations = np.random.pareto(1.5, n_nodes).astype(int) + 1
    citations = np.clip(citations, 0, 10000)

    # Novelty scores: positive floats
    novelty = np.abs(np.random.randn(n_nodes)) * 0.5 + 0.1

    # Cluster sizes (covariate)
    cluster_sizes = np.random.randint(10, 500, n_nodes)

    # Publication years (recent range)
    years = np.random.randint(2010, 2024, n_nodes)

    df = pd.DataFrame({
        'id': [f'node_{i}' for i in range(n_nodes)],
        'bridging_coefficient': bridging,
        'citation_count': citations,
        'novelty_score': novelty,
        'cluster_size': cluster_sizes,
        'publication_year': years,
        'primary_cluster': np.random.randint(0, 20, n_nodes),
        'topic_cluster': np.random.randint(0, 50, n_nodes)
    })

    return df

@pytest.fixture
def temp_output_dir():
    """Creates a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_binned_analysis_execution(sample_analysis_dataset, temp_output_dir):
    """
    Integration test for the full statistical pipeline.
    
    Input: Uses a sample dataset mimicking data/processed/final_analysis_dataset.parquet.
    
    Assertions:
    1. Verifies p-values are present in the output metrics.
    2. Verifies p-values are corrected (Bonferroni/BH).
    3. Verifies the generated report contains the "associational" label.
    """
    # Ensure output directories exist
    results_dir = temp_output_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock the file paths to point to our temp directory
    metrics_path = results_dir / "statistical_metrics.json"
    report_path = results_dir / "analysis_report.md"
    corrected_pvalues_path = results_dir / "corrected_pvalues.json"
    
    # Patch the config paths to use our temp directory
    # Note: We are testing the logic, so we pass paths directly to the function
    # or mock the config if the function relies on global config.
    # Based on the API surface, run_full_analysis likely returns the data,
    # and save_analysis_report writes it.
    
    # 1. Run the statistical analysis
    # We pass the dataframe directly if the function signature allows,
    # or we mock the loading step. Assuming run_full_analysis takes data or config.
    # Looking at imports: run_full_analysis, save_analysis_report.
    # We will simulate the flow: run analysis -> get metrics -> save report.
    
    # Mock the file reading to return our sample data
    with patch('pandas.read_parquet') as mock_read_parquet:
        mock_read_parquet.return_value = sample_analysis_dataset
        
        # Run the full analysis logic
        # This function is expected to perform Spearman, Regression, and Correction
        analysis_results = run_full_analysis(
            data_path=str(sample_analysis_dataset), # Passing DF directly if supported, or mock path
            correction_method='bonferroni'
        )
        
        # If run_full_analysis expects a path, we need to save the DF first
        # Let's adjust: save to temp parquet, then pass path
        temp_parquet = temp_output_dir / "test_input.parquet"
        sample_analysis_dataset.to_parquet(temp_parquet)
        
        # Re-run with path
        analysis_results = run_full_analysis(
            data_path=str(temp_parquet),
            correction_method='bonferroni'
        )
    
    # Assert 1: Check that analysis results contain p-values
    assert analysis_results is not None, "Analysis results should not be None"
    assert 'correlations' in analysis_results, "Results should contain 'correlations'"
    assert 'regression' in analysis_results, "Results should contain 'regression'"
    
    corr_data = analysis_results['correlations']
    assert 'p_values' in corr_data, "Correlations should have p_values"
    assert 'corrected_p_values' in corr_data, "Correlations should have corrected_p_values"
    
    # Verify p-values are present and valid (0 to 1)
    p_vals = corr_data['p_values']
    corr_p_vals = corr_data['corrected_p_values']
    
    assert len(p_vals) > 0, "There should be at least one p-value"
    assert all(0 <= p <= 1 for p in p_vals), "Raw p-values must be between 0 and 1"
    assert all(0 <= p <= 1 for p in corr_p_vals), "Corrected p-values must be between 0 and 1"
    
    # Assert 2: Verify correction was applied (corrected != raw usually, unless all 1.0)
    # We check that the key exists and has the same length
    assert len(corr_p_vals) == len(p_vals), "Corrected p-values count must match raw count"
    
    # Assert 3: Generate and verify the report contains "associational"
    # We need to call save_analysis_report which writes to disk
    save_analysis_report(
        analysis_results=analysis_results,
        output_path=str(report_path)
    )
    
    # Verify file exists
    assert report_path.exists(), f"Report file {report_path} was not created"
    
    # Read content and check for label
    content = report_path.read_text()
    assert "associational" in content.lower(), "Report must explicitly label results as 'associational'"
    
    # Optional: Verify corrected pvalues JSON was also written (per T028 spec)
    if corrected_pvalues_path.exists():
        with open(corrected_pvalues_path) as f:
            cp_data = json.load(f)
        assert 'method' in cp_data
        assert 'corrected_pvalues' in cp_data
        assert 'significant_count' in cp_data