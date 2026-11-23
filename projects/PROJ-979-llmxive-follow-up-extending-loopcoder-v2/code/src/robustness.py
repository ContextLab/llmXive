import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import math

import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm

logger = logging.getLogger(__name__)

def load_full_splits(splits_path: Path) -> Dict[str, List[Dict]]:
    """Load full splits JSON."""
    with open(splits_path, 'r') as f:
        return json.load(f)

def load_strata_log(strata_log_path: Path) -> List[Dict]:
    """Load strata log JSON."""
    with open(strata_log_path, 'r') as f:
        return json.load(f)

def load_entropy_results(entropy_path: Path) -> List[Dict]:
    """Load entropy results CSV."""
    results = []
    with open(entropy_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'task_id': row['task_id'],
                'entropy': float(row['entropy'])
            })
    return results

def load_convergence_results(convergence_path: Path) -> List[Dict]:
    """Load convergence results CSV."""
    results = []
    with open(convergence_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'task_id': row['task_id'],
                'k': int(row['k']),
                'is_correct': row['is_correct'] == 'True',
                'first_correct_step': int(row['first_correct_step']) if row['first_correct_step'] != '' else None,
                'censored': row['censored'] == 'True',
                'time_to_event': int(row['time_to_event'])
            })
    return results

def get_stratum_for_task(task_id: str, full_splits: Dict[str, List[Dict]], strata_log: List[Dict]) -> Optional[str]:
    """Determine the stratum for a given task_id."""
    # Reconstruct strata mapping if not directly stored in splits
    # Assuming strata_log contains: [{"strata_name": "...", "task_ids": [...]}, ...]
    for stratum_entry in strata_log:
        if task_id in stratum_entry.get('task_ids', []):
            return stratum_entry['strata_name']
    return None

def compute_per_stratum_correlation(entropy_data: List[Dict], convergence_data: List[Dict], strata_log: List[Dict]) -> Dict[str, Dict[str, float]]:
    """Compute Spearman correlation per stratum."""
    import scipy.stats as stats

    results = {}
    merged = {}
    for e in entropy_data:
        merged[e['task_id']] = {'entropy': e['entropy']}
    for c in convergence_data:
        if c['task_id'] in merged:
            merged[c['task_id']]['first_correct_step'] = c['first_correct_step']

    for stratum_entry in strata_log:
        stratum_name = stratum_entry['strata_name']
        task_ids = stratum_entry.get('task_ids', [])
        stratum_data = [merged[tid] for tid in task_ids if tid in merged and 'first_correct_step' in merged[tid]]

        if len(stratum_data) < 3:
            results[stratum_name] = {'rho': float('nan'), 'p_value': float('nan'), 'n': len(stratum_data)}
            continue

        entropies = [d['entropy'] for d in stratum_data]
        steps = [d['first_correct_step'] for d in stratum_data]

        rho, p_val = stats.spearmanr(entropies, steps)
        results[stratum_name] = {'rho': float(rho), 'p_value': float(p_val), 'n': len(stratum_data)}

    return results

def merge_convergence_results(core_path: Path, sensitivity_path: Path) -> List[Dict]:
    """Merge core and sensitivity convergence results."""
    merged = {}
    for path in [core_path, sensitivity_path]:
        if not path.exists():
            continue
        with open(path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                task_id = row['task_id']
                k = int(row['k'])
                if task_id not in merged:
                    merged[task_id] = []
                merged[task_id].append({
                    'k': k,
                    'output': row['output'],
                    'is_correct': row['is_correct'] == 'True',
                    'first_correct_step': int(row['first_correct_step']) if row['first_correct_step'] else None,
                    'censored': row['censored'] == 'True',
                    'time_to_event': int(row['time_to_event'])
                })
    return [{'task_id': tid, 'runs': runs} for tid, runs in merged.items()]

def run_sensitivity_sweep(merged_convergence: List[Dict], thresholds: List[int]) -> Dict[str, Any]:
    """Run sensitivity sweep on merged convergence data."""
    results = {}
    for threshold in thresholds:
        # Filter data where time_to_event <= threshold or censored
        valid_count = 0
        total = len(merged_convergence)
        for item in merged_convergence:
            runs = item['runs']
            # Find if any run is correct within threshold
            correct_within = any(r['k'] <= threshold and r['is_correct'] for r in runs)
            if correct_within:
                valid_count += 1
        accuracy = valid_count / total if total > 0 else 0.0
        results[f'k_{threshold}'] = {'accuracy': accuracy, 'n': total}
    return results

def run_mixed_effects_sensitivity_analysis(
    entropy_path: Path,
    convergence_path: Path,
    full_splits_path: Path,
    strata_log_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis on the hierarchical mixed-effects model
    by varying the random effects structure.
    
    Models compared:
    1. (1 | strata) - Random intercept only
    2. (1 + entropy | strata) - Random intercept and slope for entropy
    
    Returns comparison of AIC/BIC scores.
    """
    # Load data
    entropy_data = load_entropy_results(entropy_path)
    convergence_data = load_convergence_results(convergence_path)
    full_splits = load_full_splits(full_splits_path)
    strata_log = load_strata_log(strata_log_path)

    # Merge data
    merged_df = []
    for e in entropy_data:
        task_id = e['task_id']
        entropy_val = e['entropy']
        
        # Find stratum
        stratum = get_stratum_for_task(task_id, full_splits, strata_log)
        if stratum is None:
            continue
        
        # Find convergence step (use first_correct_step or time_to_event)
        conv_entry = next((c for c in convergence_data if c['task_id'] == task_id), None)
        if conv_entry is None:
            continue
        
        # Use time_to_event as the response variable
        response = conv_entry['time_to_event']
        
        merged_df.append({
            'task_id': task_id,
            'entropy': entropy_val,
            'response': response,
            'strata': stratum
        })

    if len(merged_df) == 0:
        logger.error("No data available for mixed effects analysis.")
        return {"error": "No data available"}

    df = pd.DataFrame(merged_df)

    # Model 1: Random intercept only (1 | strata)
    logger.info("Fitting Model 1: (1 | strata)")
    try:
        model1 = mixedlm("response ~ entropy", df, groups=df["strata"])
        result1 = model1.fit()
        aic1 = result1.aic
        bic1 = result1.bic
        logger.info(f"Model 1 AIC: {aic1:.2f}, BIC: {bic1:.2f}")
    except Exception as e:
        logger.warning(f"Model 1 failed: {e}")
        aic1, bic1 = None, None

    # Model 2: Random intercept and slope (1 + entropy | strata)
    logger.info("Fitting Model 2: (1 + entropy | strata)")
    try:
        # Note: statsmodels MixedLM syntax for random slopes
        # re_formula="1" is default, "1+entropy" for random slope
        model2 = mixedlm("response ~ entropy", df, groups=df["strata"], re_formula="1+entropy")
        result2 = model2.fit()
        aic2 = result2.aic
        bic2 = result2.bic
        logger.info(f"Model 2 AIC: {aic2:.2f}, BIC: {bic2:.2f}")
    except Exception as e:
        logger.warning(f"Model 2 failed: {e}")
        aic2, bic2 = None, None

    # Prepare comparison
    comparison = {
        "model_1_intercept_only": {
            "formula": "response ~ entropy, (1 | strata)",
            "aic": aic1,
            "bic": bic1,
            "converged": result1.converged if aic1 is not None else False
        },
        "model_2_intercept_slope": {
            "formula": "response ~ entropy, (1 + entropy | strata)",
            "aic": aic2,
            "bic": bic2,
            "converged": result2.converged if aic2 is not None else False
        },
        "comparison": {
            "aic_diff": (aic2 - aic1) if (aic1 is not None and aic2 is not None) else None,
            "bic_diff": (bic2 - bic1) if (bic1 is not None and bic2 is not None) else None,
            "preferred_model": None
        }
    }

    # Determine preferred model
    if aic1 is not None and aic2 is not None:
        if aic2 < aic1:
            comparison["comparison"]["preferred_model"] = "model_2_intercept_slope"
        else:
            comparison["comparison"]["preferred_model"] = "model_1_intercept_only"
    elif aic1 is not None:
        comparison["comparison"]["preferred_model"] = "model_1_intercept_only"
    elif aic2 is not None:
        comparison["comparison"]["preferred_model"] = "model_2_intercept_slope"

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(comparison, f, indent=2)

    logger.info(f"Sensitivity analysis results saved to {output_path}")
    return comparison

def main():
    """Main entry point for mixed effects sensitivity analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Mixed Effects Sensitivity Analysis")
    parser.add_argument("--entropy", type=str, required=True, help="Path to entropy_results.csv")
    parser.add_argument("--convergence", type=str, required=True, help="Path to convergence_results_core_full.csv")
    parser.add_argument("--splits", type=str, required=True, help="Path to full_splits.json")
    parser.add_argument("--strata", type=str, required=True, help="Path to strata_log.json")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")
    
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    run_mixed_effects_sensitivity_analysis(
        entropy_path=Path(args.entropy),
        convergence_path=Path(args.convergence),
        full_splits_path=Path(args.splits),
        strata_log_path=Path(args.strata),
        output_path=Path(args.output)
    )

if __name__ == "__main__":
    main()
