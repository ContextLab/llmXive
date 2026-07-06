import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging
import json

from logger import get_logger

logger = get_logger(__name__)

def extract_psi4_energies(output_log: str) -> Dict[str, float]:
    """
    Extract total energy and D3 dispersion contribution from a Psi4 output log.
    
    Args:
        output_log: Path to the Psi4 output file.
        
    Returns:
        Dictionary with 'total_energy' and 'd3_energy' keys.
    """
    path = Path(output_log)
    if not path.exists():
        raise FileNotFoundError(f"Output file not found: {output_log}")
        
    total_energy = None
    d3_energy = None
    
    with open(path, 'r') as f:
        lines = f.readlines()
        
    # Look for total energy (usually in final lines or specific marker)
    for line in reversed(lines):
        if "Final Energy" in line or "Total Energy" in line:
            # Typical format: "Final Energy = -123.456789"
            try:
                parts = line.split('=')
                if len(parts) > 1:
                    total_energy = float(parts[1].strip().split()[0])
                    break
            except ValueError:
                continue
                
    # Look for D3 dispersion energy (often labeled as "Dispersion" or "D3")
    for line in lines:
        if "Dispersion Energy" in line or "D3 correction" in line:
            try:
                parts = line.split('=')
                if len(parts) > 1:
                    d3_energy = float(parts[1].strip().split()[0])
                    break
            except ValueError:
                continue
                
    if total_energy is None:
        raise ValueError(f"Could not find total energy in {output_log}")
    if d3_energy is None:
        # If D3 is not explicitly listed, it might be 0 or the user didn't enable it
        logger.warning(f"D3 energy not found in {output_log}, assuming 0.0")
        d3_energy = 0.0
        
    return {
        'total_energy': total_energy,
        'd3_energy': d3_energy
    }

def compute_statistics(energies: List[float]) -> Dict[str, float]:
    """
    Compute basic statistics for a list of energies.
    
    Args:
        energies: List of energy values.
        
    Returns:
        Dictionary with mean, std, min, max.
    """
    arr = np.array(energies)
    return {
        'mean': float(np.mean(arr)),
        'std': float(np.std(arr)),
        'min': float(np.min(arr)),
        'max': float(np.max(arr)),
        'count': len(energies)
    }

def calculate_metrics(
    ref_energies: List[float], 
    pred_energies: List[float]
) -> Dict[str, float]:
    """
    Calculate error metrics between reference and predicted energies.
    
    Args:
        ref_energies: Reference (CCSD(T)/CBS) energies.
        pred_energies: Predicted (DFT-D3) energies.
        
    Returns:
        Dictionary with MAE, RMSE, MSE, MSE (signed).
    """
    ref = np.array(ref_energies)
    pred = np.array(pred_energies)
    errors = pred - ref
    
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors**2)))
    mse_abs = float(np.mean(errors**2)) # Mean Squared Error (absolute)
    mse_signed = float(np.mean(errors)) # Mean Signed Error
    
    return {
        'mae': mae,
        'rmse': rmse,
        'mse': mse_abs,
        'signed_error_mean': mse_signed
    }

def bootstrap_analysis(
    ref_energies: List[float],
    pred_energies: List[float],
    n_replicates: int = 1000,
    seed: Optional[int] = None
) -> Dict[str, float]:
    """
    Perform bootstrap resampling to estimate confidence intervals for MAE.
    
    Args:
        ref_energies: Reference energies.
        pred_energies: Predicted energies.
        n_replicates: Number of bootstrap samples.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary with MAE, 95% CI lower, 95% CI upper.
    """
    if seed is not None:
        np.random.seed(seed)
        
    n = len(ref_energies)
    if n == 0:
        raise ValueError("No data provided for bootstrap analysis")
        
    boot_mae = []
    for _ in range(n_replicates):
        indices = np.random.choice(n, size=n, replace=True)
        ref_sample = np.array(ref_energies)[indices]
        pred_sample = np.array(pred_energies)[indices]
        errors = pred_sample - ref_sample
        mae = np.mean(np.abs(errors))
        boot_mae.append(mae)
        
    boot_mae = np.array(boot_mae)
    ci_lower = np.percentile(boot_mae, 2.5)
    ci_upper = np.percentile(boot_mae, 97.5)
    
    return {
        'mae': float(np.mean(boot_mae)),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'std': float(np.std(boot_mae))
    }

def analyze_and_export(
    psi4_outputs: List[str],
    reference_data: pd.DataFrame,
    output_path: str
) -> pd.DataFrame:
    """
    Analyze Psi4 outputs, compare with reference, and export results.
    
    Args:
        psi4_outputs: List of paths to Psi4 output files.
        reference_data: DataFrame with pair_id and reference_energy columns.
        output_path: Path to save the results CSV.
        
    Returns:
        DataFrame with analysis results.
    """
    results = []
    
    for out_file in psi4_outputs:
        try:
            energies = extract_psi4_energies(out_file)
            # Infer pair_id from filename (e.g., "pair_01.out" -> "pair_01")
            pair_id = Path(out_file).stem
            
            # Look up reference energy
            ref_row = reference_data[reference_data['pair_id'] == pair_id]
            if ref_row.empty:
                logger.warning(f"No reference energy found for {pair_id}, skipping")
                continue
            ref_energy = ref_row['reference_energy'].values[0]
            
            dft_total = energies['total_energy']
            d3_disp = energies['d3_energy']
            signed_err = dft_total - ref_energy
            
            results.append({
                'pair_id': pair_id,
                'reference_energy': ref_energy,
                'dft_total_energy': dft_total,
                'd3_dispersion_energy': d3_disp,
                'signed_error': signed_err
            })
        except Exception as e:
            logger.error(f"Failed to process {out_file}: {e}")
            
    df = pd.DataFrame(results)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Exported {len(df)} results to {output_path}")
    return df

def main():
    """
    Main entry point for the analyze_energies script.
    Expects arguments: 
      --outputs: glob pattern or list of Psi4 output files
      --refs: path to reference CSV
      --output: path to output CSV
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze DFT-D3 energies')
    parser.add_argument('--outputs', nargs='+', required=True, help='Psi4 output files')
    parser.add_argument('--refs', required=True, help='Path to reference CSV')
    parser.add_argument('--output', required=True, help='Output CSV path')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    # Load reference data
    ref_df = pd.read_csv(args.refs)
    
    # Analyze and export
    df = analyze_and_export(args.outputs, ref_df, args.output)
    
    # Compute and log metrics
    if not df.empty:
        metrics = calculate_metrics(
            df['reference_energy'].tolist(),
            df['dft_total_energy'].tolist()
        )
        logger.info(f"MAE: {metrics['mae']:.6f} Ha")
        logger.info(f"RMSE: {metrics['rmse']:.6f} Ha")
        logger.info(f"MSE (signed): {metrics['signed_error_mean']:.6f} Ha")
        
        # Bootstrap
        boot = bootstrap_analysis(
            df['reference_energy'].tolist(),
            df['dft_total_energy'].tolist(),
            seed=args.seed
        )
        logger.info(f"Bootstrap MAE CI: [{boot['ci_lower']:.6f}, {boot['ci_upper']:.6f}]")

if __name__ == '__main__':
    main()