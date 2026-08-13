"""
T029b: Critical Statistical Prep - A Priori Power Analysis for TOST Test.

This module performs an a priori power analysis to estimate the required sample size
and detectable effect size for the Two One-Sided Tests (TOST) equivalence test.
It uses pilot data from the extraction phase (T013) to estimate variance.

Output: data/metrics/power_analysis.json
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
from scipy import stats

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.extract_latents import load_config as load_extract_config
from utils.validators import validate_json_file

# Constants
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
DEFAULT_TOST_DELTA = 0.05  # Equivalence margin for TOST

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_pilot_data() -> pd.DataFrame:
    """
    Load the raw extracted data from T013 (extract_latents.py) to estimate variance.
    This file is expected to be at data/processed/latents_raw.parquet or similar.
    """
    config = load_extract_config()
    # The extraction task outputs to data/processed/latents_raw.parquet usually,
    # or we look for the specific output defined in config.
    # Based on T013 description: "output raw Parquet".
    # Let's assume standard path derived from config or default.
    
    # Attempt to find the file in data/processed
    processed_dir = project_root / "data" / "processed"
    if not processed_dir.exists():
        raise FileNotFoundError(f"Processed data directory not found: {processed_dir}")
    
    # Look for the raw extraction output. 
    # T013 outputs raw Parquet. T014b samples it.
    # We need the raw or the sampled data to estimate variance.
    # Since T014b is listed as completed, we might use the sampled data, 
    # but for 'a priori' analysis on the *planned* sample size, 
    # we use the variance from the pilot (raw or sampled).
    
    possible_files = [
        "latents_raw.parquet",
        "latents_sampled.parquet",
        "preprocessed_data.parquet"
    ]
    
    data_file = None
    for fname in possible_files:
        fpath = processed_dir / fname
        if fpath.exists():
            data_file = fpath
            break
    
    if data_file is None:
        # Fallback: check if config specifies the path
        raw_path = config.get('data', {}).get('raw_path')
        if raw_path and Path(raw_path).exists():
            data_file = Path(raw_path)
        else:
            raise FileNotFoundError(
                "Could not find pilot data file in data/processed/. "
                "Ensure T013 (extract_latents.py) has been run successfully."
            )
    
    logger.info(f"Loading pilot data from: {data_file}")
    df = pd.read_parquet(data_file)
    
    # Validate required column for variance estimation
    if 'latent_delta_magnitude' not in df.columns:
        raise ValueError(
            f"Pilot data missing 'latent_delta_magnitude' column. "
            f"Columns found: {df.columns.tolist()}"
        )
    
    # Drop NaNs
    df = df.dropna(subset=['latent_delta_magnitude'])
    
    if len(df) < 2:
        raise ValueError("Pilot data has insufficient rows for variance estimation.")
    
    return df

def estimate_variance(df: pd.DataFrame) -> float:
    """
    Estimate the population variance (sigma^2) from the pilot data.
    """
    var = df['latent_delta_magnitude'].var(ddof=1)
    logger.info(f"Estimated variance (sigma^2) from pilot: {var:.6f}")
    return var

def calculate_tost_sample_size(
    variance: float,
    delta: float,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER
) -> Dict[str, Any]:
    """
    Calculate the required sample size for a TOST equivalence test.
    
    We approximate the TOST sample size using the formula for a one-sample
    equivalence test or two-sample depending on the design. 
    Given the context of "latent delta magnitude", we assume we are testing
    if the mean delta is within [-delta, +delta] against a null of 0 (or similar).
    
    Formula approximation for one-sample TOST (or paired):
    n = 2 * ( (z_{1-alpha} + z_{power})^2 * sigma^2 ) / ( (delta - |mu|)^2 )
    
    For a conservative 'a priori' analysis, we assume mu=0 (best case for power)
    or a small effect. If we assume the null is true (no difference), we calculate
    the sample size needed to detect equivalence if the true mean is 0.
    
    However, a more robust approach for TOST when the true mean is unknown is
    to assume a specific effect size (e.g., mu = delta/2) or use the worst case.
    
    Here we use the standard approximation for equivalence margin delta:
    n = ( (z_{1-alpha} + z_{power})^2 * 2 * sigma^2 ) / ( (delta - mu_diff)^2 )
    
    Assuming we want to prove equivalence to 0 (mu_diff = 0):
    n = ( (z_{1-alpha} + z_{power})^2 * 2 * sigma^2 ) / ( delta^2 )
    
    Note: TOST is two one-sided tests. The critical value is z_{1-alpha}.
    """
    z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)
    
    # Assume we are testing mean difference = 0 with margin delta
    # The denominator is the square of the distance from the true mean to the margin
    # If we assume true mean is 0, distance is delta.
    numerator = (z_alpha + z_beta) ** 2 * 2 * variance
    denominator = delta ** 2
    
    n = numerator / denominator
    n_rounded = int(np.ceil(n))
    
    return {
        "estimated_variance": variance,
        "equivalence_margin_delta": delta,
        "alpha": alpha,
        "power": power,
        "z_alpha": z_alpha,
        "z_beta": z_beta,
        "minimum_detectable_effect_size": delta, # In this context, the margin
        "required_sample_size": n_rounded,
        "formula_assumption": "One-sample TOST assuming true mean=0"
    }

def calculate_minimum_detectable_effect(
    n: int,
    variance: float,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER
) -> float:
    """
    Given a fixed sample size, calculate the minimum detectable effect size (MDES)
    or the effective equivalence margin delta that can be detected with the given power.
    """
    z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)
    
    # Rearranging the sample size formula:
    # n = ( (z_alpha + z_beta)^2 * 2 * sigma^2 ) / delta^2
    # delta = sqrt( ( (z_alpha + z_beta)^2 * 2 * sigma^2 ) / n )
    
    delta = np.sqrt( ((z_alpha + z_beta) ** 2 * 2 * variance) / n )
    return delta

def run_power_analysis(
    output_path: Optional[Path] = None,
    delta: float = DEFAULT_TOST_DELTA
) -> Dict[str, Any]:
    """
    Main function to run the power analysis and save results.
    """
    if output_path is None:
        output_path = project_root / "data" / "metrics" / "power_analysis.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting A Priori Power Analysis for TOST...")
    
    # 1. Load Pilot Data
    df = load_pilot_data()
    
    # 2. Estimate Variance
    variance = estimate_variance(df)
    
    # 3. Calculate Required Sample Size for TOST
    # We assume we want to detect equivalence within +/- delta
    sample_size_results = calculate_tost_sample_size(
        variance=variance,
        delta=delta,
        alpha=DEFAULT_ALPHA,
        power=DEFAULT_POWER
    )
    
    # 4. Calculate MDES if we were to use the current pilot size (or a target size)
    # Let's calculate MDES for the current pilot size as a sanity check
    pilot_n = len(df)
    mdes = calculate_minimum_detectable_effect(
        n=pilot_n,
        variance=variance,
        alpha=DEFAULT_ALPHA,
        power=DEFAULT_POWER
    )
    
    results = {
        "analysis_type": "a_priori_power_analysis_tost",
        "timestamp": str(pd.Timestamp.now()),
        "pilot_data_source": str(df), # Just a placeholder, real source in log
        "pilot_sample_size": pilot_n,
        "parameters": {
            "alpha": DEFAULT_ALPHA,
            "power": DEFAULT_POWER,
            "equivalence_margin_delta": delta
        },
        "statistics": {
            "estimated_variance": variance,
            "estimated_std_dev": np.sqrt(variance),
            "pilot_mdes": mdes
        },
        "recommendations": {
            "minimum_sample_size_for_power": sample_size_results["required_sample_size"],
            "justification": f"Based on pilot variance {variance:.6f} and TOST margin {delta}"
        }
    }
    
    # 5. Save to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Power analysis complete. Results saved to: {output_path}")
    logger.info(f"Recommended minimum sample size: {results['recommendations']['minimum_sample_size_for_power']}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Run A Priori Power Analysis for TOST")
    parser.add_argument(
        "--delta", 
        type=float, 
        default=DEFAULT_TOST_DELTA, 
        help="Equivalence margin (delta) for TOST"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None, 
        help="Output path for power_analysis.json"
    )
    args = parser.parse_args()
    
    output_path = Path(args.output) if args.output else None
    
    try:
        results = run_power_analysis(output_path=output_path, delta=args.delta)
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
