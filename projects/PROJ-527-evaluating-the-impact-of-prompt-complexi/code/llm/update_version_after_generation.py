"""
Script to update project version manifest after data generation.
This script is called by the main pipeline after generating prompt variants
and execution results to ensure the state manifest is up-to-date.
"""

import sys
from pathlib import Path

from utils.logger import get_logger
from utils.versioning import update_project_manifest

logger = get_logger(__name__)


def main():
    """
    Update the project manifest with newly generated artifacts.
    Expected artifacts (relative to project root):
      - data/processed/prompt_variants.parquet
      - data/results/execution_outcomes.csv
      - data/results/analysis_summary.csv
      - data/results/manual_review_queue.csv
    """
    project_id = "PROJ-527-evaluating-the-impact-of-prompt-complexi"
    output_dir = Path("state/projects")

    # Define artifacts to track
    artifacts_to_track = [
        "data/processed/prompt_variants.parquet",
        "data/results/execution_outcomes.csv",
        "data/results/analysis_summary.csv",
        "data/results/manual_review_queue.csv",
    ]

    logger.info(f"Starting manifest update for project {project_id}")

    for artifact_path_str in artifacts_to_track:
        artifact_path = Path(artifact_path_str)
        if artifact_path.exists():
            try:
                update_project_manifest(project_id, artifact_path, output_dir)
                logger.info(f"Updated manifest with {artifact_path}")
            except Exception as e:
                logger.error(f"Failed to update manifest with {artifact_path}: {e}")
                sys.exit(1)
        else:
            logger.warning(f"Artifact not found, skipping: {artifact_path}")

    logger.info("Manifest update completed successfully")


if __name__ == "__main__":
    main()