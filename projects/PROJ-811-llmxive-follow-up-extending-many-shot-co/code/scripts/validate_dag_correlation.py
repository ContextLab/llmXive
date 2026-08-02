import json
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from scipy.stats import pearsonr

# Import from project modules
from code.src.parser import get_logical_difficulty
from code.src.parser_utils import load_json_file, save_json_file
from code.src.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_dag_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the DAG manifest containing parsed traces and difficulty scores."""
    logger.info(f"Loading DAG manifest from {manifest_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"DAG manifest not found at {manifest_path}")
    
    data = load_json_file(manifest_path)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid manifest format: expected dict, got {type(data)}")
    
    return data

def load_gold_standard(gs_path: Path) -> Dict[str, Any]:
    """Load the gold standard annotations with human-rated logical complexity."""
    logger.info(f"Loading gold standard from {gs_path}")
    if not gs_path.exists():
        raise FileNotFoundError(f"Gold standard not found at {gs_path}")
    
    data = load_json_file(gs_path)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid gold standard format: expected dict, got {type(data)}")
    
    return data

def extract_matching_data(
    dag_manifest: Dict[str, Any], 
    gold_standard: Dict[str, Any]
) -> Tuple[List[float], List[float], List[str]]:
    """
    Extract paired (DAG depth, human rating) for examples present in both datasets.
    
    Returns:
        Tuple of (dag_depths, human_ratings, example_ids)
    """
    dag_entries = dag_manifest.get('entries', [])
    gs_entries = gold_standard.get('annotations', [])
    
    # Create lookup maps
    dag_map = {entry['example_id']: entry for entry in dag_entries}
    gs_map = {entry['example_id']: entry for entry in gs_entries}
    
    # Find common examples
    common_ids = set(dag_map.keys()) & set(gs_map.keys())
    
    if not common_ids:
        raise ValueError("No overlapping examples between DAG manifest and gold standard")
    
    dag_depths = []
    human_ratings = []
    matched_ids = []
    
    for example_id in sorted(common_ids):
        dag_entry = dag_map[example_id]
        gs_entry = gs_map[example_id]
        
        # Extract DAG depth (logical difficulty score)
        dag_depth = dag_entry.get('logical_difficulty_score')
        if dag_depth is None:
            logger.warning(f"Missing logical_difficulty_score for {example_id}, skipping")
            continue
        
        # Extract human rating
        human_rating = gs_entry.get('logical_complexity_rating')
        if human_rating is None:
            logger.warning(f"Missing logical_complexity_rating for {example_id}, skipping")
            continue
        
        dag_depths.append(float(dag_depth))
        human_ratings.append(float(human_rating))
        matched_ids.append(example_id)
    
    if len(dag_depths) < 2:
        raise ValueError("Insufficient overlapping examples for correlation calculation (need >= 2)")
    
    logger.info(f"Matched {len(dag_depths)} examples for correlation analysis")
    return dag_depths, human_ratings, matched_ids

def compute_correlation(
    dag_depths: List[float], 
    human_ratings: List[float]
) -> float:
    """Compute Pearson correlation coefficient between DAG depth and human ratings."""
    r, p_value = pearsonr(dag_depths, human_ratings)
    logger.info(f"Pearson correlation r = {r:.4f} (p-value = {p_value:.4f})")
    return float(r)

def main():
    """Main validation script entry point."""
    parser = argparse.ArgumentParser(description='Validate DAG depth vs human ratings correlation')
    parser.add_argument('--manifest', type=str, default=None,
                      help='Path to DAG manifest (default: from config)')
    parser.add_argument('--gold-standard', type=str, default=None,
                      help='Path to gold standard annotations (default: from config)')
    parser.add_argument('--output', type=str, default=None,
                      help='Output report path (default: from config)')
    parser.add_argument('--threshold', type=float, default=0.6,
                      help='Minimum correlation threshold (default: 0.6)')
    
    args = parser.parse_args()
    
    config = get_config()
    
    # Resolve paths
    manifest_path = Path(args.manifest) if args.manifest else config.get_processed_dir() / 'dag_manifest.json'
    gs_path = Path(args.gold_standard) if args.gold_standard else config.get_processed_dir() / 'gold_standard_annotations.json'
    output_path = Path(args.output) if args.output else config.get_processed_dir() / 'validation_report.json'
    
    logger.info(f"Manifest path: {manifest_path}")
    logger.info(f"Gold standard path: {gs_path}")
    logger.info(f"Output path: {output_path}")
    
    try:
        # Load data
        dag_manifest = load_dag_manifest(manifest_path)
        gold_standard = load_gold_standard(gs_path)
        
        # Extract matching data
        dag_depths, human_ratings, matched_ids = extract_matching_data(dag_manifest, gold_standard)
        
        logger.info(f"Sample data (first 5):")
        for i in range(min(5, len(dag_depths))):
            logger.info(f"  {matched_ids[i]}: DAG={dag_depths[i]:.2f}, Human={human_ratings[i]:.2f}")
        
        # Compute correlation
        r_value = compute_correlation(dag_depths, human_ratings)
        
        # Determine pass/fail
        passed = r_value >= args.threshold
        status = "PASS" if passed else "FAIL"
        
        logger.info(f"Correlation {status}: r = {r_value:.4f} >= {args.threshold}")
        
        # Generate report
        report = {
            'status': status,
            'pearson_r': r_value,
            'threshold': args.threshold,
            'num_matched_examples': len(dag_depths),
            'dag_depth_stats': {
                'mean': float(np.mean(dag_depths)),
                'std': float(np.std(dag_depths)),
                'min': float(np.min(dag_depths)),
                'max': float(np.max(dag_depths))
            },
            'human_rating_stats': {
                'mean': float(np.mean(human_ratings)),
                'std': float(np.std(human_ratings)),
                'min': float(np.min(human_ratings)),
                'max': float(np.max(human_ratings))
            },
            'matched_example_ids': matched_ids,
            'manifest_path': str(manifest_path),
            'gold_standard_path': str(gs_path)
        }
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save report
        save_json_file(output_path, report)
        logger.info(f"Validation report saved to {output_path}")
        
        # Exit with appropriate code
        sys.exit(0 if passed else 1)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        report = {
            'status': 'ERROR',
            'error': str(e),
            'pearson_r': None,
            'threshold': args.threshold
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_json_file(output_path, report)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        report = {
            'status': 'ERROR',
            'error': str(e),
            'pearson_r': None,
            'threshold': args.threshold
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_json_file(output_path, report)
        sys.exit(1)

if __name__ == '__main__':
    main()
