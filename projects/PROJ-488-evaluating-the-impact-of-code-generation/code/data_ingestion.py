import os
import time
import json
import hashlib
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Import from local modules
from seeds import get_seed_value
from checksum import register_dataset_checksum, compute_sha256
from logging_config import setup_logger, get_logger
from data_model import CodeSnippet, DatasetGroup

# Error codes
ERROR_101 = 101

def download_with_backoff(dataset_name: str, cache_dir: Optional[str] = None, max_retries: int = 3, backoff_factor: int = 60):
    """
    Download a dataset from HuggingFace with exponential backoff.
    """
    logger = get_logger(__name__)
    retries = 0
    
    while retries < max_retries:
        try:
            logger.info(f"Attempting to download dataset: {dataset_name} (Attempt {retries + 1}/{max_retries})")
            
            # Lazy import to avoid heavy dependency load if not needed
            from datasets import load_dataset
            
            dataset = load_dataset(dataset_name, split="train", cache_dir=cache_dir)
            logger.info(f"Successfully downloaded dataset: {dataset_name}")
            return dataset
            
        except Exception as e:
            retries += 1
            if retries == max_retries:
                logger.error(f"Failed to download {dataset_name} after {max_retries} attempts: {e}")
                raise
            wait_time = backoff_factor * (2 ** (retries - 1))
            logger.warning(f"Download failed for {dataset_name}. Retrying in {wait_time}s... Error: {e}")
            time.sleep(wait_time)

def compute_dataset_hash(dataset_obj) -> str:
    """
    Compute a hash for the dataset content.
    For this implementation, we hash the number of examples and a sample of code.
    """
    if dataset_obj is None:
        return "empty"
    
    sample_str = f"{len(dataset_obj)}"
    # Take first 5 items to hash content signature
    if len(dataset_obj) > 0:
        sample_str += str(dataset_obj[:5])
    
    return hashlib.sha256(sample_str.encode('utf-8')).hexdigest()

def save_dataset_metadata(dataset_name: str, hash_val: str, path: Path):
    """
    Save metadata about the downloaded dataset.
    """
    metadata = {
        "dataset_name": dataset_name,
        "hash": hash_val,
        "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "path": str(path)
    }
    
    metadata_file = path.parent / "dataset_metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            all_metadata = json.load(f)
    else:
        all_metadata = {}
    
    all_metadata[dataset_name] = metadata
    
    with open(metadata_file, 'w') as f:
        json.dump(all_metadata, f, indent=2)

def ingest_codesearchnet(cache_dir: Optional[str] = None) -> DatasetGroup:
    """
    Ingest CodeSearchNet dataset.
    """
    logger = get_logger(__name__)
    logger.info("Starting CodeSearchNet ingestion...")
    
    dataset = download_with_backoff('code_search_net', cache_dir=cache_dir)
    hash_val = compute_dataset_hash(dataset)
    
    # Save metadata
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    save_dataset_metadata('code_search_net', hash_val, data_dir)
    
    # Register checksum
    register_dataset_checksum('code_search_net', hash_val)
    
    logger.info("CodeSearchNet ingestion complete.")
    return DatasetGroup(label="codesearchnet", snippets=[], aggregates={})

def ingest_codegen(cache_dir: Optional[str] = None) -> DatasetGroup:
    """
    Ingest CodeParrot/CodeGen dataset.
    """
    logger = get_logger(__name__)
    logger.info("Starting CodeParrot/CodeGen ingestion...")
    
    dataset = download_with_backoff('codeparrot/codegen', cache_dir=cache_dir)
    hash_val = compute_dataset_hash(dataset)
    
    # Save metadata
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    save_dataset_metadata('codeparrot/codegen', hash_val, data_dir)
    
    # Register checksum
    register_dataset_checksum('codeparrot/codegen', hash_val)
    
    logger.info("CodeParrot/CodeGen ingestion complete.")
    return DatasetGroup(label="codegen", snippets=[], aggregates={})

def verify_datasets() -> bool:
    """
    Verify that downloaded datasets are listed in data/verified_sources.json.
    Returns True if verified, aborts with error 101 if not.
    """
    logger = get_logger(__name__)
    verified_file = Path("data") / "verified_sources.json"
    
    if not verified_file.exists():
        logger.error("Verified sources file not found. Datasets may not be properly registered.")
        return False
    
    with open(verified_file, 'r') as f:
        verified_data = json.load(f)
    
    required_datasets = ['code_search_net', 'codeparrot/codegen']
    
    for ds_name in required_datasets:
        if ds_name not in verified_data:
            logger.error(f"Dataset {ds_name} is not in verified sources.")
            return False
    
    logger.info("All required datasets verified.")
    return True

def extract_top_level_functions(code: str, language: str = "python") -> List[str]:
    """
    Extract top-level functions from code string using AST.
    """
    if language != "python":
        return []
    
    try:
        tree = ast.parse(code)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(ast.unparse(node))
        return functions
    except SyntaxError:
        return []

def filter_python_snippets(snippets: List[Dict]) -> List[Dict]:
    """
    Filter snippets to keep only Python code.
    """
    return [s for s in snippets if s.get('language') == 'python']

def main():
    """
    Main entry point for data ingestion.
    """
    logger = setup_logger("data_ingestion")
    logger.info("Starting data ingestion pipeline.")
    
    try:
        # Ingest datasets
        csn_group = ingest_codesearchnet()
        cg_group = ingest_codegen()
        
        # Verify
        if not verify_datasets():
            logger.error("Dataset verification failed. Aborting.")
            sys.exit(ERROR_101)
        
        logger.info("Data ingestion pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        raise

if __name__ == "__main__":
    import sys
    main()