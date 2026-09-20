"""
Integration test for the full statistical analysis pipeline.

This test verifies that the statistical analysis runs end-to-end on the
final analysis dataset, producing valid p-values, corrected p-values,
and a report that explicitly labels results as "associational".
"""
import pytest
import pandas as pd
import numpy as np
import os
import json
from pathlib import Path
from src.services.analysis import run_full_analysis

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
FINAL_DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "final_analysis_dataset.parquet"
RESULTS_DIR = PROJECT_ROOT / "artifacts" / "results"
REPORT_PATH = RESULTS_DIR / "analysis_report.md"
METRICS_PATH = RESULTS_DIR / "statistical_metrics.json"
CORRECTED_PVALUES_PATH = RESULTS_DIR / "corrected_pvalues.json"

@pytest.fixture
def analysis_data():
    """
    Load the final analysis dataset for testing.
    
    Returns:
        pd.DataFrame: The dataset containing bridging_coefficient, citation_count, 
                      novelty_score, and other required columns.
    
    Raises:
        FileNotFoundError: If the dataset file does not exist.
    """
    if not FINAL_DATASET_PATH.exists():
        pytest.fail(f"Final analysis dataset not found at {FINAL_DATASET_PATH}. "
                    "Please run the ingestion pipeline (T024) first.")
    
    df = pd.read_parquet(FINAL_DATASET_PATH)
    
    # Verify required columns exist
    required_cols = ['bridging_coefficient', 'citation_count', 'novelty_score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        pytest.fail(f"Missing required columns in dataset: {missing_cols}")
    
    # Ensure numeric types
    df['bridging_coefficient'] = pd.to_numeric(df['bridging_coefficient'], errors='coerce')
    df['citation_count'] = pd.to_numeric(df['citation_count'], errors='coerce')
    df['novelty_score'] = pd.to_numeric(df['novelty_score'], errors='coerce')
    
    # Drop rows with NaN in critical columns for analysis
    df_clean = df.dropna(subset=required_cols)
    
    if len(df_clean) < 10:
        pytest.fail(f"Dataset has fewer than 10 valid rows after cleaning ({len(df_clean)}). "
                    "Analysis requires sufficient data.")
    
    return df_clean

def test_binned_analysis_execution(analysis_data):
    """
    Execute the full statistical analysis pipeline and verify outputs.
    
    This test:
    1. Runs the full statistical analysis (Spearman, Linear Regression, Binned Analysis)
    2. Verifies that p-values are present in the metrics
    3. Verifies that p-values are corrected (Bonferroni/BH)
    4. Verifies the report contains the "associational" label
    5. Verifies all expected output files are created
    """
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run the full analysis pipeline
    # This function should perform:
    # - Spearman correlation (T026)
    # - Linear regression with covariates (T027)
    # - Binned non-linear analysis (T027_binned_analysis)
    # - Multiple comparison correction (T028)
    # - Report generation (T029)
    # - Save metrics (T030)
    try:
        result = run_full_analysis(
            data=analysis_data,
            correction_method='bh',  # Benjamini-Hochberg
            output_dir=str(RESULTS_DIR)
        )
    except Exception as e:
        pytest.fail(f"Statistical analysis pipeline failed: {e}")
    
    # Verify that result contains expected keys
    assert 'correlations' in result, "Missing 'correlations' in analysis result"
    assert 'regression' in result, "Missing 'regression' in analysis result"
    assert 'binned_analysis' in result, "Missing 'binned_analysis' in analysis result"
    assert 'corrected_pvalues' in result, "Missing 'corrected_pvalues' in analysis result"
    
    # Verify p-values are present and numeric
    correlations = result['correlations']
    assert 'bridging_citations' in correlations, "Missing bridging-citations correlation"
    assert 'p_value' in correlations['bridging_citations'], "Missing p_value in correlation"
    assert isinstance(correlations['bridging_citations']['p_value'], (int, float)), "p_value must be numeric"
    
    # Verify corrected p-values exist
    corrected_pvals = result['corrected_pvalues']
    assert 'method' in corrected_pvals, "Missing correction method"
    assert 'corrected_pvalues' in corrected_pvals, "Missing corrected_pvalues list"
    assert len(corrected_pvals['corrected_pvalues']) > 0, "No corrected p-values found"
    
    # Verify the report file was created and contains "associational"
    assert REPORT_PATH.exists(), f"Analysis report not created at {REPORT_PATH}"
    
    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        report_content = f.read()
    
    assert 'associational' in report_content.lower(), \
        "Report must explicitly label results as 'associational'"
    
    # Verify metrics file exists and is valid JSON
    assert METRICS_PATH.exists(), f"Statistical metrics not created at {METRICS_PATH}"
    with open(METRICS_PATH, 'r', encoding='utf-8') as f:
        metrics = json.load(f)
    
    assert 'spearman' in metrics, "Missing 'spearman' in metrics"
    assert 'linear_regression' in metrics, "Missing 'linear_regression' in metrics"
    assert 'binned_analysis' in metrics, "Missing 'binned_analysis' in metrics"
    
    # Verify corrected pvalues file
    assert CORRECTED_PVALUES_PATH.exists(), f"Corrected p-values not created at {CORRECTED_PVALUES_PATH}"
    with open(CORRECTED_PVALUES_PATH, 'r', encoding='utf-8') as f:
        corrected_data = json.load(f)
    
    assert 'significant_count' in corrected_data, "Missing significant_count"
    assert isinstance(corrected_data['significant_count'], int), "significant_count must be integer"
    
    # Additional check: ensure binned analysis has expected structure
    binned = result['binned_analysis']
    assert 'bin_edges' in binned, "Missing bin_edges in binned analysis"
    assert 'mean_bridging' in binned, "Missing mean_bridging in binned analysis"
    assert 'mean_citations' in binned, "Missing mean_citations in binned analysis"
    assert len(binned['bin_edges']) > 1, "Binned analysis must have at least 2 edges"

def test_report_label_and_structure():
    """
    Verify the analysis report structure and labeling independently.
    
    This test ensures that the report generated by T029 follows the expected
    format and explicitly states the associational nature of the findings.
    """
    if not REPORT_PATH.exists():
        # If report doesn't exist, run the analysis first
        if not FINAL_DATASET_PATH.exists():
            pytest.skip("Dataset not available; skipping report structure test")
        
        df = pd.read_parquet(FINAL_DATASET_PATH)
        df['bridging_coefficient'] = pd.to_numeric(df['bridging_coefficient'], errors='coerce')
        df['citation_count'] = pd.to_numeric(df['citation_count'], errors='coerce')
        df['novelty_score'] = pd.to_numeric(df['novelty_score'], errors='coerce')
        df_clean = df.dropna(subset=['bridging_coefficient', 'citation_count', 'novelty_score'])
        
        if len(df_clean) < 10:
            pytest.skip("Insufficient data for analysis")
        
        run_full_analysis(data=df_clean, correction_method='bh', output_dir=str(RESULTS_DIR))
    
    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for required sections
    required_sections = [
        '## Executive Summary',
        '## Statistical Methods',
        '## Results',
        '## Interpretation',
        '## Limitations'
    ]
    
    for section in required_sections:
        assert section in content, f"Missing required section: {section}"
    
    # Check for associational label in multiple places
    assert 'associational' in content.lower(), "Report must use 'associational' terminology"
    
    # Check that it does NOT claim causality
    causal_terms = ['caus', 'proves', 'demonstrates causality']
    for term in causal_terms:
        assert term not in content.lower(), \
            f"Report should not claim causality. Found: '{term}'"