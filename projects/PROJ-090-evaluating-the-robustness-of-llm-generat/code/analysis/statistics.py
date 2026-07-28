"""
Statistical analysis module for LLM code robustness evaluation.
Implements pass@1, McNemar's test, Bonferroni correction, Mixed-Effects Logistic Regression,
and sensitivity analysis.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm
from scipy.stats import chi2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class McNemarResult:
    """Result of McNemar's test."""
    statistic: float
    p_value: float
    contingency_table: Dict[str, int]
    significant: bool

@dataclass
class BonferroniResult:
    """Result of Bonferroni correction."""
    corrected_alpha: float
    original_alpha: float
    num_comparisons: int

@dataclass
class MixedEffectsResult:
    """Result of Mixed-Effects Logistic Regression."""
    variance_component_task: float
    std_dev_task: float
    fixed_effects: Dict[str, float]
    p_values: Dict[str, float]
    n_obs: int
    n_groups: int
    formula: str
    converged: bool

@dataclass
class SensitivityAnalysisResult:
    """Result of sensitivity analysis."""
    threshold: float
    pass_rate: float
    delta_from_baseline: float
    sample_count: int

def load_results_data(results_path: str) -> pd.DataFrame:
    """Load execution results from JSON file."""
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")

    with open(path, 'r') as f:
        data = json.load(f)

    if not data:
        raise ValueError("Results file is empty")

    df = pd.DataFrame(data)
    required_cols = ['task_id', 'perturbation_type', 'pass_status']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df

def load_perturbation_candidates(candidates_path: str) -> pd.DataFrame:
    """Load perturbation candidates from JSON file."""
    path = Path(candidates_path)
    if not path.exists():
        raise FileNotFoundError(f"Candidates file not found: {candidates_path}")

    with open(path, 'r') as f:
        data = json.load(f)

    if not data:
        raise ValueError("Candidates file is empty")

    df = pd.DataFrame(data)
    return df

def calculate_pass_at_1(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate pass@1 rate for each perturbation type.
    pass@1 = (number of passed tasks) / (total number of tasks)
    """
    if 'pass_status' not in df.columns or 'perturbation_type' not in df.columns:
        raise ValueError("DataFrame must contain 'pass_status' and 'perturbation_type' columns")

    pass_rates = {}
    for p_type in df['perturbation_type'].unique():
        subset = df[df['perturbation_type'] == p_type]
        total = len(subset)
        passed = subset['pass_status'].sum()
        rate = passed / total if total > 0 else 0.0
        pass_rates[p_type] = rate

    return pass_rates

def run_mcnemar_test(original_df: pd.DataFrame, perturbed_df: pd.DataFrame) -> McNemarResult:
    """
    Run McNemar's test to compare original vs perturbed performance.
    Returns statistic, p-value, and contingency table.
    """
    # Merge on task_id to get paired results
    merged = pd.merge(
        original_df[['task_id', 'pass_status']],
        perturbed_df[['task_id', 'pass_status']],
        on='task_id',
        suffixes=('_original', '_perturbed')
    )

    if len(merged) == 0:
        raise ValueError("No matching tasks between original and perturbed sets")

    # Build contingency table
    # a = both pass, b = original pass/perturbed fail, c = original fail/perturbed pass, d = both fail
    a = ((merged['pass_status_original'] == 1) & (merged['pass_status_perturbed'] == 1)).sum()
    b = ((merged['pass_status_original'] == 1) & (merged['pass_status_perturbed'] == 0)).sum()
    c = ((merged['pass_status_original'] == 0) & (merged['pass_status_perturbed'] == 1)).sum()
    d = ((merged['pass_status_original'] == 0) & (merged['pass_status_perturbed'] == 0)).sum()

    contingency = {
        'both_pass': int(a),
        'orig_pass_pert_fail': int(b),
        'orig_fail_pert_pass': int(c),
        'both_fail': int(d)
    }

    # McNemar's test statistic: (|b - c| - 1)^2 / (b + c) with continuity correction
    if (b + c) == 0:
        statistic = 0.0
        p_value = 1.0
    else:
        statistic = ((abs(b - c) - 1) ** 2) / (b + c)
        p_value = 1 - chi2.cdf(statistic, df=1)

    significant = p_value < 0.05

    return McNemarResult(
        statistic=statistic,
        p_value=p_value,
        contingency_table=contingency,
        significant=significant
    )

def apply_bonferroni_correction(num_comparisons: int, alpha: float = 0.05) -> BonferroniResult:
    """
    Apply Bonferroni correction for multiple comparisons.
    """
    corrected_alpha = alpha / num_comparisons
    return BonferroniResult(
        corrected_alpha=corrected_alpha,
        original_alpha=alpha,
        num_comparisons=num_comparisons
    )

def run_mixed_effects_logistic_regression(
    results_path: str,
    output_path: str
) -> MixedEffectsResult:
    """
    Run Mixed-Effects Logistic Regression with 'task' as random effect.
    Model: pass_status ~ perturbation_type + (1 | task_id)
    """
    logger.info(f"Loading execution results from {results_path}")
    df = load_results_data(results_path)

    # Ensure perturbation_type is categorical
    df['perturbation_type'] = df['perturbation_type'].astype('category')

    # Check for sufficient data
    n_groups = df['task_id'].nunique()
    n_obs = len(df)

    if n_groups < 2:
        raise ValueError(f"Insufficient groups for mixed-effects model: {n_groups} groups found. Need at least 2.")

    if n_obs < 10:
        raise ValueError(f"Insufficient observations for mixed-effects model: {n_obs} observations found. Need at least 10.")

    logger.info(f"Running mixed-effects logistic regression on {n_obs} observations across {n_groups} tasks")

    # Prepare formula: pass_status ~ perturbation_type + (1 | task_id)
    # Use C() to ensure perturbation_type is treated as categorical
    formula = "pass_status ~ C(perturbation_type) + (1 | task_id)"

    try:
        # Fit mixed-effects model
        # statsmodels mixedlm uses GLMM for logistic regression
        model = mixedlm(
            formula,
            df,
            groups=df['task_id'],
            family=sm.families.Binomial()
        )
        result = model.fit()

        # Extract variance components
        # The random effects variance is stored in 'var_comp'
        variance_components = result.cov_re
        if variance_components is not None and len(variance_components) > 0:
            # For a simple random intercept model, there's one variance component
            variance_task = float(variance_components.iloc[0, 0])
            std_dev_task = np.sqrt(variance_task)
        else:
            variance_task = 0.0
            std_dev_task = 0.0

        # Extract fixed effects
        fixed_effects = {}
        p_values = {}
        for param, coef in zip(result.params.index, result.params):
            if param != 'Intercept':  # Skip intercept for fixed effects dict
                fixed_effects[param] = float(coef)
                # Get p-value if available
                try:
                    p_values[param] = float(result.pvalues[param])
                except (KeyError, IndexError):
                    p_values[param] = None

        # Check convergence
        converged = result.converged if hasattr(result, 'converged') else True

        mixed_result = MixedEffectsResult(
            variance_component_task=variance_task,
            std_dev_task=std_dev_task,
            fixed_effects=fixed_effects,
            p_values=p_values,
            n_obs=n_obs,
            n_groups=n_groups,
            formula=formula,
            converged=converged
        )

    except Exception as e:
        logger.error(f"Failed to fit mixed-effects model: {e}")
        # Return a result indicating failure but with structure
        mixed_result = MixedEffectsResult(
            variance_component_task=0.0,
            std_dev_task=0.0,
            fixed_effects={},
            p_values={},
            n_obs=n_obs,
            n_groups=n_groups,
            formula=formula,
            converged=False
        )

    # Save results to JSON
    output_data = asdict(mixed_result)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Mixed-effects results saved to {output_path}")
    logger.info(f"Variance component for task: {mixed_result.variance_component_task}")
    logger.info(f"Standard deviation for task: {mixed_result.std_dev_task}")

    return mixed_result

def run_sensitivity_analysis(
    raw_candidates_path: str,
    execution_results_path: str,
    thresholds: List[float] = [0.85, 0.90, 0.95, 0.99],
    output_path: str = "data/processed/sensitivity_report.csv"
) -> List[SensitivityAnalysisResult]:
    """
    Run sensitivity analysis on semantic thresholds.
    Re-score candidates against each threshold, calculate pass@1 for subset.
    """
    logger.info(f"Loading raw candidates from {raw_candidates_path}")
    candidates_df = load_perturbation_candidates(raw_candidates_path)

    logger.info(f"Loading execution results from {execution_results_path}")
    results_df = load_results_data(execution_results_path)

    results_list = []
    baseline_pass_rate = None

    # Calculate baseline (using 0.95 threshold as reference)
    baseline_candidates = candidates_df[candidates_df['raw_score'] > 0.95]
    if len(baseline_candidates) > 0:
        baseline_task_ids = set(baseline_candidates['task_id'].unique())
        baseline_results = results_df[results_df['task_id'].isin(baseline_task_ids)]
        if len(baseline_results) > 0:
            baseline_pass_rate = baseline_results['pass_status'].mean()

    for threshold in thresholds:
        logger.info(f"Processing threshold: {threshold}")

        # Filter candidates by threshold
        filtered_candidates = candidates_df[candidates_df['raw_score'] > threshold]
        sample_count = len(filtered_candidates)

        if sample_count == 0:
            results_list.append(SensitivityAnalysisResult(
                threshold=threshold,
                pass_rate=0.0,
                delta_from_baseline=0.0 if baseline_pass_rate is None else -baseline_pass_rate,
                sample_count=0
            ))
            continue

        # Get corresponding execution results
        filtered_task_ids = set(filtered_candidates['task_id'].unique())
        filtered_results = results_df[results_df['task_id'].isin(filtered_task_ids)]

        if len(filtered_results) == 0:
            pass_rate = 0.0
        else:
            pass_rate = filtered_results['pass_status'].mean()

        delta = pass_rate - baseline_pass_rate if baseline_pass_rate is not None else 0.0

        results_list.append(SensitivityAnalysisResult(
            threshold=threshold,
            pass_rate=pass_rate,
            delta_from_baseline=delta,
            sample_count=sample_count
        ))

    # Save to CSV
    output_df = pd.DataFrame([asdict(r) for r in results_list])
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)

    logger.info(f"Sensitivity analysis results saved to {output_path}")
    return results_list

def save_sensitivity_report(results: List[SensitivityAnalysisResult], output_path: str) -> None:
    """Save sensitivity analysis results to CSV."""
    output_df = pd.DataFrame([asdict(r) for r in results])
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)

def main():
    """Main entry point for statistics module."""
    import argparse

    parser = argparse.ArgumentParser(description="Statistical analysis for LLM robustness")
    parser.add_argument("--command", choices=["mixed-effects", "sensitivity", "pass-at-1"], required=True)
    parser.add_argument("--results-path", type=str, default="data/processed/inference_logs.json")
    parser.add_argument("--candidates-path", type=str, default="data/processed/perturbation_candidates_raw.json")
    parser.add_argument("--output-path", type=str, default="data/processed/mixed_effects_results.json")
    parser.add_argument("--sensitivity-output", type=str, default="data/processed/sensitivity_report.csv")

    args = parser.parse_args()

    if args.command == "mixed-effects":
        logger.info("Running mixed-effects logistic regression...")
        result = run_mixed_effects_logistic_regression(args.results_path, args.output_path)
        print(f"Mixed-effects variance component: {result.variance_component_task}")

    elif args.command == "sensitivity":
        logger.info("Running sensitivity analysis...")
        results = run_sensitivity_analysis(
            args.candidates_path,
            args.results_path,
            output_path=args.sensitivity_output
        )
        print(f"Sensitivity analysis complete. Results saved to {args.sensitivity_output}")

    elif args.command == "pass-at-1":
        logger.info("Calculating pass@1 rates...")
        df = load_results_data(args.results_path)
        pass_rates = calculate_pass_at_1(df)
        print("Pass@1 rates by perturbation type:")
        for p_type, rate in pass_rates.items():
            print(f"  {p_type}: {rate:.4f}")

if __name__ == "__main__":
    main()
