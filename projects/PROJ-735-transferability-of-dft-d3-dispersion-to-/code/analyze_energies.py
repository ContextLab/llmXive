"""
Energy analysis module for User Story 1.

Implements T015, T016, T017, T018.
- Extracts total energy and D3 dispersion contribution.
- Computes MAE, RMSE, MSE, MSE (Mean Signed Error).
- Generates raw_energies.csv.
- Performs bootstrap resampling for MAE CI.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging
import json

from code.logger import get_logger
from code.utils import calculate_metrics, bootstrap_mae

logger = get_logger(__name__)

def analyze_and_export(
    results_df: pd.DataFrame,
    output_path: str,
    bootstrap_replicates: int = 1000
) -> None:
    """
    Analyze DFT-D3 energies against reference and export to CSV.

    Args:
        results_df: DataFrame with columns: pair_id, dft_total_energy, d3_dispersion_energy, reference_energy.
        output_path: Path to write the output CSV.
        bootstrap_replicates: Number of bootstrap samples for CI calculation (0 to skip).
    """
    logger.info(f"Analyzing {len(results_df)} energy results.")
    
    # Ensure required columns exist
    required_cols = ["pair_id", "dft_total_energy", "reference_energy"]
    for col in required_cols:
        if col not in results_df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Calculate Signed Error (DFT - Ref)
    results_df["signed_error"] = results_df["dft_total_energy"] - results_df["reference_energy"]
    
    # Calculate Metrics (MAE, RMSE, MSE, Mean Signed Error)
    ref = results_df["reference_energy"].values
    pred = results_df["dft_total_energy"].values
    
    metrics = calculate_metrics(ref, pred)
    logger.info(f"Global Metrics: {metrics}")
    
    # Bootstrap MAE CI if requested
    if bootstrap_replicates > 0:
        logger.info(f"Performing bootstrap resampling ({bootstrap_replicates} replicates) for MAE CI...")
        mae_ci = bootstrap_mae(ref, pred, n_replicates=bootstrap_replicates)
        logger.info(f"MAE 95% CI: [{mae_ci[0]:.4f}, {mae_ci[1]:.4f}]")
        
        # Store CI in a separate JSON file for downstream tasks (T019)
        ci_path = Path(output_path).parent / "mae_confidence_interval.json"
        with open(ci_path, 'w') as f:
            json.dump({
                "metric": "mae",
                "lower": float(mae_ci[0]),
                "upper": float(mae_ci[1]),
                "replicates": bootstrap_replicates
            }, f, indent=2)
        logger.info(f"MAE CI saved to {ci_path}")
    
    # Export to CSV
    output_df = results_df[["pair_id", "reference_energy", "dft_total_energy", "d3_dispersion_energy", "signed_error"]]
    output_df.to_csv(output_path, index=False)
    logger.info(f"Results exported to {output_path}")

def compute_statistics(
    ref_energies: np.ndarray,
    pred_energies: np.ndarray
) -> Dict[str, float]:
    """
    Compute error statistics between reference and predicted energies.

    Returns dict with 'mae', 'rmse', 'mse', 'mse_signed'.
    """
    return calculate_metrics(ref_energies, pred_energies)

def bootstrap_analysis(
    ref_energies: np.ndarray,
    pred_energies: np.ndarray,
    n_replicates: int = 1000
) -> Dict[str, Tuple[float, float]]:
    """
    Perform bootstrap resampling to compute confidence intervals for error metrics.

    Returns dict with metric names as keys and (lower, upper) CI tuples.
    """
    # Currently we focus on MAE as per T018
    mae_ci = bootstrap_mae(ref_energies, pred_energies, n_replicates=n_replicates)
    return {
        "mae": mae_ci
    }

def extract_psi4_energies(output_files: List[str]) -> pd.DataFrame:
    """
    Extract total energy and D3 dispersion contribution from Psi4 output files.
    
    This function implements T015: parsing Psi4 output to retrieve:
    - Total energy (E_total)
    - D3 dispersion energy (E_disp)
    
    Args:
        output_files: List of paths to Psi4 output files (.out).
        
    Returns:
        DataFrame with columns: pair_id, dft_total_energy, d3_dispersion_energy.
    """
    logger.info(f"Extracting energies from {len(output_files)} Psi4 output files.")
    
    results = []
    
    for file_path in output_files:
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            continue
        
        # Extract pair_id from filename (expected format: pair_XX.out or similar)
        pair_id = path.stem
        
        dft_total = None
        d3_dispersion = None
        
        try:
            with open(path, 'r') as f:
                lines = f.readlines()
            
            # Parse Psi4 output for final energy
            # Psi4 typically prints "Final Energy" or "Total Energy"
            for line in lines:
                line = line.strip()
                
                # Look for final energy (usually the last energy printed)
                if "Final Energy" in line or "Total Energy" in line:
                    # Extract the numeric value
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part in ["Final", "Total", "Energy", "="]:
                            continue
                        try:
                            val = float(part)
                            dft_total = val
                        except ValueError:
                            pass
                
                # Look for D3 dispersion contribution
                # Psi4-D3 typically prints "Dispersion energy" or "D3 contribution"
                if "Dispersion" in line or "D3" in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part in ["Dispersion", "D3", "energy", "contribution", "="]:
                            continue
                        try:
                            val = float(part)
                            # D3 energy is typically negative and small
                            if d3_dispersion is None or abs(val) < abs(d3_dispersion):
                                d3_dispersion = val
                        except ValueError:
                            pass
            
            # If we couldn't find D3 explicitly, try to find it in the energy breakdown
            if d3_dispersion is None:
                for line in lines:
                    if "Dispersion correction" in line or "S6" in line or "s6" in line:
                        # Try to parse the number after the keyword
                        parts = line.split()
                        for part in parts:
                            try:
                                val = float(part)
                                d3_dispersion = val
                                break
                            except ValueError:
                                continue
                        if d3_dispersion is not None:
                            break
            
            if dft_total is None:
                logger.warning(f"Could not find total energy in {file_path}")
                continue
            
            if d3_dispersion is None:
                logger.warning(f"Could not find D3 dispersion energy in {file_path}, setting to 0.0")
                d3_dispersion = 0.0
            
            results.append({
                "pair_id": pair_id,
                "dft_total_energy": dft_total,
                "d3_dispersion_energy": d3_dispersion
            })
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            continue
    
    df = pd.DataFrame(results)
    logger.info(f"Successfully extracted {len(df)} energy entries.")
    return df

def main():
    """
    Main entry point for energy analysis.
    
    This script is intended to be run after Psi4 calculations complete.
    It extracts energies from Psi4 output files, compares with reference,
    and exports results to CSV.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze DFT-D3 energies from Psi4 output")
    parser.add_argument("--input-dir", type=str, required=True, 
                        help="Directory containing Psi4 output files (.out)")
    parser.add_argument("--output", type=str, required=True,
                        help="Path to output CSV file")
    parser.add_argument("--bootstrap", type=int, default=1000,
                        help="Number of bootstrap replicates for MAE CI (default: 1000)")
    parser.add_argument("--reference-csv", type=str, required=True,
                        help="Path to CSV containing reference energies (pair_id, reference_energy)")
    
    args = parser.parse_args()
    
    # Setup logging
    configure_logging()
    
    # Load reference energies
    logger.info(f"Loading reference energies from {args.reference_csv}")
    ref_df = pd.read_csv(args.reference_csv)
    
    if "pair_id" not in ref_df.columns or "reference_energy" not in ref_df.columns:
        raise ValueError("Reference CSV must contain 'pair_id' and 'reference_energy' columns")
    
    # Extract energies from Psi4 outputs
    input_dir = Path(args.input_dir)
    output_files = list(input_dir.glob("*.out"))
    
    if not output_files:
        raise FileNotFoundError(f"No .out files found in {input_dir}")
    
    energies_df = extract_psi4_energies([str(f) for f in output_files])
    
    # Merge with reference data
    merged_df = pd.merge(energies_df, ref_df, on="pair_id", how="inner")
    
    if len(merged_df) == 0:
        raise ValueError("No matching pair_ids between Psi4 outputs and reference data")
    
    logger.info(f"Merged {len(merged_df)} entries for analysis.")
    
    # Perform analysis and export
    analyze_and_export(
        merged_df,
        args.output,
        bootstrap_replicates=args.bootstrap
    )
    
    logger.info("Analysis complete.")

if __name__ == "__main__":
    main()