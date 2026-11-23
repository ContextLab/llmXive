import json
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from scipy.stats import pearsonr

# Add code/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from parser_utils import load_json_file, save_json_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_dag_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the DAG manifest containing logical difficulty scores."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"DAG manifest not found at {manifest_path}")
    
    data = load_json_file(manifest_path)
    if not isinstance(data, dict) or 'entries' not in data:
        raise ValueError(f"Invalid DAG manifest format: missing 'entries' key")
    
    logger.info(f"Loaded DAG manifest with {len(data['entries'])} entries")
    return data

def load_gold_standard(gold_path: Path) -> Dict[str, Any]:
    """Load the gold standard annotations containing human ratings."""
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold standard annotations not found at {gold_path}")
    
    data = load_json_file(gold_path)
    if not isinstance(data, dict) or 'annotations' not in data:
        raise ValueError(f"Invalid gold standard format: missing 'annotations' key")
    
    logger.info(f"Loaded gold standard with {len(data['annotations'])} annotations")
    return data

def extract_matching_data(manifest_data: Dict[str, Any], gold_data: Dict[str, Any]) -> Tuple[List[float], List[float]]:
    """
    Extract matching entries between DAG manifest and gold standard.
    Returns two lists: [dag_depths], [human_ratings]
    """
    # Create a lookup dict from gold standard by example_id
    gold_lookup = {ann['example_id']: ann['human_complexity_rating'] for ann in gold_data['annotations']}
    
    dag_depths = []
    human_ratings = []
    matched_count = 0
    unmatched_ids = []

    for entry in manifest_data['entries']:
        example_id = entry.get('example_id')
        if not example_id:
            continue
        
        if example_id in gold_lookup:
            dag_depth = entry.get('logical_difficulty_score')
            if dag_depth is None:
                logger.warning(f"Entry {example_id} missing logical_difficulty_score, skipping")
                continue
            
            dag_depths.append(float(dag_depth))
            human_ratings.append(float(gold_lookup[example_id]))
            matched_count += 1
        else:
            unmatched_ids.append(example_id)

    if matched_count == 0:
        raise ValueError("No matching entries found between DAG manifest and gold standard")

    logger.info(f"Matched {matched_count} entries for correlation analysis")
    if unmatched_ids:
        logger.info(f"Skipped {len(unmatched_ids)} entries not in gold standard")

    return dag_depths, human_ratings

def compute_correlation(dag_depths: List[float], human_ratings: List[float]) -> Tuple[float, float]:
    """
    Compute Pearson correlation coefficient between DAG depths and human ratings.
    Returns (r_value, p_value)
    """
    if len(dag_depths) < 2:
        raise ValueError("Need at least 2 data points to compute correlation")

    r_value, p_value = pearsonr(dag_depths, human_ratings)
    return r_value, p_value

def main():
    parser = argparse.ArgumentParser(description='Validate DAG depth correlation with human ratings')
    parser.add_argument('--manifest', type=str, required=True, help='Path to DAG manifest JSON')
    parser.add_argument('--gold', type=str, required=True, help='Path to gold standard annotations JSON')
    parser.add_argument('--output', type=str, default='data/processed/validation_report.json',
                        help='Path to output validation report JSON')
    parser.add_argument('--threshold', type=float, default=0.6, help='Minimum correlation threshold for pass')
    
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    gold_path = Path(args.gold)
    output_path = Path(args.output)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load data
        logger.info(f"Loading DAG manifest from {manifest_path}")
        manifest_data = load_dag_manifest(manifest_path)
        
        logger.info(f"Loading gold standard from {gold_path}")
        gold_data = load_gold_standard(gold_path)

        # Extract matching data
        logger.info("Extracting matching data points")
        dag_depths, human_ratings = extract_matching_data(manifest_data, gold_data)

        # Compute correlation
        logger.info("Computing Pearson correlation")
        r_value, p_value = compute_correlation(dag_depths, human_ratings)

        logger.info(f"Correlation result: r = {r_value:.4f}, p = {p_value:.4f}")

        # Determine pass/fail
        passed = r_value >= args.threshold
        status = "PASS" if passed else "FAIL"

        # Create report
        report = {
            "status": status,
            "threshold": args.threshold,
            "correlation": {
                "r_value": float(r_value),
                "p_value": float(p_value),
                "sample_size": len(dag_depths)
            },
            "message": f"Correlation {'meets' if passed else 'does not meet'} threshold of {args.threshold}",
            "timestamp": "N/A"  # Could add datetime if needed
        }

        # Save report
        save_json_file(output_path, report)
        logger.info(f"Validation report saved to {output_path}")

        # Exit with appropriate code
        sys.exit(0 if passed else 1)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(2)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(3)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(4)

if __name__ == "__main__":
    main()
