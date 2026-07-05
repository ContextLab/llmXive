"""
Generate the master dataset CSV from ingestion results.

This script loads the raw JSON data produced by `code/ingest.py` (or fetches it
if not present), applies the required metric calculations (including the updated
iteration count logic per FR-002), and writes the final `data/derived/master_dataset.csv`.

It ensures all required columns are present and validates the schema before writing.
"""
import os
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project modules
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
from utils.data_validation import validate_csv_schema, ValidationResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "ingestion_results.json"
MASTER_DATASET_PATH = DATA_DERIVED_DIR / "master_dataset.csv"

# Required columns as per spec and analysis needs
REQUIRED_COLUMNS = [
    "repo_id",
    "repo_name",
    "llm_adoption_flag",
    "iteration_count",
    "avg_comment_length",
    "review_thread_depth",
    "revert_frequency",
    "diff_complexity_score",
    "is_ai_noise_flag",
    "domain_complexity",
    "total_prs",
    "total_commits",
    "total_lines",
    "languages",
    "dependencies_count",
    "has_cursorrules",
    "has_copilot_config",
    "copilot_commit_frequency"
]

def load_ingestion_data() -> List[Dict[str, Any]]:
    """Load raw ingestion data from JSON."""
    if not RAW_DATA_PATH.exists():
        logger.error(f"Raw data file not found: {RAW_DATA_PATH}")
        raise FileNotFoundError(f"Raw data file not found: {RAW_DATA_PATH}")
    
    with open(RAW_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        logger.error("Ingestion data must be a list of repository objects.")
        raise ValueError("Ingestion data must be a list of repository objects.")
    
    return data

def calculate_repo_metrics(repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate all derived metrics for a single repository."""
    # Extract raw data fields
    prs = repo_data.get("prs", [])
    commits = repo_data.get("commits", [])
    config_files = repo_data.get("config_files", {})
    languages = repo_data.get("languages", [])
    dependencies = repo_data.get("dependencies", [])
    
    # Basic counts
    total_prs = len(prs)
    total_commits = len(commits)
    total_lines = sum(c.get("lines", 0) for c in commits)
    
    # LLM Adoption flags (from ingestion logic)
    has_cursorrules = config_files.get("has_cursorrules", False)
    has_copilot_config = config_files.get("has_copilot_config", False)
    copilot_commit_frequency = repo_data.get("copilot_commit_frequency", 0.0)
    llm_adoption_flag = repo_data.get("llm_adoption_flag", False)
    
    # Calculate metrics using utility functions
    # Note: calculate_iteration_count expects PR and commit data structure
    iteration_count = calculate_iteration_count(prs, commits)
    
    avg_comment_length = calculate_avg_comment_length(prs)
    review_thread_depth = calculate_review_thread_depth(prs)
    revert_frequency = calculate_revert_frequency(commits)
    
    # Domain complexity
    domain_complexity = calculate_domain_complexity(languages, dependencies)
    
    # Diff complexity and AI noise flag (calculated per commit, then aggregated)
    # For the master dataset, we aggregate to a repo-level metric
    # We calculate the average diff_complexity_score and if any commit is AI Noise
    diff_scores = []
    has_ai_noise = False
    
    for commit in commits:
        lines_added = commit.get("lines_added", 0)
        lines_deleted = commit.get("lines_deleted", 0)
        commit_total_lines = lines_added + lines_deleted
        
        if commit_total_lines > 0:
            score = calculate_diff_complexity_score(lines_added, lines_deleted, commit_total_lines)
            diff_scores.append(score)
            
            if is_ai_noise_flag(score, commit.get("message", "")):
                has_ai_noise = True
    
    avg_diff_complexity = sum(diff_scores) / len(diff_scores) if diff_scores else 0.0
    
    # Construct the result row
    row = {
        "repo_id": repo_data.get("repo_id", ""),
        "repo_name": repo_data.get("repo_name", ""),
        "llm_adoption_flag": llm_adoption_flag,
        "iteration_count": iteration_count,
        "avg_comment_length": avg_comment_length,
        "review_thread_depth": review_thread_depth,
        "revert_frequency": revert_frequency,
        "diff_complexity_score": avg_diff_complexity,
        "is_ai_noise_flag": has_ai_noise,
        "domain_complexity": domain_complexity,
        "total_prs": total_prs,
        "total_commits": total_commits,
        "total_lines": total_lines,
        "languages": ",".join(languages) if languages else "",
        "dependencies_count": len(dependencies),
        "has_cursorrules": has_cursorrules,
        "has_copilot_config": has_copilot_config,
        "copilot_commit_frequency": copilot_commit_frequency
    }
    
    return row

def write_master_dataset(rows: List[Dict[str, Any]]) -> str:
    """Write the master dataset to CSV."""
    # Ensure output directory exists
    DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(MASTER_DATASET_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Master dataset written to {MASTER_DATASET_PATH}")
    return str(MASTER_DATASET_PATH)

def validate_output() -> bool:
    """Validate the generated CSV against the expected schema."""
    result = validate_csv_schema(MASTER_DATASET_PATH, REQUIRED_COLUMNS)
    if result.is_valid:
        logger.info("Schema validation passed.")
        return True
    else:
        logger.error(f"Schema validation failed: {result.errors}")
        return False

def main():
    """Main entry point for generating the master dataset."""
    try:
        logger.info("Loading ingestion data...")
        raw_data = load_ingestion_data()
        
        logger.info(f"Processing {len(raw_data)} repositories...")
        processed_rows = []
        
        for i, repo in enumerate(raw_data):
            # Skip repos with < 10 PRs (SC-001) - handled in ingest.py but double check here
            if repo.get("total_prs", 0) < 10:
                logger.debug(f"Skipping repo {repo.get('repo_name')} (PR count < 10)")
                continue
            
            row = calculate_repo_metrics(repo)
            processed_rows.append(row)
            
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{len(raw_data)} repos...")
        
        if not processed_rows:
            logger.warning("No repositories met the criteria. Output file will be empty (header only).")
        
        logger.info("Writing master dataset...")
        write_master_dataset(processed_rows)
        
        logger.info("Validating output...")
        if validate_output():
            logger.info("Master dataset generation completed successfully.")
            return 0
        else:
            logger.error("Master dataset generation failed validation.")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during dataset generation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
