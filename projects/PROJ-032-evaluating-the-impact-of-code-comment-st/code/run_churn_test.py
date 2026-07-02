"""
Script to run calc_churn on a specific repository and save results.
This script is the entry point to satisfy the requirement that scripts 
must produce real output files on disk.
"""
import os
import sys
import json
import logging
from pathlib import Path
import argparse

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent))

from metrics import calc_churn
from utils import configure_logging

def main():
    parser = argparse.ArgumentParser(description="Calculate churn for a repository.")
    parser.add_argument("--repo-path", type=str, required=True, help="Path to the git repository.")
    parser.add_argument("--output", type=str, default="data/processed/churn_results.json", help="Output JSON file path.")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    args = parser.parse_args()
    
    # Configure logging
    configure_logging(log_path="logs/pipeline.log", level=args.log_level)
    logger = logging.getLogger(__name__)
    
    repo_path = Path(args.repo_path)
    output_path = Path(args.output)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not repo_path.exists():
        logger.error(f"Repository path does not exist: {repo_path}")
        sys.exit(1)
    
    try:
        logger.info(f"Calculating churn for: {repo_path}")
        churn_value = calc_churn(repo_path)
        
        result = {
            "repo_path": str(repo_path),
            "churn": churn_value
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Churn calculation complete. Result: {churn_value}")
        logger.info(f"Results saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to calculate churn: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()