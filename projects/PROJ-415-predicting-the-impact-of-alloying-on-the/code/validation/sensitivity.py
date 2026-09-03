import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import REPORTS_DIR, DATA_DIR
from utils.logging import get_logger

logger = get_logger(__name__)

# Constants for the sensitivity sweep
THRESHOLD_START = 0.45
THRESHOLD_END = 0.55
THRESHOLD_STEP = 0.01

def get_pure_host_activation_energy(df: pd.DataFrame, host_symbol: str) -> float:
    """
    Retrieve the measured activation energy of the pure host metal (0 at.% concentration).
    If missing, perform linear interpolation.
    """
    host_rows = df[df['host_symbol'] == host_symbol]
    
    if host_rows.empty:
        raise ValueError(f"No data found for host metal: {host_symbol}")

    # Check for 0 at.% row
    zero_conc = host_rows[host_rows['concentration'] == 0.0]
    if not zero_conc.empty:
        return float(zero_conc.iloc[0]['activation_energy'])

    # If 0 at.% is missing, interpolate
    if len(host_rows) < 2:
        raise ValueError(f"Insufficient data points for {host_symbol} to interpolate pure host energy.")

    sorted_host = host_rows.sort_values('concentration')
    # Interpolate linearly. We need to extrapolate to 0 if the lowest concentration is > 0.
    # Pandas interpolate with 'linear' fills NaNs between known values. To extrapolate to 0,
    # we can use np.interp or fit a line. The spec says 'interpolate', but strictly 0 might be outside.
    # We will use np.interp which extrapolates if we provide the range, but let's stick to pandas logic
    # by ensuring we have points around 0 or using the trend.
    # A robust way: fit a line to the first few points and evaluate at 0.
    
    x = sorted_host['concentration'].values
    y = sorted_host['activation_energy'].values
    
    # Simple linear extrapolation to 0 using the first two points if 0 is not present
    # This is safer than pandas interpolate which might not fill the NaN at 0 if 0 is outside the range
    if len(x) >= 2:
        slope = (y[1] - y[0]) / (x[1] - x[0])
        intercept = y[0] - slope * x[0]
        pure_energy = intercept
    else:
        raise ValueError(f"Cannot interpolate pure host energy for {host_symbol} with < 2 data points.")
        
    return float(pure_energy)

def calculate_baseline_shift(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate baseline shift: measured_E_solute - measured_E_pure_host.
    Adds a 'baseline_shift' column to the dataframe.
    """
    shifts = []
    for idx, row in df.iterrows():
        try:
            host = row['host_symbol']
            # The solute energy is just the row's activation_energy
            solute_energy = row['activation_energy']
            pure_host_energy = get_pure_host_activation_energy(df, host)
            shift = solute_energy - pure_host_energy
            shifts.append(shift)
        except Exception as e:
            logger.warning(f"Could not calculate shift for row {idx}: {e}")
            shifts.append(np.nan)
    
    df = df.copy()
    df['baseline_shift'] = shifts
    return df

def run_sensitivity_sweep(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Sweep classification threshold from 0.45 to 0.55 eV.
    For each threshold, calculate the classification rate of "significant diffusion slowing".
    """
    results = []
    thresholds = np.arange(THRESHOLD_START, THRESHOLD_END + THRESHOLD_STEP, THRESHOLD_STEP)
    
    # Ensure baseline_shift is calculated
    if 'baseline_shift' not in df.columns:
        df = calculate_baseline_shift(df)
    
    # Filter out NaN shifts for calculation
    valid_df = df.dropna(subset=['baseline_shift'])
    
    if valid_df.empty:
        logger.warning("No valid data for sensitivity sweep after dropping NaNs.")
        return results

    for thresh in thresholds:
        # Classification: "significant diffusion slowing" if baseline_shift > threshold
        # Note: The spec implies slowing means the solute energy is higher (positive shift) or lower?
        # "Slowing" usually implies higher activation energy.
        # We assume positive shift (solute > host) indicates slowing.
        significant_count = (valid_df['baseline_shift'] > thresh).sum()
        total_count = len(valid_df)
        
        if total_count == 0:
            rate = 0.0
        else:
            rate = significant_count / total_count
        
        results.append({
            'threshold_eV': round(thresh, 2),
            'classification_rate': rate,
            'count_significant': int(significant_count),
            'total_count': int(total_count)
        })
    
    return results

def calculate_stability_metric(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate the Standard Deviation (SD) and Mean of the classification rates.
    """
    if not results:
        return {'stability_sd': 0.0, 'mean_classification_rate': 0.0}
    
    rates = [r['classification_rate'] for r in results]
    sd = np.std(rates, ddof=1) if len(rates) > 1 else 0.0
    mean_rate = np.mean(rates)
    
    return {
        'stability_sd': float(sd),
        'mean_classification_rate': float(mean_rate)
    }

def save_sensitivity_sweep_csv(results: List[Dict[str, Any]], stability_metrics: Dict[str, float], output_path: Path) -> None:
    """
    Save the sensitivity sweep results to a CSV file.
    Format: threshold, classification_rate, stability_metric (SD), mean_rate
    The stability metric (SD) and mean rate are constant for all rows as they describe the whole sweep.
    """
    output_df = pd.DataFrame(results)
    output_df['stability_sd'] = stability_metrics['stability_sd']
    output_df['mean_classification_rate'] = stability_metrics['mean_classification_rate']
    
    # Reorder columns for clarity
    cols = ['threshold_eV', 'classification_rate', 'stability_sd', 'mean_classification_rate', 'count_significant', 'total_count']
    # Only keep existing columns
    cols = [c for c in cols if c in output_df.columns]
    output_df = output_df[cols]
    
    output_df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity sweep CSV saved to: {output_path}")

def main():
    """
    Main entry point for the sensitivity analysis task T048.
    Loads curated data, runs the sweep, calculates stability, and saves the CSV.
    """
    ensure_dir = REPORTS_DIR
    ensure_dir.mkdir(parents=True, exist_ok=True)
    
    curated_path = DATA_DIR / 'curated' / 'filtered.csv'
    if not curated_path.exists():
        raise FileNotFoundError(f"Curated data not found at {curated_path}. Run T014 first.")
    
    logger.info(f"Loading curated data from {curated_path}")
    df = pd.read_csv(curated_path)
    
    logger.info("Running sensitivity sweep (0.45 - 0.55 eV)...")
    sweep_results = run_sensitivity_sweep(df)
    
    if not sweep_results:
        logger.warning("Sensitivity sweep produced no results. Saving empty CSV.")
        # Save empty CSV with headers
        pd.DataFrame(columns=['threshold_eV', 'classification_rate', 'stability_sd', 'mean_classification_rate']).to_csv(
            ensure_dir / 'sensitivity_sweep.csv', index=False
        )
        return

    stability = calculate_stability_metric(sweep_results)
    logger.info(f"Stability metrics calculated: SD={stability['stability_sd']:.4f}, Mean={stability['mean_classification_rate']:.4f}")
    
    output_csv = ensure_dir / 'sensitivity_sweep.csv'
    save_sensitivity_sweep_csv(sweep_results, stability, output_csv)
    
    # Also update the main validation report if it exists, or create a snippet
    # (T034 handles the main JSON report, this task focuses on the CSV)
    logger.info("Task T048 completed successfully.")

if __name__ == '__main__':
    main()
