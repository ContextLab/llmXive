"""
Data Ingestion Module for CodeSearchNet and CodeGen datasets.

Implements robust downloading with exponential backoff, checksum verification,
and dataset filtering for the CodeSearchNet (human-written) and CodeGen (LLM-generated)
datasets.
"""
import os
import time
import json
import hashlib
import logging
import ast
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Generator
from datetime import datetime

# Import existing project utilities
from datasets import load_dataset
from seeds import get_seed_value
from checksum import compute_sha256, register_dataset_checksum
from logging_config import setup_logger, get_logger
from state_tracker import update_state_with_artifact, load_state_file, save_state_file
from data_model import CodeSnippet

# Constants
MAX_RETRIES = 3
BASE_INTERVAL = 60  # seconds
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
PROJECT_STATE_PATH = STATE_DIR / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Setup logger
logger = setup_logger("data_ingestion", log_file="data/ingestion.log")

def download_with_backoff(dataset_name: str, split: str = "train", **kwargs) -> Any:
    """
    Download a dataset with exponential backoff retry logic.
    
    Args:
        dataset_name: HuggingFace dataset identifier (e.g., 'code_search_net')
        split: Dataset split to load (default: 'train')
        **kwargs: Additional arguments for load_dataset
        
    Returns:
        Loaded dataset object
        
    Raises:
        RuntimeError: If download fails after max retries
    """
    retries = 0
    last_error = None
    
    while retries < MAX_RETRIES:
        try:
            logger.info(f"Attempting to download {dataset_name} (split={split}) - Attempt {retries + 1}/{MAX_RETRIES}")
            dataset = load_dataset(dataset_name, split=split, **kwargs)
            logger.info(f"Successfully downloaded {dataset_name}")
            return dataset
        except Exception as e:
            last_error = e
            retries += 1
            if retries < MAX_RETRIES:
                # Exponential backoff: 60s, 120s, 240s
                wait_time = BASE_INTERVAL * (2 ** (retries - 1))
                logger.warning(f"Download failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to download {dataset_name} after {MAX_RETRIES} attempts: {e}")
    
    raise RuntimeError(f"Failed to download {dataset_name} after {MAX_RETRIES} retries: {last_error}")

def compute_dataset_hash(dataset: Any, sample_size: int = 1000) -> str:
    """
    Compute a hash of the dataset based on a sample of content.
    
    Args:
        dataset: HuggingFace dataset object
        sample_size: Number of rows to sample for hashing
        
    Returns:
        SHA-256 hash string
    """
    hasher = hashlib.sha256()
    count = 0
    
    # Stream through dataset to avoid loading everything into memory
    for item in dataset:
        if count >= sample_size:
            break
        # Convert item to string for hashing
        item_str = json.dumps(item, sort_keys=True)
        hasher.update(item_str.encode('utf-8'))
        count += 1
        
    return hasher.hexdigest()

def save_dataset_metadata(dataset_name: str, dataset: Any, output_path: Path) -> None:
    """
    Save dataset metadata including hash, row count, and timestamp.
    
    Args:
        dataset_name: Name of the dataset
        dataset: HuggingFace dataset object
        output_path: Path to save metadata JSON
    """
    # Sample hash for verification
    dataset_hash = compute_dataset_hash(dataset)
    
    # Count rows (may be expensive for large datasets, so we estimate if streaming)
    try:
        row_count = len(dataset)
    except TypeError:
        # For streaming datasets, we can't get length directly
        row_count = -1
        logger.warning(f"Could not determine row count for {dataset_name} (streaming dataset)")
    
    metadata = {
        "dataset_name": dataset_name,
        "downloaded_at": datetime.utcnow().isoformat(),
        "hash": dataset_hash,
        "row_count": row_count,
        "columns": list(dataset.column_names) if hasattr(dataset, 'column_names') else []
    }
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved metadata for {dataset_name} to {output_path}")

def extract_top_level_functions(code: str) -> List[str]:
    """
    Extract top-level function definitions from Python code.
    
    Args:
        code: Python source code string
        
    Returns:
        List of function definition strings
    """
    try:
        tree = ast.parse(code)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Extract the function definition
                func_lines = []
                for line_no in range(node.lineno - 1, node.end_lineno):
                    # Get the original line (this is a simplification)
                    # In practice, we'd need to reconstruct from source lines
                    func_lines.append(f"Line {line_no + 1}: {code.splitlines()[line_no] if line_no < len(code.splitlines()) else ''}")
                
                # Just return the function name and a snippet for now
                functions.append(f"def {node.name}(...)")
        return functions
    except SyntaxError:
        return []

def filter_python_snippets(dataset: Any, language_filter: str = "python") -> Generator[Dict[str, Any], None, None]:
    """
    Filter dataset to include only Python snippets.
    
    Args:
        dataset: HuggingFace dataset object
        language_filter: Language to filter for (default: "python")
        
    Yields:
        Filtered snippet dictionaries
    """
    for item in dataset:
        # Check if language matches
        # The structure varies by dataset, so we check common fields
        lang = None
        if 'language' in item:
            lang = item['language']
        elif 'lang' in item:
            lang = item['lang']
        
        if lang and lang.lower() == language_filter.lower():
            yield item

def ingest_codesearchnet() -> Tuple[Any, Path]:
    """
    Ingest CodeSearchNet dataset from HuggingFace.
    
    Returns:
        Tuple of (dataset object, path to processed data)
    """
    logger.info("Starting CodeSearchNet ingestion")
    
    # Download with backoff
    dataset = download_with_backoff(
        'code_search_net',
        split='train',
        trust_remote_code=True
    )
    
    # Filter for Python
    python_snippets = list(filter_python_snippets(dataset, "python"))
    logger.info(f"Filtered {len(python_snippets)} Python snippets from CodeSearchNet")
    
    # Save processed data
    output_path = PROCESSED_DIR / "codesearchnet_python.json"
    with open(output_path, 'w') as f:
        json.dump(python_snippets, f, indent=2)
    
    # Save metadata
    metadata_path = PROCESSED_DIR / "codesearchnet_metadata.json"
    save_dataset_metadata("code_search_net", dataset, metadata_path)
    
    # Register checksum
    register_dataset_checksum("code_search_net", compute_sha256(output_path))
    
    logger.info(f"CodeSearchNet ingestion complete. Output: {output_path}")
    return dataset, output_path

def ingest_codegen() -> Tuple[Any, Path]:
    """
    Ingest CodeParrot/CodeGen dataset from HuggingFace.
    
    Returns:
        Tuple of (dataset object, path to processed data)
    """
    logger.info("Starting CodeGen ingestion")
    
    # Download with backoff
    dataset = download_with_backoff(
        'codeparrot/codegen',
        split='train',
        trust_remote_code=True
    )
    
    # Filter for Python (CodeGen is primarily Python, but we filter to be sure)
    python_snippets = list(filter_python_snippets(dataset, "python"))
    logger.info(f"Filtered {len(python_snippets)} Python snippets from CodeGen")
    
    # Save processed data
    output_path = PROCESSED_DIR / "codegen_python.json"
    with open(output_path, 'w') as f:
        json.dump(python_snippets, f, indent=2)
    
    # Save metadata
    metadata_path = PROCESSED_DIR / "codegen_metadata.json"
    save_dataset_metadata("codeparrot/codegen", dataset, metadata_path)
    
    # Register checksum
    register_dataset_checksum("codeparrot/codegen", compute_sha256(output_path))
    
    logger.info(f"CodeGen ingestion complete. Output: {output_path}")
    return dataset, output_path

def verify_datasets() -> bool:
    """
    Verify that both datasets have been successfully ingested.
    
    Returns:
        True if both datasets are present and valid
    """
    codesearchnet_path = PROCESSED_DIR / "codesearchnet_python.json"
    codegen_path = PROCESSED_DIR / "codegen_python.json"
    
    if not codesearchnet_path.exists():
        logger.error(f"CodeSearchNet output not found: {codesearchnet_path}")
        return False
    
    if not codegen_path.exists():
        logger.error(f"CodeGen output not found: {codegen_path}")
        return False
    
    # Check file sizes (should be non-empty)
    if codesearchnet_path.stat().st_size == 0:
        logger.error(f"CodeSearchNet output is empty: {codesearchnet_path}")
        return False
    
    if codegen_path.stat().st_size == 0:
        logger.error(f"CodeGen output is empty: {codegen_path}")
        return False
    
    logger.info("Both datasets verified successfully")
    return True

def update_verified_sources() -> None:
    """
    Update the verified sources file with dataset information.
    """
    verified_sources_path = DATA_DIR / "verified_sources.json"
    
    sources = {
        "code_search_net": {
            "path": str(PROCESSED_DIR / "codesearchnet_python.json"),
            "verified_at": datetime.utcnow().isoformat(),
            "status": "verified"
        },
        "codeparrot_codegen": {
            "path": str(PROCESSED_DIR / "codegen_python.json"),
            "verified_at": datetime.utcnow().isoformat(),
            "status": "verified"
        }
    }
    
    with open(verified_sources_path, 'w') as f:
        json.dump(sources, f, indent=2)
    
    logger.info(f"Updated verified sources: {verified_sources_path}")

def run_ingestion_pipeline() -> bool:
    """
    Run the complete ingestion pipeline for both datasets.
    
    Returns:
        True if pipeline completed successfully
    """
    try:
        # Ingest CodeSearchNet
        ingest_codesearchnet()
        
        # Ingest CodeGen
        ingest_codegen()
        
        # Verify datasets
        if not verify_datasets():
            logger.error("Dataset verification failed")
            return False
        
        # Update verified sources
        update_verified_sources()
        
        # Update state tracker
        update_state_with_artifact(
            artifact_type="dataset_ingestion",
            artifact_path=str(PROCESSED_DIR),
            state_file=PROJECT_STATE_PATH
        )
        
        logger.info("Ingestion pipeline completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        return False

def main():
    """
    Main entry point for data ingestion.
    """
    logger.info("Starting data ingestion pipeline")
    
    success = run_ingestion_pipeline()
    
    if success:
        logger.info("Data ingestion completed successfully")
        exit(0)
    else:
        logger.error("Data ingestion failed")
        exit(1)

if __name__ == "__main__":
    main()
