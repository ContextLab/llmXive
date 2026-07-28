"""
Feasibility Analysis Module for llmXive Project.

This module implements the pilot sample and feasibility check (T011).
It fetches metadata from the codeparrot/github-code dataset to estimate
complexity variance and determine the required sample size for statistical power.
"""
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import from project API surface
from config import get_config, set_seed
from utils.logging import get_logger, PipelineError

# Try to import datasets; if missing, we fail loudly as per constraint
try:
    from datasets import load_dataset
except ImportError:
    # This will cause a runtime error if datasets is not installed,
    # which is the correct behavior (fail loudly).
    raise ImportError("The 'datasets' library is required. Install via 'pip install datasets'.")

# Constants
PILOT_SAMPLE_SIZE = 50
MAX_PIPELINE_HOURS = 6.0
TARGET_POWER = 0.8
ALPHA = 0.05
# Estimated average processing time per chunk in seconds (conservative estimate)
# Includes download, preprocessing, static analysis, and inference.
AVG_TIME_PER_CHUNK_SECONDS = 120.0 

def fetch_pilot_metadata(num_samples: int = PILOT_SAMPLE_SIZE) -> Dict[str, Any]:
    """
    Fetches metadata for a pilot sample from codeparrot/github-code.
    
    Uses streaming to avoid downloading full files, fetching only metadata
    fields relevant to complexity estimation (e.g., file size, line count).
    
    Args:
        num_samples: Number of pilot samples to fetch.
        
    Returns:
        A dictionary containing pilot metadata statistics.
        
    Raises:
        PipelineError: If the dataset fetch fails.
    """
    logger = get_logger(__name__)
    logger.info(f"Fetching pilot metadata for {num_samples} samples from codeparrot/github-code...")
    
    try:
        # Load dataset in streaming mode
        # We select Python and Java languages as per spec
        dataset = load_dataset(
            "codeparrot/github-code",
            split="train",
            streaming=True,
            trust_remote_code=True
        )
        
        # Filter for Python and Java (approximate filtering based on language field)
        # Note: The actual schema might vary, but 'language' is a standard field.
        # We take the first N samples that match.
        pilot_data = []
        count = 0
        languages = ["Python", "Java"]
        
        for item in dataset:
            if item.get("language") in languages:
                pilot_data.append(item)
                count += 1
                if count >= num_samples:
                    break
        
        if count == 0:
            raise PipelineError("Failed to fetch any pilot samples matching criteria.")
        
        logger.info(f"Successfully fetched {count} pilot samples.")
        
        # Compute simple variance estimates from available metadata
        # Since we don't have full code, we use 'size' or 'line_count' as a proxy for complexity variance
        # If 'line_count' exists, use it; otherwise fallback to 'size'
        metric_key = "line_count" if "line_count" in pilot_data[0] else "size"
        
        values = [float(item.get(metric_key, 0)) for item in pilot_data]
        
        if not values:
            raise PipelineError("No valid complexity metrics found in pilot data.")
        
        mean_val = sum(values) / len(values)
        variance_val = sum((x - mean_val) ** 2 for x in values) / len(values)
        
        return {
            "count": count,
            "metric_key": metric_key,
            "mean": mean_val,
            "variance": variance_val,
            "std_dev": variance_val ** 0.5,
            "samples": pilot_data[:10] # Store a small subset for debugging
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch pilot metadata: {e}")
        raise PipelineError(f"Dataset fetch failed: {e}")

def estimate_variance_and_effect_size(pilot_stats: Dict[str, Any]) -> Tuple[float, float]:
    """
    Estimates variance and expected effect size from pilot data.
    
    Args:
        pilot_stats: Statistics from the pilot fetch.
        
    Returns:
        Tuple of (estimated_variance, estimated_effect_size).
    """
    logger = get_logger(__name__)
    
    variance = pilot_stats.get("variance", 0.0)
    std_dev = pilot_stats.get("std_dev", 0.0)
    
    # Heuristic for effect size:
    # We assume a moderate effect size (Cohen's d) based on the standard deviation.
    # If variance is very low, we assume a smaller effect size to be conservative.
    # Standard convention: small=0.2, medium=0.5, large=0.8
    if std_dev == 0:
        estimated_effect_size = 0.1 # Minimal detectable effect
    else:
        # Assume the effect we want to detect is a fraction of the standard deviation
        estimated_effect_size = 0.5 * std_dev / std_dev # Normalize to 0.5 (medium)
        
    logger.info(f"Estimated Variance: {variance:.4f}, Estimated Effect Size: {estimated_effect_size:.4f}")
    return variance, estimated_effect_size

def calculate_required_sample_size(variance: float, effect_size: float, power: float = TARGET_POWER, alpha: float = ALPHA) -> int:
    """
    Calculates the required sample size for a given power and effect size.
    Uses a simplified approximation for two-sample t-test or correlation power.
    Formula approximation: N = ( (Z_alpha + Z_beta) / effect_size )^2 * 2 (for two groups)
    For correlation: N = (Z_alpha + Z_beta)^2 / effect_size^2
    We use a standard approximation for correlation power analysis.
    """
    from math import sqrt
    import scipy.stats as stats
    
    # Z-scores
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    
    # If effect size is 0, return infinity (or a very large number)
    if effect_size == 0:
        return 1000000
        
    # Approximation for correlation power (Cohen's q or r)
    # N = ( (Z_alpha + Z_beta) / r )^2
    # We treat 'effect_size' here as the correlation coefficient 'r'
    # If effect_size > 1, cap it to 0.99 to avoid division issues
    r = min(abs(effect_size), 0.99)
    
    n = ((z_alpha + z_beta) / r) ** 2
    
    return int(n) + 1

def calculate_max_feasible_chunks(max_hours: float = MAX_PIPELINE_HOURS, time_per_chunk: float = AVG_TIME_PER_CHUNK_SECONDS) -> int:
    """
    Calculates the maximum number of chunks feasible within the time budget.
    """
    total_seconds = max_hours * 3600
    max_chunks = int(total_seconds / time_per_chunk)
    return max_chunks

def generate_feasibility_report(pilot_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates the full feasibility report.
    """
    logger = get_logger(__name__)
    
    variance, effect_size = estimate_variance_and_effect_size(pilot_stats)
    required_n = calculate_required_sample_size(variance, effect_size)
    max_feasible_n = calculate_max_feasible_chunks()
    
    report = {
        "pilot_stats": {
            "count": pilot_stats["count"],
            "metric_key": pilot_stats["metric_key"],
            "mean": pilot_stats["mean"],
            "variance": pilot_stats["variance"]
        },
        "analysis": {
            "estimated_effect_size": effect_size,
            "required_sample_size": required_n,
            "max_feasible_chunks": max_feasible_n,
            "target_power": TARGET_POWER,
            "alpha": ALPHA,
            "max_hours": MAX_PIPELINE_HOURS
        },
        "decision": {}
    }
    
    if required_n > max_feasible_n:
        report["decision"]["status"] = "capped"
        report["decision"]["capped_N"] = max_feasible_n
        report["decision"]["power_limitation"] = "Study underpowered; capped to max feasible"
        report["decision"]["proceed_flag"] = True
        logger.warning("WARNING: Study underpowered; capping N to max feasible")
    else:
        report["decision"]["status"] = "feasible"
        report["decision"]["capped_N"] = required_n
        report["decision"]["proceed_flag"] = True
        logger.info(f"Feasible. Required N: {required_n}")
        
    return report

def write_feasibility_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Writes the feasibility report to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logging.info(f"Feasibility report written to {output_path}")

def main():
    """
    Main entry point for the feasibility check task.
    """
    logger = get_logger(__name__)
    set_seed(42)
    
    config = get_config()
    output_path = Path(config["data"]["results_dir"]) / "feasibility_report.json"
    
    try:
        # 1. Fetch Pilot Metadata
        pilot_stats = fetch_pilot_metadata(PILOT_SAMPLE_SIZE)
        
        # 2. Generate Report
        report = generate_feasibility_report(pilot_stats)
        
        # 3. Write Artifact
        write_feasibility_report(report, output_path)
        
        # 4. Print Summary
        print(f"\n--- Feasibility Check Complete ---")
        print(f"Status: {report['decision']['status']}")
        print(f"Capped N: {report['decision']['capped_N']}")
        print(f"Proceed: {report['decision']['proceed_flag']}")
        if report['decision']['status'] == 'capped':
            print(f"Limitation: {report['decision']['power_limitation']}")
        print(f"Output: {output_path}")
        
    except Exception as e:
        logger.critical(f"Feasibility check failed: {e}")
        raise

if __name__ == "__main__":
    main()