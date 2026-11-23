"""
Verification module for annotation coverage.
"""
import csv
import json
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config import get_project_root, get_path, ensure_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_annotated_data(data_path: Path) -> List[Dict[str, Any]]:
    """Load annotated dataset from CSV."""
    with open(data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def calculate_coverage(annotated_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate annotation coverage statistics."""
    total_records = len(annotated_data)
    unresolvable_count = sum(1 for r in annotated_data if r.get("chain_bin") == "unresolvable")
    annotated_count = total_records - unresolvable_count
    proportion = annotated_count / total_records if total_records > 0 else 0.0

    return {
        "total_input_records": total_records,
        "unresolvable_count": unresolvable_count,
        "annotated_count": annotated_count,
        "proportion": proportion
    }

def save_coverage_results(results: Dict[str, Any], output_path: Path):
    """Save coverage results to JSON."""
    ensure_dir(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

def main():
    """Main entry point for coverage verification."""
    project_root = get_project_root()
    processed_dir = get_path(project_root, "processed_data")

    input_path = processed_dir / "annotated_videokr.csv"
    output_path = processed_dir / "annotation_coverage.json"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading annotated data from {input_path}")
    annotated_data = load_annotated_data(input_path)

    logger.info("Calculating coverage...")
    coverage = calculate_coverage(annotated_data)

    logger.info(f"Saving results to {output_path}")
    save_coverage_results(coverage, output_path)

    logger.info(f"Coverage: {coverage['proportion']:.2%}")

if __name__ == "__main__":
    main()