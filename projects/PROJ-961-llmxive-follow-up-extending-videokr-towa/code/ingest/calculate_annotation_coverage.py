"""
Calculate and log the proportion of questions successfully annotated.

This script reads the annotated dataset produced by T013 (annotate_graph.py),
counts the total input records and the number of unresolvable records
(where chain_length is None or the entity mapping failed), and calculates
the annotation coverage proportion.

Formula: proportion = (total_input_records - unresolvable_count) / total_input_records

Output: data/processed/annotation_coverage.json
"""
import json
import logging
import sys
from collections import Counter
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_project_root, get_path, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_annotated_data(csv_path: Path) -> list:
    """Load the annotated CSV file."""
    import csv
    records = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def calculate_coverage(records: list) -> dict:
    """
    Calculate annotation coverage statistics.

    Args:
        records: List of dictionaries representing the annotated dataset.

    Returns:
        Dictionary with coverage statistics.
    """
    total_records = len(records)

    if total_records == 0:
        logger.warning("No records found in the annotated dataset.")
        return {
            "total_input_records": 0,
            "unresolvable_count": 0,
            "successfully_annotated_count": 0,
            "proportion": 0.0,
            "status": "no_data"
        }

    # Count unresolvable records
    # A record is unresolvable if chain_length is None, empty string, or 'unresolvable'
    unresolvable_count = 0
    chain_length_values = []

    for record in records:
        chain_length = record.get('chain_length', None)

        # Check for unresolvable states
        if chain_length is None or chain_length == '' or chain_length == 'unresolvable':
            unresolvable_count += 1
        else:
            try:
                chain_length_values.append(int(chain_length))
            except (ValueError, TypeError):
                # If it can't be converted to int, treat as unresolvable
                unresolvable_count += 1

    successfully_annotated_count = total_records - unresolvable_count
    proportion = successfully_annotated_count / total_records if total_records > 0 else 0.0

    # Calculate distribution of chain lengths for successfully annotated records
    chain_length_distribution = Counter(chain_length_values)

    return {
        "total_input_records": total_records,
        "unresolvable_count": unresolvable_count,
        "successfully_annotated_count": successfully_annotated_count,
        "proportion": proportion,
        "chain_length_distribution": dict(chain_length_distribution),
        "status": "success" if proportion > 0 else "failed",
        "message": f"Successfully annotated {successfully_annotated_count}/{total_records} records ({proportion:.2%})"
    }


def save_coverage_results(results: dict, output_path: Path) -> None:
    """Save coverage results to JSON file."""
    ensure_dir(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Coverage results saved to {output_path}")


def main():
    """Main entry point for the coverage calculation script."""
    project_root = get_project_root()
    annotated_csv_path = get_path(project_root, "data/processed/annotated_videokr.csv")
    output_json_path = get_path(project_root, "data/processed/annotation_coverage.json")

    logger.info(f"Starting annotation coverage calculation...")
    logger.info(f"Input file: {annotated_csv_path}")
    logger.info(f"Output file: {output_json_path}")

    # Check if input file exists
    if not annotated_csv_path.exists():
        logger.error(f"Input file not found: {annotated_csv_path}")
        logger.error("Please ensure T013 (annotate_graph.py) has been run successfully first.")
        sys.exit(1)

    try:
        # Load annotated data
        logger.info("Loading annotated dataset...")
        records = load_annotated_data(annotated_csv_path)
        logger.info(f"Loaded {len(records)} records from {annotated_csv_path}")

        # Calculate coverage
        logger.info("Calculating annotation coverage...")
        coverage_results = calculate_coverage(records)

        # Log results
        logger.info(f"Total input records: {coverage_results['total_input_records']}")
        logger.info(f"Unresolvable count: {coverage_results['unresolvable_count']}")
        logger.info(f"Successfully annotated: {coverage_results['successfully_annotated_count']}")
        logger.info(f"Coverage proportion: {coverage_results['proportion']:.4f} ({coverage_results['proportion']:.2%})")

        if coverage_results['chain_length_distribution']:
            logger.info("Chain length distribution:")
            for hop, count in sorted(coverage_results['chain_length_distribution'].items()):
                logger.info(f"  {hop}-hop: {count} records")

        # Save results
        save_coverage_results(coverage_results, output_json_path)

        logger.info("Annotation coverage calculation completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during coverage calculation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
