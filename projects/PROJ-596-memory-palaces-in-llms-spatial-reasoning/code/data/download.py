import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Ensure parent is in path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from datasets import load_dataset

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Computes the SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        return ""

def get_dataset_cache_paths(dataset_name: str, config_name: Optional[str] = None) -> List[Path]:
    """
    Returns a list of paths to cached files for a given dataset.
    This relies on the `datasets` library's caching mechanism.
    We attempt to locate the cache directory by loading the dataset
    and inspecting the cache info if available, or by scanning the
    default HuggingFace cache if environment variables are set.
    """
    # The `datasets` library stores data in ~/.cache/huggingface/datasets/
    # by default, or $HF_DATASETS_CACHE.
    # Since we need the actual files that were downloaded, we will
    # rely on the fact that `load_dataset` returns a dataset object
    # which has a `cache_files` attribute in some versions, or we
    # can scan the specific dataset directory.
    
    # A more robust way for this specific task (which requires checksums
    # of the downloaded artifacts) is to inspect the cache directory
    # structure created by the `datasets` library after loading.
    
    # Default cache locations
    cache_dir = Path(os.getenv("HF_DATASETS_CACHE", Path.home() / ".cache" / "huggingface" / "datasets"))
    
    # Construct the potential path based on dataset name and config
    # The datasets library creates a folder structure like:
    # <cache_dir>/<dataset_name>_<config_name>_<hash>/
    # We will try to find the most recent folder matching the dataset name.
    
    dataset_dir_name = dataset_name.replace("/", "_")
    if config_name:
        dataset_dir_name += f"_{config_name.replace('/', '_')}"
    
    matching_dirs = []
    if cache_dir.exists():
        # Search for directories starting with the dataset name
        for item in cache_dir.iterdir():
            if item.is_dir() and item.name.startswith(dataset_dir_name):
                matching_dirs.append(item)
    
    if not matching_dirs:
        logger.warning(f"No cache directory found for {dataset_name} at {cache_dir}")
        return []
    
    # Sort by modification time to get the latest download
    matching_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_dir = matching_dirs[0]
    
    # Recursively find all files (excluding __pycache__ or hidden)
    files = []
    for root, dirs, filenames in os.walk(latest_dir):
        # Filter out hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for filename in filenames:
            if not filename.startswith('.') and not filename.endswith('.lock'):
                files.append(Path(root) / filename)
    
    return files

def download_and_verify(
    dataset_name: str, 
    config_name: Optional[str] = None, 
    output_checksums: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Downloads a dataset using the HuggingFace `datasets` library,
    computes checksums for all cached files, and returns the result.
    If output_checksums is provided, updates the global checksums file.
    """
    logger.info(f"Downloading dataset: {dataset_name} (config: {config_name})")
    
    try:
        # Load dataset to trigger download and caching
        # We load with streaming=False to ensure full download for checksumming
        ds = load_dataset(dataset_name, config_name, trust_remote_code=True)
        logger.info(f"Dataset {dataset_name} loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        return {"status": "error", "message": str(e)}

    # Get cache paths
    cache_files = get_dataset_cache_paths(dataset_name, config_name)
    
    if not cache_files:
        logger.warning(f"No cache files found for {dataset_name}. Assuming in-memory or remote-only.")
        # If no files found, we can't compute a checksum. 
        # We record a placeholder or skip.
        checksum_data = {
            "dataset": dataset_name,
            "config": config_name,
            "status": "no_cache_files",
            "checksums": {}
        }
    else:
        checksums = {}
        for file_path in cache_files:
            checksum = compute_file_checksum(file_path)
            if checksum:
                # Store relative path to cache dir for portability in the record
                rel_path = str(file_path)
                checksums[rel_path] = checksum
        
        checksum_data = {
            "dataset": dataset_name,
            "config": config_name,
            "status": "success",
            "file_count": len(cache_files),
            "checksums": checksums
        }
        logger.info(f"Computed checksums for {len(cache_files)} files for {dataset_name}.")

    # Update the global checksums file if requested
    if output_checksums:
        output_checksums.parent.mkdir(parents=True, exist_ok=True)
        
        if output_checksums.exists():
            try:
                with open(output_checksums, 'r', encoding='utf-8') as f:
                    all_checksums = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Could not read existing checksums file: {e}")
                all_checksums = {}
        else:
            all_checksums = {}

        # Key by dataset name and config
        key = f"{dataset_name}_{config_name}" if config_name else dataset_name
        all_checksums[key] = checksum_data

        with open(output_checksums, 'w', encoding='utf-8') as f:
            json.dump(all_checksums, f, indent=2)
        
        logger.info(f"Updated checksums file: {output_checksums}")

    return checksum_data

def main():
    """
    Main entry point to download and verify the three permitted datasets.
    """
    # Define the project root and output paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    checksums_file = data_raw_dir / "checksums.json"

    data_raw_dir.mkdir(parents=True, exist_ok=True)

    datasets_to_download = [
        {"name": "babi", "config": "task3_10k"},
        {"name": "lambada", "config": None},
        {"name": "story_cloze", "config": None} # Default config for story_cloze
    ]

    results = {}

    for ds_config in datasets_to_download:
        name = ds_config["name"]
        config = ds_config["config"]
        
        # Handle story_cloze specific config if needed (often '2016' or '2018')
        # The prompt says "story_cloze", we try default first.
        if name == "story_cloze":
            # Try to load with a common config if default fails, but 
            # the task says "story_cloze" specifically.
            # We'll attempt the default load first.
            pass

        result = download_and_verify(name, config, checksums_file)
        results[f"{name}_{config}"] = result

        if result.get("status") == "error":
            logger.error(f"Stopping due to error in {name}")
            # Depending on strictness, we might stop or continue. 
            # We continue to log all errors.

    logger.info("All download and verification tasks completed.")
    return results

if __name__ == "__main__":
    main()