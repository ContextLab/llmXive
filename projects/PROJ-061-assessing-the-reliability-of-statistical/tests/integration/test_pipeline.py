"""
Integration test for User Story 2: Bias calculation with induced violations.

This test verifies that the pipeline correctly handles induced violations
(heavy-tailed noise, AR(1) autocorrelation, effect size heterogeneity)
and calculates the resulting bias between theoretical and empirical power.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import RANDOM_SEED, BOOTSTRAP_ITERATIONS
from code.main import load_dataset_info, get_data_for_dataset, clean_data_listwise
from code.power_theory import theoretical_power_ttest
from code.power_empirical import bootstrap_power_estimate
from code.perturbations import (
    inject_heavy_tailed_noise,
    inject_ar1_autocorrelation,
    inject_effect_size_heterogeneity,
    verify_ar1_coefficient
)
from code.utils import save_json, setup_logging

# Setup logging for the test
logger = setup_logging("test_pipeline_integration", level=logging.INFO)


@pytest.fixture
def sample_dataset():
    """
    Create a small, deterministic sample dataset for integration testing.
    Simulates a real dataset with N=100, two groups, continuous outcome.
    """
    np.random.seed(RANDOM_SEED)
    n = 100
    # Generate two groups with a known effect size (Cohen's d ~ 0.5)
    group0 = np.random.normal(loc=0, scale=1, size=n // 2)
    group1 = np.random.normal(loc=0.5, scale=1, size=n - n // 2)
    
    # Combine into a structured format
    data = {
        "outcome": np.concatenate([group0, group1]),
        "group": np.array([0] * (n // 2) + [1] * (n - n // 2)),
        "dataset_id": "test_integration_dataset"
    }
    return data


@pytest.fixture
def violation_configs():
    """
    Return a list of violation configurations to test.
    """
    return [
        {
            "type": "heavy_tailed",
            "params": {"df": 3, "scale": 1.0},
            "description": "Heavy-tailed noise (t-distribution, df=3)"
        },
        {
            "type": "ar1",
            "params": {"rho": 0.5},
            "description": "AR(1) autocorrelation (rho=0.5)"
        },
        {
            "type": "heterogeneity",
            "params": {"mixing_ratio": 0.2, "separation": 1.5},
            "description": "Effect size heterogeneity (mix=0.2, sep=1.5)"
        }
    ]


def test_bias_calculation_with_violations(
    sample_dataset: Dict[str, np.ndarray],
    violation_configs: List[Dict[str, Any]]
):
    """
    Integration test:
    1. Load/clean data.
    2. For each violation type:
       a. Inject violation.
       b. Calculate theoretical power.
       c. Calculate empirical power (bootstrap).
       d. Compute bias.
       e. Verify bias is non-zero (indicating the violation had an effect).
    3. Save results to data/results/violations_test.json.
    """
    # Ensure output directory exists
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = results_dir / "violations_test.json"

    # 1. Clean data (listwise deletion)
    clean_data = clean_data_listwise(sample_dataset)
    assert clean_data["outcome"].size > 0, "Data cleaning resulted in empty dataset"
    
    groups = np.unique(clean_data["group"])
    assert len(groups) == 2, "Dataset must have exactly 2 groups for t-test"

    results = []

    # Calculate baseline theoretical power (no violation)
    # Using Cohen's d approximation based on sample data
    mean0 = np.mean(clean_data["outcome"][clean_data["group"] == 0])
    mean1 = np.mean(clean_data["outcome"][clean_data["group"] == 1])
    std_pooled = np.sqrt(
        (np.var(clean_data["outcome"][clean_data["group"] == 0]) + 
         np.var(clean_data["outcome"][clean_data["group"] == 1])) / 2
    )
    cohens_d = (mean1 - mean0) / std_pooled if std_pooled > 0 else 0
    
    n0 = np.sum(clean_data["group"] == 0)
    n1 = np.sum(clean_data["group"] == 1)
    n_total = n0 + n1

    baseline_theoretical = theoretical_power_ttest(
        n1=n1, n2=n0, effect_size=cohens_d, alpha=0.05
    )
    
    logger.info(f"Baseline Theoretical Power: {baseline_theoretical:.4f}")

    # 2. Iterate over violation configurations
    for config in violation_configs:
        v_type = config["type"]
        v_params = config["params"]
        v_desc = config["description"]

        logger.info(f"Testing violation: {v_desc}")

        # Clone data to avoid modifying original
        current_data = {k: v.copy() for k, v in clean_data.items()}
        outcome = current_data["outcome"]
        group = current_data["group"]

        # Inject violation
        if v_type == "heavy_tailed":
            perturbed_outcome, _ = inject_heavy_tailed_noise(
                outcome, df=v_params["df"], scale=v_params["scale"]
            )
        elif v_type == "ar1":
            # Check if data is time-ordered (for this test, we assume it is)
            perturbed_outcome, _ = inject_ar1_autocorrelation(
                outcome, rho=v_params["rho"]
            )
            # Verify achieved magnitude
            achieved_rho, _ = verify_ar1_coefficient(perturbed_outcome)
            logger.info(f"  Achieved AR(1) coefficient: {achieved_rho:.4f} (target: {v_params['rho']})")
        elif v_type == "heterogeneity":
            perturbed_outcome, _ = inject_effect_size_heterogeneity(
                outcome, group, 
                mixing_ratio=v_params["mixing_ratio"], 
                separation=v_params["separation"]
            )
        else:
            raise ValueError(f"Unknown violation type: {v_type}")

        current_data["outcome"] = perturbed_outcome

        # Recalculate effect size for theoretical power on perturbed data
        mean0_p = np.mean(perturbed_outcome[group == 0])
        mean1_p = np.mean(perturbed_outcome[group == 1])
        std_p_pooled = np.sqrt(
            (np.var(perturbed_outcome[group == 0]) + 
             np.var(perturbed_outcome[group == 1])) / 2
        )
        cohens_d_p = (mean1_p - mean0_p) / std_p_pooled if std_p_pooled > 0 else 0

        theoretical_power = theoretical_power_ttest(
            n1=n1, n2=n0, effect_size=cohens_d_p, alpha=0.05
        )

        # Calculate empirical power via bootstrap
        empirical_power = bootstrap_power_estimate(
            outcome=perturbed_outcome,
            group=group,
            n_iterations=BOOTSTRAP_ITERATIONS,
            effect_size_target=cohens_d_p, # Using observed effect size as target for comparison
            alpha=0.05
        )

        # Calculate bias
        bias = empirical_power - theoretical_power
        absolute_bias = abs(bias)

        logger.info(f"  Theoretical: {theoretical_power:.4f}, Empirical: {empirical_power:.4f}, Bias: {bias:.4f}")

        result_entry = {
            "violation_type": v_type,
            "description": v_desc,
            "parameters": v_params,
            "theoretical_power": float(theoretical_power),
            "empirical_power": float(empirical_power),
            "bias": float(bias),
            "absolute_bias": float(absolute_bias)
        }

        # Add verification info for AR1
        if v_type == "ar1":
            result_entry["achieved_rho"] = float(achieved_rho)

        results.append(result_entry)

        # Assert that bias is detected (non-zero) for the test
        # Note: In real data, bias might be small, but for integration test with synthetic perturbations,
        # we expect a measurable difference. We assert bias is not exactly 0.0 to ensure logic ran.
        assert bias != 0.0, f"Bias should not be zero for {v_type} violation in this test context."

    # 3. Save results
    output_data = {
        "test_id": "T020_integration",
        "dataset_id": sample_dataset["dataset_id"],
        "baseline_theoretical_power": float(baseline_theoretical),
        "violation_results": results
    }

    save_json(output_data, output_path)
    logger.info(f"Results saved to {output_path}")

    # Verify file exists and is valid JSON
    assert output_path.exists(), "Output file was not created."
    with open(output_path, 'r') as f:
        loaded = json.load(f)
        assert "violation_results" in loaded
        assert len(loaded["violation_results"]) == len(violation_configs)

    logger.info("Integration test passed.")