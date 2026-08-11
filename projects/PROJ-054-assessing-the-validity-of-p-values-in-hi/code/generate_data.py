import numpy as np
import json
import hashlib
import os
import logging
import argparse
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator, Callable
from utils.simulation import RNGWrapper
from utils.exceptions import HighDimensionalInstabilityError
from utils.regularization import regularize_covariance, is_condition_number_acceptable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_required_iterations() -> int:
    """Load required_iterations from power analysis result or use default."""
    base_dir = Path(__file__).parent.parent
    path = base_dir / 'data' / 'sweep' / 'power_analysis_result.json'
    if path.exists():
        with open(path, 'r') as f:
            data = json.load(f)
            return data.get('required_iterations', 1000)
    return 1000

def generate_correlated_data(n: int, p: int, rho: float, distribution_type: str, rng: np.random.Generator) -> np.ndarray:
    """Generate correlated data with specific distribution."""
    if distribution_type == 'normal':
        Z = rng.standard_normal(size=(n, p))
    elif distribution_type == 't':
        Z = rng.standard_t(df=3, size=(n, p))
    elif distribution_type == 'skew_normal':
        Z = rng.standard_normal(size=(n, p))
        Z = Z + 1.5 * np.abs(Z)
    else:
        raise ValueError(f"Unknown distribution: {distribution_type}")
    
    if p > 1 and rho > 0:
        safe_rho = max(0.0, min(rho, 0.99))
        common = rng.standard_normal(size=(n, 1))
        Z = np.sqrt(1 - safe_rho) * Z + np.sqrt(safe_rho) * common
    
    return Z

def generate_distribution_violations(data: np.ndarray, distribution_type: str) -> np.ndarray:
    """Apply distribution violations if not normal."""
    # This is handled in generate_correlated_data
    return data

def write_dataset_metadata(params: Dict[str, Any], seed: int, output_path: str):
    """Write metadata JSON for a dataset."""
    param_str = json.dumps(params, sort_keys=True)
    sha256 = hashlib.sha256(param_str.encode()).hexdigest()
    
    metadata = {
        'sha256': sha256,
        'seed': seed,
        'n': params['n'],
        'p': params['p'],
        'rho': params['rho'],
        'distribution_type': params['distribution_type']
    }
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(metadata, f, indent=2)

def streaming_data_generator(
    params_path: str,
    callback: Callable[[np.ndarray, Dict[str, Any]], bool]
) -> Iterator[Dict[str, Any]]:
    """
    Streaming generator that iterates over params.csv, generates data, and yields to callback.
    """
    path = Path(params_path)
    if not path.exists():
        raise FileNotFoundError(f"Params file not found: {params_path}")
    
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            n = int(row['n'])
            p = int(row['p'])
            rho = float(row['rho'])
            dist_type = row['distribution_type']
            seed = int(row['seed'])
            iteration = int(row['iteration'])
            
            # Check constraints
            if p / n > 10:
                raise HighDimensionalInstabilityError(f"p/n ratio {p/n} > 10")
            
            # Initialize RNG
            rng = RNGWrapper()
            rng.reset(seed)
            np_rng = rng.get_generator()
            
            # Generate data
            data = generate_correlated_data(n, p, rho, dist_type, np_rng)
            
            params = {
                'n': n, 'p': p, 'rho': rho, 
                'distribution_type': dist_type, 
                'seed': seed, 'iteration': iteration
            }
            
            # Call callback
            result = callback(data, params)
            if not result:
                logger.warning(f"Callback returned False for seed {seed}. Stopping.")
                break
            
            yield params

def build_parameter_sweep(
    n_values: List[int],
    p_values: List[int],
    rho_values: List[float],
    dist_types: List[str],
    required_iterations: int,
    output_path: str
):
    """
    Build the parameter sweep CSV with Cartesian product of parameters.
    """
    import itertools
    
    # Create combinations
    combinations = list(itertools.product(n_values, p_values, rho_values, dist_types))
    
    # We need 'required_iterations' for each combination?
    # The task says: "iterate over the full Cartesian product ... AND distribution_type"
    # And "Dependency: Must read required_iterations ... If > 1000, create file"
    # And "Output data/sweep/params.csv with columns seed,n,p,rho,distribution_type,iteration"
    # This implies we run 'required_iterations' for EACH combination?
    # Or is 'required_iterations' the total number of seeds?
    # "The system MUST iterate over the full Cartesian product ... to generate every combination."
    # "Output ... with ... iteration".
    # This suggests: For each combination (n, p, rho, dist), we run 'required_iterations' times.
    
    base_dir = Path(output_path).parent.parent
    master_seed_path = base_dir / 'data' / 'sweep' / 'master_seed.txt'
    
    # Load or create master seed
    if master_seed_path.exists():
        with open(master_seed_path, 'r') as f:
            master_seed = int(f.read().strip())
    else:
        master_seed = 42
        master_seed_path.parent.mkdir(parents=True, exist_ok=True)
        with open(master_seed_path, 'w') as f:
            f.write(str(master_seed))
    
    current_seed = master_seed
    
    rows = []
    for n, p, rho, dist in combinations:
        for i in range(required_iterations):
            rows.append({
                'seed': current_seed,
                'n': n,
                'p': p,
                'rho': rho,
                'distribution_type': dist,
                'iteration': i
            })
            current_seed += 1
    
    # Write CSV
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['seed', 'n', 'p', 'rho', 'distribution_type', 'iteration'])
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Generated {len(rows)} parameter combinations.")

def main():
    parser = argparse.ArgumentParser(description="Generate data and parameter sweep")
    parser.add_argument('--n', type=int, help='Sample size (single run mode)')
    parser.add_argument('--p', type=int, help='Feature size (single run mode)')
    parser.add_argument('--rho', type=float, help='Correlation (single run mode)')
    parser.add_argument('--dist', type=str, choices=['normal', 't', 'skew_normal'], help='Distribution (single run mode)')
    parser.add_argument('--seed', type=int, help='Seed (single run mode)')
    parser.add_argument('--out', type=str, required=True, help='Output path for single run mode or sweep path')
    parser.add_argument('--sweep', action='store_true', help='Run sweep mode')
    
    args = parser.parse_args()
    
    if args.sweep:
        # Sweep mode
        n_values = [50, 100, 200, 500]
        p_values = [500, 1000, 2000, 5000]
        rho_values = [0, 0.1, 0.3, 0.5, 0.7, 0.9]
        dist_types = ['normal', 't', 'skew_normal']
        
        required_iterations = load_required_iterations()
        build_parameter_sweep(n_values, p_values, rho_values, dist_types, required_iterations, args.out)
    else:
        # Single run mode
        if not all([args.n, args.p, args.rho, args.dist, args.seed]):
            parser.error("Single run mode requires --n, --p, --rho, --dist, --seed")
        
        rng = RNGWrapper()
        rng.reset(args.seed)
        np_rng = rng.get_generator()
        
        data = generate_correlated_data(args.n, args.p, args.rho, args.dist, np_rng)
        
        params = {'n': args.n, 'p': args.p, 'rho': args.rho, 'distribution_type': args.dist}
        
        # Write metadata
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save data as npy? Or just metadata?
        # Task T018 says: "Write data/synthetic/{seed}.json containing sha256..."
        # So we write metadata.
        metadata_path = path.parent / f"{args.seed}.json"
        write_dataset_metadata(params, args.seed, str(metadata_path))
        
        # Optionally save data if needed
        data_path = path.parent / f"{args.seed}.npy"
        np.save(data_path, data)
        
        logger.info(f"Generated data for seed {args.seed} at {data_path}")

if __name__ == '__main__':
    main()
