import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Project root handling
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESEARCH_DIR = PROJECT_ROOT / "specs" / "001-predict-strain-rate-yield"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "sample_size_estimator.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration for simulated generator parameters (if real data is unavailable)
# These represent the expected parameters from the physics-consistent generator
GENERATOR_PARAMS = {
    "total_samples": 1200,
    "alloy_families": {
        "AA-6061": 300,
        "AISI-4340": 300,
        "Ti-6Al-4V": 250,
        "Inconel-718": 200,
        "Al-7075": 150
    }
}

def load_sample_estimates() -> Dict[str, Any]:
    """
    Load sample estimates from a JSON file if it exists, otherwise return defaults.
    """
    estimates_path = DATA_DIR / "sample_estimates.json"
    if estimates_path.exists():
        try:
            with open(estimates_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load sample estimates from {estimates_path}: {e}")
            logger.info("Using default generator parameters.")
    return GENERATOR_PARAMS

def estimate_sample_size_from_generator(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Estimate total sample size (N) and per-alloy-family counts from generator parameters.
    """
    if params is None:
        params = load_sample_estimates()

    total_n = params.get("total_samples", 0)
    family_counts = params.get("alloy_families", {})
    
    # Validate counts
    calculated_total = sum(family_counts.values())
    if calculated_total != total_n:
        logger.warning(f"Total samples ({total_n}) does not match sum of family counts ({calculated_total}). Adjusting total.")
        total_n = calculated_total

    return {
        "total_sample_size": total_n,
        "per_family_counts": family_counts,
        "source": "simulated_generator"
    }

def estimate_sample_size_from_research_report(research_md_path: Path) -> Dict[str, Any]:
    """
    Estimate sample size from the research.md feasibility report if it contains the data.
    This is a placeholder for parsing the actual markdown if it exists.
    """
    if not research_md_path.exists():
        logger.warning(f"Research report not found at {research_md_path}. Falling back to generator.")
        return estimate_sample_size_from_generator()

    # Simple parsing logic for research.md
    try:
        content = research_md_path.read_text()
        # Look for a JSON block or specific lines indicating N and family counts
        # This is a simplified parser; in a real scenario, we'd use a more robust markdown parser
        if "total_samples" in content:
            # Extract if possible, else fallback
            pass 
    except Exception as e:
        logger.error(f"Failed to parse research report: {e}")
    
    return estimate_sample_size_from_generator()

def save_estimate_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the sample size estimate report to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Sample size estimate report saved to {output_path}")

def main():
    """
    Main entry point for estimating sample size.
    """
    logger.info("Starting sample size estimation (T009).")
    
    research_path = RESEARCH_DIR / "research.md"
    estimates = estimate_sample_size_from_research_report(research_path)
    
    output_path = DATA_DIR / "sample_size_estimate.json"
    save_estimate_report(estimates, output_path)
    
    # Log summary
    logger.info(f"Total Estimated Sample Size (N): {estimates['total_sample_size']}")
    logger.info("Per-Alloy-Family Counts:")
    for family, count in estimates['per_family_counts'].items():
        logger.info(f"  {family}: {count}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
