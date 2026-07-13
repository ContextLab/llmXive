import os
import time
import json
import hashlib
import ast
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

# Import existing utilities from project
from checksum import register_dataset_checksum, write_checksums, read_checksums
from logging_config import get_logger
from seeds import get_seed_value

try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("The 'datasets' library is required. Install it via pip.")

logger = get_logger(__name__)

def download_with_backoff(
    dataset_name: str,
    config_name: Optional[str] = None,
    split: str = "train",
    max_retries: int = 3,
    base_delay: float = 60.0,
    streaming: bool = False,
    trust_remote_code: bool = True
) -> Any:
    """
    Download a dataset from HuggingFace with exponential backoff.
    
    Args:
        dataset_name: HuggingFace dataset identifier (e.g., 'codeparrot/codegen')
        config_name: Configuration name if required
        split: Dataset split to load
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        streaming: If True, use streaming mode
        trust_remote_code: Trust remote code in dataset script
        
    Returns:
        The loaded dataset object or generator
        
    Raises:
        RuntimeError: If download fails after max retries
    """
    attempt = 0
    while attempt < max_retries:
        try:
            logger.info(f"Attempting to load dataset '{dataset_name}' (attempt {attempt + 1}/{max_retries})")
            
            load_kwargs = {
                "split": split,
                "trust_remote_code": trust_remote_code
            }
            
            if config_name:
                load_kwargs["name"] = config_name
                
            if streaming:
                load_kwargs["streaming"] = True
                dataset = load_dataset(dataset_name, **load_kwargs)
            else:
                dataset = load_dataset(dataset_name, **load_kwargs)
                
            logger.info(f"Successfully loaded dataset '{dataset_name}'")
            return dataset
            
        except Exception as e:
            attempt += 1
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(f"Download failed: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                logger.error(f"Failed to download dataset '{dataset_name}' after {max_retries} attempts")
                raise RuntimeError(f"Dataset download failed: {e}") from e

def compute_dataset_hash(dataset_obj: Any, sample_size: int = 1000) -> str:
    """
    Compute a SHA-256 hash of a dataset sample for verification.
    
    Args:
        dataset_obj: The loaded dataset object
        sample_size: Number of samples to hash
        
    Returns:
        Hexadecimal SHA-256 hash string
    """
    hasher = hashlib.sha256()
    count = 0
    
    # Handle streaming vs non-streaming
    if hasattr(dataset_obj, '__iter__'):
        iterator = iter(dataset_obj)
    else:
        # For non-streaming datasets that might need split access
        if hasattr(dataset_obj, 'values'):
            iterator = iter(list(dataset_obj.values())[0])
        else:
            iterator = iter(dataset_obj)
    
    for item in iterator:
        if count >= sample_size:
            break
        # Convert item to string representation for hashing
        item_str = json.dumps(item, sort_keys=True, default=str)
        hasher.update(item_str.encode('utf-8'))
        count += 1
        
    return hasher.hexdigest()

def save_dataset_metadata(dataset_name: str, metadata: Dict[str, Any], output_path: Path):
    """
    Save dataset metadata to a JSON file.
    
    Args:
        dataset_name: Name of the dataset
        metadata: Dictionary of metadata
        output_path: Path to save the metadata file
    """
    metadata["dataset_name"] = dataset_name
    metadata["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata for '{dataset_name}' to {output_path}")

def ingest_codesearchnet(
    split: str = "train",
    output_dir: str = "data/raw",
    max_samples: Optional[int] = None
) -> Dict[str, Any]:
    """
    Download and ingest CodeSearchNet dataset.
    
    Args:
        split: Dataset split to load
        output_dir: Directory to save raw data
        max_samples: Maximum number of samples to process
        
    Returns:
        Dictionary containing ingestion results
    """
    logger.info("Starting CodeSearchNet ingestion")
    dataset = download_with_backoff(
        "code_search_net",
        config_name="python",
        split=split
    )
    
    metadata = {
        "source": "CodeSearchNet",
        "hf_dataset": "code_search_net",
        "config": "python",
        "split": split,
        "status": "downloaded"
    }
    
    dataset_hash = compute_dataset_hash(dataset)
    metadata["hash"] = dataset_hash
    
    # Register checksum
    checksums = read_checksums()
    checksums["code_search_net"] = dataset_hash
    write_checksums(checksums)
    
    output_path = Path(output_dir) / "codesearchnet_metadata.json"
    save_dataset_metadata("code_search_net", metadata, output_path)
    
    logger.info(f"CodeSearchNet ingestion complete. Hash: {dataset_hash}")
    return metadata

def ingest_codegen(
    split: str = "train",
    output_dir: str = "data/raw",
    max_samples: Optional[int] = None
) -> Dict[str, Any]:
    """
    Download and ingest CodeParrot/CodeGen dataset.
    
    Args:
        split: Dataset split to load
        output_dir: Directory to save raw data
        max_samples: Maximum number of samples to process
        
    Returns:
        Dictionary containing ingestion results
    """
    logger.info("Starting CodeParrot/CodeGen ingestion")
    
    # Load CodeGen dataset from HuggingFace
    dataset = download_with_backoff(
        "codeparrot/codegen",
        split=split
    )
    
    # Compute hash for verification
    dataset_hash = compute_dataset_hash(dataset)
    
    # Prepare metadata
    metadata = {
        "source": "CodeParrot/CodeGen",
        "hf_dataset": "codeparrot/codegen",
        "split": split,
        "status": "downloaded",
        "hash": dataset_hash,
        "sample_count": len(list(dataset)) if not hasattr(dataset, '__iter__') else "streaming"
    }
    
    # Update checksums file with real SHA-256
    checksums = read_checksums()
    checksums["codegen"] = dataset_hash
    write_checksums(checksums)
    
    # Save metadata
    output_path = Path(output_dir) / "codegen_metadata.json"
    save_dataset_metadata("codegen", metadata, output_path)
    
    logger.info(f"CodeParrot/CodeGen ingestion complete. Hash: {dataset_hash}")
    return metadata

def verify_datasets(checksums_path: str = "data/checksums.json") -> bool:
    """
    Verify that required datasets have been ingested and checksums are valid.
    
    Args:
        checksums_path: Path to checksums file
        
    Returns:
        True if verification passes
        
    Raises:
        RuntimeError: If verification fails (error 101)
    """
    try:
        checksums = read_checksums()
    except FileNotFoundError:
        logger.error("Checksums file not found")
        raise RuntimeError("Error 101: Checksums file missing")
    
    required_datasets = ["code_search_net", "codegen"]
    for dataset in required_datasets:
        if dataset not in checksums:
            logger.error(f"Dataset '{dataset}' not found in checksums")
            raise RuntimeError(f"Error 101: Dataset '{dataset}' not verified")
        
        if checksums[dataset] == "pending_download":
            logger.error(f"Dataset '{dataset}' has not been downloaded yet")
            raise RuntimeError(f"Error 101: Dataset '{dataset}' not verified (pending download)")
            
        if not isinstance(checksums[dataset], str) or len(checksums[dataset]) != 64:
            logger.error(f"Invalid checksum format for '{dataset}'")
            raise RuntimeError(f"Error 101: Invalid checksum for '{dataset}'")
    
    logger.info("All datasets verified successfully")
    return True

def extract_top_level_functions(code: str) -> List[str]:
    """
    Extract top-level function definitions from code string.
    
    Args:
        code: Source code string
        
    Returns:
        List of function definition strings
    """
    try:
        tree = ast.parse(code)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Extract the function definition and body
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                lines = code.split('\n')
                func_code = '\n'.join(lines[start_line:end_line])
                functions.append(func_code)
        return functions
    except SyntaxError:
        return []

def filter_python_snippets(dataset: Any, language_field: str = "language") -> Any:
    """
    Filter dataset to only include Python snippets.
    
    Args:
        dataset: The dataset object
        language_field: Field name containing language info
        
    Returns:
        Filtered dataset
    """
    # This is a placeholder for actual filtering logic
    # In a real implementation, this would filter the dataset
    logger.info("Filtering for Python snippets")
    return dataset

def main():
    """Main entry point for data ingestion."""
    logger.info("Starting data ingestion workflow")
    
    # Ingest CodeSearchNet
    try:
        cs_metadata = ingest_codesearchnet()
        logger.info(f"CodeSearchNet metadata: {cs_metadata}")
    except Exception as e:
        logger.error(f"Failed to ingest CodeSearchNet: {e}")
        
    # Ingest CodeGen
    try:
        cg_metadata = ingest_codegen()
        logger.info(f"CodeGen metadata: {cg_metadata}")
    except Exception as e:
        logger.error(f"Failed to ingest CodeGen: {e}")
        
    # Verify datasets
    try:
        verify_datasets()
        logger.info("Dataset verification passed")
    except RuntimeError as e:
        logger.error(f"Dataset verification failed: {e}")
        
    logger.info("Data ingestion workflow complete")

if __name__ == "__main__":
    main()
