import os
import sys
import hashlib
import json
import logging
import random
from typing import Optional, Tuple, Dict, Any, List
import pandas as pd
import numpy as np

from config import get_config_from_args
from utils.logger import get_logger, log_synthetic_fallback_trigger

# Constants for synthetic generation
ELEMENTS = ['Ni', 'Cr', 'Al', 'Co', 'Fe', 'Ti', 'Nb', 'Ta', 'Mo', 'W']
BASE_COMPOSITIONS = {
    'Ni': 0.50,
    'Cr': 0.20,
    'Al': 0.10,
    'Co': 0.10,
    'Fe': 0.05,
    'Ti': 0.02,
    'Nb': 0.01,
    'Ta': 0.01,
    'Mo': 0.005,
    'W': 0.005
}

logger = get_logger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_data_from_url(url: str, dest_path: str) -> Tuple[bool, str]:
    """
    Fetch data from a URL.
    Returns (success, message).
    """
    try:
        import requests
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        return True, f"Successfully downloaded {dest_path}"
    except Exception as e:
        return False, f"Failed to download from {url}: {str(e)}"

def generate_synthetic_data(n_samples: int = 100, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic alloy data for pipeline validation only.
    This is used when real data is unavailable to ensure the pipeline functions.
    
    The data mimics the structure of real oxidation resistance datasets:
    - Elemental compositions (wt%)
    - Thermodynamic descriptors (simulated)
    - Observed weight gain (simulated based on physical heuristics)
    
    Args:
        n_samples: Number of samples to generate
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with synthetic alloy data
    """
    random.seed(seed)
    np.random.seed(seed)
    
    data = []
    
    for i in range(n_samples):
        # Generate random composition variations around base
        composition = {}
        total = 0.0
        
        # Start with base and add random noise
        for elem in ELEMENTS:
            base_val = BASE_COMPOSITIONS.get(elem, 0.0)
            noise = np.random.normal(0, 0.05)
            val = max(0.0, base_val + noise)
            composition[elem] = val
            total += val
        
        # Normalize to sum to 1.0
        if total > 0:
            for elem in composition:
                composition[elem] /= total
        
        # Calculate simulated thermodynamic descriptors
        # Heuristic: Al and Cr are protective, others vary
        al_content = composition.get('Al', 0)
        cr_content = composition.get('Cr', 0)
        
        # Simulate oxide formation enthalpy (kJ/mol) - lower is better
        oxide_enthalpy = -300 * (al_content + 0.5 * cr_content) + np.random.normal(0, 20)
        
        # Simulate atomic radius weighted average (pm)
        atomic_radii = {'Ni': 124, 'Cr': 128, 'Al': 143, 'Co': 125, 'Fe': 126, 
                       'Ti': 147, 'Nb': 146, 'Ta': 146, 'Mo': 139, 'W': 139}
        weighted_radius = sum(composition.get(e, 0) * r for e, r in atomic_radii.items())
        
        # Simulate observed weight gain (mg/cm2) - lower is better
        # Heuristic: Higher Al/Cr -> lower weight gain, with noise
        base_weight_gain = 2.0 - 8.0 * (al_content + 0.6 * cr_content)
        weight_gain = max(0.1, base_weight_gain + np.random.normal(0, 0.3))
        
        row = {
            'sample_id': f'SYNTH_{i:04d}',
            'Ni': composition.get('Ni', 0),
            'Cr': composition.get('Cr', 0),
            'Al': composition.get('Al', 0),
            'Co': composition.get('Co', 0),
            'Fe': composition.get('Fe', 0),
            'Ti': composition.get('Ti', 0),
            'Nb': composition.get('Nb', 0),
            'Ta': composition.get('Ta', 0),
            'Mo': composition.get('Mo', 0),
            'W': composition.get('W', 0),
            'oxide_formation_enthalpy': oxide_enthalpy,
            'avg_atomic_radius': weighted_radius,
            'observed_weight_gain': weight_gain,
            'data_source': 'synthetic'
        }
        data.append(row)
    
    return pd.DataFrame(data)

def load_and_validate_data(file_path: str) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Load and validate data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Tuple of (DataFrame, message)
        If successful, DataFrame is returned with message "Success"
        If failed, None is returned with error message
    """
    if not os.path.exists(file_path):
        return None, f"File not found: {file_path}"
    
    try:
        df = pd.read_csv(file_path)
        
        # Basic schema validation
        required_cols = ['sample_id', 'Ni', 'Cr', 'Al', 'observed_weight_gain']
        missing_cols = [c for c in required_cols if c not in df.columns]
        
        if missing_cols:
            return None, f"Missing required columns: {missing_cols}"
        
        # Check for non-negative values
        if (df[['Ni', 'Cr', 'Al']] < 0).any().any():
            return None, "Negative composition values found"
        
        if (df['observed_weight_gain'] < 0).any():
            return None, "Negative weight gain values found"
        
        return df, "Success"
        
    except Exception as e:
        return None, f"Error loading file: {str(e)}"

def log_data_gap_report(output_path: str, reason: str, synthetic_samples: int) -> None:
    """
    Log a formal data gap report when real data is unavailable.
    
    Args:
        output_path: Path to the log file
        reason: Reason why real data was unavailable
        synthetic_samples: Number of synthetic samples generated
    """
    report = {
        "report_type": "DATA_GAP_REPORT",
        "timestamp": pd.Timestamp.now().isoformat(),
        "status": "SYNTHETIC_FALLBACK_TRIGGERED",
        "reason": reason,
        "synthetic_data_generated": True,
        "synthetic_sample_count": synthetic_samples,
        "warning": "RESULTS BASED ON SYNTHETIC DATA - NOT VALIDATED AGAINST REAL MEASUREMENTS",
        "recommendation": "Replace synthetic data with real experimental data before drawing conclusions."
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.warning(f"Data gap report written to {output_path}")
    logger.warning(f"Reason: {reason}")
    logger.warning(f"Generated {synthetic_samples} synthetic samples for pipeline validation.")

def fetch_data(output_dir: str, mode: str = 'local') -> Tuple[Optional[pd.DataFrame], bool]:
    """
    Main entry point for fetching data.
    Attempts to load real data; if unavailable, generates synthetic data.
    
    Args:
        output_dir: Directory to store data
        mode: 'ci' or 'local'
        
    Returns:
        Tuple of (DataFrame, used_synthetic)
    """
    os.makedirs(output_dir, exist_ok=True)
    real_data_path = os.path.join(output_dir, 'raw_oxidation_data.csv')
    gap_report_path = os.path.join(os.path.dirname(output_dir), 'logs', 'data_gap_report.txt')
    
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(gap_report_path), exist_ok=True)
    
    # Try to load real data first
    if os.path.exists(real_data_path):
        df, msg = load_and_validate_data(real_data_path)
        if df is not None:
            logger.info(f"Loaded real data from {real_data_path} ({len(df)} samples)")
            return df, False
        else:
            logger.warning(f"Real data validation failed: {msg}")
    
    # Real data unavailable - generate synthetic
    logger.info("Real data unavailable. Generating synthetic data for pipeline validation.")
    
    # Determine sample count based on mode
    n_samples = 500 if mode == 'ci' else 1000
    
    synthetic_df = generate_synthetic_data(n_samples=n_samples, seed=42)
    
    # Save synthetic data
    synthetic_df.to_csv(real_data_path, index=False)
    logger.info(f"Saved synthetic data to {real_data_path}")
    
    # Log the gap report
    log_data_gap_report(
        gap_report_path, 
        reason="Real data file not found or validation failed",
        synthetic_samples=n_samples
    )
    
    return synthetic_df, True

def main():
    """CLI entry point for data fetching."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch or generate alloy oxidation data')
    parser.add_argument('--mode', type=str, default='local', 
                      choices=['ci', 'local'],
                      help='Execution mode: ci (strict) or local (permissive)')
    parser.add_argument('--output-dir', type=str, default='data/raw',
                      help='Directory to store data')
    
    args = parser.parse_args()
    config = get_config_from_args(args)
    
    df, used_synthetic = fetch_data(args.output_dir, mode=args.mode)
    
    if df is None:
        logger.error("Failed to fetch or generate data")
        sys.exit(1)
    
    logger.info(f"Data ready: {len(df)} samples, synthetic={used_synthetic}")
    
    if used_synthetic:
        print("WARNING: Using synthetic data for pipeline validation only.")
        print("Results are not validated against real experimental measurements.")

if __name__ == '__main__':
    main()