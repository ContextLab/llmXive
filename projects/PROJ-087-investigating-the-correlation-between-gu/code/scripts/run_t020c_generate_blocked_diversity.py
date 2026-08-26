"""
Task T020c: Generate Blocked Diversity Artifact.

This script is triggered when the data feasibility check (T012a) or schema
verification (T012d) fails. It creates a placeholder diversity results file
to ensure the US1 pipeline has a measurable artifact even in the blocked state.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_blocked_diversity_artifact(output_path: str, reason: str = "No verified data source found"):
    """
    Generates a CSV file with the expected schema for diversity results,
    but marked as 'blocked' with no actual data.

    Args:
        output_path: Path to the output CSV file.
        reason: The reason for the block status.
    """
    logger.info(f"Generating blocked diversity artifact at: {output_path}")
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Define the header columns as per spec
    columns = [
        "sample_id", 
        "shannon", 
        "simpson", 
        "observed_otus",
        "status",
        "reason"
    ]

    # Create the content with a single header row and a status row
    # Since no real data exists, we write a CSV that indicates the state.
    # The spec asks for "empty diversity columns", but a CSV usually needs headers.
    # We will write a file with headers and a single row indicating the block status.
    
    lines = []
    lines.append(",".join(columns))
    
    # Add a row indicating the blocked state
    # Using an empty sample_id or a specific ID like "BLOCKED"
    lines.append(f'BLOCKED,,,,{reason}')

    content = "\n".join(lines)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"Successfully wrote blocked diversity artifact to {output_path}")
    return True

def main():
    """Main entry point for T020c."""
    config = load_config()
    
    # Default output path based on project structure
    output_path = str(project_root / "data" / "processed" / "diversity_results.csv")
    
    # Allow override via environment variable for flexibility
    env_output = os.getenv("DIVERSITY_RESULTS_PATH")
    if env_output:
        output_path = env_output

    reason = os.getenv("BLOCK_REASON", "No verified data source found")

    try:
        generate_blocked_diversity_artifact(output_path, reason)
        logger.info("T020c completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate blocked diversity artifact: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())