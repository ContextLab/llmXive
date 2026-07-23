"""
T021b: Execute rubric on candidate repos, calculate LOC/CC metrics,
generate rubric and metrics JSONs, implement exclusion logic,
and record checksums.
"""
import json
import os
import sys
import hashlib
import logging
from typing import List, Dict, Any, Tuple

# Import from the provided API surface
from validation import (
    run_rubric_on_candidates,
    scan_repository_for_metrics,
    evaluate_repository_rubric
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_RAW_DIR = "data/raw"
DATA_CHECKSUMS_FILE = "data/checksums.txt"
RUBRIC_OUTPUT = os.path.join(DATA_RAW_DIR, "repo_selection_rubric.json")
METRICS_OUTPUT = os.path.join(DATA_RAW_DIR, "repo_metrics.json")

# Candidate repositories (hardcoded for this task as per typical pipeline setup)
# In a real scenario, these might come from a config or previous selection step
CANDIDATE_REPOS = [
    "https://github.com/pallets/flask.git",
    "https://github.com/psf/requests.git",
    "https://github.com/charliermarsh/ruff.git"
]

def ensure_dirs():
    """Ensure output directories exist."""
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DATA_CHECKSUMS_FILE), exist_ok=True)

def calculate_file_checksum(filepath: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums(filepath: str, checksum: str):
    """Append or update checksum in the checksums file."""
    with open(DATA_CHECKSUMS_FILE, "a") as f:
        f.write(f"{os.path.basename(filepath)}:{checksum}\n")

def main():
    logger.info("Starting T021b: Rubric execution and metrics collection")
    ensure_dirs()

    # 1. Run Rubric on Candidates
    # This calls the function from validation.py which implements T021a logic
    rubric_results = run_rubric_on_candidates(CANDIDATE_REPOS)

    # 2. Calculate Metrics (LOC, CC) for each repo
    # We need to collect metrics for ALL candidates first, then filter
    all_metrics = []
    for repo_url in CANDIDATE_REPOS:
        try:
            # scan_repository_for_metrics returns dict with loc, cc, etc.
            metrics = scan_repository_for_metrics(repo_url)
            metrics['repo_url'] = repo_url
            all_metrics.append(metrics)
        except Exception as e:
            logger.error(f"Failed to process metrics for {repo_url}: {e}")
            # Log error but continue with others if possible
            continue

    # 3. Determine Exclusions based on Rubric
    # The rubric result should contain a 'passed' or 'excluded' flag
    # We assume run_rubric_on_candidates returns a list of dicts with 'repo_url', 'score', 'passed'
    passed_repos = [r for r in rubric_results if r.get('passed', False)]
    excluded_repos = [r for r in rubric_results if not r.get('passed', False)]

    logger.info(f"Passed repos: {len(passed_repos)}")
    logger.info(f"Excluded repos: {len(excluded_repos)}")

    # 4. Filter metrics to only include passed repos (or keep all with exclusion flag?)
    # Task says "implement exclusion logic for failing repos".
    # Usually, we save the full rubric, but the metrics used for analysis might be filtered.
    # Let's save the metrics for the passed repos as the primary dataset for next steps,
    # but we can also include a flag in the metrics JSON if needed.
    # For T021c (covariates), we likely need metrics of the selected repos.
    selected_metrics = [m for m in all_metrics if any(r['repo_url'] == m['repo_url'] for r in passed_repos)]

    # 5. Write Outputs
    # Write Rubric JSON
    with open(RUBRIC_OUTPUT, "w") as f:
        json.dump(rubric_results, f, indent=2)
    logger.info(f"Wrote rubric results to {RUBRIC_OUTPUT}")

    # Write Metrics JSON
    with open(METRICS_OUTPUT, "w") as f:
        json.dump(selected_metrics, f, indent=2)
    logger.info(f"Wrote metrics for selected repos to {METRICS_OUTPUT}")

    # 6. Generate Checksums
    # Task: "generate a checksum of data/raw/repo_selection_rubric.json and record it in data/checksums.txt"
    rubric_checksum = calculate_file_checksum(RUBRIC_OUTPUT)
    update_checksums(RUBRIC_OUTPUT, rubric_checksum)
    logger.info(f"Checksum for {RUBRIC_OUTPUT}: {rubric_checksum}")

    # Also checksum the metrics file for integrity
    metrics_checksum = calculate_file_checksum(METRICS_OUTPUT)
    update_checksums(METRICS_OUTPUT, metrics_checksum)
    logger.info(f"Checksum for {METRICS_OUTPUT}: {metrics_checksum}")

    logger.info("T021b completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
