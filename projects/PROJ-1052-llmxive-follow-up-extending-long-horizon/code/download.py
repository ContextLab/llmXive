"""
Download and validate the AgentBench dataset.

This script fetches the 'lmz/agentbench' dataset from Hugging Face,
saves it to 'data/raw/', performs cryptographic hash validation,
verifies the presence of required variables (observations, actions, rewards),
and implements task selection logic to filter error-prone tasks.
"""
import hashlib
import logging
import os
import sys
import itertools
from pathlib import Path

from datasets import load_dataset

# Configuration
DATASET_ID = "lmz/agentbench"
OUTPUT_DIR = Path("data/raw")
# Expected checksum for the dataset archive (example placeholder; 
# in a real scenario, this would be the verified SHA-256 from the dataset card).
# Since the specific split file checksums vary by version, we will validate
# the integrity of the download via the datasets library's built-in checks
# and log the actual hash of the downloaded file for verification.
# If a specific checksum is mandated by the spec, it should be updated here.
EXPECTED_SHA256 = None  # Replace with actual hash if known from documentation

# Required variables for the research pipeline
REQUIRED_VARIABLES = ["observations", "actions", "rewards"]

# Task selection configuration
# Filter for tasks known to be error-prone based on domain characteristics
# or specific task IDs from the benchmark.
# In a real implementation, this would be populated from a configuration file
# or research specification.
ERROR_PRONE_TASK_KEYWORDS = [
    "math",  # Mathematical reasoning tasks
    "code",  # Code generation tasks
    "logic", # Logic puzzles
    "planning" # Multi-step planning
]

# Size constraints for sampling (in rows)
# If the filtered dataset exceeds this, we sample the first N rows
MAX_TASKS_LIMIT = 100  # Example limit; adjust based on compute constraints

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/download.log", mode="a", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_variables(dataset, dataset_id: str) -> None:
    """
    Verify that the dataset contains the required variables: observations, actions, rewards.
    
    Raises:
        ValueError: If any required variable is missing, with error code ERR_MISSING_VAR.
    """
    missing_vars = []
    available_columns = set(dataset.column_names)
    
    for var in REQUIRED_VARIABLES:
        if var not in available_columns:
            missing_vars.append(var)
    
    if missing_vars:
        error_msg = f"ERR_MISSING_VAR: The dataset '{dataset_id}' is missing required variables: {missing_vars}. " \
                    f"Available columns: {list(available_columns)}."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"✓ Validation PASSED: All required variables {REQUIRED_VARIABLES} found in '{dataset_id}'.")

def filter_error_prone_tasks(dataset, keywords=None) -> list:
    """
    Filter the dataset to include only error-prone tasks based on keywords.
    
    Args:
        dataset: The Hugging Face dataset object.
        keywords: List of keywords to search for in task descriptions or IDs.
                
    Returns:
        List of indices of tasks that match the error-prone criteria.
    """
    if keywords is None:
        keywords = ERROR_PRONE_TASK_KEYWORDS
    
    filtered_indices = []
    
    # Determine the column to search for task identification
    # Typically 'task_id', 'task_name', or 'description'
    search_columns = []
    for col in ["task_id", "task_name", "description", "category"]:
        if col in dataset.column_names:
            search_columns.append(col)
    
    if not search_columns:
        logger.warning("No suitable column found for task filtering. Returning all tasks.")
        return list(range(len(dataset)))
    
    logger.info(f"Searching for error-prone tasks using keywords: {keywords} in columns: {search_columns}")
    
    for idx, item in enumerate(dataset):
        is_error_prone = False
        for col in search_columns:
            if col in item and item[col]:
                text = str(item[col]).lower()
                if any(keyword.lower() in text for keyword in keywords):
                    is_error_prone = True
                    break
        
        if is_error_prone:
            filtered_indices.append(idx)
    
    return filtered_indices

def select_tasks_for_baseline(dataset, max_tasks=None):
    """
    Select tasks for baseline execution with sampling strategy if constraints are hit.
    
    This implements the task selection logic for T012a:
    - Filters for error-prone tasks
    - If the count exceeds max_tasks, samples the first N rows using itertools.islice
    - Logs the sampling strategy used
    
    Args:
        dataset: The Hugging Face dataset object.
        max_tasks: Maximum number of tasks to select. If None, uses MAX_TASKS_LIMIT.
    
    Returns:
        List of selected task indices.
    """
    if max_tasks is None:
        max_tasks = MAX_TASKS_LIMIT
    
    logger.info(f"Starting task selection for baseline execution with limit: {max_tasks}")
    
    # Filter for error-prone tasks
    filtered_indices = filter_error_prone_tasks(dataset)
    total_filtered = len(filtered_indices)
    
    logger.info(f"Found {total_filtered} error-prone tasks out of {len(dataset)} total tasks.")
    
    if total_filtered == 0:
        logger.warning("No error-prone tasks found. Falling back to all tasks.")
        return list(range(len(dataset)))
    
    # Apply size constraint if necessary
    if total_filtered > max_tasks:
        logger.info(f"Constraint hit: {total_filtered} tasks > {max_tasks} limit.")
        logger.info(f"Sampling strategy: Using itertools.islice to select first {max_tasks} rows.")
        
        # Use itertools.islice to select the first N rows
        selected_indices = list(itertools.islice(filtered_indices, max_tasks))
        
        logger.info(f"Selected {len(selected_indices)} tasks for baseline execution.")
        return selected_indices
    else:
        logger.info(f"All {total_filtered} error-prone tasks selected (within limit).")
        return filtered_indices

def main():
    """Main entry point for downloading, validating, and checking the dataset."""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Ensure logs directory exists
    Path("logs").mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting download and validation for dataset '{DATASET_ID}'...")

    try:
        # Log the substitution note as per task requirements
        logger.info("ℹ Note: 'Long-Horizon-Terminal-Bench' was substituted with 'AgentBench' (lmz/agentbench).")

        # Load the dataset
        # We use streaming=False to download the full dataset for local validation
        logger.info(f"Loading dataset '{DATASET_ID}' split='train'...")
        dataset = load_dataset(DATASET_ID, split="train", trust_remote_code=True)
        
        # Save the dataset to disk in Parquet format for efficiency
        output_path = OUTPUT_DIR / "agentbench.parquet"
        logger.info(f"Saving dataset to: {output_path}")
        dataset.to_parquet(str(output_path))

        # Calculate and log the hash of the downloaded file
        actual_hash = calculate_sha256(output_path)
        logger.info(f"Calculated SHA-256: {actual_hash}")

        if EXPECTED_SHA256:
            if actual_hash == EXPECTED_SHA256:
                logger.info("✓ Checksum verification PASSED.")
            else:
                logger.error(f"✗ Checksum verification FAILED.")
                logger.error(f"  Expected: {EXPECTED_SHA256}")
                logger.error(f"  Actual:   {actual_hash}")
                sys.exit(1)
        else:
            logger.warning("⚠ No expected checksum provided for verification. "
                         "Please verify the hash against the dataset documentation manually.")

        # Validate required variables
        logger.info("Validating required variables (observations, actions, rewards)...")
        validate_variables(dataset, DATASET_ID)

        # Task selection logic for T012a
        selected_indices = select_tasks_for_baseline(dataset)
        
        # Create a subset dataset for the selected tasks
        if selected_indices:
            selected_dataset = dataset.select(selected_indices)
            subset_output_path = OUTPUT_DIR / "agentbench_baseline_subset.parquet"
            logger.info(f"Saving baseline subset ({len(selected_indices)} tasks) to: {subset_output_path}")
            selected_dataset.to_parquet(str(subset_output_path))
            
            # Log the selected task IDs for verification
            logger.info("Selected task IDs (first 10):")
            for i, idx in enumerate(selected_indices[:10]):
                task_id = dataset[idx].get("task_id", f"index_{idx}")
                logger.info(f"  {i+1}. {task_id}")
            if len(selected_indices) > 10:
                logger.info(f"  ... and {len(selected_indices) - 10} more.")
        else:
            logger.warning("No tasks selected for baseline execution.")

        logger.info("Dataset download, validation, and task selection completed successfully.")

    except ValueError as e:
        if "ERR_MISSING_VAR" in str(e):
            logger.error(f"Validation failed: {e}")
            sys.exit(1)
        else:
            logger.error(f"Unexpected error during validation: {e}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error downloading or processing dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()