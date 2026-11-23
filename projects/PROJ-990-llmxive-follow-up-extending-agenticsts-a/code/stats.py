import os
import json
import logging
import hashlib
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import ttest_rel, permutation_test, chi2_contingency

from config import load_config_from_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('llmXive.stats')

def load_simulation_results(policy: str) -> pd.DataFrame:
    """Load simulation results for a policy."""
    config = load_config_from_file('config.json')
    path = Path(config['data']['processed']) / f'simulation_logs_{policy}.json'
    if not path.exists():
        logger.warning(f"Simulation file not found: {path}")
        return pd.DataFrame()
    with open(path, 'r') as f:
        data = json.load(f)
    if 'simulations' not in data:
        logger.error(f"Invalid simulation file structure: {path}")
        return pd.DataFrame()
    return pd.DataFrame(data['simulations'])

def load_divergence_report() -> dict:
    """Load divergence report."""
    config = load_config_from_file('config.json')
    path = Path(config['data']['processed']) / 'divergence_report.json'
    if not path.exists():
        logger.warning(f"Divergence report not found: {path}")
        return {"is_divergent": False}
    with open(path, 'r') as f:
        return json.load(f)

def compute_aggregates(df: pd.DataFrame) -> dict:
    """Compute aggregate statistics from simulation results.
    
    Handles the 'dynamic' policy by separating 'dynamic' and 'fallback' modes
    if the 'mode' column exists in the dataframe.
    
    Args:
        df: DataFrame containing simulation results with columns:
            - 'outcome': 'win' or 'loss'
            - 'tokens_used': integer token count
            - 'mode' (optional): 'dynamic' or 'fallback' for dynamic policy runs
    
    Returns:
        Dictionary with keys:
            - 'win_rate': float (0.0 to 1.0)
            - 'avg_tokens': float
            - 'std_tokens': float
            - 'n_samples': int
            - 'mode_breakdown' (optional): dict of mode -> stats if modes detected
    """
    if df.empty:
        return {
            "win_rate": 0.0,
            "avg_tokens": 0.0,
            "std_tokens": 0.0,
            "n_samples": 0,
            "mode_breakdown": None
        }
    
    # Check if we need to separate by mode (for dynamic policy)
    if 'mode' in df.columns and df['mode'].nunique() > 1:
        mode_breakdown = {}
        for mode, group in df.groupby('mode'):
          mode_breakdown[mode] = {
              "win_rate": float(group['outcome'].apply(lambda x: 1 if x == 'win' else 0).mean()),
              "avg_tokens": float(group['tokens_used'].mean()),
              "std_tokens": float(group['tokens_used'].std()),
              "n_samples": int(len(group))
          }
        
        # Overall stats still computed on full set
        return {
            "win_rate": float(df['outcome'].apply(lambda x: 1 if x == 'win' else 0).mean()),
            "avg_tokens": float(df['tokens_used'].mean()),
            "std_tokens": float(df['tokens_used'].std()),
            "n_samples": int(len(df)),
            "mode_breakdown": mode_breakdown
        }
    else:
        return {
            "win_rate": float(df['outcome'].apply(lambda x: 1 if x == 'win' else 0).mean()),
            "avg_tokens": float(df['tokens_used'].mean()),
            "std_tokens": float(df['tokens_used'].std()),
            "n_samples": int(len(df)),
            "mode_breakdown": None
        }

def detect_divergence():
    """Detect if trajectories diverged between Dynamic and Static runs.
    
    Computes SHA256 hash of final game state for each trajectory pair.
    Final game state is defined as JSON object with 'win', 'loss', 'final_score'.
    """
    config = load_config_from_file('config.json')
    dynamic_path = Path(config['data']['processed']) / 'simulation_logs_dynamic.json'
    static_path = Path(config['data']['processed']) / 'simulation_logs_static.json'
    out_path = Path(config['data']['processed']) / 'divergence_report.json'
    
    if not dynamic_path.exists() or not static_path.exists():
        logger.error("Missing simulation logs for divergence check")
        report = {"is_divergent": False, "divergent_ids": [], "error": "Missing files"}
        with open(out_path, 'w') as f:
            json.dump(report, f, indent=2)
        return
    
    with open(dynamic_path, 'r') as f:
        dynamic_data = json.load(f)
    with open(static_path, 'r') as f:
        static_data = json.load(f)
    
    dynamic_sims = {s['trajectory_id']: s for s in dynamic_data.get('simulations', [])}
    static_sims = {s['trajectory_id']: s for s in static_data.get('simulations', [])}
    
    divergent_ids = []
    
    for tid in dynamic_sims:
        if tid not in static_sims:
            continue
        
        dyn_state = dynamic_sims[tid].get('final_state', {})
        stat_state = static_sims[tid].get('final_state', {})
        
        # Canonical serialization: sort keys, remove whitespace
        dyn_str = json.dumps(dyn_state, sort_keys=True, separators=(',', ':'))
        stat_str = json.dumps(stat_state, sort_keys=True, separators=(',', ':'))
        
        dyn_hash = hashlib.sha256(dyn_str.encode()).hexdigest()
        stat_hash = hashlib.sha256(stat_str.encode()).hexdigest()
        
        if dyn_hash != stat_hash:
            divergent_ids.append(tid)
    
    is_divergent = len(divergent_ids) > 0
    report = {
        "is_divergent": is_divergent,
        "divergent_ids": divergent_ids,
        "total_pairs": len(dynamic_sims),
        "divergent_count": len(divergent_ids)
    }
    
    with open(out_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Divergence report saved: {out_path}")

def run_permutation_test():
    """Run permutation test for unpaired data."""
    config = load_config_from_file('config.json')
    out_path = Path(config['data']['processed']) / 'statistical_results.json'
    
    dynamic_df = load_simulation_results('dynamic')
    static_df = load_simulation_results('static')
    
    if dynamic_df.empty or static_df.empty:
        logger.warning("Cannot run permutation test: missing data")
        return
    
    # Extract win/loss as binary
    dyn_win = (dynamic_df['outcome'] == 'win').astype(int).values
    stat_win = (static_df['outcome'] == 'win').astype(int).values
    
    # Permutation test on difference in proportions
    combined = np.concatenate([dyn_win, stat_win])
    n1, n2 = len(dyn_win), len(stat_win)
    observed_diff = np.mean(dyn_win) - np.mean(stat_win)
    
    # Run permutation test
    result = permutation_test(
        (dyn_win, stat_win),
        lambda x, y: np.mean(x) - np.mean(y),
        vectorized=False,
        permutation_type='two-samples',
        alternative='two-sided'
    )
    
    p_value = result.pvalue
    
    report = {
        "test_type": "Permutation Test",
        "p_value": float(p_value),
        "observed_diff": float(observed_diff),
        "significant": p_value < 0.05
    }
    
    results = {}
    if out_path.exists():
        with open(out_path, 'r') as f:
            results = json.load(f)
    results.update(report)
    
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Permutation test result saved: {out_path}")

def run_mcnemar_test():
    """Run McNemar's test for paired data."""
    config = load_config_from_file('config.json')
    out_path = Path(config['data']['processed']) / 'statistical_results.json'
    
    dynamic_path = Path(config['data']['processed']) / 'simulation_logs_dynamic.json'
    static_path = Path(config['data']['processed']) / 'simulation_logs_static.json'
    
    if not dynamic_path.exists() or not static_path.exists():
        logger.error("Missing simulation logs for McNemar test")
        return
    
    with open(dynamic_path, 'r') as f:
        dynamic_data = json.load(f)
    with open(static_path, 'r') as f:
        static_data = json.load(f)
    
    # Build contingency table for paired data
    # Map trajectory_id to outcome
    dyn_outcomes = {s['trajectory_id']: s['outcome'] for s in dynamic_data.get('simulations', [])}
    stat_outcomes = {s['trajectory_id']: s['outcome'] for s in static_data.get('simulations', [])}
    
    common_ids = set(dyn_outcomes.keys()) & set(stat_outcomes.keys())
    
    # McNemar contingency: [[both_win, dyn_win_stat_loss], [stat_win_dyn_loss, both_loss]]
    n_both_win = 0
    n_dyn_win_stat_loss = 0
    n_stat_win_dyn_loss = 0
    n_both_loss = 0
    
    for tid in common_ids:
        d = dyn_outcomes[tid]
        s = stat_outcomes[tid]
        if d == 'win' and s == 'win':
            n_both_win += 1
        elif d == 'win' and s == 'loss':
            n_dyn_win_stat_loss += 1
        elif d == 'loss' and s == 'win':
            n_stat_win_dyn_loss += 1
        else:
            n_both_loss += 1
    
    contingency = np.array([[n_both_win, n_dyn_win_stat_loss],
                            [n_stat_win_dyn_loss, n_both_loss]])
    
    if n_dyn_win_stat_loss + n_stat_win_dyn_loss == 0:
        # No discordant pairs, p-value is 1.0
        p_value = 1.0
    else:
        _, p_value, _, _ = chi2_contingency(contingency, correction=True)
    
    report = {
        "test_type": "McNemar",
        "p_value": float(p_value),
        "contingency_table": contingency.tolist(),
        "significant": p_value < 0.05
    }
    
    results = {}
    if out_path.exists():
        with open(out_path, 'r') as f:
            results = json.load(f)
    results.update(report)
    
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"McNemar test result saved: {out_path}")

def run_ttest_token_usage():
    """Run paired t-test for token usage."""
    config = load_config_from_file('config.json')
    out_path = Path(config['data']['processed']) / 'statistical_results.json'
    
    dynamic_path = Path(config['data']['processed']) / 'simulation_logs_dynamic.json'
    static_path = Path(config['data']['processed']) / 'simulation_logs_static.json'
    
    if not dynamic_path.exists() or not static_path.exists():
        logger.error("Missing simulation logs for t-test")
        return
    
    with open(dynamic_path, 'r') as f:
        dynamic_data = json.load(f)
    with open(static_path, 'r') as f:
        static_data = json.load(f)
    
    # Map trajectory_id to tokens
    dyn_tokens = {s['trajectory_id']: s['tokens_used'] for s in dynamic_data.get('simulations', [])}
    stat_tokens = {s['trajectory_id']: s['tokens_used'] for s in static_data.get('simulations', [])}
    
    common_ids = sorted(set(dyn_tokens.keys()) & set(stat_tokens.keys()))
    
    if len(common_ids) < 2:
        logger.warning("Insufficient paired data for t-test")
        return
    
    dyn_vals = [dyn_tokens[tid] for tid in common_ids]
    stat_vals = [stat_tokens[tid] for tid in common_ids]
    
    # Paired t-test
    stat_res = ttest_rel(dyn_vals, stat_vals)
    
    report = {
        "token_test_type": "Paired T-Test",
        "token_p_value": float(stat_res.pvalue),
        "token_mean_diff": float(np.mean(dyn_vals) - np.mean(stat_vals)),
        "token_significant": stat_res.pvalue < 0.05
    }
    
    results = {}
    if out_path.exists():
        with open(out_path, 'r') as f:
            results = json.load(f)
    results.update(report)
    
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Token t-test result saved: {out_path}")

def apply_bonferroni_correction():
    """Apply Bonferroni correction to family of tests."""
    config = load_config_from_file('config.json')
    out_path = Path(config['data']['processed']) / 'statistical_results.json'
    
    results = {}
    if out_path.exists():
        with open(out_path, 'r') as f:
            results = json.load(f)
    
    # Count how many tests we are correcting for
    # Typically: 1 win-rate test + 1 token test = 2 tests
    n_tests = 2
    alpha = 0.05
    corrected_alpha = alpha / n_tests
    
    # Adjust p-values if present
    if 'p_value' in results:
        results['bonferroni_adjusted_p_value'] = min(results['p_value'] * n_tests, 1.0)
    if 'token_p_value' in results:
        results['token_bonferroni_adjusted_p_value'] = min(results['token_p_value'] * n_tests, 1.0)
    
    results['bonferroni_adjusted'] = True
    results['alpha_corrected'] = corrected_alpha
    results['n_tests_corrected'] = n_tests
    
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Bonferroni correction applied (n={n_tests}, alpha={corrected_alpha})")

def save_statistical_results():
    """Finalize statistical results."""
    # Results are saved incrementally in individual functions
    pass

def main():
    """Run full statistical analysis pipeline."""
    logger.info("Starting statistical analysis...")
    
    detect_divergence()
    run_mcnemar_test()
    run_ttest_token_usage()
    apply_bonferroni_correction()
    
    logger.info("Statistical analysis complete.")

if __name__ == '__main__':
    main()