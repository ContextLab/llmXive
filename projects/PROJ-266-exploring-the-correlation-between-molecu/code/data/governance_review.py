import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

# Configure logging
configure_root_logger()
logger = get_logger(__name__)

# Constants
MAX_RUNTIME_HOURS = 6.0
GOVERNANCE_FLAG_PATH = "state/pending/governance_review_required.json"
BENCHMARK_RESULTS_PATH = "data/processed/benchmark_results.json"

def load_benchmark_results() -> Dict[str, Any]:
    """Load benchmark results from the previous step (T040a)."""
    root = get_project_root()
    path = root / BENCHMARK_RESULTS_PATH
    
    if not path.exists():
        raise FileNotFoundError(
            f"Benchmark results file not found at {path}. "
            "Please ensure T040a (benchmark execution) has been completed successfully."
        )
    
    with open(path, 'r') as f:
        return json.load(f)

def evaluate_runtime_requirement(benchmark_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate if the estimated runtime exceeds the governance threshold.
    
    Returns a dictionary with:
    - estimated_runtime_hours: float
    - exceeds_limit: bool
    - sample_size_used: int
    - total_molecules: int
    - action: str (one of 'proceed', 'reduce_sample', 'manual_review')
    - message: str
    """
    estimated_runtime_hours = benchmark_data.get('estimated_runtime_hours', 0.0)
    sample_size = benchmark_data.get('sample_size', 0)
    total_molecules = benchmark_data.get('total_molecules', 0)
    
    exceeds_limit = estimated_runtime_hours > MAX_RUNTIME_HOURS
    
    action = 'proceed'
    message = f"Estimated runtime ({estimated_runtime_hours:.2f}h) is within the {MAX_RUNTIME_HOURS}h limit."
    
    if exceeds_limit:
        # Per task requirement: "reduce sample size by [deferred]"
        # Since the reduction logic is deferred, we flag for manual review
        # rather than automatically modifying the pipeline parameters.
        action = 'manual_review'
        message = (
            f"Estimated runtime ({estimated_runtime_hours:.2f}h) exceeds the {MAX_RUNTIME_HOURS}h limit. "
            f"Sample size {sample_size} molecules (from {total_molecules} total). "
            "Manual governance review required to determine sample size reduction strategy."
        )
    
    return {
        'estimated_runtime_hours': estimated_runtime_hours,
        'exceeds_limit': exceeds_limit,
        'sample_size_used': sample_size,
        'total_molecules': total_molecules,
        'action': action,
        'message': message,
        'threshold_hours': MAX_RUNTIME_HOURS
    }

def write_governance_flag(governance_result: Dict[str, Any]) -> None:
    """
    Write the governance review flag to the state/pending directory.
    
    This file serves as the documented flag for governance review as required
    by the task specification.
    """
    root = get_project_root()
    flag_path = root / GOVERNANCE_FLAG_PATH
    
    # Ensure the directory exists
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(flag_path, 'w') as f:
        json.dump(governance_result, f, indent=2)
    
    logger.info(f"Governance review flag written to {flag_path}")

def main():
    """Main entry point for the governance review logic."""
    logger.info("Starting governance review for runtime constraints (T040b)...")
    
    try:
        # Load benchmark results from T040a
        benchmark_data = load_benchmark_results()
        logger.info(f"Loaded benchmark results: sample_size={benchmark_data.get('sample_size')}, "
                    f"total_molecules={benchmark_data.get('total_molecules')}")
        
        # Evaluate against runtime requirement
        governance_result = evaluate_runtime_requirement(benchmark_data)
        
        # Log the result
        logger.info(f"Governance evaluation: {governance_result['action'].upper()}")
        logger.info(f"Message: {governance_result['message']}")
        
        # Write the flag if manual review is required
        if governance_result['action'] == 'manual_review':
            write_governance_flag(governance_result)
            logger.warning("MANUAL GOVERNANCE REVIEW REQUIRED - Flag written to state/pending/")
        else:
            logger.info("No manual review required. Pipeline can proceed.")
        
        # Return exit code based on action
        if governance_result['action'] == 'manual_review':
            # Don't fail the script, just log the requirement
            # The actual blocking would happen in the pipeline orchestrator
            return 0
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in benchmark results: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during governance review: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())