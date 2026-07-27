"""
Generate the master dataset by processing ingestion data and calculating metrics.
"""
import os
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.metrics import (
    calculate_iteration_count,
    calculate_avg_comment_length,
    calculate_review_thread_depth,
    calculate_revert_frequency,
    calculate_diff_complexity_score,
    is_ai_noise_flag,
    calculate_domain_complexity,
    process_review_metrics
)
from utils.config import get_config

logger = logging.getLogger(__name__)


def load_ingestion_data(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load ingestion data from JSON or CSV file.

    Args:
        input_path: Path to the ingestion data file

    Returns:
        List of repository dictionaries
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Ingestion data not found: {input_path}")

    if input_path.suffix == '.json':
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif input_path.suffix == '.csv':
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")


def calculate_repo_metrics(repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate all metrics for a single repository.

    Args:
        repo_data: Dictionary containing repository metadata

    Returns:
        Dictionary with all calculated metrics
    """
    prs = repo_data.get('prs') or []
    commits = repo_data.get('commits') or []
    languages = repo_data.get('languages') or []
    dependencies = repo_data.get('dependencies') or []

    # Process review metrics
    review_metrics = process_review_metrics(repo_data)

    # Calculate iteration count
    all_push_events = []
    for pr in prs:
        push_events = pr.get('push_events') or []
        all_push_events.extend(push_events)

    iteration_count = calculate_iteration_count(all_push_events)

    # Calculate domain complexity
    domain_complexity = calculate_domain_complexity(
        languages,
        len(dependencies)
    )

    # Calculate diff complexity for each commit
    diff_complexity_scores = []
    ai_noise_flags = []

    for commit in commits:
        lines_added = commit.get('lines_added', 0)
        lines_deleted = commit.get('lines_deleted', 0)
        total_lines = commit.get('total_lines', 1)
        message = commit.get('message', '')

        score = calculate_diff_complexity_score(lines_added, lines_deleted, total_lines)
        diff_complexity_scores.append(score)

        if is_ai_noise_flag(score, message):
            ai_noise_flags.append(True)
        else:
            ai_noise_flags.append(False)

    avg_diff_complexity = sum(diff_complexity_scores) / len(diff_complexity_scores) if diff_complexity_scores else 0.0
    ai_noise_ratio = sum(ai_noise_flags) / len(ai_noise_flags) if ai_noise_flags else 0.0

    return {
        'avg_comment_length': review_metrics['avg_comment_length'],
        'review_thread_depth': review_metrics['review_thread_depth'],
        'revert_frequency': review_metrics['revert_frequency'],
        'iteration_count': iteration_count,
        'domain_complexity': domain_complexity,
        'avg_diff_complexity': avg_diff_complexity,
        'ai_noise_ratio': ai_noise_ratio,
        'total_prs': len(prs),
        'total_commits': len(commits)
    }


def write_master_dataset(
    repos: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Write the master dataset to CSV.

    Args:
        repos: List of repository dictionaries with metrics
        output_path: Path to output CSV file
    """
    if not repos:
        logger.warning("No repositories to write to master dataset")
        return

    # Define all columns
    columns = [
        'repo_name',
        'llm_adoption_flag',
        'avg_comment_length',
        'review_thread_depth',
        'revert_frequency',
        'iteration_count',
        'domain_complexity',
        'avg_diff_complexity',
        'ai_noise_ratio',
        'total_prs',
        'total_commits'
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()

        for repo in repos:
            row = {col: repo.get(col, '') for col in columns}
            writer.writerow(row)

    logger.info(f"Master dataset written to {output_path}")


def validate_output(output_path: Path) -> bool:
    """
    Validate the generated master dataset.

    Args:
        output_path: Path to the output CSV file

    Returns:
        True if validation passes, False otherwise
    """
    if not output_path.exists():
        logger.error(f"Output file not found: {output_path}")
        return False

    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        logger.error("Master dataset is empty")
        return False

    # Check required columns
    required_columns = [
        'avg_comment_length',
        'review_thread_depth',
        'revert_frequency',
        'iteration_count'
    ]

    if rows:
        first_row = rows[0]
        for col in required_columns:
            if col not in first_row:
                logger.error(f"Missing required column: {col}")
                return False

    logger.info(f"Validation passed: {len(rows)} rows")
    return True


def main():
    """Main entry point for master dataset generation."""
    config = get_config()
    input_path = config.get('ingestion_data_path', 'data/derived/ingestion_data.json')
    output_path = config.get('master_dataset_path', 'data/derived/master_dataset.csv')

    logging.basicConfig(level=logging.INFO)

    try:
        repos = load_ingestion_data(Path(input_path))
        logger.info(f"Loaded {len(repos)} repositories from ingestion data")

        processed_repos = []
        for repo in repos:
            metrics = calculate_repo_metrics(repo)
            processed_repo = {**repo, **metrics}
            processed_repos.append(processed_repo)

        write_master_dataset(processed_repos, Path(output_path))

        if validate_output(Path(output_path)):
            logger.info("Master dataset generation completed successfully")
        else:
            logger.error("Master dataset validation failed")
            return 1

    except Exception as e:
        logger.error(f"Error generating master dataset: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
