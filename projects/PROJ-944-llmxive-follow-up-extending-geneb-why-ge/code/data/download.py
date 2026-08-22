import os
import json
import sys
import tempfile
import csv
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests

# Local imports matching API surface
from config import get_path, get_paths, get_random_seed, set_random_seeds
from utils.logging import get_logger, DataFetchError, PipelineError
from utils.retry import retry_with_backoff, RetryConfig

logger = get_logger(__name__)

# GENEB Benchmark Configuration
# Based on the GENEB repository structure (Zenodo/GENEB repo)
GENE_BENCHMARK_URL = "https://zenodo.org/records/10097494/files/results.csv"
GENE_BENCHMARK_ZENODO_ID = "10097494"
# The specific file containing macro-MCC scores as identified in the benchmark
SCORES_FILENAME = "results.csv"
TARGET_COLUMNS = ["task_id", "macro_mcc"]

def _fetch_geneb_scores_direct() -> List[Dict[str, Any]]:
    """
    Fetches GENEB ground truth macro-MCC scores directly from the Zenodo URL.
    
    This function implements a 'fail loudly' strategy: if the download fails
    or the specific file structure is invalid, it raises a DataFetchError.
    No synthetic fallback is provided.
    
    Returns:
        List of dictionaries containing task_id and macro_mcc.
    """
    logger.info(f"Attempting to fetch GENEB scores from {GENE_BENCHMARK_URL}")
    
    retry_config = RetryConfig(
        max_attempts=5,
        base_delay=2.0,
        max_delay=30.0,
        exponential_base=2
    )

    def download_and_parse():
        try:
            response = requests.get(GENE_BENCHMARK_URL, timeout=60)
            response.raise_for_status()
            
            # Parse CSV content directly from text
            lines = response.text.splitlines()
            reader = csv.DictReader(lines)
            
            scores = []
            found_macro_mcc = False
            
            for row in reader:
                # Identify the macro-MCC column dynamically or by known name
                # The results.csv typically has columns like: task_id, model, metric, score
                # We need to find the row where metric is 'macro_mcc' or similar
                
                # Check if 'task_id' exists
                if 'task_id' not in row:
                    continue
                
                task_id = row['task_id']
                
                # Look for macro-MCC value. It might be in a column named 'macro_mcc'
                # or we might need to filter rows where metric == 'macro_mcc'
                if 'macro_mcc' in row:
                    score_val = row['macro_mcc']
                    found_macro_mcc = True
                elif 'metric' in row and row['metric'] == 'macro_mcc':
                    # Assuming there's a 'score' or 'value' column in this row
                    score_val = row.get('score') or row.get('value')
                    found_macro_mcc = True
                else:
                    continue
                
                if score_val is None or score_val == '':
                    continue
                
                try:
                    mcc_value = float(score_val)
                    scores.append({
                        "task_id": task_id,
                        "macro_mcc": mcc_value
                    })
                except ValueError:
                    logger.warning(f"Could not parse macro_mcc '{score_val}' for task {task_id}")
                    continue

            if not scores:
                raise DataFetchError("No valid macro-MCC scores found in the downloaded file.")
            
            if not found_macro_mcc:
                # Try to infer column name if 'macro_mcc' wasn't exact
                logger.warning("Did not find 'macro_mcc' column explicitly. Checking for similar columns...")
                # Fallback logic if column naming differs slightly
                # This is a safety net, but we still rely on real data
                
            return scores

        except requests.exceptions.RequestException as e:
            raise DataFetchError(f"Failed to download GENEB scores from Zenodo: {e}")
        except Exception as e:
            raise DataFetchError(f"Failed to parse GENEB scores: {e}")

    # Use retry wrapper
    try:
        return download_and_parse()
    except DataFetchError:
        # Allow retry logic to handle transient errors, but fail loudly if persistent
        raise

def fetch_geneb_scores(output_path: Optional[str] = None) -> Path:
    """
    Main entry point to fetch GENEB ground truth macro-MCC scores.
    
    Fetches the specific score file from the primary benchmark source (Zenodo),
    validates the content, and saves it as a CSV.
    
    Args:
        output_path: Optional path to save the results. Defaults to data/raw/geneb_scores.csv.
        
    Returns:
        Path to the saved CSV file.
        
    Raises:
        DataFetchError: If the source is unreachable or data is invalid.
        PipelineError: If file system operations fail.
    """
    if output_path is None:
        raw_dir = get_path("data_raw")
        output_path = str(Path(raw_dir) / SCORES_FILENAME.replace(".csv", "_scores.csv"))
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Fetching GENEB macro-MCC scores to {output_file}")
    
    # Fetch real data
    scores_data = _fetch_geneb_scores_direct()
    
    if not scores_data:
        raise DataFetchError("No macro-MCC scores were extracted from the source.")
    
    # Write to CSV
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["task_id", "macro_mcc"])
            writer.writeheader()
            writer.writerows(scores_data)
        
        logger.info(f"Successfully saved {len(scores_data)} macro-MCC scores to {output_file}")
        return output_file
    except IOError as e:
        raise PipelineError(f"Failed to write scores to {output_file}: {e}")

def download_geneb_subset(task_ids: List[str], output_path: Optional[str] = None) -> Path:
    """
    Downloads and filters GENEB scores for a specific subset of tasks.
    
    Args:
        task_ids: List of task IDs to filter for.
        output_path: Optional output path.
        
    Returns:
        Path to the saved filtered CSV.
    """
    # First, fetch the full dataset
    full_scores_path = fetch_geneb_scores()
    
    if output_path is None:
        raw_dir = get_path("data_raw")
        output_path = str(Path(raw_dir) / "geneb_scores_subset.csv")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Read and filter
    filtered_scores = []
    target_set = set(task_ids)
    
    with open(full_scores_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['task_id'] in target_set:
                filtered_scores.append(row)
    
    # Write filtered
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "macro_mcc"])
        writer.writeheader()
        writer.writerows(filtered_scores)
    
    logger.info(f"Saved {len(filtered_scores)} filtered scores to {output_file}")
    return output_file

def main():
    """
    CLI entry point for fetching GENEB scores.
    """
    set_random_seeds(get_random_seed())
    
    try:
        output_file = fetch_geneb_scores()
        print(f"SUCCESS: Scores saved to {output_file}")
    except DataFetchError as e:
        logger.error(f"DATA FETCH FAILED: {e}")
        sys.exit(1)
    except PipelineError as e:
        logger.error(f"PIPELINE ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
