import csv
import json
import logging
import os
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from statsmodels.discrete.discrete_model import OrderedLogit
import statsmodels.api as sm
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.utils import concordance_index
import warnings
warnings.filterwarnings('ignore')

from src.config import load_config, get_config_value
from src.router_evaluation import train_ordinal_logistic_router, evaluate_router, save_cv_fold_metrics

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_entropy_results(input_path: str) -> pd.DataFrame:
    """Load entropy results from CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Entropy results not found at {input_path}")
    return pd.read_csv(input_path)

def load_convergence_results(input_path: str) -> pd.DataFrame:
    """Load convergence results from CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Convergence results not found at {input_path}")
    return pd.read_csv(input_path)

def load_exclusion_log(input_path: str) -> List[Dict[str, Any]]:
    """Load exclusion log from JSON."""
    if not os.path.exists(input_path):
        return []
    with open(input_path, 'r') as f:
        return json.load(f)

def load_strata_log(input_path: str) -> Dict[str, Any]:
    """Load strata log from JSON."""
    if not os.path.exists(input_path):
        return {}
    with open(input_path, 'r') as f:
        return json.load(f)

def load_filtered_splits(input_path: str) -> Dict[str, Any]:
    """Load filtered splits from JSON."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Filtered splits not found at {input_path}")
    with open(input_path, 'r') as f:
        return json.load(f)

def compute_spearman_correlation(entropy_df: pd.DataFrame, convergence_df: pd.DataFrame) -> Dict[str, float]:
    """Compute Spearman correlation between entropy and first_correct_step."""
    # Merge on task_id
    merged = pd.merge(entropy_df, convergence_df, on='task_id', how='inner')
    # Use time_to_event or first_correct_step
    if 'time_to_event' in merged.columns:
        x = merged['entropy']
        y = merged['time_to_event']
    elif 'first_correct_step' in merged.columns:
        x = merged['entropy']
        y = merged['first_correct_step']
    else:
        raise ValueError("Neither time_to_event nor first_correct_step found in convergence data")
    
    rho, p_value = spearmanr(x, y)
    return {'rho': float(rho), 'p_value': float(p_value)}

def run_survival_analysis(entropy_df: pd.DataFrame, convergence_df: pd.DataFrame) -> Dict[str, Any]:
    """Run Kaplan-Meier and Cox PH analysis."""
    merged = pd.merge(entropy_df, convergence_df, on='task_id', how='inner')
    
    # Prepare survival data
    # time = time_to_event, event = ~censored (1 if event happened, 0 if censored)
    # Note: In survival analysis, event=1 means the event of interest occurred.
    # Here, the event is "convergence". If censored=True, it means we didn't see convergence by k=3.
    # So event = 1 if not censored, 0 if censored.
    merged['event'] = (~merged['censored']).astype(int)
    
    # Kaplan-Meier
    kmf = KaplanMeierFitter()
    kmf.fit(merged['time_to_event'], event_observed=merged['event'])
    
    # Cox PH
    cph = CoxPHFitter()
    cph.fit(merged[['time_to_event', 'entropy', 'event']], duration_col='time_to_event', event_col='event')
    
    # Concordance index
    c_index = concordance_index(merged['time_to_event'], -cph.predict_partial_hazard(merged), merged['event'])
    
    return {
        'cox_summary': cph.summary.to_dict(),
        'concordance_index': float(c_index)
    }

def perform_power_analysis(effect_size: float, n_samples: int, alpha: float = 0.05) -> Dict[str, float]:
    """Perform power analysis for correlation."""
    # Simplified power calculation for Spearman correlation
    # Using approximation: z = 0.5 * ln((1+r)/(1-r))
    # SE = 1 / sqrt(n-3)
    # This is a rough estimate
    z = 0.5 * np.log((1 + effect_size) / (1 - effect_size))
    se = 1 / np.sqrt(n_samples - 3)
    z_alpha = 1.96 # for alpha=0.05
    power_z = abs(z) - z_alpha
    # Approximate power using normal CDF
    from scipy.stats import norm
    power = norm.cdf(power_z)
    return {'power': float(power), 'n_samples': n_samples, 'effect_size': effect_size}

def run_analysis(entropy_path: str, convergence_path: str) -> Dict[str, Any]:
    """Run full correlation analysis."""
    entropy_df = load_entropy_results(entropy_path)
    convergence_df = load_convergence_results(convergence_path)
    
    spearman = compute_spearman_correlation(entropy_df, convergence_df)
    survival = run_survival_analysis(entropy_df, convergence_df)
    power = perform_power_analysis(spearman['rho'], len(entropy_df))
    
    return {
        'spearman': spearman,
        'survival': survival,
        'power': power
    }

def save_correlation_results(results: Dict[str, Any], output_path: str):
    """Save correlation results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def save_router_model(model, output_path: str):
    """Save router model to pickle."""
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)

def generate_significance_flag(p_value: float, alpha: float = 0.05) -> bool:
    """Generate significance flag based on p-value."""
    return p_value < alpha

def integrate_router_results(entropy_path: str, convergence_path: str, router_path: str) -> Dict[str, Any]:
    """Integrate router results with correlation data."""
    entropy_df = load_entropy_results(entropy_path)
    convergence_df = load_convergence_results(convergence_path)
    
    # Load router predictions
    router_df = pd.read_csv(router_path)
    
    # Merge
    merged = pd.merge(entropy_df, convergence_df, on='task_id', how='inner')
    merged = pd.merge(merged, router_df[['task_id', 'predicted_k', 'accuracy']], on='task_id', how='inner')
    
    # Compute correlation between entropy and predicted_k
    rho, p = spearmanr(merged['entropy'], merged['predicted_k'])
    
    return {'entropy_predicted_k_rho': rho, 'p_value': p}

def main():
    """Main function for analysis."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='spearman')
    parser.add_argument('--entropy', type=str, required=True)
    parser.add_argument('--convergence', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    args = parser.parse_args()
    
    if args.mode == 'spearman':
        results = run_analysis(args.entropy, args.convergence)
        save_correlation_results(results, args.output)
    elif args.mode == 'router':
        # This would call router training logic
        pass

if __name__ == "__main__":
    main()
