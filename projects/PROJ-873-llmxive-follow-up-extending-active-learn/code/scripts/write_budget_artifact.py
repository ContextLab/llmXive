"""
Script to execute Task T013a: Budget Definition.
Defines, logs, and enforces the total_budget, writing the artifact to disk.

This script MUST run first to ensure the denominator for ratio calculations is defined.
It writes data/results/budget_config.json with the schema:
{"total_budget": int, "budget_type": "LLM_calls", "calls_executed": int}

If the pipeline terminates early (e.g., due to budget exhaustion), this artifact
records the ACTUAL number of calls executed, not just the configured limit.
"""
import os
import sys
import json
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config, PipelineConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Execute T013a: Define budget, initialize state, and write artifact.
    """
    logger.info("Starting Task T013a: Budget Definition")
    
    # Initialize or retrieve global config
    cfg = get_config()
    
    # Ensure the budget is set (default is 100 per US-1, but can be overridden)
    # If called with args, they would be handled by config.py main, but here we ensure defaults
    logger.info(f"Initialized budget: {cfg.total_budget} calls ({cfg.budget_type})")
    
    # Write the artifact immediately to establish the baseline
    # Even if calls_executed is 0 now, this file establishes the 'total_budget'
    # for downstream tasks (T013d) to use as the denominator.
    cfg.write_budget_artifact()
    
    # Verify the file was written
    artifact_path = cfg._budget_artifact_path
    if os.path.exists(artifact_path):
        with open(artifact_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Successfully wrote budget artifact: {artifact_path}")
        logger.info(f"Artifact content: {json.dumps(data, indent=2)}")
        return 0
    else:
        logger.error(f"Failed to write budget artifact to {artifact_path}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
