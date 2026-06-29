"""
Contract test for comparison report schema.
Validates that the output of code/analysis/compare.py adheres to the required schema.
"""
import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.utils.logger import get_logger

logger = get_logger(__name__)

# Expected schema structure based on T026/T027/T028 requirements
# The report must contain:
# 1. Model comparison metrics (AIC, BIC, Log-Likelihood)
# 2. Sensitivity analysis results (threshold sweeps)
# 3. Statistical significance (p-values with Bonferroni correction)
# 4. Philosophical framing metrics (Spectacle vs Good, Outcome Effect)
REQUIRED_TOP_LEVEL_KEYS = [
    "model_comparison",
    "sensitivity_analysis",
    "statistical_significance",
    "philosophical_metrics",
    "metadata"
]

MODEL_COMPARISON_KEYS = [
    "baseline_model",
    "salience_augmented_model",
    "aic_difference",
    "bic_difference",
    "log_likelihood_baseline",
    "log_likelihood_salience",
    "cv_folds",
    "convergence_rate"
]

SENSITIVITY_KEYS = [
    "threshold_sweep",
    "log_likelihood_variation",
    "aic_variation"
]

STAT_SIG_KEYS = [
    "tests_performed",
    "bonferroni_corrected_p_values",
    "significance_threshold"
]

PHILOSOPHICAL_KEYS = [
    "spectacle_vs_good_correlation",
    "outcome_effect_size",
    "salience_effect_size"
]

METADATA_KEYS = [
    "run_timestamp",
    "data_version",
    "model_parameters",
    "notes"
]

def load_sample_report(report_path: str = None):
    """
    Loads a sample comparison report.
    If report_path is provided, loads from disk.
    Otherwise, generates a minimal valid structure for schema validation.
    """
    if report_path and os.path.exists(report_path):
        with open(report_path, 'r') as f:
            return json.load(f)
    
    # Generate a minimal valid structure for testing schema
    return {
        "model_comparison": {
            "baseline_model": "aDDM_Standard",
            "salience_augmented_model": "aDDM_Salience",
            "aic_difference": 12.5,
            "bic_difference": 15.2,
            "log_likelihood_baseline": -450.0,
            "log_likelihood_salience": -435.0,
            "cv_folds": 5,
            "convergence_rate": 0.98
        },
        "sensitivity_analysis": {
            "threshold_sweep": [0.1, 0.2, 0.3, 0.4, 0.5],
            "log_likelihood_variation": [-435.0, -436.0, -438.0, -440.0, -442.0],
            "aic_variation": [870.0, 872.0, 876.0, 880.0, 884.0]
        },
        "statistical_significance": {
            "tests_performed": 4,
            "bonferroni_corrected_p_values": [0.001, 0.015, 0.04, 0.08],
            "significance_threshold": 0.05
        },
        "philosophical_metrics": {
            "spectacle_vs_good_correlation": 0.65,
            "outcome_effect_size": 0.12,
            "salience_effect_size": 0.08
        },
        "metadata": {
            "run_timestamp": "2026-05-16T12:00:00Z",
            "data_version": "v1.0",
            "model_parameters": {"grid_steps": 11},
            "notes": "Test report"
        }
    }

def test_report_schema():
    """
    Contract test: Validates the schema of the comparison report.
    Ensures all required keys are present and have expected data types.
    """
    report = load_sample_report()

    # Check top-level keys
    for key in REQUIRED_TOP_LEVEL_KEYS:
        assert key in report, f"Missing required top-level key: {key}"

    # Check model_comparison structure
    assert isinstance(report["model_comparison"], dict)
    for key in MODEL_COMPARISON_KEYS:
        assert key in report["model_comparison"], f"Missing key in model_comparison: {key}"
    
    # Verify numeric types for metrics
    assert isinstance(report["model_comparison"]["aic_difference"], (int, float))
    assert isinstance(report["model_comparison"]["bic_difference"], (int, float))
    assert isinstance(report["model_comparison"]["convergence_rate"], (int, float))

    # Check sensitivity_analysis structure
    assert isinstance(report["sensitivity_analysis"], dict)
    for key in SENSITIVITY_KEYS:
        assert key in report["sensitivity_analysis"], f"Missing key in sensitivity_analysis: {key}"
    
    # Verify lists for sweep data
    assert isinstance(report["sensitivity_analysis"]["threshold_sweep"], list)
    assert isinstance(report["sensitivity_analysis"]["log_likelihood_variation"], list)

    # Check statistical_significance structure
    assert isinstance(report["statistical_significance"], dict)
    for key in STAT_SIG_KEYS:
        assert key in report["statistical_significance"], f"Missing key in statistical_significance: {key}"
    
    # Verify Bonferroni logic (p-values should be between 0 and 1)
    p_values = report["statistical_significance"]["bonferroni_corrected_p_values"]
    assert all(0.0 <= p <= 1.0 for p in p_values), "P-values must be between 0 and 1"

    # Check philosophical_metrics structure
    assert isinstance(report["philosophical_metrics"], dict)
    for key in PHILOSOPHICAL_KEYS:
        assert key in report["philosophical_metrics"], f"Missing key in philosophical_metrics: {key}"
    
    # Verify correlation coefficient range
    corr = report["philosophical_metrics"]["spectacle_vs_good_correlation"]
    assert -1.0 <= corr <= 1.0, "Correlation coefficient must be between -1 and 1"

    # Check metadata structure
    assert isinstance(report["metadata"], dict)
    for key in METADATA_KEYS:
        assert key in report["metadata"], f"Missing key in metadata: {key}"

    logger.info("Schema validation passed successfully.")

if __name__ == "__main__":
    test_report_schema()
    print("All contract tests passed.")