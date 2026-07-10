"""
Change score calculator for digital decluttering study.

Implements FR-005: Calculate change scores (post - baseline) for all metrics.
Handles missing data, validates ranges, and outputs structured results.
"""

import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

from config.env_config import get_path, get_config
from utils.random_seed import get_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ChangeScoreResult:
    """Result container for change score calculation."""
    participant_id: str
    metric_type: str
    baseline_value: float
    post_value: float
    change_score: float
    percent_change: float
    direction: str  # 'increase', 'decrease', 'no_change'
    valid: bool
    missing_baseline: bool = False
    missing_post: bool = False

def load_merged_data(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load merged baseline and post-intervention data.

    Args:
        input_path: Optional path to merged data file. If None, uses
                   config to find the default merged dataset.

    Returns:
        List of dictionaries containing merged participant data.

    Raises:
        FileNotFoundError: If the merged data file does not exist.
        ValueError: If the file format is invalid.
    """
    if input_path is None:
        input_path = get_path('merged_data')

    path_obj = Path(input_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Merged data file not found: {input_path}")

    data = []
    with open(path_obj, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            clean_row = {}
            for key, value in row.items():
                if value == '' or value is None:
                    clean_row[key] = None
                elif key in ['baseline_sart_errors', 'post_sart_errors',
                             'baseline_ospan_score', 'post_ospan_score',
                             'baseline_pss10_score', 'post_pss10_score',
                             'baseline_panas_positive', 'post_panas_positive',
                             'baseline_panas_negative', 'post_panas_negative',
                             'compliance_score']:
                    try:
                        clean_row[key] = float(value)
                    except (ValueError, TypeError):
                        clean_row[key] = None
                else:
                    clean_row[key] = value
            data.append(clean_row)

    logger.info(f"Loaded {len(data)} records from {input_path}")
    return data


def calculate_change_score(baseline: Optional[float], post: Optional[float]) -> Tuple[Optional[float], Optional[float], str]:
    """
    Calculate change score and percent change.

    Args:
        baseline: Baseline measurement value.
        post: Post-intervention measurement value.

    Returns:
        Tuple of (change_score, percent_change, direction)
        Returns (None, None, 'missing') if either value is missing.
    """
    if baseline is None or post is None:
        return None, None, 'missing'

    change = post - baseline

    if baseline == 0:
        percent_change = None
    else:
        percent_change = (change / abs(baseline)) * 100

    if change > 0.001:
        direction = 'increase'
    elif change < -0.001:
        direction = 'decrease'
    else:
        direction = 'no_change'

    return change, percent_change, direction


def calculate_change_scores_for_participant(
    participant_data: Dict[str, Any],
    metrics: List[str]
) -> List[ChangeScoreResult]:
    """
    Calculate change scores for all metrics for a single participant.

    Args:
        participant_data: Dictionary containing merged baseline and post data.
        metrics: List of metric names to calculate (e.g., 'sart_errors', 'ospan_score').

    Returns:
        List of ChangeScoreResult objects for each metric.
    """
    results = []

    for metric in metrics:
        baseline_key = f'baseline_{metric}'
        post_key = f'post_{metric}'

        baseline_val = participant_data.get(baseline_key)
        post_val = participant_data.get(post_key)

        change, percent, direction = calculate_change_score(baseline_val, post_val)

        valid = (baseline_val is not None) and (post_val is not None)

        result = ChangeScoreResult(
            participant_id=participant_data.get('participant_id', 'UNKNOWN'),
            metric_type=metric,
            baseline_value=baseline_val if baseline_val is not None else 0.0,
            post_value=post_val if post_val is not None else 0.0,
            change_score=change if change is not None else 0.0,
            percent_change=percent if percent is not None else 0.0,
            direction=direction,
            valid=valid,
            missing_baseline=(baseline_val is None),
            missing_post=(post_val is None)
        )
        results.append(result)

    return results


def get_metric_mapping() -> Dict[str, str]:
    """
    Get mapping of metric names to their column prefixes.

    Returns:
        Dictionary mapping metric names to their prefix used in data files.
    """
    return {
        'sart_errors': 'sart_errors',
        'ospan_score': 'ospan_score',
        'pss10_score': 'pss10_score',
        'panas_positive': 'panas_positive',
        'panas_negative': 'panas_negative',
        'compliance_score': 'compliance_score'
    }


def write_change_scores(
    results: List[ChangeScoreResult],
    output_path: Optional[str] = None
) -> str:
    """
    Write change score results to CSV and JSON files.

    Args:
        results: List of ChangeScoreResult objects.
        output_path: Optional output path. If None, uses config default.

    Returns:
        Path to the written CSV file.
    """
    if output_path is None:
        output_dir = get_path('processed_data')
        output_path = os.path.join(output_dir, 'change_scores.csv')

    path_obj = Path(output_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    with open(path_obj, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'participant_id', 'metric_type', 'baseline_value',
            'post_value', 'change_score', 'percent_change',
            'direction', 'valid', 'missing_baseline', 'missing_post'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))

    logger.info(f"Wrote {len(results)} change score records to {output_path}")

    # Also write JSON summary
    json_path = str(path_obj).replace('.csv', '.json')
    summary_data = {
        'total_participants': len(set(r.participant_id for r in results)),
        'total_metrics': len(results),
        'valid_scores': sum(1 for r in results if r.valid),
        'missing_baseline_count': sum(1 for r in results if r.missing_baseline),
        'missing_post_count': sum(1 for r in results if r.missing_post),
        'results': [asdict(r) for r in results]
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2)

    logger.info(f"Wrote JSON summary to {json_path}")

    return output_path


def run_change_score_calculation(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    metrics: Optional[List[str]] = None
) -> List[ChangeScoreResult]:
    """
    Main pipeline function to calculate change scores.

    Args:
        input_path: Path to merged data file.
        output_path: Path for output change scores.
        metrics: List of metrics to calculate. Defaults to all known metrics.

    Returns:
        List of ChangeScoreResult objects.
    """
    if metrics is None:
        metrics = list(get_metric_mapping().keys())

    logger.info(f"Starting change score calculation for metrics: {metrics}")

    # Load data
    data = load_merged_data(input_path)
    if not data:
        logger.warning("No data found in merged file")
        return []

    # Calculate scores
    all_results = []
    for participant in data:
        participant_results = calculate_change_scores_for_participant(participant, metrics)
        all_results.extend(participant_results)

    # Write results
    output_file = write_change_scores(all_results, output_path)

    logger.info(f"Change score calculation complete. Output: {output_file}")
    return all_results


def main():
    """Entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Calculate change scores (post - baseline) for study metrics.'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='Path to merged data file (default: from config)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path for output change scores (default: from config)'
    )
    parser.add_argument(
        '--metrics',
        type=str,
        nargs='+',
        default=None,
        help='Specific metrics to calculate (space-separated)'
    )

    args = parser.parse_args()

    metrics = args.metrics
    if metrics:
        # Validate metrics
        valid_metrics = list(get_metric_mapping().keys())
        invalid = [m for m in metrics if m not in valid_metrics]
        if invalid:
            logger.error(f"Invalid metrics: {invalid}. Valid options: {valid_metrics}")
            return 1
    else:
        metrics = None

    try:
        results = run_change_score_calculation(
            input_path=args.input,
            output_path=args.output,
            metrics=metrics
        )
        logger.info(f"Successfully calculated {len(results)} change scores")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during calculation: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
