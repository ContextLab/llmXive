import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm
from scipy import stats
from scipy.stats import chi2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_experiment_data(data_dir: str) -> pd.DataFrame:
    """
    Load and concatenate all experiment result JSON files from data_dir.
    Expects files like results/hanabi_seed_*.json, results/spear_seed_*.json, etc.
    Returns a single DataFrame with all metrics.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        logger.error(f"Data directory {data_dir} does not exist.")
        return pd.DataFrame()

    dfs = []
    for json_file in data_path.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                for row in data:
                    dfs.append(pd.json_normalize(row))
            elif isinstance(data, dict):
                dfs.append(pd.json_normalize([data]))
        except Exception as e:
            logger.warning(f"Failed to load {json_file}: {e}")

    if not dfs:
        logger.warning("No data found in specified directory.")
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)
    # Ensure numeric columns are numeric
    numeric_cols = ['episode_length', 'msg_count', 'bytes_sent', 'recovery_success', 'recovery_latency', 'task_success']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

def prepare_lmm_data(df: pd.DataFrame, target_metric: str) -> pd.DataFrame:
    """
    Prepare data for Linear Mixed-Effects Model analysis.
    Assumes columns: 'protocol' (Foundation/Native), 'seed', and target_metric.
    """
    if target_metric not in df.columns:
        raise ValueError(f"Target metric '{target_metric}' not found in data.")

    # Drop rows with missing target metric
    clean_df = df.dropna(subset=[target_metric])

    # Ensure protocol is categorical
    clean_df['protocol'] = pd.Categorical(clean_df['protocol'], categories=['Foundation', 'Native Direct'])

    return clean_df

def run_lmm_analysis(df: pd.DataFrame, target_metric: str, group_col: str = 'seed') -> Dict[str, Any]:
    """
    Run Linear Mixed-Effects Model: target_metric ~ protocol + (1|group_col)
    Returns results dictionary with fixed effects, p-values, and estimates.
    """
    formula = f"{target_metric} ~ protocol + (1|{group_col})"
    
    # Handle categorical encoding for statsmodels
    # statsmodels handles C() internally if formula is string, but we ensure types
    model = mixedlm(formula, df, groups=df[group_col])
    result = model.fit()

    # Extract fixed effects for 'protocol[T.Foundation]' (difference from baseline 'Native Direct')
    # Note: The reference level is the first category alphabetically or as set.
    # We set categories explicitly above, so 'Foundation' is the second one if 'Foundation' > 'Native Direct' alphabetically?
    # Actually, Categorical categories order matters. Let's check the coeff name.
    params = result.params
    std_errors = result.bse
    p_values = result.pvalues

    # Find the coefficient for Foundation protocol
    # The variable name might be 'protocol[T.Foundation]' or similar
    coeff_name = None
    for name in params.index:
        if 'protocol' in name and 'Foundation' in name:
            coeff_name = name
            break

    if coeff_name is None:
        # Fallback: if only one protocol column exists (e.g. binary 0/1 encoding)
        # But with Categorical, it should be T.Foundation
        logger.warning("Could not find Foundation protocol coefficient. Checking all params.")
        logger.warning(f"Params: {params.index.tolist()}")
        # If we can't find it, return empty or raise
        return {
            'success': False,
            'error': 'Could not identify protocol coefficient in LMM results'
        }

    return {
        'success': True,
        'metric': target_metric,
        'coefficient': params[coeff_name],
        'std_error': std_errors[coeff_name],
        'p_value': p_values[coeff_name],
        'baseline_estimate': params['Intercept'],
        'formula': formula,
        'summary': str(result.summary())
    }

def run_mcnemar_test(df: pd.DataFrame, metric_col: str = 'recovery_success') -> Dict[str, Any]:
    """
    Run McNemar's test for binary metric (recovery_success, task_success).
    Expects paired data (same seed, two protocols).
    Returns contingency table and p-value.
    """
    # Pivot to get paired data: rows = Foundation, cols = Native Direct
    # We need to group by seed and ensure we have exactly one row per protocol per seed
    if 'seed' not in df.columns or 'protocol' not in df.columns:
        return {'success': False, 'error': 'Missing seed or protocol column'}

    # Pivot table
    pivot = df.pivot_table(index='seed', columns='protocol', values=metric_col, aggfunc='first')
    
    # Drop rows with missing values (incomplete pairs)
    pivot = pivot.dropna()

    if len(pivot) < 2:
        return {'success': False, 'error': 'Not enough paired samples for McNemar'}

    # Extract binary values (0 or 1)
    foundation = pivot['Foundation'].astype(int).values
    native = pivot['Native Direct'].astype(int).values

    # Construct contingency table for McNemar:
    #           Native=0   Native=1
    # Found=0     n00        n01
    # Found=1     n10        n11
    # We need discordant pairs: n01 (Found=0, Native=1) and n10 (Found=1, Native=0)
    
    n01 = np.sum((foundation == 0) & (native == 1))
    n10 = np.sum((foundation == 1) & (native == 0))

    if n01 + n10 == 0:
        return {
            'success': True,
            'metric': metric_col,
            'contingency': {'n01': n01, 'n10': n10},
            'p_value': 1.0,
            'chi2_statistic': 0.0,
            'interpretation': 'No discordant pairs; no difference detected'
        }

    # McNemar's test statistic: (|n01 - n10| - 1)^2 / (n01 + n10) (continuity correction)
    chi2_stat = (abs(n01 - n10) - 1) ** 2 / (n01 + n10)
    p_val = 1 - chi2.cdf(chi2_stat, 1)

    return {
        'success': True,
        'metric': metric_col,
        'contingency': {'n01': int(n01), 'n10': int(n10)},
        'chi2_statistic': float(chi2_stat),
        'p_value': float(p_val),
        'interpretation': 'Significant difference' if p_val < 0.05 else 'No significant difference'
    }

def run_paired_ttest(df: pd.DataFrame, metric_col: str) -> Dict[str, Any]:
    """
    Run paired t-test for continuous metrics (episode_length, msg_count, etc.).
    """
    if 'seed' not in df.columns or 'protocol' not in df.columns:
        return {'success': False, 'error': 'Missing seed or protocol column'}

    pivot = df.pivot_table(index='seed', columns='protocol', values=metric_col, aggfunc='first')
    pivot = pivot.dropna()

    if len(pivot) < 2:
        return {'success': False, 'error': 'Not enough paired samples'}

    foundation = pivot['Foundation'].values
    native = pivot['Native Direct'].values

    t_stat, p_val = stats.ttest_rel(foundation, native)

    # Calculate Cohen's d for paired samples
    diff = foundation - native
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    cohens_d = mean_diff / std_diff if std_diff != 0 else 0.0

    return {
        'success': True,
        'metric': metric_col,
        't_statistic': float(t_stat),
        'p_value': float(p_val),
        'cohen_d': float(cohens_d),
        'mean_diff': float(mean_diff),
        'interpretation': 'Significant difference' if p_val < 0.05 else 'No significant difference'
    }

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Bonferroni correction to a list of p-values.
    Returns list of booleans indicating significance after correction.
    """
    n = len(p_values)
    if n == 0:
        return []
    corrected_alpha = alpha / n
    return [p < corrected_alpha for p in p_values]

def analyze_metrics(df: pd.DataFrame, metrics: List[str], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run full analysis suite: LMM for all metrics, McNemar for binary, T-test for continuous.
    """
    results = {
        'lmm_results': [],
        'mcnemar_results': [],
        'ttest_results': [],
        'summary': {}
    }

    # Binary metrics
    binary_metrics = ['recovery_success', 'task_success']
    continuous_metrics = [m for m in metrics if m not in binary_metrics]

    # Run McNemar for binary
    for metric in binary_metrics:
        if metric in df.columns:
            res = run_mcnemar_test(df, metric)
            results['mcnemar_results'].append(res)

    # Run T-test for continuous (as sensitivity)
    for metric in continuous_metrics:
        if metric in df.columns:
            res = run_paired_ttest(df, metric)
            results['ttest_results'].append(res)

    # Run LMM for all metrics (Primary analysis)
    for metric in metrics:
        if metric in df.columns:
            try:
                clean_df = prepare_lmm_data(df, metric)
                if len(clean_df) > 0:
                    res = run_lmm_analysis(clean_df, metric)
                    results['lmm_results'].append(res)
            except Exception as e:
                logger.error(f"LMM failed for {metric}: {e}")
                results['lmm_results'].append({'success': False, 'metric': metric, 'error': str(e)})

    # Summarize
    significant_lmm = [r for r in results['lmm_results'] if r.get('success') and r.get('p_value', 1.0) < alpha]
    significant_mcnemar = [r for r in results['mcnemar_results'] if r.get('success') and r.get('p_value', 1.0) < alpha]
    significant_ttest = [r for r in results['ttest_results'] if r.get('success') and r.get('p_value', 1.0) < alpha]

    results['summary'] = {
        'total_metrics': len(metrics),
        'significant_lmm': len(significant_lmm),
        'significant_mcnemar': len(significant_mcnemar),
        'significant_ttest': len(significant_ttest),
        'alpha': alpha
    }

    return results

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save analysis results to JSON.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Analyze Foundation Protocol experiment results")
    parser.add_argument('--data-dir', type=str, default='results', help='Directory containing experiment JSON files')
    parser.add_argument('--output', type=str, default='results/analysis_results.json', help='Output file path')
    parser.add_argument('--metrics', type=str, nargs='+', 
                        default=['episode_length', 'msg_count', 'bytes_sent', 'recovery_success', 'recovery_latency', 'task_success'],
                        help='Metrics to analyze')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')

    args = parser.parse_args()

    logger.info(f"Loading data from {args.data_dir}...")
    df = load_experiment_data(args.data_dir)

    if df.empty:
        logger.error("No data loaded. Exiting.")
        sys.exit(1)

    logger.info(f"Analyzing {len(args.metrics)} metrics...")
    results = analyze_metrics(df, args.metrics, args.alpha)

    logger.info(f"Saving results to {args.output}...")
    save_results(results, args.output)

    # Print summary
    print("\n=== Analysis Summary ===")
    print(f"Total metrics analyzed: {results['summary']['total_metrics']}")
    print(f"Significant (LMM): {results['summary']['significant_lmm']}")
    print(f"Significant (McNemar): {results['summary']['significant_mcnemar']}")
    print(f"Significant (T-test): {results['summary']['significant_ttest']}")
    print(f"Alpha level: {results['summary']['alpha']}")

if __name__ == '__main__':
    main()