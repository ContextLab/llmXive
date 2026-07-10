"""
Integration test for the full analysis pipeline using synthetic data.

This test verifies that the pipeline correctly:
1. Merges anxiety scores and control proxies.
2. Performs statistical analysis (Shapiro-Wilk on residuals, correlation selection).
3. Generates the analysis_results.json with the correct structure and flags.
4. Produces a visualization file.

It uses a deterministic synthetic dataset with a known negative correlation
to ensure the output regression coefficient is negative and p-value < 0.05.
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
import pytest

# Import pipeline components
from code.main import stage_05_merge_and_validate, stage_06_statistical_analysis, stage_07_visualization
from code.config import CONFIG, DATA_PROCESSED_DIR
from code.analysis.statistical_test import run_statistical_analysis_pipeline

# Ensure the processed data directory exists for the test
@pytest.fixture(scope="module")
def processed_dir():
    """Create a temporary directory to mimic data/processed for this test."""
    # We use the actual CONFIG path but ensure it exists
    # In a real CI, this would be the actual data folder.
    # For this test, we assume the environment is set up or we create it.
    if not DATA_PROCESSED_DIR.exists():
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_PROCESSED_DIR

@pytest.fixture(scope="module")
def synthetic_data(processed_dir: Path) -> Path:
    """
    Generates a synthetic dataset with a known negative correlation
    between control_proxy and anxiety_score.
    
    The data is saved to the processed directory to simulate the output
    of previous stages (T017 and T026).
    """
    np.random.seed(42)
    n_samples = 500
    
    # Generate control_proxy values (0.0 to 2.0)
    control_proxy = np.random.uniform(0.0, 2.0, n_samples)
    
    # Generate anxiety_score with a strong negative correlation
    # anxiety = -2.0 * control_proxy + noise
    # We add some noise to make it realistic but keep the trend clear
    noise = np.random.normal(0, 0.5, n_samples)
    anxiety_score = -2.0 * control_proxy + 3.0 + noise
    
    # Ensure scores are within a reasonable range (0 to 4)
    anxiety_score = np.clip(anxiety_score, 0.0, 4.0)
    
    # Create DataFrames
    df_scores = pd.DataFrame({
        'post_id': [f'post_{i}' for i in range(n_samples)],
        'text': ['Sample text'] * n_samples,
        'anxiety_score': anxiety_score,
        'confidence_score': np.ones(n_samples) * 0.9  # High confidence
    })
    
    df_proxies = pd.DataFrame({
        'post_id': [f'post_{i}' for i in range(n_samples)],
        'user_id': [f'user_{i % 50}' for i in range(n_samples)],
        'control_proxy': control_proxy,
        'timestamp_regularity': np.random.uniform(0.0, 1.0, n_samples)
    })
    
    # Save to the processed directory
    scores_path = processed_dir / "scoring_results.csv"
    proxies_path = processed_dir / "proxy_results.csv"
    
    df_scores.to_csv(scores_path, index=False)
    df_proxies.to_csv(proxies_path, index=False)
    
    return processed_dir

def test_full_analysis_pipeline_synthetic_data(synthetic_data: Path):
    """
    Run the full analysis pipeline on synthetic data and verify results.
    
    Acceptance Criteria:
    1. `data/processed/final_analysis.csv` is created.
    2. `data/processed/normality_check.json` is created.
    3. `data/processed/analysis_results.json` is created with:
       - `is_significant` is True (p < 0.05)
       - Correlation coefficient is negative.
    4. `data/processed/correlation_plot.png` is created.
    """
    # Step 1: Merge data (Stage 5)
    # Note: stage_05_merge_and_validate expects the files to exist in DATA_PROCESSED_DIR
    # which we populated in the fixture.
    final_df = stage_05_merge_and_validate()
    
    assert final_df is not None, "Merge stage failed to return a DataFrame"
    assert 'anxiety_score' in final_df.columns, "Merged data missing anxiety_score"
    assert 'control_proxy' in final_df.columns, "Merged data missing control_proxy"
    assert len(final_df) > 0, "Merged data is empty"
    
    # Verify the negative correlation exists in the data
    corr_val = final_df['anxiety_score'].corr(final_df['control_proxy'])
    assert corr_val < 0, f"Synthetic data should have negative correlation, got {corr_val}"
    
    # Step 2: Statistical Analysis (Stage 6)
    # This should run the Shapiro-Wilk test on residuals and select the correlation method
    analysis_results = stage_06_statistical_analysis()
    
    assert analysis_results is not None, "Statistical analysis stage failed"
    
    # Check for expected keys in the result
    required_keys = ['correlation_method', 'coefficient', 'p_value', 'is_significant', 'normality_p_value']
    for key in required_keys:
        assert key in analysis_results, f"Missing key '{key}' in analysis results"
    
    # Verify the specific acceptance criteria for synthetic data
    assert analysis_results['is_significant'] is True, \
        f"Expected is_significant=True for synthetic negative correlation, got {analysis_results['is_significant']}"
    
    assert analysis_results['coefficient'] < 0, \
        f"Expected negative correlation coefficient, got {analysis_results['coefficient']}"
    
    assert analysis_results['p_value'] < 0.05, \
        f"Expected p-value < 0.05, got {analysis_results['p_value']}"
    
    # Step 3: Visualization (Stage 7)
    viz_path = stage_07_visualization()
    
    assert viz_path is not None, "Visualization stage failed to return a path"
    assert viz_path.exists(), f"Visualization file does not exist at {viz_path}"
    
    # Verify the file is not empty
    assert viz_path.stat().st_size > 0, "Visualization file is empty"

def test_analysis_results_json_content(synthetic_data: Path):
    """
    Directly verify the content of analysis_results.json after running the pipeline.
    """
    # Re-run the pipeline to ensure files are fresh (or rely on the previous test's side effects)
    # Since the previous test runs the full pipeline, we can just check the file here.
    # However, to be safe and idempotent, we run the analysis stage again.
    stage_05_merge_and_validate()
    stage_06_statistical_analysis()
    
    results_file = DATA_PROCESSED_DIR / "analysis_results.json"
    assert results_file.exists(), "analysis_results.json was not created"
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    # Verify structure
    assert 'is_significant' in results
    assert 'coefficient' in results
    assert 'p_value' in results
    
    # Verify logic for synthetic data
    assert results['is_significant'] == True
    assert results['coefficient'] < 0.0
    assert results['p_value'] < 0.05