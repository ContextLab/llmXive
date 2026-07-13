"""
Data loader module for fetching and checksumming MobileGym tasks.

This module handles the retrieval of raw MobileGym task data from the official
repository and ensures data integrity through SHA-256 checksums.
"""
import os
import sys
import hashlib
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging import get_task_logger, log_task_start, log_task_complete, log_task_failed, log_error

# Constants
MOBILEGYM_REPO_URL = "https://raw.githubusercontent.com/mobilegym/mobilegym/main"
MOBILEGYM_TASKS_PATH = "tasks"
RAW_DATA_DIR = "data/raw"
CHECKSUMS_FILE = os.path.join(RAW_DATA_DIR, ".checksums.txt")
TASKS_CACHE_DIR = os.path.join(RAW_DATA_DIR, "mobilegym_tasks")

logger = get_task_logger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_string_sha256(content: str) -> str:
    """Calculate SHA-256 hash of a string."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def ensure_directories() -> None:
    """Ensure required directories exist."""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(TASKS_CACHE_DIR, exist_ok=True)

def load_existing_checksums() -> Dict[str, str]:
    """Load existing checksums from file."""
    if not os.path.exists(CHECKSUMS_FILE):
        return {}
    
    checksums = {}
    try:
        with open(CHECKSUMS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        checksums[parts[1]] = parts[0]
    except Exception as e:
        log_error(f"Failed to load existing checksums: {e}")
    return checksums

def save_checksums(checksums: Dict[str, str]) -> None:
    """Save checksums to file."""
    ensure_directories()
    try:
        with open(CHECKSUMS_FILE, 'w', encoding='utf-8') as f:
            f.write(f"# MobileGym Task Checksums - Generated {datetime.now(timezone.utc).isoformat()}\n")
            for file_path, checksum in sorted(checksums.items()):
                f.write(f"{checksum} {file_path}\n")
    except Exception as e:
        log_error(f"Failed to save checksums: {e}")
        raise

def fetch_task_file(task_name: str) -> Tuple[str, str]:
    """
    Fetch a single task file from the MobileGym repository.
    
    Args:
        task_name: Name of the task file (e.g., 'task_001.json')
        
    Returns:
        Tuple of (file_content, remote_checksum)
        
    Raises:
        urllib.error.URLError: If the file cannot be fetched
        FileNotFoundError: If the task file doesn't exist in the repository
    """
    url = f"{MOBILEGYM_REPO_URL}/{MOBILEGYM_TASKS_PATH}/{task_name}"
    logger.info(f"Fetching task file from: {url}")
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read().decode('utf-8')
            checksum = calculate_string_sha256(content)
            return content, checksum
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise FileNotFoundError(f"Task file '{task_name}' not found in MobileGym repository")
        raise
    except urllib.error.URLError as e:
        raise urllib.error.URLError(f"Failed to fetch task file: {e.reason}")

def get_available_tasks() -> List[str]:
    """
    Get list of available task files from the MobileGym repository.
    
    Returns:
        List of task filenames
    """
    # For now, we'll use a predefined list based on common MobileGym task naming
    # In a more sophisticated implementation, we could parse the directory listing
    base_tasks = [
        f"task_{i:03d}.json" for i in range(1, 101)  # Common range of tasks
    ]
    
    # Filter to only existing tasks by attempting to fetch
    available = []
    for task_name in base_tasks:
        try:
            fetch_task_file(task_name)
            available.append(task_name)
        except (FileNotFoundError, urllib.error.URLError):
            continue
    
    return available

def fetch_and_cache_tasks(task_names: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Fetch task files and cache them locally with checksums.
    
    Args:
        task_names: Optional list of specific task names to fetch.
                   If None, fetches all available tasks.
                   
    Returns:
        Dictionary mapping task names to their checksums
    """
    log_task_start("fetch_and_cache_tasks", {
        "task_count": len(task_names) if task_names else "all",
        "cache_dir": TASKS_CACHE_DIR
    })
    
    try:
        ensure_directories()
        existing_checksums = load_existing_checksums()
        new_checksums = {}
        fetched_count = 0
        
        if task_names is None:
            task_names = get_available_tasks()
            logger.info(f"Discovered {len(task_names)} available tasks")
        
        for task_name in task_names:
            try:
                # Check if we already have this task with matching checksum
                if task_name in existing_checksums:
                    local_path = os.path.join(TASKS_CACHE_DIR, task_name)
                    if os.path.exists(local_path):
                        local_checksum = calculate_sha256(local_path)
                        if local_checksum == existing_checksums[task_name]:
                            logger.debug(f"Task {task_name} already cached and verified")
                            new_checksums[task_name] = local_checksum
                            continue
                
                # Fetch the task
                content, remote_checksum = fetch_task_file(task_name)
                
                # Save to cache
                local_path = os.path.join(TASKS_CACHE_DIR, task_name)
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Verify local checksum
                local_checksum = calculate_sha256(local_path)
                if local_checksum != remote_checksum:
                    log_error(f"Checksum mismatch for {task_name}: expected {remote_checksum}, got {local_checksum}")
                    os.remove(local_path)
                    continue
                
                new_checksums[task_name] = local_checksum
                fetched_count += 1
                logger.info(f"Successfully cached and verified: {task_name}")
                
            except Exception as e:
                log_error(f"Failed to fetch task {task_name}: {e}")
                continue
        
        # Update checksums file
        all_checksums = {**existing_checksums, **new_checksums}
        save_checksums(all_checksums)
        
        log_task_complete("fetch_and_cache_tasks", {
            "total_tasks": len(task_names),
            "fetched_count": fetched_count,
            "total_cached": len(all_checksums)
        })
        
        return all_checksums
        
    except Exception as e:
        log_task_failed("fetch_and_cache_tasks", str(e))
        raise

def load_task(task_name: str) -> Dict[str, Any]:
    """
    Load a task from the local cache.
    
    Args:
        task_name: Name of the task file
        
    Returns:
        Parsed JSON content of the task
        
    Raises:
        FileNotFoundError: If the task is not in cache
        json.JSONDecodeError: If the task file is not valid JSON
    """
    local_path = os.path.join(TASKS_CACHE_DIR, task_name)
    
    if not os.path.exists(local_path):
        # Try to fetch it first
        logger.info(f"Task {task_name} not in cache, fetching...")
        fetch_and_cache_tasks([task_name])
        
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Task {task_name} not found in cache and could not be fetched")
    
    try:
        with open(local_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in task file {task_name}: {e}")
        raise

def verify_all_tasks() -> Dict[str, bool]:
    """
    Verify integrity of all cached tasks against stored checksums.
    
    Returns:
        Dictionary mapping task names to verification status
    """
    log_task_start("verify_all_tasks", {})
    
    try:
        checksums = load_existing_checksums()
        results = {}
        
        for task_name, expected_checksum in checksums.items():
            local_path = os.path.join(TASKS_CACHE_DIR, task_name)
            
            if not os.path.exists(local_path):
                results[task_name] = False
                log_error(f"Task {task_name} missing from cache")
                continue
            
            actual_checksum = calculate_sha256(local_path)
            results[task_name] = (actual_checksum == expected_checksum)
            
            if not results[task_name]:
                log_error(f"Checksum mismatch for {task_name}")
        
        log_task_complete("verify_all_tasks", {
            "verified_count": sum(results.values()),
            "total_count": len(checksums)
        })
        
        return results
        
    except Exception as e:
        log_task_failed("verify_all_tasks", str(e))
        raise

def main():
    """Main entry point for data loader script."""
    logger.info("Starting MobileGym data loader")
    
    try:
        # Fetch all available tasks
        checksums = fetch_and_cache_tasks()
        
        logger.info(f"Successfully fetched and cached {len(checksums)} tasks")
        
        # Verify all tasks
        verification_results = verify_all_tasks()
        verified_count = sum(verification_results.values())
        
        logger.info(f"Verification complete: {verified_count}/{len(verification_results)} tasks verified")
        
        if verified_count != len(verification_results):
            logger.warning("Some tasks failed verification")
            sys.exit(1)
        
        logger.info("All tasks verified successfully")
        
    except Exception as e:
        logger.error(f"Data loader failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()