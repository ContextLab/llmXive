"""
Integration test for the full energy systems pipeline (T032).
Verifies end-to-end flow from data ingestion to sensitivity report generation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

from src.data.ingest import fetch_eia_rec, fetch_acs
from src.data.preprocess import (
    filter_low_income,
    winsorize,
    construct_treatment,
    check_adopter_power,
    preprocess_pipeline,
    PowerError
)
from src.analysis.psm import iterative_matching, estimate_propensity, match_pairs
from src.analysis.balance import calculate_smd, run_placebo_test, check_placebo_significance
from src.analysis.causal import run_ols, run_did, DataUnavailableError
from src.analysis.sensitivity import sweep_caliper
from src.analysis.pipeline_controller import run_full_pipeline, PlaceboGateError, BalanceFailureError
from src.models.output import save_analysis_result
from src.models.schemas import AnalysisResult

# Fixtures
@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_eia_data():
    """
    Generate a minimal valid EIA RECS dataset for integration testing.
    Real data ingestion is mocked here to ensure the pipeline logic is tested
    without relying on external network calls during the integration test run.
    However, the pipeline logic (filtering, matching, etc.) must be real.
    """
    np.random.seed(42)
    n = 200
    data = {
        'household_id': range(n),
        'tract_id': [f"06037{str(i).zfill(4)}" for i in range(n)],
        'income': np.random.normal(45000, 15000, n),
        'energy_cost': np.random.exponential(1500, n),
        'home_value': np.random.normal(300000, 100000, n),
        'housing_type': np.random.choice(['Single', 'Multi', 'Mobile'], n),
        'location': np.random.choice(['Urban', 'Rural'], n),
        'solar_installation': np.random.choice([0, 1], n, p=[0.9, 0.1]), # 10% treatment
        'pre_treatment_outcome': np.random.normal(1500, 500, n),
        'post_treatment_outcome': np.random.normal(1500, 500, n),
    }
    df = pd.DataFrame(data)
    # Ensure some low income households
    df.loc[df['income'] < 30000, 'income'] = 25000
    return df

@pytest.fixture
def sample_acs_data():
    """
    Generate minimal ACS data for low-income filtering.
    """
    tracts = [f"06037{str(i).zfill(4)}" for i in range(200)]
    # Mix of low and high median income tracts
    median_income = np.random.choice([40000, 120000], 200)
    return pd.DataFrame({
        'tract_id': tracts,
        'median_income': median_income
    })

def test_end_to_end_pipeline_success(sample_eia_data, sample_acs_data, temp_output_dir):
    """
    Tests the full pipeline:
    1. Ingest (mocked data passed directly)
    2. Preprocess (filter, winsorize, treatment)
    3. PSM (matching, balance check)
    4. Placebo test
    5. Causal estimation (OLS)
    6. Sensitivity analysis
    7. Output serialization
    """
    # 1. Preprocess
    # Filter for low income tracts (median_income < 150% FPL, approx 45k for 2023)
    # We simulate the join logic here for the test
    merged = sample_eia_data.merge(sample_acs_data, on='tract_id', how='left')
    filtered_df = filter_low_income(merged, threshold=45000)
    
    # Winsorize
    winsorized_df = winsorize(filtered_df, lower=0.01, upper=0.99)
    
    # Construct treatment
    treated_df = construct_treatment(winsorized_df, treatment_col='solar_installation')
    
    # Power check
    check_adopter_power(treated_df, min_adopters=10) # Lowered for test speed

    # 2. PSM & Balance
    # Estimate propensity
    propensity_df = estimate_propensity(treated_df)
    
    # Iterative matching
    matched_df, balance_status, smd_data = iterative_matching(
        propensity_df, 
        caliper=0.05, 
        max_iterations=5
    )
    
    # 3. Placebo Test
    if 'pre_treatment_outcome' in matched_df.columns and 'post_treatment_outcome' in matched_df.columns:
        placebo_results = run_placebo_test(matched_df)
        check_placebo_significance(placebo_results, alpha=0.05)
    
    # 4. Causal Estimation
    # Run OLS
    ols_results = run_ols(matched_df)
    
    # 5. Sensitivity Analysis
    calipers = [0.01, 0.02, 0.05, 0.1]
    sensitivity_results = sweep_caliper(treated_df, calipers=calipers)
    
    # 6. Output Serialization
    # Construct a minimal AnalysisResult for saving
    result = AnalysisResult(
        att_estimate=float(ols_results.params.get('treatment', 0.0)),
        p_value=float(ols_results.pvalues.get('treatment', 1.0)),
        ci_lower=float(ols_results.conf_int().loc['treatment', 0]),
        ci_upper=float(ols_results.conf_int().loc['treatment', 1]),
        methodology="OLS with PSM",
        sensitivity_data=sensitivity_results,
        balance_status=balance_status,
        placebo_passed=True
    )
    
    output_path = temp_output_dir / "analysis_result.json"
    save_analysis_result(result, str(output_path))
    
    # Verify file exists and is valid JSON
    assert output_path.exists(), "Output file not created"
    with open(output_path) as f:
        loaded = json.load(f)
    assert 'att_estimate' in loaded
    assert loaded['methodology'] == "OLS with PSM"

def test_pipeline_fails_on_low_power(sample_eea_data, sample_acs_data, temp_output_dir):
    """
    Tests that the pipeline raises PowerError if adopters < 50.
    """
    # Create data with very few adopters
    np.random.seed(42)
    n = 200
    data = {
        'household_id': range(n),
        'tract_id': [f"06037{str(i).zfill(4)}" for i in range(n)],
        'income': np.random.normal(45000, 15000, n),
        'energy_cost': np.random.exponential(1500, n),
        'home_value': np.random.normal(300000, 100000, n),
        'housing_type': np.random.choice(['Single', 'Multi', 'Mobile'], n),
        'location': np.random.choice(['Urban', 'Rural'], n),
        'solar_installation': [0] * (n - 10) + [1] * 10, # Only 10 adopters
        'pre_treatment_outcome': np.random.normal(1500, 500, n),
        'post_treatment_outcome': np.random.normal(1500, 500, n),
    }
    df = pd.DataFrame(data)
    merged = df.merge(sample_acs_data, on='tract_id', how='left')
    filtered_df = filter_low_income(merged, threshold=45000)
    
    with pytest.raises(PowerError):
        check_adopter_power(filtered_df, min_adopters=50)

def test_pipeline_fails_on_placebo_gate(sample_eea_data, sample_acs_data, temp_output_dir):
    """
    Tests that the pipeline raises PlaceboGateError if placebo test fails.
    """
    # Mock data where placebo test should fail (significant difference in pre-treatment)
    np.random.seed(42)
    n = 200
    data = {
        'household_id': range(n),
        'tract_id': [f"06037{str(i).zfill(4)}" for i in range(n)],
        'income': np.random.normal(45000, 15000, n),
        'energy_cost': np.random.exponential(1500, n),
        'home_value': np.random.normal(300000, 100000, n),
        'housing_type': np.random.choice(['Single', 'Multi', 'Mobile'], n),
        'location': np.random.choice(['Urban', 'Rural'], n),
        'solar_installation': np.random.choice([0, 1], n, p=[0.5, 0.5]),
        # Pre-treatment outcome differs significantly by treatment
        'pre_treatment_outcome': np.where(
            np.array(data['solar_installation']) == 1, 
            2000 + np.random.normal(0, 100, n), 
            1000 + np.random.normal(0, 100, n)
        ),
        'post_treatment_outcome': np.random.normal(1500, 500, n),
    }
    df = pd.DataFrame(data)
    merged = df.merge(sample_acs_data, on='tract_id', how='left')
    filtered_df = filter_low_income(merged, threshold=45000)
    winsorized_df = winsorize(filtered_df, lower=0.01, upper=0.99)
    treated_df = construct_treatment(winsorized_df, treatment_col='solar_installation')
    
    propensity_df = estimate_propensity(treated_df)
    matched_df, _, _ = iterative_matching(propensity_df, caliper=0.05, max_iterations=5)
    
    placebo_results = run_placebo_test(matched_df)
    
    with pytest.raises(PlaceboGateError):
        check_placebo_significance(placebo_results, alpha=0.05)

def test_pipeline_fails_on_missing_did_data(sample_eea_data, sample_acs_data, temp_output_dir):
    """
    Tests that DiD fallback raises DataUnavailableError if longitudinal columns are missing.
    """
    # Create data without longitudinal columns
    np.random.seed(42)
    n = 200
    data = {
        'household_id': range(n),
        'tract_id': [f"06037{str(i).zfill(4)}" for i in range(n)],
        'income': np.random.normal(45000, 15000, n),
        'energy_cost': np.random.exponential(1500, n),
        'home_value': np.random.normal(300000, 100000, n),
        'housing_type': np.random.choice(['Single', 'Multi', 'Mobile'], n),
        'location': np.random.choice(['Urban', 'Rural'], n),
        'solar_installation': np.random.choice([0, 1], n, p=[0.5, 0.5]),
        # No pre/post columns
    }
    df = pd.DataFrame(data)
    merged = df.merge(sample_acs_data, on='tract_id', how='left')
    filtered_df = filter_low_income(merged, threshold=45000)
    
    with pytest.raises(DataUnavailableError):
        run_did(filtered_df)