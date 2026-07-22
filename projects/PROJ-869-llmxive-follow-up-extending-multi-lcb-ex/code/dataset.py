import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datasets import load_dataset
import hashlib
import json

from code.config import get_path
from code.utils.common import save_json, load_json
from code.utils.logger import get_logger
from code.utils.checksum_tracker import register_file

logger = get_logger(__name__)

# Constants for the Multi-LCB dataset
# Based on the project context, we assume the dataset is hosted on HuggingFace
# and contains columns for 'language', 'difficulty', 'topic', 'pass_at_1', 'python_pass_at_1'
# or similar metrics indicating success in target language vs Python.
# We will attempt to load the specific dataset referenced in the project specs.
DATASET_NAME = "multilcb/multi-lcb" 
DATASET_SPLIT = "train"

def load_multi_lcb_dataset(split: str = "train", streaming: bool = False) -> pd.DataFrame:
    """
    Loads the Multi-LCB dataset from HuggingFace.
    
    Args:
        split: The dataset split to load.
        streaming: If True, streams the dataset to handle large sizes.
        
    Returns:
        A pandas DataFrame containing the dataset.
    """
    logger.info(f"Loading dataset: {DATASET_NAME}, split: {split}")
    try:
        ds = load_dataset(DATASET_NAME, split=split, streaming=streaming)
        if streaming:
            # Convert to dataframe by iterating (memory efficient for stats, 
            # but for full pool selection we might need to materialize or stream carefully)
            # For the purpose of this task, we assume we can iterate to build the list
            # or load a subset if the dataset is massive. 
            # However, for robust "Static Pool Selection", we need to see the Pass@1 stats.
            # If the dataset is too large to fit in memory, we might need to filter on the fly.
            # Given the constraints of this environment, we will try to load it fully first.
            # If it fails, we fall back to a streaming approach that collects only necessary rows.
            df = ds.to_pandas()
        else:
            df = ds.to_pandas()
        logger.info(f"Dataset loaded successfully. Shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def verify_checksum(file_path: Path) -> str:
    """Computes SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_dataset_with_checksum(df: pd.DataFrame, output_path: Path) -> None:
    """Saves the dataset to a JSON file and tracks its checksum."""
    df.to_json(output_path, orient='records', lines=True)
    checksum = verify_checksum(output_path)
    logger.info(f"Saved dataset to {output_path} with checksum: {checksum}")
    register_file(output_path, checksum)

def stratify_tasks(df: pd.DataFrame, difficulty_col: str = "difficulty", 
                   topic_col: str = "topic", language_col: str = "language") -> pd.DataFrame:
    """
    Stratifies the dataset by difficulty, topic, and language.
    This is a placeholder for the actual stratification logic required in T009.
    """
    logger.info("Stratifying tasks...")
    # Implementation would involve groupby and sampling
    return df

def save_filtered_tasks(tasks: List[Dict[str, Any]], output_path: Path) -> None:
    """Saves a list of task dictionaries to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2)
    logger.info(f"Saved {len(tasks)} tasks to {output_path}")

def select_static_pool(input_data_path: Optional[Path] = None, 
                       output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Selects the initial pool of tasks where the model previously failed in the target language
    (blind Pass@1 < 1.0) AND succeeded in Python.
    
    This function implements T016.
    
    Logic:
    1. Load the dataset (or use provided input data if pre-filtered).
    2. Filter for tasks where:
       - target_language_pass_at_1 < 1.0 (Failed in target)
       - python_pass_at_1 == 1.0 (Succeeded in Python)
       - Note: The exact column names might vary. We assume standard Multi-LCB columns.
    3. Return the list of matching tasks.
    4. Save to output_path.
    
    Constraints:
    - No replacement logic here (that is T018).
    - Must use real data.
    """
    if output_path is None:
        output_path = get_path("initial_pool.json")
    
    logger.info(f"Starting Static Pool Selection. Output: {output_path}")
    
    # Determine source of data
    # If input_data_path is provided, we might assume it's a pre-processed file.
    # However, T016 typically starts from the raw loaded dataset to apply the filter.
    # Let's assume we load the raw dataset here to apply the filter.
    
    try:
        df = load_multi_lcb_dataset()
    except Exception as e:
        logger.error(f"Critical: Could not load dataset for T016. {e}")
        raise

    # Identify columns. Multi-LCB usually has 'language' and performance metrics.
    # We need to find columns that indicate "Pass@1" or similar.
    # Common patterns: 'pass_at_1', 'pass_rate', or language-specific keys.
    # For this implementation, we assume the dataset has:
    # - 'language': The target language of the task.
    # - 'python_pass_at_1': Pass rate in Python (1.0 means success).
    # - 'pass_at_1': Pass rate in the target language.
    # If these columns don't exist, we must inspect the dataframe or fail loudly.
    
    required_columns = ['language', 'python_pass_at_1', 'pass_at_1']
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        # Fallback: Try to infer column names if the standard ones are missing
        # This is risky, but we need to be robust.
        logger.warning(f"Standard columns {required_columns} not found. Inspecting columns: {df.columns.tolist()}")
        # Attempt to map generic names
        # If we can't find them, we raise an error to avoid silent failure.
        raise ValueError(f"Missing required columns for pool selection: {missing_cols}. "
                         f"Available columns: {df.columns.tolist()}")

    # Filter Logic:
    # 1. Failed in target language: pass_at_1 < 1.0
    # 2. Succeeded in Python: python_pass_at_1 == 1.0 (or > 0.99 to allow float tolerance)
    # We use a small epsilon for float comparison.
    epsilon = 1e-6
    
    mask_failed_target = df['pass_at_1'] < (1.0 - epsilon)
    mask_success_python = df['python_pass_at_1'] > (1.0 - epsilon)
    
    filtered_df = df[mask_failed_target & mask_success_python]
    
    logger.info(f"Filtered {len(filtered_df)} tasks from {len(df)} total.")
    
    if len(filtered_df) == 0:
        logger.warning("No tasks found matching the criteria. The pool is empty.")
        # We still output an empty list, but log the warning.
    
    # Convert to list of dicts
    tasks = filtered_df.to_dict(orient='records')
    
    # Save
    save_filtered_tasks(tasks, output_path)
    
    logger.info(f"Static pool selection complete. {len(tasks)} tasks saved to {output_path}")
    return tasks

# Main execution block for T016
if __name__ == "__main__":
    # Ensure the data directory exists
    output_path = get_path("initial_pool.json")
    select_static_pool(output_path=output_path)
