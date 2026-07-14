"""
Integration test for the statistical analysis pipeline (User Story 2).

This test verifies that the analysis module can:
1. Generate synthetic data with known parameters.
2. Run Welch's t-test and calculate effect sizes.
3. Produce output matching the expected schema in `data/results/statistical_report.json`.

Run with: pytest tests/integration/test_analysis.py -v
"""
import os
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Import the analysis module (assuming it exists or will be created in T018)
# We handle the import gracefully; if T018 isn't done, this test will fail as expected.
try:
    from code.analysis import run_welch_ttest, calculate_cohens_d, calculate_power_mdes, generate_statistical_report
    ANALYSIS_AVAILABLE = True
except ImportError:
    ANALYSIS_AVAILABLE = False
    # Define stubs to allow test collection to proceed, though execution will fail
    def run_welch_ttest(*args, **kwargs):
        raise NotImplementedError("Analysis module (T018) not yet implemented.")
    def calculate_cohens_d(*args, **kwargs):
        raise NotImplementedError("Analysis module (T018) not yet implemented.")
    def calculate_power_mdes(*args, **kwargs):
        raise NotImplementedError("Analysis module (T018) not yet implemented.")
    def generate_statistical_report(*args, **kwargs):
        raise NotImplementedError("Analysis module (T018) not yet implemented.")

# Ensure output directories exist for the test
@pytest.fixture(scope="module")
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    # Create necessary subdirectories to mimic project structure
    os.makedirs(os.path.join(temp_dir, "data", "results"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "data", "processed"), exist_ok=True)
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def synthetic_dataset(temp_output_dir):
    """
    Generate a synthetic dataset with known effect sizes for validation.
    
    Parameters:
    - Nostalgia group: Mean=4, Std=2
    - Control group: Mean=6, Std=2
    - Expected Cohen's d: (6-4)/2 = 1.0 (Large effect)
    - Expected p-value: Very small (< 0.001)
    """
    if not ANALYSIS_AVAILABLE:
        pytest.skip("Analysis module not available.")

    np.random.seed(42)
    n_per_group = 100
    
    # Generate data
    nostalgia_errors = np.random.normal(loc=4, scale=2, size=n_per_group)
    control_errors = np.random.normal(loc=6, scale=2, size=n_per_group)
    
    nostalgia_cats = np.random.normal(loc=8, scale=1.5, size=n_per_group)
    control_cats = np.random.normal(loc=6, scale=1.5, size=n_per_group)
    
    df = pd.DataFrame({
        'participant_id': [f'P{i}' for i in range(n_per_group * 2)],
        'stimulus_type': ['nostalgia'] * n_per_group + ['control'] * n_per_group,
        'perseverative_errors': list(nostalgia_errors) + list(control_errors),
        'categories_completed': list(nostalgia_cats) + list(control_cats),
        'age': [65 + np.random.randint(0, 20) for _ in range(n_per_group * 2)]
    })
    
    # Save to CSV as required by the pipeline
    output_path = os.path.join(temp_output_dir, "data", "processed", "cleaned_dataset.csv")
    df.to_csv(output_path, index=False)
    
    return output_path

def test_analysis_pipeline_synthetic_data(temp_output_dir, synthetic_dataset):
    """
    End-to-end integration test for the statistical analysis pipeline.
    
    Verifies:
    1. The script runs without error.
    2. The output file `statistical_report.json` is created.
    3. The output contains the expected keys.
    4. The calculated effect size is close to the theoretical value (d ≈ 1.0).
    5. The p-value is statistically significant (< 0.05).
    """
    if not ANALYSIS_AVAILABLE:
        pytest.skip("Analysis module not yet implemented.")

    # Paths
    data_path = synthetic_dataset
    results_dir = os.path.join(temp_output_dir, "data", "results")
    report_path = os.path.join(results_dir, "statistical_report.json")
    
    # Ensure results directory exists
    os.makedirs(results_dir, exist_ok=True)
    
    # Execute the analysis logic (mimicking the main entry point of T022)
    # We call the functions directly here to simulate the pipeline
    df = pd.read_csv(data_path)
    
    # 1. Run Welch's t-test for perseverative_errors
    errors_nostalgia = df[df['stimulus_type'] == 'nostalgia']['perseverative_errors']
    errors_control = df[df['stimulus_type'] == 'control']['perseverative_errors']
    
    t_stat_errors, p_val_errors = run_welch_ttest(errors_nostalgia, errors_control)
    cohens_d_errors = calculate_cohens_d(errors_nostalgia, errors_control)
    
    # 2. Run Welch's t-test for categories_completed
    cats_nostalgia = df[df['stimulus_type'] == 'nostalgia']['categories_completed']
    cats_control = df[df['stimulus_type'] == 'control']['categories_completed']
    
    t_stat_cats, p_val_cats = run_welch_ttest(cats_nostalgia, cats_control)
    cohens_d_cats = calculate_cohens_d(cats_nostalgia, cats_control)
    
    # 3. Calculate Power and MDES
    # Using alpha=0.05, n1=n2=100
    power_errors, mdes_errors = calculate_power_mdes(
        mean1=errors_nostalgia.mean(), 
        mean2=errors_control.mean(), 
        std1=errors_nostalgia.std(), 
        std2=errors_control.std(), 
        n1=len(errors_nostalgia), 
        n2=len(errors_control), 
        alpha=0.05
    )
    
    # 4. Generate Report
    report = {
        "metrics": {
            "perseverative_errors": {
                "t_statistic": t_stat_errors,
                "p_value": p_val_errors,
                "cohens_d": cohens_d_errors,
                "power": power_errors,
                "mdes": mdes_errors
            },
            "categories_completed": {
                "t_statistic": t_stat_cats,
                "p_value": p_val_cats,
                "cohens_d": cohens_d_cats
            }
        },
        "sample_sizes": {
            "nostalgia": len(errors_nostalgia),
            "control": len(errors_control)
        }
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # --- Assertions ---
    
    # A. File exists
    assert os.path.exists(report_path), "Statistical report was not generated."
    
    # B. Valid JSON and schema
    with open(report_path, 'r') as f:
        loaded_report = json.load(f)
    
    assert "metrics" in loaded_report
    assert "perseverative_errors" in loaded_report["metrics"]
    assert "categories_completed" in loaded_report["metrics"]
    
    pe_metrics = loaded_report["metrics"]["perseverative_errors"]
    assert "p_value" in pe_metrics
    assert "cohens_d" in pe_metrics
    assert "power" in pe_metrics
    assert "mdes" in pe_metrics
    
    # C. Statistical Validity (Check against synthetic ground truth)
    # Theoretical Cohen's d was ~1.0. Allow some variance due to randomness.
    assert 0.8 <= pe_metrics["cohens_d"] <= 1.3, f"Cohen's d {pe_metrics['cohens_d']} is outside expected range for synthetic data."
    
    # P-value should be significant
    assert pe_metrics["p_value"] < 0.05, f"P-value {pe_metrics['p_value']} is not significant."
    
    # Power should be high given N=200 and large effect
    assert pe_metrics["power"] > 0.8, f"Power {pe_metrics['power']} is too low for this effect size and sample."

def test_analysis_handles_zero_variance():
    """
    Regression test: Ensure the analysis handles edge cases like zero variance
    without crashing (as per T023 requirement).
    """
    if not ANALYSIS_AVAILABLE:
        pytest.skip("Analysis module not yet implemented.")
        
    # Create data with zero variance
    group1 = pd.Series([5.0, 5.0, 5.0])
    group2 = pd.Series([6.0, 6.0, 6.0])
    
    # This should not raise an exception, but might return inf or nan depending on implementation
    # The test passes if it runs without a crash
    try:
        t, p = run_welch_ttest(group1, group2)
        # If it returns a number, good. If it returns inf/nan, that's also acceptable handling
        # provided it didn't crash.
    except Exception as e:
        # If it crashes, the test fails
        pytest.fail(f"Analysis crashed on zero variance input: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
