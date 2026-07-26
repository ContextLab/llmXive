"""
Feasibility Check Module (Task T011).

This module performs a pilot sample analysis to estimate complexity variance
and determine the required sample size for 0.8 statistical power within
a 6-hour pipeline limit.

It fetches metadata ONLY (N=50) from codeparrot/github-code to estimate
effect size without downloading full files.

If the calculated N exceeds the max feasible chunks for the time limit,
it caps N, logs a warning, and proceeds with the capped value.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import from project API surface
from config import get_config, ensure_dirs, set_seed
from utils.logging import get_logger, PipelineError

# Constants
PILOT_SAMPLE_SIZE = 50
MAX_PIPELINE_HOURS = 6
MAX_PIPELINE_SECONDS = MAX_PIPELINE_HOURS * 3600
TARGET_POWER = 0.8
ALPHA = 0.05
ESTIMATED_CHUNK_PROCESSING_TIME_SECONDS = 120  # Conservative estimate for full pipeline per chunk

logger = get_logger(__name__)


def fetch_pilot_metadata() -> Tuple[list, int]:
    """
    Fetch metadata for a pilot sample of code chunks from codeparrot/github-code.
    Uses streaming to avoid downloading full files.

    Returns:
        Tuple of (list of metadata dicts, total estimated chunks available)
    """
    logger.info(f"Fetching pilot sample of {PILOT_SAMPLE_SIZE} chunks from codeparrot/github-code...")
    
    try:
        from datasets import load_dataset
        
        # Load dataset in streaming mode, filtering for Python and Java
        # We only need metadata (path, size, language) for variance estimation
        dataset = load_dataset(
            "codeparrot/github-code",
            split="train",
            streaming=True,
            trust_remote_code=True
        )
        
        # Filter for Python and Java
        filtered = dataset.filter(
            lambda x: x.get('language', '').lower() in ['python', 'java']
        )
        
        pilot_data = []
        count = 0
        
        for item in filtered:
            if count >= PILOT_SAMPLE_SIZE:
                break
            
            # Extract relevant metadata for complexity estimation
            # We use file size as a proxy for complexity in the pilot phase
            # since full static analysis requires the full file content
            metadata = {
                'path': item.get('path', ''),
                'language': item.get('language', ''),
                'size': item.get('size', 0),
                'repo': item.get('repo', '')
            }
            pilot_data.append(metadata)
            count += 1
        
        # Estimate total available chunks (approximate based on pilot rate)
        # In a real scenario, we might query the dataset info API, but for now
        # we'll use a conservative estimate based on the dataset description
        estimated_total = 1000000  # Placeholder, will be refined if needed
        
        logger.info(f"Successfully fetched {len(pilot_data)} pilot samples")
        return pilot_data, estimated_total
        
    except Exception as e:
        logger.error(f"ERROR: Failed to fetch dataset metadata: {str(e)}")
        raise PipelineError(f"Dataset fetch failed: {str(e)}")


def estimate_variance_and_effect_size(pilot_data: list) -> Dict[str, float]:
    """
    Estimate variance and effect size from pilot metadata.
    
    Uses file size as a proxy for complexity in the pilot phase.
    In the full pipeline, this will be replaced by actual complexity metrics.
    
    Returns:
        Dictionary with variance and effect size estimates
    """
    if not pilot_data:
        raise PipelineError("No pilot data available for variance estimation")
    
    sizes = [item['size'] for item in pilot_data if item.get('size', 0) > 0]
    
    if len(sizes) < 2:
        logger.warning("Insufficient pilot data for variance estimation. Using default estimates.")
        # Default conservative estimates
        return {
            'variance': 1.0,
            'effect_size': 0.5,  # Medium effect size (Cohen's d)
            'mean': 1000.0
        }
    
    # Calculate variance
    mean_size = sum(sizes) / len(sizes)
    variance = sum((x - mean_size) ** 2 for x in sizes) / (len(sizes) - 1)
    
    # Estimate effect size (Cohen's d) - assume we're comparing to a baseline
    # For feasibility, we use a conservative medium effect size if variance is low
    if variance < 1e-6:
        effect_size = 0.5  # Medium effect size
    else:
        # Use coefficient of variation as a proxy for effect size
        cv = (variance ** 0.5) / mean_size if mean_size > 0 else 0.5
        effect_size = max(0.2, min(1.0, cv))  # Clamp between small and large
    
    return {
        'variance': variance,
        'effect_size': effect_size,
        'mean': mean_size
    }


def calculate_required_sample_size(effect_size: float, power: float = TARGET_POWER, alpha: float = ALPHA) -> int:
    """
    Calculate required sample size for given power and effect size.
    
    Uses standard power analysis formula for two-sample t-test.
    """
    if effect_size <= 0:
        return 1000000  # Return very large number if effect size is zero or negative
    
    # Approximation for sample size per group (two-sided t-test)
    # n = 2 * ((Z_alpha + Z_beta) / effect_size)^2
    # Z_alpha for alpha=0.05 is ~1.96, Z_beta for power=0.8 is ~0.84
    from math import sqrt
    
    z_alpha = 1.96  # For 95% confidence
    z_beta = 0.84   # For 80% power
    
    n_per_group = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return int(n_per_group * 2)  # Total sample size (both groups)


def calculate_max_feasible_chunks() -> int:
    """
    Calculate the maximum number of chunks that can be processed within
    the 6-hour pipeline limit.
    
    Returns:
        Maximum feasible sample size
    """
    # Estimate based on conservative processing time per chunk
    # This includes download, preprocessing, inference, and analysis
    max_chunks = MAX_PIPELINE_SECONDS // ESTIMATED_CHUNK_PROCESSING_TIME_SECONDS
    return max(max_chunks, 1)  # At least 1 chunk


def generate_feasibility_report(
    required_n: int,
    max_feasible_n: int,
    pilot_stats: Dict[str, float],
    estimated_total: int
) -> Dict[str, Any]:
    """
    Generate the feasibility report based on calculations.
    
    Returns:
        Dictionary containing the feasibility report
    """
    if required_n > max_feasible_n:
        # Study is underpowered - cap to max feasible
        status = "capped"
        capped_n = max_feasible_n
        power_limitation = "Study underpowered; capped to max feasible"
        proceed_flag = True
        
        logger.warning("WARNING: Study underpowered; capping N to max feasible")
        logger.warning(f"Required N ({required_n}) > Max feasible N ({max_feasible_n})")
    else:
        # Study is feasible
        status = "feasible"
        capped_n = required_n
        power_limitation = None
        proceed_flag = True
        
        logger.info(f"Study is feasible with N={required_n}")
    
    report = {
        "status": status,
        "capped_N": capped_n,
        "power_limitation": power_limitation,
        "proceed_flag": proceed_flag,
        "pilot_sample_size": PILOT_SAMPLE_SIZE,
        "pilot_variance": pilot_stats.get('variance', 0),
        "pilot_effect_size": pilot_stats.get('effect_size', 0),
        "pilot_mean": pilot_stats.get('mean', 0),
        "required_n_for_power": required_n,
        "max_feasible_n": max_feasible_n,
        "estimated_total_chunks": estimated_total,
        "pipeline_time_limit_hours": MAX_PIPELINE_HOURS,
        "estimated_processing_time_per_chunk_seconds": ESTIMATED_CHUNK_PROCESSING_TIME_SECONDS
    }
    
    return report


def write_feasibility_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Write the feasibility report to a JSON file.
    
    Args:
        report: The feasibility report dictionary
        output_path: Path to the output file
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Feasibility report written to {output_path}")


def main():
    """
    Main entry point for the feasibility check.
    
    This function:
    1. Fetches pilot metadata (N=50) from codeparrot/github-code
    2. Estimates variance and effect size
    3. Calculates required sample size for 0.8 power
    4. Calculates max feasible chunks within 6-hour limit
    5. Caps N if necessary and generates report
    6. Writes report to data/results/feasibility_report.json
    """
    logger.info("Starting feasibility check (Task T011)...")
    
    # Set random seed for reproducibility
    config = get_config()
    set_seed(config.get('random_seed', 42))
    
    # Ensure directories exist
    ensure_dirs()
    
    # Define output path
    output_path = Path(config['data_results_dir']) / "feasibility_report.json"
    
    try:
        # Step 1: Fetch pilot metadata
        pilot_data, estimated_total = fetch_pilot_metadata()
        
        if not pilot_data:
            raise PipelineError("Failed to fetch pilot data")
        
        # Step 2: Estimate variance and effect size
        pilot_stats = estimate_variance_and_effect_size(pilot_data)
        logger.info(f"Pilot variance estimate: {pilot_stats['variance']:.4f}")
        logger.info(f"Pilot effect size estimate: {pilot_stats['effect_size']:.4f}")
        
        # Step 3: Calculate required sample size
        required_n = calculate_required_sample_size(pilot_stats['effect_size'])
        logger.info(f"Required sample size for 0.8 power: {required_n}")
        
        # Step 4: Calculate max feasible chunks
        max_feasible_n = calculate_max_feasible_chunks()
        logger.info(f"Max feasible sample size (6h limit): {max_feasible_n}")
        
        # Step 5: Generate report (with capping if necessary)
        report = generate_feasibility_report(
            required_n=required_n,
            max_feasible_n=max_feasible_n,
            pilot_stats=pilot_stats,
            estimated_total=estimated_total
        )
        
        # Step 6: Write report
        write_feasibility_report(report, output_path)
        
        logger.info("Feasibility check completed successfully.")
        logger.info(f"Proceed flag: {report['proceed_flag']}")
        
        if report['status'] == 'capped':
            logger.warning("WARNING: Study capped to max feasible size. Results may be underpowered.")
        
        return report
        
    except Exception as e:
        logger.error(f"ERROR: Feasibility check failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
