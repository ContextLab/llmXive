"""
Cohen's Kappa Calculation and Threshold Sensitivity Analysis.

This module implements Cohen's kappa calculation for inter-rater reliability
and performs threshold sensitivity analysis to determine the robustness of
conclusions across a range of kappa thresholds, as required by FR-011.

The analysis reports the benchmark threshold but does not enforce it as a
hard gate in the analysis logic itself.
"""

import os
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# Configure logger
logger = logging.getLogger(__name__)


class KappaSensitivityError(Exception):
    """Custom exception for kappa sensitivity analysis errors."""
    pass


def load_ratings(file_path: str) -> List[Dict[str, Any]]:
    """
    Load human ratings from a CSV file.

    Args:
        file_path: Path to the CSV file containing ratings.
                   Expected columns: 'report_id', 'rater_id', 'rating'.

    Returns:
        List of dictionaries containing rating data.

    Raises:
        KappaSensitivityError: If file not found or invalid format.
    """
    ratings = []
    path = Path(file_path)

    if not path.exists():
        raise KappaSensitivityError(f"Ratings file not found: {file_path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert rating to numeric
                try:
                    row['rating'] = float(row['rating'])
                except (ValueError, KeyError):
                    logger.warning(f"Skipping invalid rating row: {row}")
                    continue
                ratings.append(row)
    except Exception as e:
        raise KappaSensitivityError(f"Failed to parse ratings file: {e}")

    return ratings


def build_rating_matrix(ratings: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Build a matrix of ratings by report_id and rater_id.

    Args:
        ratings: List of rating dictionaries.

    Returns:
        Dictionary mapping report_id to rater_id to rating.
    """
    matrix = {}
    for item in ratings:
        report_id = item['report_id']
        rater_id = item['rater_id']
        rating = item['rating']

        if report_id not in matrix:
            matrix[report_id] = {}
        matrix[report_id][rater_id] = rating

    return matrix


def compute_cohen_kappa(rater1_ratings: List[float], rater2_ratings: List[float]) -> float:
    """
    Compute Cohen's kappa coefficient for two raters.

    Cohen's kappa measures inter-rater agreement for categorical items,
    correcting for agreement occurring by chance.

    Formula: κ = (Po - Pe) / (1 - Pe)
    where:
      Po = observed agreement
      Pe = expected agreement by chance

    Args:
        rater1_ratings: List of ratings from rater 1.
        rater2_ratings: List of ratings from rater 2.

    Returns:
        Cohen's kappa coefficient. Returns -1.0 if calculation fails.
    """
    if len(rater1_ratings) != len(rater2_ratings):
        raise KappaSensitivityError("Rating lists must be of equal length")

    if len(rater1_ratings) == 0:
        return -1.0

    n = len(rater1_ratings)

    # Calculate observed agreement (Po)
    agreements = sum(1 for r1, r2 in zip(rater1_ratings, rater2_ratings) if r1 == r2)
    Po = agreements / n

    # Calculate expected agreement (Pe)
    # Count frequencies for each rater
    from collections import Counter
    count1 = Counter(rater1_ratings)
    count2 = Counter(rater2_ratings)

    Pe = 0.0
    all_categories = set(count1.keys()) | set(count2.keys())

    for category in all_categories:
        p1 = count1.get(category, 0) / n
        p2 = count2.get(category, 0) / n
        Pe += p1 * p2

    # Calculate kappa
    if Pe == 1.0:
        # Perfect agreement by chance (all ratings same category)
        return 1.0 if Po == 1.0 else 0.0

    kappa = (Po - Pe) / (1 - Pe)

    return kappa


def compute_kappa_for_pairs(matrix: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """
    Compute Cohen's kappa for all pairs of raters in the matrix.

    Args:
        matrix: Rating matrix from build_rating_matrix.

    Returns:
        Dictionary mapping (rater1_id, rater2_id) to kappa coefficient.
    """
    raters = set()
    for report_ratings in matrix.values():
        raters.update(report_ratings.keys())

    raters = list(raters)
    kappa_results = {}

    for i, rater1 in enumerate(raters):
        for rater2 in raters[i + 1:]:
            # Collect paired ratings
            rater1_ratings = []
            rater2_ratings = []

            for report_id, ratings in matrix.items():
                if rater1 in ratings and rater2 in ratings:
                    rater1_ratings.append(ratings[rater1])
                    rater2_ratings.append(ratings[rater2])

            if len(rater1_ratings) >= 2:  # Need at least 2 items for meaningful kappa
                try:
                    kappa = compute_cohen_kappa(rater1_ratings, rater2_ratings)
                    kappa_results[(rater1, rater2)] = kappa
                except KappaSensitivityError as e:
                    logger.warning(f"Could not compute kappa for {rater1}-{rater2}: {e}")

    return kappa_results


def analyze_threshold_sensitivity(
    kappa_results: Dict[Tuple[str, str], float],
    thresholds: List[float],
    metric: str = 'proportion_above_threshold'
) -> Dict[str, Any]:
    """
    Analyze robustness of conclusions across a range of kappa thresholds.

    This function tests how conclusions change as the kappa threshold varies,
    addressing FR-011's requirement for threshold sensitivity analysis.

    Args:
        kappa_results: Dictionary of kappa coefficients for rater pairs.
        thresholds: List of kappa thresholds to test.
        metric: Metric to compute ('proportion_above_threshold', 'mean_kappa', etc.)

    Returns:
        Dictionary containing sensitivity analysis results.
    """
    if not kappa_results:
        return {'error': 'No kappa results to analyze'}

    kappa_values = list(kappa_results.values())
    mean_kappa = np.mean(kappa_values)
    std_kappa = np.std(kappa_values)

    sensitivity_results = {
        'thresholds_tested': thresholds,
        'overall_statistics': {
            'mean_kappa': float(mean_kappa),
            'std_kappa': float(std_kappa),
            'min_kappa': float(min(kappa_values)),
            'max_kappa': float(max(kappa_values)),
            'num_pairs': len(kappa_values)
        },
        'threshold_analysis': []
    }

    for threshold in thresholds:
        count_above = sum(1 for k in kappa_values if k >= threshold)
        proportion = count_above / len(kappa_values) if len(kappa_values) > 0 else 0.0

        # Determine conclusion stability
        # If proportion is near 0 or 1, conclusion is stable
        # If proportion is near 0.5, conclusion is sensitive to threshold
        stability = 'stable' if proportion < 0.2 or proportion > 0.8 else 'sensitive'

        sensitivity_results['threshold_analysis'].append({
            'threshold': threshold,
            'pairs_above': count_above,
            'total_pairs': len(kappa_values),
            'proportion_above': float(proportion),
            'conclusion': 'reliable' if proportion > 0.5 else 'unreliable',
            'stability': stability
        })

    # Identify the benchmark threshold (where stability changes)
    benchmark_threshold = mean_kappa  # Default to mean
    for i, analysis in enumerate(sensitivity_results['threshold_analysis']):
        if analysis['stability'] == 'sensitive':
            # The threshold where we're most uncertain is a good benchmark to report
            benchmark_threshold = analysis['threshold']
            break

    sensitivity_results['benchmark_threshold'] = float(benchmark_threshold)
    sensitivity_results['recommendation'] = (
        f"Report benchmark threshold of {benchmark_threshold:.3f}. "
        f"Conclusions are {'stable' if sensitivity_results['threshold_analysis'][0]['stability'] == 'stable' else 'sensitive'} "
        f"across the tested range."
    )

    return sensitivity_results


def run_sensitivity_kappa_analysis(
    ratings_file: str,
    output_file: str,
    thresholds: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Main function to run Cohen's kappa calculation and threshold sensitivity analysis.

    Args:
        ratings_file: Path to the human ratings CSV file.
        output_file: Path to save the analysis results JSON.
        thresholds: List of kappa thresholds to test. Defaults to [0.4, 0.6, 0.8].

    Returns:
        Dictionary containing the full analysis results.
    """
    if thresholds is None:
        thresholds = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    logger.info(f"Loading ratings from {ratings_file}")
    ratings = load_ratings(ratings_file)
    logger.info(f"Loaded {len(ratings)} rating records")

    logger.info("Building rating matrix")
    matrix = build_rating_matrix(ratings)
    logger.info(f"Found {len(matrix)} reports with ratings")

    logger.info("Computing Cohen's kappa for all rater pairs")
    kappa_results = compute_kappa_for_pairs(matrix)
    logger.info(f"Computed {len(kappa_results)} kappa coefficients")

    logger.info(f"Running threshold sensitivity analysis with thresholds: {thresholds}")
    sensitivity_results = analyze_threshold_sensitivity(kappa_results, thresholds)

    # Prepare final output
    output = {
        'metadata': {
            'ratings_file': ratings_file,
            'thresholds_tested': thresholds,
            'num_rater_pairs': len(kappa_results)
        },
        'kappa_coefficients': {
            f"{pair[0]}-{pair[1]}": float(k) for pair, k in kappa_results.items()
        },
        'sensitivity_analysis': sensitivity_results
    }

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    logger.info(f"Analysis results saved to {output_file}")

    return output


def main():
    """
    Entry point for running Cohen's kappa sensitivity analysis from the command line.

    Usage:
        python -m code.analysis.sensitivity_kappa \
            --ratings data/qualitative/ratings.csv \
            --output data/processed/kappa_sensitivity.json
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Compute Cohen\'s kappa and perform threshold sensitivity analysis.'
    )
    parser.add_argument(
        '--ratings',
        type=str,
        default='data/qualitative/ratings.csv',
        help='Path to the human ratings CSV file.'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/kappa_sensitivity.json',
        help='Path to save the analysis results JSON.'
    )
    parser.add_argument(
        '--thresholds',
        type=str,
        default='0.0,0.2,0.4,0.6,0.8,1.0',
        help='Comma-separated list of kappa thresholds to test.'
    )

    args = parser.parse_args()

    # Parse thresholds
    thresholds = [float(t.strip()) for t in args.thresholds.split(',')]

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        results = run_sensitivity_kappa_analysis(
            ratings_file=args.ratings,
            output_file=args.output,
            thresholds=thresholds
        )

        # Print summary
        print("\n" + "=" * 60)
        print("COHEN'S KAPPA SENSITIVITY ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Mean Kappa: {results['sensitivity_analysis']['overall_statistics']['mean_kappa']:.3f}")
        print(f"Std Kappa:  {results['sensitivity_analysis']['overall_statistics']['std_kappa']:.3f}")
        print(f"Benchmark Threshold: {results['sensitivity_analysis']['benchmark_threshold']:.3f}")
        print(f"\nRecommendation: {results['sensitivity_analysis']['recommendation']}")
        print(f"\nResults saved to: {args.output}")
        print("=" * 60)

    except KappaSensitivityError as e:
        logger.error(f"Analysis failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == '__main__':
    main()
