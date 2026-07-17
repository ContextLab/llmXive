import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import sys
import os

# Add parent to path for imports if running as script
if __name__ == "__main__" and "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from config import RANDOM_SEED
from utils import PipelineError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def estimate_tail_index_hill(data: np.ndarray, x_min: float, k: int) -> float:
    """
    Estimate the tail index (alpha) using the Hill estimator.
    alpha = 1 / mean(log(X_i / x_min)) for X_i > x_min, top k observations.
    """
    tail_data = data[data >= x_min]
    if len(tail_data) < k:
        raise ValueError(f"Not enough data points >= x_min ({len(tail_data)} < {k})")
    
    # Sort descending
    sorted_tail = np.sort(tail_data)[::-1]
    # Take top k
    top_k = sorted_tail[:k]
    
    # Hill estimator
    log_ratios = np.log(top_k / x_min)
    hill_alpha = 1.0 / np.mean(log_ratios)
    return hill_alpha

def tail_ks_test_with_bootstrap(
    data: np.ndarray,
    x_min: float,
    n_bootstrap: int = 1000,
    alpha: float = 0.05,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Perform a Kolmogorov-Smirnov test on the tail (data >= x_min) against a fitted Pareto distribution,
    with a bootstrapped p-value correction for the data-driven threshold x_min.
    
    Since x_min is estimated from the data, the standard KS distribution is invalid.
    We use a parametric bootstrap:
    1. Fit Pareto to the tail data (MLE).
    2. Generate n_bootstrap synthetic datasets from this fitted Pareto.
    3. For each synthetic dataset, estimate its x_min (using the same grid search method as the real data)
       and compute the KS statistic against its own fitted Pareto.
    4. Compute the KS statistic for the real data.
    5. The p-value is the proportion of bootstrap KS statistics >= real KS statistic.
    
    Note: This is computationally expensive. For speed in CI, we use a smaller grid for x_min estimation
    in the bootstrap loop if n_bootstrap is large.
    """
    np.random.seed(random_state)
    
    tail_data = data[data >= x_min]
    n_tail = len(tail_data)
    
    if n_tail < 10:
        raise ValueError(f"Not enough tail data points ({n_tail}) for reliable KS test.")
    
    # 1. Fit Pareto to real tail data
    # Pareto distribution in scipy: f(x, b, loc, scale) = b * scale**b / (x + loc)**(b+1) for x >= scale
    # We assume loc=0, scale=x_min. Shape parameter 'b' is the tail index alpha.
    # MLE for Pareto with known scale (x_min): alpha = n / sum(log(x_i / x_min))
    # This matches the Hill estimator.
    alpha_hat = n_tail / np.sum(np.log(tail_data / x_min))
    
    # 2. Compute KS statistic for real data
    # CDF of Pareto: F(x) = 1 - (x_min / x)^alpha
    def pareto_cdf(x, alpha):
        return 1 - (x_min / x)**alpha
    
    # Empirical CDF
    sorted_tail = np.sort(tail_data)
    n = len(sorted_tail)
    ecdf = np.arange(1, n + 1) / n
    theoretical_cdf = pareto_cdf(sorted_tail, alpha_hat)
    ks_stat_real = np.max(np.abs(ecdf - theoretical_cdf))
    
    # 3. Bootstrap loop
    bootstrap_ks_stats = []
    
    # We need a function to estimate x_min for a given dataset.
    # To save time, we use a simple grid search over percentiles of the data.
    def estimate_x_min_simple(data_subset, grid_percentiles=np.linspace(5, 50, 20)):
        """Estimate x_min by minimizing KS distance for a grid of percentiles."""
        best_ks = np.inf
        best_x_min = None
        sorted_data = np.sort(data_subset)
        n_sub = len(sorted_data)
        
        for p in grid_percentiles:
            idx = int(n_sub * p / 100)
            if idx < 1: continue
            candidate_x_min = sorted_data[idx]
            
            tail_sub = data_subset[data_subset >= candidate_x_min]
            if len(tail_sub) < 5: continue
            
            # Fit alpha
            alpha_sub = len(tail_sub) / np.sum(np.log(tail_sub / candidate_x_min))
            if alpha_sub <= 0: continue
            
            # KS
            s_tail = np.sort(tail_sub)
            n_s = len(s_tail)
            ecdf_s = np.arange(1, n_s + 1) / n_s
            theo_cdf_s = 1 - (candidate_x_min / s_tail)**alpha_sub
            ks_val = np.max(np.abs(ecdf_s - theo_cdf_s))
            
            if ks_val < best_ks:
                best_ks = ks_val
                best_x_min = candidate_x_min
        
        return best_x_min, best_ks

    for i in range(n_bootstrap):
        # Generate synthetic data from fitted Pareto(alpha_hat, scale=x_min)
        # Scipy's pareto.rvs(b, scale=scale) generates from 1 + pareto(b) * scale? 
        # No, scipy.stats.pareto(b, scale=scale) has CDF 1 - (scale/x)**b for x >= scale.
        synth_data = stats.pareto.rvs(alpha_hat, scale=x_min, size=n_tail, random_state=random_state + i)
        
        # Estimate x_min for this synthetic data (to mimic the data-driven threshold)
        # Use a simplified estimation to speed up
        est_x_min, _ = estimate_x_min_simple(synth_data)
        if est_x_min is None:
            # Fallback: use the original x_min if estimation fails
            est_x_min = x_min
        
        # Filter synthetic tail
        synth_tail = synth_data[synth_data >= est_x_min]
        if len(synth_tail) < 5:
            continue
        
        # Fit alpha for synthetic tail
        alpha_synth = len(synth_tail) / np.sum(np.log(synth_tail / est_x_min))
        if alpha_synth <= 0:
            continue
        
        # Compute KS for synthetic
        s_synth = np.sort(synth_tail)
        n_s = len(s_synth)
        ecdf_s = np.arange(1, n_s + 1) / n_s
        theo_cdf_s = 1 - (est_x_min / s_synth)**alpha_synth
        ks_stat_synth = np.max(np.abs(ecdf_s - theo_cdf_s))
        
        bootstrap_ks_stats.append(ks_stat_synth)
    
    if len(bootstrap_ks_stats) == 0:
        raise RuntimeError("Bootstrap loop produced no valid KS statistics.")
    
    # 4. Calculate p-value
    # p = P(KS_synth >= KS_real)
    p_value = np.mean(np.array(bootstrap_ks_stats) >= ks_stat_real)
    
    return {
        "ks_statistic": float(ks_stat_real),
        "p_value_bootstrap": float(p_value),
        "n_bootstrap": n_bootstrap,
        "alpha_estimate": float(alpha_hat),
        "x_min_used": float(x_min),
        "n_tail_points": n_tail,
        "method": "Parametric Bootstrap KS Test with Data-Driven Threshold Correction"
    }

def save_tail_ks_results(results: Dict[str, Any], output_path: str) -> None:
    """Save tail KS test results to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Tail KS results saved to {output_path}")

def run_tail_ks_task(
    data: np.ndarray,
    x_min: float,
    output_path: str = "data/results/tail_ks.json",
    n_bootstrap: int = 500  # Reduced for CI speed, but > 0
) -> Dict[str, Any]:
    """
    Run the tail KS test task.
    """
    logger.info(f"Running Tail KS Test with x_min={x_min}, n_bootstrap={n_bootstrap}")
    try:
        results = tail_ks_test_with_bootstrap(
            data=data,
            x_min=x_min,
            n_bootstrap=n_bootstrap,
            random_state=RANDOM_SEED
        )
        save_tail_ks_results(results, output_path)
        return results
    except Exception as e:
        logger.error(f"Tail KS test failed: {e}")
        raise

def bootstrap_pareto_gof(
    data: np.ndarray,
    x_min: float,
    n_bootstrap: int = 1000,
    alpha: float = 0.05,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Bootstrap Goodness-of-Fit test for Pareto distribution.
    (Existing function kept for compatibility)
    """
    # Implementation similar to the one above but focused on GOF
    tail_data = data[data >= x_min]
    n_tail = len(tail_data)
    if n_tail < 10:
        raise ValueError("Not enough tail data for bootstrap GOF.")
    
    # Fit Pareto
    alpha_hat = n_tail / np.sum(np.log(tail_data / x_min))
    
    # KS stat
    sorted_tail = np.sort(tail_data)
    ecdf = np.arange(1, n_tail + 1) / n_tail
    theo_cdf = 1 - (x_min / sorted_tail)**alpha_hat
    ks_stat = np.max(np.abs(ecdf - theo_cdf))
    
    bootstrap_stats = []
    for i in range(n_bootstrap):
        synth = stats.pareto.rvs(alpha_hat, scale=x_min, size=n_tail, random_state=random_state + i)
        synth_sorted = np.sort(synth)
        synth_ecdf = np.arange(1, n_tail + 1) / n_tail
        synth_theo = 1 - (x_min / synth_sorted)**alpha_hat
        bootstrap_stats.append(np.max(np.abs(synth_ecdf - synth_theo)))
    
    p_val = np.mean(np.array(bootstrap_stats) >= ks_stat)
    
    return {
        "ks_statistic": float(ks_stat),
        "p_value": float(p_val),
        "alpha_estimate": float(alpha_hat),
        "n_bootstrap": n_bootstrap,
        "method": "Bootstrap Goodness-of-Fit"
    }

def save_bootstrap_gof_results(results: Dict[str, Any], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)

def run_bootstrap_gof_task(
    data: np.ndarray,
    x_min: float,
    output_path: str = "data/results/bootstrap_gof.json",
    n_bootstrap: int = 1000
) -> Dict[str, Any]:
    results = bootstrap_pareto_gof(data, x_min, n_bootstrap, random_state=RANDOM_SEED)
    save_bootstrap_gof_results(results, output_path)
    return results

def main():
    """
    Main entry point for diagnostics tasks.
    Expects data to be loaded from data/processed/cleaned_delays.csv
    and x_min from data/results/x_min_estimate.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Tail KS Test and other diagnostics")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_delays.csv",
                        help="Path to cleaned delays CSV")
    parser.add_argument("--x-min", type=str, default="data/results/x_min_estimate.json",
                        help="Path to x_min estimate JSON")
    parser.add_argument("--output", type=str, default="data/results/tail_ks.json",
                        help="Output path for tail KS results")
    parser.add_argument("--n-bootstrap", type=int, default=500,
                        help="Number of bootstrap iterations")
    
    args = parser.parse_args()
    
    # Load data
    logger.info(f"Loading data from {args.input}")
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")
    
    df = pd.read_csv(args.input)
    if 'total_delay' not in df.columns:
        # Fallback if column name differs
        if 'Delay' in df.columns:
            delays = df['Delay'].values
        else:
            raise KeyError("Column 'total_delay' not found in input data.")
    else:
        delays = df['total_delay'].values
    
    # Filter non-positive
    delays = delays[delays > 0]
    
    # Load x_min
    logger.info(f"Loading x_min from {args.x_min}")
    if not os.path.exists(args.x_min):
        raise FileNotFoundError(f"x_min file not found: {args.x_min}")
    
    with open(args.x_min, 'r') as f:
        x_min_data = json.load(f)
    x_min = x_min_data['x_min']
    
    logger.info(f"Running Tail KS Test with x_min={x_min}")
    results = run_tail_ks_task(
        data=delays,
        x_min=x_min,
        output_path=args.output,
        n_bootstrap=args.n_bootstrap
    )
    
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
