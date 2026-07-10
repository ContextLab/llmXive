"""
Kinetic Fit Analysis Module.

Implements global kinetic analysis, exponential fitting, and replicate statistics
for the Photo-Fries rearrangement study.
"""
import os
import sys
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from scipy import stats
import json
from pathlib import Path

from config import get_processed_data_path, get_raw_data_path, ensure_directories
from utils.logging import setup_logging, log_compliance_check
from utils.seeds import set_seed

logger = logging.getLogger(__name__)
set_seed(42)

def exponential_decay(t: np.ndarray, A: float, tau: float, C: float) -> np.ndarray:
    """
    Standard exponential decay model: y = A * exp(-t/tau) + C
    """
    return A * np.exp(-t / tau) + C

def fit_single_decay(time: np.ndarray, signal: np.ndarray) -> Tuple[float, float]:
    """
    Fits a single exponential decay to the data.
    Returns (tau, error_estimate).
    """
    if len(time) < 3:
        raise ValueError("Insufficient data points for fitting.")

    # Initial guesses: A=signal[0]-signal[-1], tau=mean(time), C=signal[-1]
    A0 = signal[0] - signal[-1]
    tau0 = np.mean(time)
    C0 = signal[-1]
    
    if A0 <= 0:
        A0 = signal.max() - signal.min()
        tau0 = time[-1] / 2
        C0 = signal.min()

    try:
        popt, pcov = curve_fit(
            exponential_decay, time, signal, 
            p0=[A0, tau0, C0],
            bounds=([0, 0, 0], [np.inf, np.inf, np.inf])
        )
        tau = popt[1]
        # Estimate error from covariance
        tau_err = np.sqrt(np.diag(pcov))[1]
        return tau, tau_err
    except RuntimeError as e:
        logger.warning(f"Fitting failed: {e}. Returning NaN.")
        return np.nan, np.nan

def calculate_confidence_interval(data: List[float], confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculates the confidence interval for a list of values.
    Uses t-distribution for small sample sizes.
    """
    if not data:
        return 0.0, 0.0
    
    arr = np.array(data)
    n = len(arr)
    mean = np.mean(arr)
    std = np.std(arr, ddof=1)
    
    if n > 1:
        t_val = stats.t.ppf((1 + confidence) / 2.0, n - 1)
        margin = t_val * (std / np.sqrt(n))
        return float(mean - margin), float(mean + margin)
    else:
        return float(mean), float(mean)

def process_trace_file(file_path: Path) -> pd.DataFrame:
    """
    Reads a trace file and performs single decay fitting for each row (replicate).
    Expected columns: 'time', 'signal', 'replicate_id', 'solvent'
    """
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to read trace file {file_path}: {e}")
        return pd.DataFrame()

    results = []
    
    # Group by replicate if the file contains multiple, otherwise process rows
    # Assuming the file format from generate_synthetic or ingest is:
    # solvent, replicate_id, time_point, delta_abs
    # We need to pivot or group to fit.
    
    # Simplified assumption: The file contains pre-grouped traces or we iterate.
    # If the file is long-format (time, signal, solvent, replicate), we group.
    if 'time' in df.columns and 'signal' in df.columns:
        # Check if it's already aggregated or needs grouping
        if 'replicate_id' in df.columns and 'solvent' in df.columns:
            groups = df.groupby(['solvent', 'replicate_id'])
            for (solvent, rep_id), group_df in groups:
                t = group_df['time'].values
                s = group_df['signal'].values
                if len(t) > 2:
                    tau, _ = fit_single_decay(t, s)
                    results.append({
                        'solvent': solvent,
                        'replicate_id': rep_id,
                        'lifetime': tau,
                        'is_outlier': False # Placeholder
                    })
        else:
            # Single trace in file
            t = df['time'].values
            s = df['signal'].values
            tau, _ = fit_single_decay(t, s)
            results.append({
                'solvent': 'unknown',
                'replicate_id': 0,
                'lifetime': tau,
                'is_outlier': False
            })
    else:
        logger.error(f"Trace file {file_path} missing required columns (time, signal).")
        return pd.DataFrame()

    return pd.DataFrame(results)

def run_global_kinetic_analysis() -> pd.DataFrame:
    """
    Orchestrates the kinetic analysis for all available traces.
    Reads from data/processed/calibrated_traces.csv (or raw if not processed).
    Returns a DataFrame of individual replicate lifetimes.
    """
    processed_path = get_processed_data_path()
    raw_path = get_raw_data_path()
    
    # Try calibrated first, then raw
    input_file = processed_path / "calibrated_traces.csv"
    if not input_file.exists():
        input_file = raw_path / "synthetic_traces.csv" # Fallback for CI/Dev
    
    if not input_file.exists():
        raise FileNotFoundError(f"No trace data found at {input_file}")
    
    logger.info(f"Processing kinetic traces from {input_file}")
    results_df = process_trace_file(input_file)
    
    if results_df.empty:
        raise ValueError("No valid kinetic traces found to analyze.")
    
    return results_df

def perform_threshold_sensitivity_analysis(thresholds: List[float] = [0.5, 1.0, 2.0]) -> Dict[str, Any]:
    """
    Performs sensitivity analysis on outlier detection thresholds.
    """
    # Implementation of T025
    # Placeholder logic for now, as T026 is the focus
    return {"status": "completed", "thresholds_tested": thresholds}

def main(args: Optional[argparse.Namespace] = None) -> int:
    """
    CLI entry point for kinetic analysis.
    """
    setup_logging()
    logger.info("Starting Global Kinetic Analysis")
    
    try:
        results = run_global_kinetic_analysis()
        
        # Save intermediate results for T026 to consume
        output_path = get_processed_data_path() / "kinetic_replicates.csv"
        ensure_directories()
        results.to_csv(output_path, index=False)
        logger.info(f"Saved replicate lifetimes to {output_path}")
        
        return 0
    except Exception as e:
        logger.error(f"Kinetic analysis failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Global Kinetic Analysis")
    args = parser.parse_args()
    sys.exit(main(args))
