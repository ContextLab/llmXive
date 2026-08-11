import logging
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from scipy import stats
import csv

from utils.simulation import RNGWrapper
from utils.exceptions import HighDimensionalInstabilityError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_seed_map(seed_map_path: str) -> Dict[str, List[int]]:
    path = Path(seed_map_path)
    if not path.exists():
        raise FileNotFoundError(f"Seed map not found at {seed_map_path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_params(params_path: str) -> List[Dict[str, Any]]:
    path = Path(params_path)
    if not path.exists():
        raise FileNotFoundError(f"Params file not found at {params_path}")
    params_list = []
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['n'] = int(row['n'])
            row['p'] = int(row['p'])
            row['rho'] = float(row['rho'])
            row['seed'] = int(row['seed'])
            row['iteration'] = int(row['iteration'])
            params_list.append(row)
    return params_list

def run_hypothesis_tests(data: np.ndarray) -> np.ndarray:
    """Run t-test on each feature against mean=0."""
    n, p = data.shape
    t_stats, p_values = stats.ttest_1samp(data, popmean=0, axis=0)
    p_values = np.nan_to_num(p_values, nan=1.0, posinf=1.0, neginf=1.0)
    p_values = np.clip(p_values, 0, 1)
    return p_values

def run_hypothesis_tests_batch(params_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run tests for all parameters."""
    results = []
    for params in params_list:
        try:
            logger.info(f"Running tests for seed {params['seed']}")
            rng = RNGWrapper()
            rng.reset(params['seed'])
            np_rng = rng.get_generator()
            
            # Regenerate data
            n, p = params['n'], params['p']
            rho = params['rho']
            dist = params['distribution_type']
            
            # Generate data (simplified from generate_data.py)
            if dist == 'normal':
                Z = np_rng.standard_normal(size=(n, p))
            elif dist == 't':
                Z = np_rng.standard_t(df=3, size=(n, p))
            elif dist == 'skew_normal':
                Z = np_rng.standard_normal(size=(n, p))
                Z = Z + 1.5 * np.abs(Z)
            else:
                Z = np_rng.standard_normal(size=(n, p))
            
            if p > 1 and rho > 0:
                safe_rho = max(0.0, min(rho, 0.99))
                common = np_rng.standard_normal(size=(n, 1))
                Z = np.sqrt(1 - safe_rho) * Z + np.sqrt(safe_rho) * common
            
            p_values = run_hypothesis_tests(Z)
            
            # Save p-values
            output_path = Path(f"data/results/pvalues_{params['seed']}.csv")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(p_values)
            
            results.append({
                'seed': params['seed'],
                'n': n,
                'p': p,
                'rho': rho,
                'dist': dist,
                'pvalues_count': len(p_values)
            })
        except Exception as e:
            logger.error(f"Error for seed {params['seed']}: {e}")
            continue
    return results

def detect_embarrassment(results: List[Dict[str, Any]], ks_stats_path: str):
    """Flag runs where KS > 0.1."""
    # This requires KS stats, which are calculated in T029.
    # We will just log a placeholder for now.
    logger.info("Embarrassment detection placeholder (requires T029 results)")

def main():
    base_dir = Path(__file__).parent.parent
    seed_map_path = base_dir / 'data' / 'sweep' / 'seed_map.json'
    params_path = base_dir / 'data' / 'sweep' / 'params.csv'
    
    try:
        params_list = load_params(str(params_path))
    except FileNotFoundError:
        logger.error("Params file missing. Run generate_data.py first.")
        sys.exit(1)
    
    run_hypothesis_tests_batch(params_list)
    logger.info("Hypothesis tests complete.")

if __name__ == '__main__':
    main()
