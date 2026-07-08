"""
Script to generate the synthetic validation dataset for T029.

This script wraps the T026 synthetic generator to ensure the data
is available for evaluation. It creates:
1. synthetic_summaries.json (full dataset)
2. ground_truth_labels.json (explicit labels for evaluation)

Run this before T029 if the data does not exist.
"""
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.audit.synthetic import main as generate_synthetic_main
from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)

def main():
    data_dir = project_root / "data" / "synthetic"
    data_dir.mkdir(parents=True, exist_ok=True)

    summaries_path = data_dir / "synthetic_summaries.json"
    ground_truth_path = data_dir / "ground_truth_labels.json"

    # Check if data already exists
    if summaries_path.exists() and ground_truth_path.exists():
        logger.info(f"Synthetic data already exists at {summaries_path} and {ground_truth_path}")
        logger.info("Skipping generation. To regenerate, delete these files first.")
        return 0

    logger.info("Generating synthetic dataset...")
    
    # Run the synthetic generator (T026)
    # We need to ensure it writes to our expected location
    # The synthetic module writes to output/ by default, so we might need to adapt
    # For now, we assume the synthetic module can be configured or we post-process
    
    # Since T026 is marked as completed, we assume the data exists or we call it
    # Let's call the main function of the synthetic module
    # Note: The synthetic module's main() writes to output/ by default.
    # We need to ensure it writes to data/synthetic/ or we copy it.
    
    # For this implementation, we will call the generation logic directly
    # or assume the user has run T026. If not, we run it.
    
    # Import the generation function
    from code.src.audit.synthetic import generate_synthetic_dataset, write_summaries, write_metadata
    from code.src.config import set_rng_seed, SEED

    set_rng_seed(SEED)

    # Generate 10,000+ records
    num_records = 10000
    summaries = generate_synthetic_dataset(num_records)

    # Write to expected location
    write_summaries(summaries, summaries_path)
    
    # Create ground truth labels
    ground_truth = {}
    for summary in summaries:
        record_id = summary['id']
        # The synthetic generator sets 'ground_truth_inconsistent' based on injected errors
        is_inconsistent = summary.get('ground_truth_inconsistent', False)
        ground_truth[record_id] = {
            'is_inconsistent': is_inconsistent,
            'injection_details': summary.get('injection_details', {})
        }
    
    with open(ground_truth_path, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2)

    logger.info(f"Generated {len(summaries)} synthetic summaries.")
    logger.info(f"Saved to {summaries_path}")
    logger.info(f"Saved ground truth to {ground_truth_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())