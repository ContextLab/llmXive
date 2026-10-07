import csv
import json
import logging
import os
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from scipy.stats import spearmanr
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from lifelines import KaplanMeierFitter, CoxPHFitter
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_entropy_results(entropy_path: str) -> pd.DataFrame:
    """Load entropy results CSV."""
    path = Path(entropy_path)
    if not path.exists():
        raise FileNotFoundError(f"Entropy results not found at {entropy_path}")
    df = pd.read_csv(path)
    required_cols = {'task_id', 'entropy'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Entropy results missing columns: {missing}")
    return df

def load_convergence_results(conv_path: str) -> pd.DataFrame:
    """Load convergence results CSV."""
    path = Path(conv_path)
    if not path.exists():
        raise FileNotFoundError(f"Convergence results not found at {conv_path}")
    df = pd.read_csv(path)
    required_cols = {'task_id', 'k', 'is_correct', 'first_correct_step', 'censored', 'time_to_event'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Convergence results missing columns: {missing}")
    return df

def load_exclusion_log(log_path: str) -> List[Dict[str, Any]]:
    """Load exclusion log JSON."""
    path = Path(log_path)
    if not path.exists():
        return []
    with open(path, 'r') as f:
        return json.load(f)

def load_strata_log(strata_path: str) -> List[Dict[str, Any]]:
    """Load strata log JSON."""
    path = Path(strata_path)
    if not path.exists():
        raise FileNotFoundError(f"Strata log not found at {strata_path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_filtered_splits(splits_path: str) -> Dict[str, Any]:
    """Load filtered splits JSON."""
    path = Path(splits_path)
    if not path.exists():
        raise FileNotFoundError(f"Filtered splits not found at {splits_path}")
    with open(path, 'r') as f:
        return json.load(f)

def compute_spearman_correlation(
    entropy_df: pd.DataFrame,
    convergence_df: pd.DataFrame
) -> Tuple[float, float]:
    """Compute Spearman correlation between entropy and first_correct_step."""
    merged = pd.merge(entropy_df, convergence_df, on='task_id', how='inner')
    
    # Drop rows with missing values
    merged = merged.dropna(subset=['entropy', 'first_correct_step'])
    
    if len(merged) < 2:
        logger.warning("Insufficient data for correlation (n < 2)")
        return float('nan'), float('nan')
    
    rho, p_val = spearmanr(merged['entropy'], merged['first_correct_step'])
    return float(rho), float(p_val)

def run_survival_analysis(
    convergence_df: pd.DataFrame,
    entropy_df: pd.DataFrame,
    output_path: str
) -> Dict[str, Any]:
    """Fit Kaplan-Meier and Cox PH models."""
    merged = pd.merge(entropy_df, convergence_df, on='task_id', how='inner')
    
    # Prepare survival data
    # time = time_to_event, event = ~censored (1 if event occurred, 0 if censored)
    # In our case, "event" is convergence (finding the correct solution).
    # Censored means we didn't find it by k_max.
    
    df = merged.dropna(subset=['entropy', 'time_to_event', 'censored'])
    df['event'] = ~df['censored'].astype(bool)
    
    if len(df) == 0:
        raise ValueError("No valid data for survival analysis")
    
    # Kaplan Meier
    kmf = KaplanMeierFitter()
    kmf.fit(df['time_to_event'], event_observed=df['event'])
    
    # Cox PH
    cph = CoxPHFitter()
    # CoxPHFitter expects a DataFrame with 'duration_col' and 'event_col'
    cph_df = df[['entropy', 'time_to_event', 'event']].copy()
    cph_df = cph_df.rename(columns={'time_to_event': 'T', 'event': 'E'})
    
    cph.fit(cph_df, duration_col='T', event_col='E')
    
    results = {
        'cox_summary': cph.summary.to_dict(),
        'concordance_index': float(cph.concordance_index_),
        'median_survival_time': float(kmf.median_survival_time_) if not np.isinf(kmf.median_survival_time_) else None
    }
    
    # Save
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Survival analysis results saved to {output_path}")
    return results

def perform_power_analysis(
    rho: float,
    n_samples: int,
    alpha: float = 0.05
) -> Dict[str, float]:
    """Compute MDES and power."""
    # Simplified power calculation for correlation
    # Using Fisher's z-transformation
    if np.isnan(rho) or n_samples < 3:
        return {'power': float('nan'), 'mdes': float('nan')}
    
    z = 0.5 * np.log((1 + rho) / (1 - rho))
    se = 1 / np.sqrt(n_samples - 3)
    
    # Critical z for alpha
    z_crit = 1.96 # approx for 0.05 two-sided
    
    # Power = P(Z > z_crit - z / se) ... simplified
    # This is a rough estimate
    power = 1 - (1 + np.exp(-np.sqrt(n_samples) * abs(rho))) ** -1
    
    # MDES: minimum detectable effect size for 80% power
    # z_power = 0.84 for 80%
    z_power = 0.84
    mdes_z = (z_crit + z_power) / np.sqrt(n_samples - 3)
    mdes = np.tanh(mdes_z)
    
    return {
        'power': float(power),
        'mdes': float(mdes)
    }

def save_correlation_results(
    rho: float,
    p_value: float,
    output_path: str
) -> None:
    """Save correlation results to JSON."""
    results = {
        'rho': rho,
        'p_value': p_value
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)

def save_router_model(model, path: str) -> None:
    """Save router model to pickle."""
    with open(path, 'wb') as f:
        pickle.dump(model, f)

def generate_significance_flag(p_value: float, alpha: float = 0.05) -> bool:
    """Generate significance flag."""
    return p_value < alpha

def integrate_router_results(
    router_results: pd.DataFrame,
    convergence_results: pd.DataFrame
) -> pd.DataFrame:
    """Integrate router predictions with actual convergence."""
    merged = pd.merge(router_results, convergence_results, on='task_id', how='inner')
    return merged

def run_analysis(
    entropy_path: str,
    convergence_path: str,
    output_path: str
) -> Dict[str, Any]:
    """Run full analysis pipeline."""
    entropy_df = load_entropy_results(entropy_path)
    conv_df = load_convergence_results(convergence_path)
    
    rho, p_val = compute_spearman_correlation(entropy_df, conv_df)
    
    results = {
        'correlation': {
            'rho': rho,
            'p_value': p_val,
            'significant': generate_significance_flag(p_val)
        },
        'sample_size': len(entropy_df)
    }
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Analysis Pipeline")
    subparsers = parser.add_subparsers(dest='mode', help='Analysis mode')
    
    # Spearman
    spearman_parser = subparsers.add_parser('spearman', help='Compute Spearman correlation')
    spearman_parser.add_argument('--entropy', required=True, help='Path to entropy results')
    spearman_parser.add_argument('--convergence', required=True, help='Path to convergence results')
    spearman_parser.add_argument('--output', required=True, help='Path to output JSON')
    
    # Survival
    survival_parser = subparsers.add_parser('survival', help='Run survival analysis')
    survival_parser.add_argument('--convergence', required=True, help='Path to convergence results')
    survival_parser.add_argument('--entropy', required=True, help='Path to entropy results')
    survival_parser.add_argument('--output', required=True, help='Path to output JSON')
    
    # Power
    power_parser = subparsers.add_parser('power', help='Run power analysis')
    power_parser.add_argument('--input', required=True, help='Path to correlation JSON')
    power_parser.add_argument('--output', required=True, help='Path to output JSON')
    
    args = parser.parse_args()
    
    if args.mode == 'spearman':
        run_analysis(args.entropy, args.convergence, args.output)
    elif args.mode == 'survival':
        conv_df = load_convergence_results(args.convergence)
        ent_df = load_entropy_results(args.entropy)
        run_survival_analysis(conv_df, ent_df, args.output)
    elif args.mode == 'power':
        with open(args.input, 'r') as f:
            data = json.load(f)
        rho = data['correlation']['rho']
        n = data['sample_size']
        power_results = perform_power_analysis(rho, n)
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(power_results, f, indent=2)
    else:
        parser.print_help()
        exit(1)

if __name__ == '__main__':
    main()