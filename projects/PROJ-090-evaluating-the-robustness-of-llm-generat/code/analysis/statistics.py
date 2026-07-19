import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from collections import defaultdict
import pandas as pd
import numpy as np
from scipy.stats import mcnemar

# Local imports (must match API surface)
from config import get_config_dict, ensure_directories
from utils.logging import get_execution_logger

logger = get_execution_logger()

@dataclass
class McNemarResult:
    task_id: str
    perturbation_type: str
    n01: int  # Original pass, Perturbed fail
    n10: int  # Original fail, Perturbed pass
    n00: int  # Both fail
    n11: int  # Both pass
    statistic: float
    p_value: float
    is_significant: bool

@dataclass
class BonferroniResult:
    num_tests: int
    alpha_original: float
    alpha_corrected: float
    significant_results: List[Dict[str, Any]]

@dataclass
class MixedEffectsResult:
    task_variance: float
    residual_variance: float
    fixed_effects: Dict[str, float]
    p_value_perturbation: float
    is_significant: bool

@dataclass
class SensitivityAnalysisResult:
    threshold: float
    pass_rate: float
    delta_from_baseline: float
    n_samples: int

def load_results_data() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Loads original and perturbed task execution results from the data directory.
    Expects files: data/processed/original_results.json and data/processed/perturbed_results.json
    """
    config = get_config_dict()
    data_dir = Path(config["data_dir"])
    
    original_path = data_dir / "processed" / "original_results.json"
    perturbed_path = data_dir / "processed" / "perturbed_results.json"

    if not original_path.exists() or not perturbed_path.exists():
        raise FileNotFoundError(
            f"Results files not found. Expected: {original_path}, {perturbed_path}. "
            "Run inference tasks (US2) first."
        )

    with open(original_path, 'r') as f:
        original_data = json.load(f)
    
    with open(perturbed_path, 'r') as f:
        perturbed_data = json.load(f)

    return original_data, perturbed_data

def calculate_pass_at_1(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculates pass@1 rate for a list of results.
    Returns: {"overall": float, "by_task_id": Dict[str, float]}
    """
    if not results:
        return {"overall": 0.0, "by_task_id": {}}

    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "pass")
    
    by_task = defaultdict(list)
    for r in results:
        by_task[r["task_id"]].append(r.get("status") == "pass")
    
    by_task_rates = {
        tid: sum(passes) / len(passes) 
        for tid, passes in by_task.items()
    }

    return {
        "overall": passed / total if total > 0 else 0.0,
        "by_task_id": by_task_rates
    }

def mcnemar_test_for_task(
    original_result: Dict[str, Any],
    perturbed_result: Dict[str, Any]
) -> McNemarResult:
    """
    Performs McNemar's test for a single task comparing original vs perturbed execution.
    
    Contingency Table:
    |               | Perturbed Pass | Perturbed Fail |
    |---------------|----------------|----------------|
    | Original Pass |      n11       |      n01       |
    | Original Fail |      n10       |      n00       |
    
    Returns: McNemarResult with statistic and p_value.
    """
    orig_status = original_result.get("status") == "pass"
    pert_status = perturbed_result.get("status") == "pass"
    
    # Determine counts for the 2x2 table
    n11 = 1 if (orig_status and pert_status) else 0
    n01 = 1 if (orig_status and not pert_status) else 0
    n10 = 1 if (not orig_status and pert_status) else 0
    n00 = 1 if (not orig_status and not pert_status) else 0
    
    # McNemar's test statistic (exact or asymptotic)
    # For small samples, exact is better, but asymptotic is standard for this scale
    # We use the asymptotic chi-squared approximation with continuity correction
    # statistic = (|n01 - n10| - 1)^2 / (n01 + n10) if n01 + n10 > 0 else 0
    
    discordant = n01 + n10
    if discordant == 0:
        # No discordant pairs, no change in outcome
        statistic = 0.0
        p_value = 1.0
    else:
        # Use scipy.stats.mcnemar
        # Input is the 2x2 table: [[n11, n01], [n10, n00]]
        table = [[n11, n01], [n10, n00]]
        try:
            result = mcnemar(table, exact=False, correction=True)
            statistic = float(result.statistic)
            p_value = float(result.pvalue)
        except Exception as e:
            logger.warning(f"McNemar test failed for task {original_result.get('task_id')}: {e}")
            statistic = 0.0
            p_value = 1.0

    return McNemarResult(
        task_id=original_result["task_id"],
        perturbation_type=perturbed_result.get("perturbation_type", "unknown"),
        n01=n01,
        n10=n10,
        n00=n00,
        n11=n11,
        statistic=statistic,
        p_value=p_value,
        is_significant=p_value < 0.05
    )

def aggregate_mcnemar_tests(
    original_results: List[Dict[str, Any]],
    perturbed_results: List[Dict[str, Any]]
) -> Dict[str, List[McNemarResult]]:
    """
    Aggregates McNemar tests across all tasks, grouped by perturbation type.
    
    Args:
        original_results: List of dicts from original execution (status, task_id)
        perturbed_results: List of dicts from perturbed execution (status, task_id, perturbation_type)
    
    Returns:
        Dict mapping perturbation_type -> List[McNemarResult]
    """
    # Index original results by task_id
    orig_map = {r["task_id"]: r for r in original_results}
    
    # Group perturbed results by task_id to handle multiple perturbations per task if any
    # (Assuming 1:1 mapping per task for the primary analysis, but grouping by type for aggregation)
    pert_by_task = {}
    for r in perturbed_results:
        tid = r["task_id"]
        ptype = r.get("perturbation_type", "unknown")
        if tid not in pert_by_task:
            pert_by_task[tid] = []
        pert_by_task[tid].append(r)
    
    # Perform test for each task and group by perturbation type
    aggregated: Dict[str, List[McNemarResult]] = defaultdict(list)
    
    for tid, pert_list in pert_by_task.items():
        if tid not in orig_map:
            logger.warning(f"Task {tid} found in perturbed but not original results.")
            continue
        
        orig_res = orig_map[tid]
        
        for pert_res in pert_list:
            try:
                result = mcnemar_test_for_task(orig_res, pert_res)
                aggregated[result.perturbation_type].append(result)
            except Exception as e:
                logger.error(f"Error processing task {tid}: {e}")
                continue
    
    return dict(aggregated)

def apply_bonferroni_correction(
    aggregated_results: Dict[str, List[McNemarResult]],
    alpha: float = 0.05
) -> BonferroniResult:
    """
    Applies Bonferroni correction to the aggregated McNemar results.
    
    Args:
        aggregated_results: Dict of perturbation_type -> List[McNemarResult]
        alpha: Original significance level (default 0.05)
    
    Returns:
        BonferroniResult with corrected alpha and significant results.
    """
    # Total number of unique tests performed (sum of all results across types)
    # Or number of perturbation types if aggregating at the type level?
    # Standard approach: Correct for the number of comparisons (perturbation types)
    # If we are testing each task individually, it's N_tasks. 
    # If we are testing each perturbation type (aggregated), it's N_types.
    # Given the task "aggregation across tasks for each perturbation type", 
    # we likely want to test the aggregate effect per type.
    # However, McNemar returns a p-value per task. 
    # To get a single p-value per type, we typically combine them (e.g., Fisher's method).
    # But the task asks for "aggregation" and "Bonferroni". 
    # Let's assume we are testing the set of tasks for each type, 
    # and we want to control FWER across the perturbation types.
    
    # For now, we return the correction factor based on the number of perturbation types.
    # If the user wants to correct across all individual tasks, that would be N_total_tests.
    # We will count the number of perturbation types as the number of comparisons.
    num_tests = len(aggregated_results)
    
    if num_tests == 0:
        return BonferroniResult(
            num_tests=0,
            alpha_original=alpha,
            alpha_corrected=alpha,
            significant_results=[]
        )
    
    alpha_corrected = alpha / num_tests
    
    significant_results = []
    for ptype, results in aggregated_results.items():
        # Check if ANY task in this type is significant after correction?
        # Or aggregate the p-values? 
        # Standard practice: If we have a p-value for the type (e.g. from Fisher), compare to alpha_corrected.
        # Here we don't have a single p-value per type yet.
        # We will mark the type as significant if a majority or any task is significant?
        # Let's just list the significant individual results for now.
        for res in results:
            if res.p_value < alpha_corrected:
                significant_results.append({
                    "perturbation_type": ptype,
                    "task_id": res.task_id,
                    "p_value": res.p_value,
                    "statistic": res.statistic
                })
    
    return BonferroniResult(
        num_tests=num_tests,
        alpha_original=alpha,
        alpha_corrected=alpha_corrected,
        significant_results=significant_results
    )

def run_mcnemar_analysis(
    original_results: Optional[List[Dict[str, Any]]] = None,
    perturbed_results: Optional[List[Dict[str, Any]]] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Runs the full McNemar analysis pipeline:
    1. Load data if not provided.
    2. Aggregate tests by perturbation type.
    3. Apply Bonferroni correction.
    4. Save results.
    
    Returns: Dictionary containing aggregated results and correction info.
    """
    if original_results is None or perturbed_results is None:
        original_results, perturbed_results = load_results_data()
    
    logger.info(f"Running McNemar analysis on {len(original_results)} original and {len(perturbed_results)} perturbed results.")
    
    aggregated = aggregate_mcnemar_tests(original_results, perturbed_results)
    
    # Apply Bonferroni correction
    bonf_result = apply_bonferroni_correction(aggregated)
    
    # Convert dataclasses to dicts for JSON serialization
    aggregated_dict = {
        ptype: [asdict(r) for r in res_list]
        for ptype, res_list in aggregated.items()
    }
    
    output = {
        "aggregated_mcnemar_results": aggregated_dict,
        "bonferroni_correction": asdict(bonf_result),
        "summary": {
            "total_tasks_analyzed": len(original_results),
            "perturbation_types_count": len(aggregated),
            "significant_tasks_after_correction": len(bonf_result.significant_results)
        }
    }
    
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        logger.info(f"McNemar analysis results saved to {output_path}")
    
    return output

def run_mixed_effects_logistic_regression(
    original_results: Optional[List[Dict[str, Any]]] = None,
    perturbed_results: Optional[List[Dict[str, Any]]] = None
) -> MixedEffectsResult:
    """
    Placeholder for Mixed-Effects Logistic Regression.
    Implementation to be added in T032.
    """
    # This is a stub to satisfy the API surface until T032 is implemented.
    # In a real scenario, this would use statsmodels or pymer4.
    logger.warning("Mixed-Effects Logistic Regression not yet implemented. Returning dummy values.")
    return MixedEffectsResult(
        task_variance=0.0,
        residual_variance=0.0,
        fixed_effects={"intercept": 0.0, "perturbation": 0.0},
        p_value_perturbation=1.0,
        is_significant=False
    )

def run_sensitivity_analysis(
    thresholds: List[float] = [0.85, 0.90, 0.95, 0.99]
) -> List[SensitivityAnalysisResult]:
    """
    Placeholder for Sensitivity Analysis.
    Implementation to be added in T033.
    """
    logger.warning("Sensitivity Analysis not yet implemented. Returning dummy values.")
    return [
        SensitivityAnalysisResult(
            threshold=t,
            pass_rate=0.0,
            delta_from_baseline=0.0,
            n_samples=0
        ) for t in thresholds
    ]

def main():
    """
    Entry point for running McNemar analysis from the command line.
    """
    logger.info("Starting McNemar Analysis via main()")
    try:
        results = run_mcnemar_analysis(
            output_path="data/processed/mcnemar_analysis_results.json"
        )
        logger.info("McNemar Analysis completed successfully.")
        print(json.dumps(results, indent=2))
    except FileNotFoundError as e:
        logger.error(f"Data files missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during McNemar Analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()