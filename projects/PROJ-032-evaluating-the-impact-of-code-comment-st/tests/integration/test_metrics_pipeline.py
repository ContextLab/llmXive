"""
Integration test for the full metric pipeline on a reference repository.

This test validates the end-to-end flow of:
1. Loading a reference repository (assumed to be cloned in data/raw/).
2. Extracting comments via tree-sitter.
3. Calculating metrics: readability, sentiment, density, complexity, churn.
4. Aggregating results into a structured dictionary.

It verifies that the pipeline runs without error and produces
metrics that fall within expected physical bounds.
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
from pathlib import Path
import logging

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from extract import extract_comments_batch, run_extraction_pipeline
from metrics import (
    calc_readability,
    calc_sentiment,
    calc_complexity,
    calc_churn,
    calc_density,
    run_metric_aggregation_with_memory_monitor
)
from utils import configure_logging, CommitSampler

# Configure logging for the test
configure_logging(log_path=str(PROJECT_ROOT / "logs" / "integration_test.log"))
logger = logging.getLogger(__name__)

# Reference repo for testing (using a small, well-known repo if available,
# or creating a mock structure if the full clone is not present).
# We will attempt to use a repo cloned in data/raw/ or create a minimal temp repo.
REF_REPO_NAME = "reference_test_repo"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def setup_reference_repo():
    """
    Ensures a reference repository exists at data/raw/reference_test_repo.
    If not present, creates a minimal git repo with Python files and comments.
    """
    repo_path = DATA_RAW_DIR / REF_REPO_NAME
    
    if repo_path.exists() and (repo_path / ".git").exists():
        logger.info(f"Reference repo found at {repo_path}")
        return repo_path

    logger.info(f"Creating minimal reference repo at {repo_path}")
    repo_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize git
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)

    # Create a Python file with comments
    py_file = repo_path / "sample_code.py"
    py_file.write_text(
        "# This is a simple comment.\n"
        "# Another line of comment.\n"
        "def add(a, b):\n"
        "    # Adds two numbers\n"
        "    return a + b\n"
    )

    # Create a file with docstrings
    py_file2 = repo_path / "sample_doc.py"
    py_file2.write_text(
        '"""Module docstring."""\n'
        "def subtract(a, b):\n"
        '    """Subtracts b from a."""\n'
        "    return a - b\n"
    )

    # Commit
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)

    return repo_path

def test_full_metric_pipeline():
    """
    Runs the full metric pipeline on the reference repo and validates outputs.
    """
    repo_path = setup_reference_repo()
    
    # Ensure processed dir exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_file = DATA_PROCESSED_DIR / "integration_test_results.json"

    logger.info(f"Starting pipeline for {repo_path}")

    try:
        # 1. Extract Comments
        # The extract module expects a path to the repo or files.
        # We use extract_comments_batch which handles directory traversal.
        comments_data = extract_comments_batch([str(repo_path)])
        
        assert isinstance(comments_data, list), "extract_comments_batch must return a list"
        assert len(comments_data) > 0, "Expected comments to be extracted"
        
        logger.info(f"Extracted {len(comments_data)} comment nodes.")

        # 2. Calculate Metrics
        # We aggregate metrics at the repository level for this integration test.
        # The run_metric_aggregation_with_memory_monitor function is designed for this.
        # It expects a list of repo paths.
        
        metrics_result = run_metric_aggregation_with_memory_monitor(
            repo_paths=[str(repo_path)],
            output_file=str(output_file)
        )

        # 3. Validate Results
        assert metrics_result is not None, "Metric aggregation returned None"
        assert "repo_id" in metrics_result, "Missing repo_id in result"
        assert metrics_result["repo_id"] == REF_REPO_NAME, f"Repo ID mismatch: {metrics_result['repo_id']}"

        # Check numeric bounds
        assert 0.0 <= metrics_result.get("readability", 0) <= 100.0, "Readability out of bounds"
        assert -1.0 <= metrics_result.get("sentiment", 0) <= 1.0, "Sentiment out of bounds"
        assert metrics_result.get("density", -1) >= 0.0, "Density cannot be negative"
        assert metrics_result.get("complexity", -1) >= 0.0, "Complexity cannot be negative"
        assert metrics_result.get("churn", -1) >= 0.0, "Churn cannot be negative"

        logger.info("Pipeline metrics validation passed.")
        logger.info(f"Results written to {output_file}")

        # Verify file exists on disk
        assert output_file.exists(), f"Output file {output_file} was not created"

        with open(output_file, "r") as f:
            saved_data = json.load(f)
        
        assert saved_data["repo_id"] == REF_REPO_NAME
        logger.info("Integration test completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    test_full_metric_pipeline()