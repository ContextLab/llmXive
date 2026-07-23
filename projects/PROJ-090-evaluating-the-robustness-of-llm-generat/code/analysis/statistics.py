import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict

import pandas as pd
import numpy as np
from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import Binomial

# Ensure project root is in path for imports if run as script
if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from config import get_config_dict

@dataclass
class McNemarResult:
    task_id: str
    contingency: List[List[int]]
    statistic: float
    pvalue: float
    perturbation_type: str

@dataclass
class BonferroniResult:
    perturbation_type: str
    raw_pvalue: float
    corrected_alpha: float
    significant: bool

@dataclass
class MixedEffectsResult:
    variance_component: float
    std_dev_task: float
    p_values: Dict[str, float]
    n_obs: int
    n_groups: int

@dataclass
class SensitivityAnalysisResult:
    threshold: float
    pass_rate: float
    delta_from_baseline: float

def load_results_data() -> pd.DataFrame:
    """
    Loads execution results from data/processed/execution_results.json.
    Returns a DataFrame with columns: task_id, perturbation_type, original_pass, perturbed_pass, threshold.
    """
    results_path = Path("data/processed/execution_results.json")
    if not results_path.exists():
        raise FileNotFoundError(f"Execution results not found at {results_path}. "
                                "Please ensure Phase 4 (Inference/Execution) is complete.")
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    # Ensure boolean/int conversion for calculations
    if 'original_pass' in df.columns:
        df['original_pass'] = df['original_pass'].astype(int)
    if 'perturbed_pass' in df.columns:
        df['perturbed_pass'] = df['perturbed_pass'].astype(int)
    if 'threshold' not in df.columns:
        # If threshold isn't stored in execution results, we might need to join with perturbation data
        # For this task, we assume the perturbation data includes the threshold used or we simulate
        # based on the raw candidate pool if available. However, per spec, we need to re-evaluate
        # the pass rate based on the threshold.
        # Since execution results are binary (pass/fail) based on a fixed threshold (0.95),
        # we need to reconstruct the "what if" scenarios.
        # We will load the perturbation candidates to get the raw scores.
        pass
    
    return df

def load_perturbation_candidates() -> pd.DataFrame:
    """
    Loads raw perturbation candidates to access raw similarity scores.
    Expected file: data/processed/perturbation_candidates_raw.json
    """
    candidates_path = Path("data/processed/perturbation_candidates_raw.json")
    if not candidates_path.exists():
        raise FileNotFoundError(f"Raw perturbation candidates not found at {candidates_path}. "
                                "Please ensure T017 is complete.")
    
    with open(candidates_path, 'r') as f:
        data = json.load(f)
    
    # Flatten if necessary, assuming list of dicts
    df = pd.DataFrame(data)
    # Ensure numeric types
    if 'raw_score' in df.columns:
        df['raw_score'] = pd.to_numeric(df['raw_score'], errors='coerce')
    return df

def calculate_pass_at_1(df: pd.DataFrame, perturbation_type: str, threshold: float) -> float:
    """
    Calculates pass@1 for a specific perturbation type and threshold.
    Logic:
    1. Filter candidates by perturbation_type.
    2. Filter candidates by raw_score >= threshold (simulating the semantic validation step).
    3. Join with execution results to get pass/fail.
    4. Calculate pass rate.
    """
    candidates = df
    # Filter by type
    type_mask = candidates['perturbation_type'] == perturbation_type
    # Filter by threshold
    score_mask = candidates['raw_score'] >= threshold
    
    valid_candidates = candidates[type_mask & score_mask]
    
    if len(valid_candidates) == 0:
        return 0.0
    
    # We need to map these candidates to their execution results.
    # The execution results file should have a mapping of task_id + perturbation_id to result.
    # Since we are simulating the threshold effect, we assume the execution result is available
    # for the generated perturbation.
    
    # Load execution results to merge
    exec_path = Path("data/processed/execution_results.json")
    if not exec_path.exists():
        # If execution results are missing, we cannot calculate real pass rates.
        # We must fail loudly as per constraints.
        raise FileNotFoundError(f"Cannot calculate pass rate: {exec_path} missing.")
    
    with open(exec_path, 'r') as f:
        exec_data = json.load(f)
    
    exec_df = pd.DataFrame(exec_data)
    
    # Merge on task_id and perturbation_id (assuming unique ID for perturbation)
    # If 'perturbation_id' is not in exec_df, we might need to join on task_id only if 1:1 mapping exists.
    # Assuming the execution results contain the perturbation details.
    if 'perturbation_id' in valid_candidates.columns and 'perturbation_id' in exec_df.columns:
        merged = pd.merge(valid_candidates, exec_df, on=['task_id', 'perturbation_id'], how='inner')
    elif 'task_id' in valid_candidates.columns and 'task_id' in exec_df.columns:
        # Fallback to task_id if 1:1 relationship is guaranteed
        merged = pd.merge(valid_candidates, exec_df, on='task_id', how='inner')
    else:
        raise ValueError("Cannot merge candidates and execution results: missing join keys.")
    
    if len(merged) == 0:
        return 0.0
    
    # Calculate pass rate (assuming 'perturbed_pass' is 1 for pass, 0 for fail)
    pass_rate = merged['perturbed_pass'].mean()
    return pass_rate

def run_sensitivity_analysis() -> List[SensitivityAnalysisResult]:
    """
    Implements sensitivity analysis on semantic thresholds.
    Thresholds: {0.85, 0.90, 0.95, 0.99}
    Calculates pass_rate and delta_from_baseline (relative to 0.95).
    """
    thresholds = [0.85, 0.90, 0.95, 0.99]
    results = []
    
    # Load data
    candidates_df = load_perturbation_candidates()
    
    # Get unique perturbation types
    perturbation_types = candidates_df['perturbation_type'].unique()
    
    baseline_threshold = 0.95
    baseline_rates = {}
    
    # First pass: Calculate baseline rates (0.95) for all types
    for p_type in perturbation_types:
        rate = calculate_pass_at_1(candidates_df, p_type, baseline_threshold)
        baseline_rates[p_type] = rate
    
    # Second pass: Calculate for all thresholds
    for threshold in thresholds:
        for p_type in perturbation_types:
            rate = calculate_pass_at_1(candidates_df, p_type, threshold)
            baseline = baseline_rates.get(p_type, 0.0)
            delta = rate - baseline
            
            results.append(SensitivityAnalysisResult(
                threshold=threshold,
                pass_rate=rate,
                delta_from_baseline=delta
            ))
    
    return results

def save_sensitivity_report(results: List[SensitivityAnalysisResult], output_path: str):
    """
    Saves the sensitivity analysis results to a CSV file.
    """
    data = [asdict(r) for r in results]
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logging.info(f"Sensitivity report saved to {output_path}")

def main():
    """
    Main entry point for sensitivity analysis.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        results = run_sensitivity_analysis()
        output_file = "data/processed/sensitivity_report.csv"
        save_sensitivity_report(results, output_file)
        
        # Verification
        df = pd.read_csv(output_file)
        assert len(df) == 4, f"Expected 4 rows, got {len(df)}"
        assert set(df['threshold']) == {0.85, 0.90, 0.95, 0.99}, "Thresholds mismatch"
        
        logging.info("Sensitivity analysis completed successfully.")
        print(f"Report generated: {output_file}")
        
    except FileNotFoundError as e:
        logging.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error during analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
