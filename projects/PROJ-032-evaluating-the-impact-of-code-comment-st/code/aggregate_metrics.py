import os
import json
import logging
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from project utils for logging setup
from utils import configure_logging

# Import metric calculation functions to ensure they are available if needed for re-calculation,
# though T027 specifically focuses on aggregation of existing outputs.
# We assume T021, T021b, T022, T023, T024, T025, T006b have run and produced intermediate files.
# However, to be robust and self-contained as per "real runnable research code",
# we will implement the aggregation logic that reads the intermediate JSONs produced by previous steps
# and combines them into the final CSV.

# Expected intermediate files based on task dependencies:
# T021: data/processed/comments.json (contains readability, sentiment, density per repo)
# T024: data/processed/churn_metrics.json (contains churn per repo)
# T025: data/processed/quality_metrics.json (contains bug_fix_rate, quality_rate per repo)
# T006b: data/processed/complexity_metrics.json (contains complexity per repo)

# Note: The exact filenames for intermediate steps might vary slightly based on implementation
# of previous tasks, but we will assume standard naming conventions derived from the task descriptions.
# If previous tasks wrote directly to a single metrics file, this script would need to adapt.
# Given the task is "Aggregate metrics", we assume the existence of separate intermediate files.

# Fallback paths if intermediate files are named differently or merged
COMMENTS_FILE = Path("data/processed/comments.json")
CHURN_FILE = Path("data/processed/churn_metrics.json")
QUALITY_FILE = Path("data/processed/quality_metrics.json")
COMPLEXITY_FILE = Path("data/processed/complexity_metrics.json")
OUTPUT_FILE = Path("data/processed/metrics.csv")

logger = logging.getLogger(__name__)

def load_metric_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON metric file and return its content as a dictionary."""
    if not file_path.exists():
        logger.warning(f"Metric file not found: {file_path}. Skipping.")
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error reading {file_path}: {e}")
        return {}

def aggregate_metrics() -> None:
    """
    Aggregate readability, sentiment, density, churn, bug_fix_rate, and complexity
    into data/processed/metrics.csv with precision >= 2 decimal places.
    
    This function assumes that previous tasks (T021, T024, T025, T006b) have generated
    the necessary intermediate JSON files.
    """
    logger.info("Starting metric aggregation...")
    
    # Load intermediate data
    comments_data = load_metric_file(COMMENTS_FILE)
    churn_data = load_metric_file(CHURN_FILE)
    quality_data = load_metric_file(QUALITY_FILE)
    complexity_data = load_metric_file(COMPLEXITY_FILE)
    
    # Normalize data structures: expected to be a list of dicts or a dict of dicts keyed by repo_id
    # We assume the format is a list of objects where each object has a 'repo_id' field.
    # If it's a dict keyed by repo_id, we convert it to a list.
    
    def normalize_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # If it's a dict of metrics, we might need to construct a list
            # Assuming keys are repo_ids and values are metric dicts
            return [{"repo_id": k, **v} for k, v in data.items()]
        return []

    comments_list = normalize_list(comments_data)
    churn_list = normalize_list(churn_data)
    quality_list = normalize_list(quality_data)
    complexity_list = normalize_list(complexity_data)
    
    # Create a master dictionary keyed by repo_id
    master_metrics: Dict[str, Dict[str, Any]] = {}
    
    # Helper to populate master dict
    def populate_master(source_list: List[Dict[str, Any]], source_name: str):
        for item in source_list:
            repo_id = item.get("repo_id")
            if not repo_id:
                logger.warning(f"Missing repo_id in {source_name}: {item}")
                continue
            if repo_id not in master_metrics:
                master_metrics[repo_id] = {"repo_id": repo_id}
            
            # Merge metrics, avoiding overwriting repo_id
            for key, value in item.items():
                if key != "repo_id":
                    master_metrics[repo_id][key] = value
    
    populate_master(comments_list, "comments")
    populate_master(churn_list, "churn")
    populate_master(quality_list, "quality")
    populate_master(complexity_list, "complexity")
    
    # Define the columns for the output CSV
    # Based on T009 schema: repo_id, readability, sentiment, density, churn, bug_fix_rate, complexity, age, contributors
    # We will include all available metrics from the loaded data.
    columns = ["repo_id", "readability", "sentiment", "density", "churn", "bug_fix_rate", "complexity"]
    
    # Check for optional fields if present in any record
    all_keys = set()
    for repo_metrics in master_metrics.values():
        all_keys.update(repo_metrics.keys())
    
    # Ensure standard columns are first, then append others if they exist
    final_columns = []
    for col in columns:
        if col in all_keys:
            final_columns.append(col)
    for key in sorted(all_keys):
        if key not in final_columns:
            final_columns.append(key)
    
    # Ensure repo_id is first
    if "repo_id" in final_columns:
        final_columns.remove("repo_id")
        final_columns.insert(0, "repo_id")
    
    logger.info(f"Aggregating {len(master_metrics)} repositories.")
    logger.info(f"Output columns: {final_columns}")
    
    # Write to CSV
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=final_columns, extrasaction='ignore')
        writer.writeheader()
        
        for repo_id in sorted(master_metrics.keys()):
            row = master_metrics[repo_id]
            
            # Format numeric values to 2 decimal places
            formatted_row = {}
            for key, value in row.items():
                if isinstance(value, (int, float)):
                    formatted_row[key] = round(float(value), 2)
                else:
                    formatted_row[key] = value
            
            writer.writerow(formatted_row)
    
    logger.info(f"Successfully wrote aggregated metrics to {OUTPUT_FILE}")

def main():
    """Entry point for the aggregation script."""
    log_path = Path("logs/pipeline.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    configure_logging(log_path=str(log_path))
    
    try:
        aggregate_metrics()
        logger.info("Aggregation completed successfully.")
    except Exception as e:
        logger.error(f"Aggregation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
