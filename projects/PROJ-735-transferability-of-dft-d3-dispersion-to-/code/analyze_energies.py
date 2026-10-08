"""
Energy analysis module for computing statistics, metrics, and bootstrap analysis
of DFT-D3 interaction energies.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging
import json
import os
import sys

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import calculate_metrics, bootstrap_resample, bootstrap_mae
from logger import get_logger, info, warning, error, critical

logger = get_logger(__name__)

def load_scaling_factor(filepath: str = "data/derived/scaling_factor.txt") -> float:
    """
    Load the optimal scaling factor from the derived file.
    """
    path = Path(filepath)
    if not path.exists():
        error(f"Scaling factor file not found: {filepath}")
        raise FileNotFoundError(f"Scaling factor file not found: {filepath}")
    
    content = path.read_text().strip()
    # Parse the first line or first number found
    try:
        # Expect format like "s = 1.234" or just "1.234"
        if "=" in content:
            value = float(content.split("=")[1].strip())
        else:
            value = float(content.split()[0])
        info(f"Loaded scaling factor s = {value}")
        return value
    except (ValueError, IndexError) as e:
        error(f"Failed to parse scaling factor from {filepath}: {e}")
        raise

def extract_psi4_energies(output_dir: str) -> List[Dict]:
    """
    Extract total energy and D3 dispersion contribution from Psi4 output files.
    Assumes output files are named <pair_id>.out in the specified directory.
    """
    results = []
    out_dir = Path(output_dir)
    
    if not out_dir.exists():
        error(f"Output directory not found: {output_dir}")
        return results
    
    for out_file in sorted(out_dir.glob("*.out")):
        pair_id = out_file.stem
        try:
            content = out_file.read_text()
            
            # Parse total energy (look for 'Total Energy' or similar)
            total_energy = None
            d3_energy = None
            
            for line in content.split('\n'):
                if 'Total Energy' in line or 'Final Energy' in line:
                    # Extract number after '='
                    if '=' in line:
                        try:
                            val = float(line.split('=')[-1].strip())
                            total_energy = val
                        except ValueError:
                            pass
                
                # Parse D3 dispersion energy (look for 'D3' or 'dispersion')
                if 'D3' in line and 'Energy' in line:
                    if '=' in line:
                        try:
                            val = float(line.split('=')[-1].strip())
                            d3_energy = val
                        except ValueError:
                            pass
                
                # Fallback: look for specific Psi4 output patterns
                if 'Dispersion energy' in line:
                    if '=' in line:
                        try:
                            val = float(line.split('=')[-1].strip())
                            d3_energy = val
                        except ValueError:
                            pass
            
            if total_energy is None:
                warning(f"Could not find total energy in {out_file}")
                continue
            
            if d3_energy is None:
                warning(f"Could not find D3 energy in {out_file}, using 0.0")
                d3_energy = 0.0
            
            results.append({
                'pair_id': pair_id,
                'dft_total_energy': total_energy,
                'd3_dispersion_energy': d3_energy
            })
            
        except Exception as e:
            error(f"Error parsing {out_file}: {e}")
            continue
    
    return results

def compute_statistics(energies_df: pd.DataFrame) -> Dict:
    """
    Compute basic statistics for the energy errors.
    """
    if 'signed_error' not in energies_df.columns:
        energies_df = energies_df.copy()
        energies_df['signed_error'] = energies_df['dft_total_energy'] - energies_df['reference_energy']
    
    errors = energies_df['signed_error'].values
    
    stats = {
        'mean_error': float(np.mean(errors)),
        'std_error': float(np.std(errors)),
        'min_error': float(np.min(errors)),
        'max_error': float(np.max(errors)),
        'n_samples': len(errors)
    }
    
    return stats

def calculate_metrics(
    reference: np.ndarray,
    predicted: np.ndarray
) -> Tuple[float, float, float]:
    """
    Calculate MAE, RMSE, and MSE between reference and predicted values.
    Returns (MAE, RMSE, MSE).
    """
    return calculate_metrics(reference, predicted)

def bootstrap_analysis(
    reference: np.ndarray,
    predicted: np.ndarray,
    n_replicates: int = 1000,
    random_state: int = 42
) -> Dict:
    """
    Perform bootstrap resampling to compute 95% confidence intervals for MAE.
    """
    np.random.seed(random_state)
    
    # Calculate original MAE
    original_mae = calculate_metrics(reference, predicted)[0]
    
    # Bootstrap resampling
    mae_samples = []
    for _ in range(n_replicates):
        indices = np.random.randint(0, len(reference), len(reference))
        ref_sample = reference[indices]
        pred_sample = predicted[indices]
        mae_sample = calculate_metrics(ref_sample, pred_sample)[0]
        mae_samples.append(mae_sample)
    
    mae_samples = np.array(mae_samples)
    ci_lower = float(np.percentile(mae_samples, 2.5))
    ci_upper = float(np.percentile(mae_samples, 97.5))
    
    return {
        'mae': float(original_mae),
        'mae_ci_lower': ci_lower,
        'mae_ci_upper': ci_upper,
        'mae_std': float(np.std(mae_samples))
    }

def analyze_and_export(
    input_csv: str,
    output_csv: str,
    stats_json: str,
    scaling_factor: Optional[float] = None
):
    """
    Main analysis function to compute metrics, perform bootstrap, and export results.
    """
    logger.info(f"Analyzing energies from {input_csv}")
    
    df = pd.read_csv(input_csv)
    
    # Ensure required columns exist
    required_cols = ['reference_energy', 'dft_total_energy', 'd3_dispersion_energy']
    for col in required_cols:
        if col not in df.columns:
            error(f"Missing required column: {col}")
            raise ValueError(f"Missing required column: {col}")
    
    # Compute signed error
    df['signed_error'] = df['dft_total_energy'] - df['reference_energy']
    
    # Apply scaling if provided
    if scaling_factor is not None:
        df['scaled_d3_energy'] = scaling_factor * df['d3_dispersion_energy']
        df['corrected_energy'] = df['dft_total_energy'] - df['d3_dispersion_energy'] + df['scaled_d3_energy']
        df['corrected_error'] = df['corrected_energy'] - df['reference_energy']
    else:
        df['corrected_energy'] = df['dft_total_energy']
        df['corrected_error'] = df['signed_error']
    
    # Export raw energies
    output_df = df[['pair_id', 'reference_energy', 'dft_total_energy', 'd3_dispersion_energy', 'signed_error']]
    if scaling_factor is not None:
        output_df['corrected_energy'] = df['corrected_energy']
        output_df['corrected_error'] = df['corrected_error']
    
    output_df.to_csv(output_csv, index=False)
    info(f"Exported raw energies to {output_csv}")
    
    # Compute statistics
    stats = compute_statistics(df)
    stats['scaling_factor_applied'] = scaling_factor is not None
    
    # Perform bootstrap analysis
    ref_vals = df['reference_energy'].values
    pred_vals = df['dft_total_energy'].values
    bootstrap_stats = bootstrap_analysis(ref_vals, pred_vals)
    
    stats['bootstrap'] = bootstrap_stats
    
    # Write statistics to JSON
    stats_path = Path(stats_json)
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    info(f"Exported statistics to {stats_json}")
    
    return df, stats

def main():
    """
    Main entry point for energy analysis.
    """
    # Default paths
    input_csv = "data/derived/raw_energies.csv"
    output_csv = "data/derived/raw_energies.csv"
    stats_json = "data/derived/energy_statistics.json"
    scaling_file = "data/derived/scaling_factor.txt"
    
    # Check if scaling factor exists
    scaling_factor = None
    if Path(scaling_file).exists():
        try:
            scaling_factor = load_scaling_factor(scaling_file)
            info(f"Applying scaling factor: {scaling_factor}")
        except Exception as e:
            warning(f"Could not load scaling factor: {e}")
    else:
        info("No scaling factor found, proceeding with raw energies")
    
    # Run analysis
    try:
        df, stats = analyze_and_export(input_csv, output_csv, stats_json, scaling_factor)
        info("Energy analysis completed successfully")
        
        # Print summary
        logger.info(f"Number of samples: {stats['n_samples']}")
        logger.info(f"Mean Error: {stats['mean_error']:.4f}")
        logger.info(f"MAE (raw): {stats['bootstrap']['mae']:.4f}")
        if scaling_factor:
            logger.info(f"MAE CI (95%): [{stats['bootstrap']['mae_ci_lower']:.4f}, {stats['bootstrap']['mae_ci_upper']:.4f}]")
            logger.info(f"Scaling factor applied: {scaling_factor}")
        
    except Exception as e:
        error(f"Energy analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()