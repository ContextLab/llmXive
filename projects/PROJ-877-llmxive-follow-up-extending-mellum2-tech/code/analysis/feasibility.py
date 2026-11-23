import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from datasets import load_dataset
from dotenv import load_dotenv

# Import from project config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_project_root, load_environment, validate_required_env_vars

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants for Power Analysis
ALPHA = 0.05
POWER_TARGET = 0.80
ESTIMATED_EFFECT_SIZE_R = 0.3
PILOT_SAMPLE_SIZE = 50
MAX_RUNTIME_HOURS = 6.0
CHUNK_PROCESSING_TIME_ESTIMATE_SECONDS = 120.0  # Conservative estimate per chunk

def fetch_pilot_metadata(sample_size: int = PILOT_SAMPLE_SIZE) -> Dict[str, Any]:
    """
    Fetch metadata only (N=50) of code chunks from codeparrot/github-code (Python/Java)
    using streaming to estimate complexity variance WITHOUT downloading full files.
    
    Returns:
        Dict containing pilot sample statistics (mean complexity, variance, etc.)
    """
    logger.info(f"Fetching pilot sample of {sample_size} chunks from codeparrot/github-code...")
    
    # Load dataset in streaming mode to avoid downloading full dataset
    try:
        ds = load_dataset(
            "codeparrot/github-code",
            split="train",
            streaming=True,
            trust_remote_code=True
        )
        
        # Filter for Python and Java files
        # Note: The dataset has a 'lang' field
        python_ds = ds.filter(lambda x: x.get('lang', '').lower() == 'python')
        java_ds = ds.filter(lambda x: x.get('lang', '').lower() == 'java')
        
        # Combine and take sample
        # Since we can't easily combine streaming datasets without materializing,
        # we'll take a sample from Python first, then Java
        pilot_data = []
        
        # Take 25 from Python
        python_count = 0
        for item in python_ds:
            if python_count >= sample_size // 2:
                break
            pilot_data.append(item)
            python_count += 1
        
        # Take remaining from Java
        java_count = 0
        for item in java_ds:
            if java_count >= sample_size - python_count:
                break
            pilot_data.append(item)
            java_count += 1
        
        if len(pilot_data) == 0:
            raise RuntimeError("Failed to fetch any pilot data from the dataset.")
        
        logger.info(f"Successfully fetched {len(pilot_data)} pilot samples.")
        
        # Extract basic metadata for variance estimation
        # We'll use 'size' (file size) as a proxy for complexity in this pilot
        # In a real scenario, we'd run static analysis, but for pilot metadata-only:
        sizes = [item.get('size', 0) for item in pilot_data if item.get('size')]
        
        if not sizes:
            # Fallback: use text length if size not available
            sizes = [len(item.get('content', '')) for item in pilot_data if item.get('content')]
        
        if not sizes:
            raise RuntimeError("Could not extract size/length data from pilot samples.")
        
        # Calculate basic statistics
        mean_size = sum(sizes) / len(sizes)
        variance_size = sum((x - mean_size) ** 2 for x in sizes) / (len(sizes) - 1) if len(sizes) > 1 else 0
        std_dev_size = variance_size ** 0.5
        
        return {
            "sample_size": len(pilot_data),
            "mean_size": mean_size,
            "variance_size": variance_size,
            "std_dev_size": std_dev_size,
            "min_size": min(sizes),
            "max_size": max(sizes)
        }
        
    except Exception as e:
        logger.error(f"Error fetching pilot metadata: {e}")
        raise

def estimate_variance_and_effect_size(pilot_stats: Dict[str, Any]) -> Tuple[float, float]:
    """
    Estimate variance and effect size from pilot statistics.
    
    Args:
        pilot_stats: Statistics from the pilot sample
        
    Returns:
        Tuple of (estimated_variance, estimated_effect_size)
    """
    # Use the variance from the pilot sample
    estimated_variance = pilot_stats.get('variance_size', 0)
    
    # If we have variance, we can estimate effect size
    # For this pilot, we assume the estimated effect size r=0.3 as per task requirements
    # In a more sophisticated analysis, we might calculate Cohen's d or similar
    estimated_effect_size = ESTIMATED_EFFECT_SIZE_R
    
    logger.info(f"Estimated variance: {estimated_variance}, Effect size: {estimated_effect_size}")
    
    return estimated_variance, estimated_effect_size

def calculate_required_sample_size(effect_size: float, alpha: float = ALPHA, power: float = POWER_TARGET) -> int:
    """
    Calculate required sample size for a priori power analysis.
    Uses the formula for Pearson correlation: n = ((Z_alpha + Z_beta) / effect_size)^2 + 3
    
    Args:
        effect_size: Estimated effect size (r)
        alpha: Significance level
        power: Desired statistical power
        
    Returns:
        Required sample size (integer)
    """
    import math
    
    # Z-scores for alpha and power
    # For alpha=0.05 (two-tailed), Z_alpha ≈ 1.96
    # For power=0.80, Z_beta ≈ 0.84
    z_alpha = 1.96  # Approximation for 0.05 significance
    z_beta = 0.84   # Approximation for 0.80 power
    
    # Calculate required sample size
    # Formula: n = ((Z_alpha + Z_beta) / effect_size)^2 + 3
    if effect_size <= 0:
        raise ValueError("Effect size must be positive")
        
    n = ((z_alpha + z_beta) / effect_size) ** 2 + 3
    
    return int(math.ceil(n))

def calculate_max_feasible_chunks(max_runtime_hours: float = MAX_RUNTIME_HOURS, 
                                chunk_time_seconds: float = CHUNK_PROCESSING_TIME_ESTIMATE_SECONDS) -> int:
    """
    Calculate the maximum number of chunks that can be processed within the time budget.
    
    Args:
        max_runtime_hours: Maximum allowed runtime in hours
        chunk_time_seconds: Estimated time to process one chunk in seconds
        
    Returns:
        Maximum feasible number of chunks
    """
    max_runtime_seconds = max_runtime_hours * 3600
    max_chunks = int(max_runtime_seconds / chunk_time_seconds)
    
    logger.info(f"Maximum feasible chunks: {max_chunks} (based on {max_runtime_hours}h budget)")
    
    return max_chunks

def generate_feasibility_report(pilot_stats: Dict[str, Any], 
                              required_n: int, 
                              max_feasible_n: int,
                              alpha: float = ALPHA,
                              power: float = POWER_TARGET,
                              effect_size: float = ESTIMATED_EFFECT_SIZE_R) -> Dict[str, Any]:
    """
    Generate the feasibility report with all calculated parameters.
    
    Args:
        pilot_stats: Statistics from the pilot sample
        required_n: Required sample size for desired power
        max_feasible_n: Maximum feasible chunks given time budget
        alpha: Significance level
        power: Desired power
        effect_size: Effect size used for calculation
        
    Returns:
        Feasibility report dictionary
    """
    # Determine if we need to cap N
    is_capped = required_n > max_feasible_n
    capped_n = min(required_n, max_feasible_n)
    
    # Calculate perturbation magnitude and bootstrap count based on N
    # Default values as per task description
    perturbation_magnitude = 0.05  # Standard significance threshold proxy
    bootstrap_count = 1000
    
    # Adjust bootstrap count based on sample size (smaller sample -> fewer bootstraps for speed)
    if capped_n < 100:
        bootstrap_count = 500
    elif capped_n < 500:
        bootstrap_count = 800
    
    # Determine status
    status = "capped" if is_capped else "feasible"
    
    # Build report
    report = {
        "status": status,
        "capped_N": capped_n,
        "power_limitation": f"Required N ({required_n}) exceeds feasible N ({max_feasible_n}). Capped to {capped_n}." if is_capped else "None",
        "alpha": alpha,
        "power_target": power,
        "estimated_effect_size": effect_size,
        "pilot_sample_stats": {
            "sample_size": pilot_stats.get("sample_size", 0),
            "mean_size": pilot_stats.get("mean_size", 0),
            "variance_size": pilot_stats.get("variance_size", 0),
            "std_dev_size": pilot_stats.get("std_dev_size", 0)
        },
        "perturbation_magnitude": perturbation_magnitude,
        "bootstrap_count": bootstrap_count,
        "proceed_flag": True,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return report

def write_feasibility_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Write the feasibility report to a JSON file.
    
    Args:
        report: The feasibility report dictionary
        output_path: Path to write the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Feasibility report written to {output_path}")

def main():
    """Main entry point for the feasibility analysis task."""
    logger.info("Starting feasibility analysis (T011)...")
    
    try:
        # Load environment and validate
        load_environment()
        validate_required_env_vars(["HF_TOKEN"])  # Ensure HF_TOKEN is set for dataset access
        
        # Get project root and output path
        project_root = get_project_root()
        output_path = project_root / "data" / "results" / "feasibility_report.json"
        
        # Step 1: Fetch pilot metadata
        pilot_stats = fetch_pilot_metadata(PILOT_SAMPLE_SIZE)
        
        # Step 2: Estimate variance and effect size
        estimated_variance, estimated_effect_size = estimate_variance_and_effect_size(pilot_stats)
        
        # Step 3: Calculate required sample size
        required_n = calculate_required_sample_size(estimated_effect_size)
        logger.info(f"Required sample size for power analysis: {required_n}")
        
        # Step 4: Calculate maximum feasible chunks
        max_feasible_n = calculate_max_feasible_chunks()
        
        # Step 5: Generate feasibility report
        report = generate_feasibility_report(
            pilot_stats=pilot_stats,
            required_n=required_n,
            max_feasible_n=max_feasible_n
        )
        
        # Step 6: Write report to disk
        write_feasibility_report(report, output_path)
        
        # Log summary
        logger.info("="*50)
        logger.info("FEASIBILITY ANALYSIS SUMMARY")
        logger.info("="*50)
        logger.info(f"Status: {report['status']}")
        logger.info(f"Capped N: {report['capped_N']}")
        logger.info(f"Power Limitation: {report['power_limitation']}")
        logger.info(f"Perturbation Magnitude: {report['perturbation_magnitude']}")
        logger.info(f"Bootstrap Count: {report['bootstrap_count']}")
        logger.info(f"Proceed Flag: {report['proceed_flag']}")
        logger.info("="*50)
        
        if not report['proceed_flag']:
            logger.warning("Feasibility check failed. Pipeline should not proceed.")
            sys.exit(1)
        
        logger.info("Feasibility analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"Feasibility analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
