"""
Stratified Sampler for Phenomenological AI Validation

Selects a representative set of reports per condition for human rating (SC-002).
Ensures balanced sampling across prompting strategies and validity score strata.
"""

import os
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils.io import load_json, safe_write_json, ensure_dir
from utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

class StratifiedSamplingError(Exception):
    """Custom exception for stratified sampling errors."""
    pass

def load_generated_reports(reports_path: Path) -> List[Dict[str, Any]]:
    """
    Load generated reports from the raw data directory.

    Args:
        reports_path: Path to the directory containing generated report JSON files.

    Returns:
        List of report dictionaries.

    Raises:
        StratifiedSamplingError: If no reports are found or loading fails.
    """
    if not reports_path.exists():
        raise StratifiedSamplingError(f"Reports path does not exist: {reports_path}")

    reports = []
    json_files = list(reports_path.glob("*.json"))

    if not json_files:
        raise StratifiedSamplingError(f"No JSON report files found in {reports_path}")

    for json_file in json_files:
        try:
            report = load_json(json_file)
            if report and isinstance(report, dict):
                reports.append(report)
            else:
                logger.warning(f"Skipping invalid report structure in {json_file}")
        except Exception as e:
            logger.warning(f"Failed to load {json_file}: {e}")

    if not reports:
        raise StratifiedSamplingError("No valid reports loaded from the specified path.")

    logger.info(f"Loaded {len(reports)} valid reports from {reports_path}")
    return reports

def validate_report_structure(report: Dict[str, Any]) -> bool:
    """
    Validate that a report has the required fields for stratification.

    Required fields:
    - strategy: The prompting strategy used (e.g., 'Direct', 'Hypothetical')
    - validity_scores: Dict containing metric scores (consistency, stability, markers)

    Args:
        report: A report dictionary.

    Returns:
        True if the report structure is valid, False otherwise.
    """
    required_keys = ['strategy', 'validity_scores']
    for key in required_keys:
        if key not in report:
            logger.debug(f"Report missing required key: {key}")
            return False

    if not isinstance(report['validity_scores'], dict):
        logger.debug("validity_scores is not a dictionary")
        return False

    return True

def stratify_reports(reports: List[Dict[str, Any]], n_per_stratum: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    """
    Stratify reports by prompting strategy and validity score quartiles.

    This ensures human raters see a representative sample across:
    1. Different prompting strategies (Direct, Hypothetical, Comparative, Role-play)
    2. Performance levels (Low, Medium, High validity scores)

    Args:
        reports: List of validated report dictionaries.
        n_per_stratum: Number of samples to select from each stratum.

    Returns:
        Dictionary mapping stratum keys to lists of sampled reports.
    """
    # Group by strategy first
    strategy_groups: Dict[str, List[Dict[str, Any]]] = {}
    for report in reports:
        strategy = report.get('strategy', 'Unknown')
        if strategy not in strategy_groups:
            strategy_groups[strategy] = []
        strategy_groups[strategy].append(report)

    stratified: Dict[str, List[Dict[str, Any]]] = {}

    for strategy, group_reports in strategy_groups.items():
        if not group_reports:
            continue

        # Calculate validity score (composite of consistency, stability, markers)
        # We use the average of the three metrics for stratification
        scored_reports = []
        for report in group_reports:
            scores = report.get('validity_scores', {})
            consistency = scores.get('consistency_score', 0.0) or 0.0
            stability = scores.get('stability_score', 0.0) or 0.0
            markers = scores.get('marker_presence_score', 0.0) or 0.0

            # Avoid division by zero if all are None
            total = consistency + stability + markers
            if total == 0:
                avg_score = 0.0
            else:
                avg_score = total / 3.0

            scored_reports.append((report, avg_score))

        # Sort by score to determine quartiles
        scored_reports.sort(key=lambda x: x[1])
        n_total = len(scored_reports)

        # Define quartile boundaries
        quartile_size = max(1, n_total // 4)

        # Create strata: Low (0-25%), Medium-Low (25-50%), Medium-High (50-75%), High (75-100%)
        strata_labels = ['Low', 'Medium-Low', 'Medium-High', 'High']
        strata_indices = [
            (0, quartile_size),
            (quartile_size, 2 * quartile_size),
            (2 * quartile_size, 3 * quartile_size),
            (3 * quartile_size, n_total)
        ]

        for label, (start, end) in zip(strata_labels, strata_indices):
            stratum_reports = [r for r, _ in scored_reports[start:end]]
            if stratum_reports:
                stratum_key = f"{strategy}_{label}"
                stratified[stratum_key] = stratum_reports

    return stratified

def sample_from_strata(stratified: Dict[str, List[Dict[str, Any]]], n_per_stratum: int = 5) -> List[Dict[str, Any]]:
    """
    Sample a fixed number of reports from each stratum.

    Args:
        stratified: Dictionary of strata (strategy_score_level) to report lists.
        n_per_stratum: Number of samples to take from each stratum.

    Returns:
        List of sampled reports.
    """
    import random

    sampled_reports = []
    total_samples = 0

    for stratum_key, reports in stratified.items():
        # Randomly sample without replacement
        sample_size = min(n_per_stratum, len(reports))
        sample = random.sample(reports, sample_size)
        sampled_reports.extend(sample)
        total_samples += sample_size
        logger.debug(f"Sampled {sample_size} from stratum '{stratum_key}' (size: {len(reports)})")

    logger.info(f"Total sampled reports: {total_samples} from {len(stratified)} strata")
    return sampled_reports

def save_sampled_reports(sampled_reports: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the sampled reports to a JSON file.

    Args:
        sampled_reports: List of report dictionaries to save.
        output_path: Path to the output JSON file.
    """
    ensure_dir(output_path.parent)
    safe_write_json(output_path, sampled_reports)
    logger.info(f"Saved {len(sampled_reports)} sampled reports to {output_path}")

def run_stratified_sampling(
    input_dir: str,
    output_file: str,
    n_per_stratum: int = 5
) -> List[Dict[str, Any]]:
    """
    Orchestrate the full stratified sampling pipeline.

    1. Load all generated reports.
    2. Validate structure.
    3. Stratify by strategy and validity score.
    4. Sample from each stratum.
    5. Save results.

    Args:
        input_dir: Path to the directory containing raw report JSON files.
        output_file: Path to the output JSON file for sampled reports.
        n_per_stratum: Number of samples to select from each stratum.

    Returns:
        List of sampled report dictionaries.
    """
    input_path = Path(input_dir)
    output_path = Path(output_file)

    # Step 1: Load
    reports = load_generated_reports(input_path)

    # Step 2: Validate and filter
    valid_reports = [r for r in reports if validate_report_structure(r)]
    invalid_count = len(reports) - len(valid_reports)
    if invalid_count > 0:
        logger.warning(f"Filtered out {invalid_count} invalid reports.")

    if not valid_reports:
        raise StratifiedSamplingError("No valid reports available for stratification.")

    # Step 3: Stratify
    stratified = stratify_reports(valid_reports)
    logger.info(f"Created {len(stratified)} strata for sampling.")

    # Step 4: Sample
    sampled = sample_from_strata(stratified, n_per_stratum)

    # Step 5: Save
    save_sampled_reports(sampled, output_path)

    return sampled

def main() -> None:
    """
    Entry point for the stratified sampling script.
    Reads from data/raw/ and writes to data/processed/sampled_reports.json.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Stratified sampler for human rating selection.")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/raw",
        help="Directory containing generated report JSON files."
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="data/processed/sampled_reports.json",
        help="Path for the output sampled reports JSON file."
    )
    parser.add_argument(
        "--n-per-stratum",
        type=int,
        default=5,
        help="Number of samples to select from each stratum."
    )

    args = parser.parse_args()

    try:
        run_stratified_sampling(
            input_dir=args.input_dir,
            output_file=args.output_file,
            n_per_stratum=args.n_per_stratum
        )
        logger.info("Stratified sampling completed successfully.")
    except StratifiedSamplingError as e:
        logger.error(f"Stratified sampling failed: {e}")
        raise

if __name__ == "__main__":
    main()