import os
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

# Import configuration for marker dictionaries
# Assuming config.py is in the code/ root relative to code/analysis/
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import get_marker_dictionaries

from utils.io import safe_write_csv, load_json
from utils.logging import get_logger, retry_on_failure

logger = get_logger(__name__)

class MarkerError(Exception):
    """Custom exception for marker analysis errors."""
    pass

def count_markers_in_text(text: str, markers: List[str]) -> int:
    """
    Count occurrences of specific markers in a text.
    Case-insensitive, whole-word matching to avoid partial matches.
    """
    if not text:
        return 0
    
    count = 0
    # Create a regex pattern for whole word matching, case insensitive
    # Escape special regex characters in markers
    escaped_markers = [re.escape(m) for m in markers]
    pattern = r'\b(' + '|'.join(escaped_markers) + r')\b'
    
    matches = re.findall(pattern, text, re.IGNORECASE)
    return len(matches)

def compute_marker_scores(
    text: str, 
    marker_dict: Dict[str, List[str]]
) -> Dict[str, float]:
    """
    Compute raw counts and normalized scores for each marker category.
    
    Args:
        text: The phenomenological report text
        marker_dict: Dictionary with keys 'sensory', 'temporal', 'intentional'
                    
    Returns:
        Dictionary with counts and densities for each category
    """
    if not text:
        return {
            'sensory_count': 0, 'sensory_density': 0.0,
            'temporal_count': 0, 'temporal_density': 0.0,
            'intentional_count': 0, 'intentional_density': 0.0,
            'total_markers': 0, 'marker_density': 0.0
        }

    word_count = len(text.split())
    if word_count == 0:
        word_count = 1  # Avoid division by zero

    results = {}
    total_count = 0

    for category, markers in marker_dict.items():
        count = count_markers_in_text(text, markers)
        results[f'{category}_count'] = count
        results[f'{category}_density'] = count / word_count
        total_count += count

    results['total_markers'] = total_count
    results['marker_density'] = total_count / word_count

    return results

def run_marker_analysis(
    input_path: str,
    output_path: str,
    marker_config: Optional[Dict[str, List[str]]] = None
) -> List[Dict[str, Any]]:
    """
    Load generated reports, compute marker metrics, and save results.
    
    Args:
        input_path: Path to JSONL or JSON file containing generated reports
        output_path: Path to save CSV results
        marker_config: Optional override for marker dictionaries. 
                       If None, loads from config.py.
                       
    Returns:
        List of dictionaries containing marker scores for each report
    """
    # Load marker dictionaries
    if marker_config is None:
        marker_config = get_marker_dictionaries()
    
    # Validate marker config
    required_keys = ['sensory', 'temporal', 'intentional']
    for key in required_keys:
        if key not in marker_config:
            raise MarkerError(f"Marker config missing required key: {key}")
    
    logger.info(f"Loaded marker dictionaries: {list(marker_config.keys())}")
    logger.info(f"  Sensory: {len(marker_config['sensory'])} keywords")
    logger.info(f"  Temporal: {len(marker_config['temporal'])} keywords")
    logger.info(f"  Intentional: {len(marker_config['intentional'])} keywords")

    # Load input data
    input_file = Path(input_path)
    if not input_file.exists():
        raise MarkerError(f"Input file not found: {input_path}")

    if input_file.suffix == '.jsonl':
        with open(input_file, 'r', encoding='utf-8') as f:
            reports = [json.loads(line) for line in f]
    elif input_file.suffix == '.json':
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            reports = data if isinstance(data, list) else [data]
    else:
        raise MarkerError(f"Unsupported input format: {input_file.suffix}")

    logger.info(f"Loaded {len(reports)} reports from {input_path}")

    # Compute scores
    results = []
    for idx, report in enumerate(reports):
        # Extract text - handle different possible keys
        text = report.get('text') or report.get('content') or report.get('generated_text')
        if not text:
            logger.warning(f"Report {idx} missing text field, skipping")
            continue

        scores = compute_marker_scores(text, marker_config)
        
        # Preserve metadata
        result_entry = {
            'report_id': report.get('id', idx),
            'prompt_id': report.get('prompt_id', report.get('prompt')),
            'strategy': report.get('strategy', 'unknown'),
            'seed': report.get('seed', 0),
            **scores
        }
        results.append(result_entry)

    logger.info(f"Computed marker scores for {len(results)} reports")

    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if results:
        safe_write_csv(results, str(output_file))
        logger.info(f"Saved marker analysis results to {output_path}")
    else:
        logger.warning("No results to save")

    return results

def main():
    """Entry point for marker analysis script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute phenomenological marker metrics on generated reports."
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        default='data/raw/generation_corpus.jsonl',
        help='Path to input JSONL file with generated reports'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='data/processed/marker_scores.csv',
        help='Path to output CSV file'
    )
    parser.add_argument(
        '--config', '-c',
        type=str,
        default=None,
        help='Optional path to custom marker configuration JSON'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    marker_config = None
    if args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            marker_config = json.load(f)
        logger.info(f"Using custom marker config from {args.config}")

    try:
        results = run_marker_analysis(
            input_path=args.input,
            output_path=args.output,
            marker_config=marker_config
        )
        
        # Summary statistics
        if results:
            total = len(results)
            avg_sensory = np.mean([r['sensory_count'] for r in results])
            avg_temporal = np.mean([r['temporal_count'] for r in results])
            avg_intentional = np.mean([r['intentional_count'] for r in results])
            avg_density = np.mean([r['marker_density'] for r in results])
            
            logger.info(f"Summary (n={total}):")
            logger.info(f"  Avg Sensory markers: {avg_sensory:.2f}")
            logger.info(f"  Avg Temporal markers: {avg_temporal:.2f}")
            logger.info(f"  Avg Intentional markers: {avg_intentional:.2f}")
            logger.info(f"  Avg Total Marker Density: {avg_density:.4f}")

    except MarkerError as e:
        logger.error(f"Marker analysis failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during marker analysis: {e}")
        raise

if __name__ == '__main__':
    main()
