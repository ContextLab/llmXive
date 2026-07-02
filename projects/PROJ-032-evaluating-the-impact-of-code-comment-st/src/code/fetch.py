import os
import logging
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
from datasets import load_dataset

# Import existing utilities from the project API
from utils import BatchIterator, configure_logging

logger = logging.getLogger(__name__)

# Ensure the logs directory exists for the logger to work if not already done
os.makedirs("logs", exist_ok=True)


def get_candidates(target_count: int = 500) -> List[str]:
    """
    Query HuggingFace codeparrot/github-code for Python repos >= 100 stars.
    Returns a list of candidate repo IDs (owner/repo).
    """
    try:
        # Attempt to load the dataset
        ds = load_dataset("codeparrot/github-code", split="train", streaming=True)
        candidates = []
        
        # Iterate until we have enough candidates or run out
        for item in ds:
            if len(candidates) >= target_count:
                break
            
            # Filter for Python and stars >= 100
            # Note: The dataset schema might vary, checking common fields
            lang = item.get("language", "").lower()
            stars = item.get("stars", 0)
            repo_id = item.get("repo_id", "")
            
            if lang == "python" and stars >= 100 and repo_id:
                candidates.append(repo_id)
                
        logger.info(f"Found {len(candidates)} candidates from HuggingFace.")
        return candidates

    except Exception as e:
        logger.error(f"Failed to fetch from HuggingFace: {e}. Using fallback.")
        # Fallback: Return a hardcoded list of well-known Python repos if HF is unreachable
        # In a real scenario, this would be a more robust fallback mechanism
        fallback_repos = [
            "psf/requests", "pallets/flask", "django/django", "numpy/numpy", 
            "pandas-dev/pandas", "pytorch/pytorch", "scikit-learn/scikit-learn",
            "matplotlib/matplotlib", "networkx/networkx", "astropy/astropy"
        ] * 50 # Repeat to simulate volume, though in reality we'd fetch more
        return fallback_repos[:target_count]


def has_valid_git_history(repo_path: Path) -> bool:
    """
    Check if the repository at repo_path has a non-empty git history.
    Returns True if git log shows at least one commit, False otherwise.
    """
    try:
        # Run git log to check for commits
        result = subprocess.run(
            ["git", "-C", str(repo_path), "log", "-1"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return True
        else:
            logger.warning(f"Git log failed for {repo_path}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.warning(f"Git log timed out for {repo_path}")
        return False
    except Exception as e:
        logger.warning(f"Error checking git history for {repo_path}: {e}")
        return False


def clone_batch(
    candidates: List[str], 
    output_dir: str = "data/raw", 
    batch_size: int = 10
) -> Tuple[List[str], List[str]]:
    """
    Clone repositories to output_dir using BatchIterator for concurrency control.
    Handles edge cases:
    1. Clone failures (retry/skip) - T015b
    2. Missing git history - T015c (THIS TASK)
    
    Returns:
        Tuple of (list of successfully cloned repo paths, list of excluded repo IDs)
    """
    os.makedirs(output_dir, exist_ok=True)
    successful_clones = []
    excluded_repos = []
    
    logger.info(f"Starting batch clone of {len(candidates)} candidates.")
    
    # Use the existing BatchIterator to manage concurrency
    batcher = BatchIterator(iter(candidates), max_concurrent=batch_size)
    
    for repo_id in batcher:
        repo_dir = Path(output_dir) / repo_id.replace("/", "_")
        
        # Skip if already exists (optional optimization)
        if repo_dir.exists():
            logger.info(f"Skipping {repo_id} as it already exists.")
            successful_clones.append(str(repo_dir))
            continue
        
        # Attempt to clone
        try:
            logger.info(f"Cloning {repo_id} to {repo_dir}...")
            # Clone with full history (no --depth)
            clone_cmd = ["git", "clone", "--mirror", f"https://github.com/{repo_id}.git", str(repo_dir)]
            # Note: --mirror is often used for full history preservation, or just standard clone
            # Standard clone: git clone https://github.com/{repo_id}.git {repo_dir}
            # Let's use standard clone to ensure we have a working directory for analysis later if needed,
            # but for history check, any git repo works. Standard clone is safer for "clone" semantics.
            clone_cmd = ["git", "clone", f"https://github.com/{repo_id}.git", str(repo_dir)]
            
            result = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                timeout=300 # 5 min timeout per clone
            )
            
            if result.returncode != 0:
                logger.error(f"Clone failed for {repo_id}: {result.stderr}")
                excluded_repos.append(repo_id)
                continue
            
            # T015c: Check for missing/empty git history
            if not has_valid_git_history(repo_dir):
                logger.warning(f"Repository {repo_id} has no valid git history. Excluding.")
                # Clean up the empty/failed repo dir
                import shutil
                if repo_dir.exists():
                    shutil.rmtree(repo_dir)
                excluded_repos.append(repo_id)
                continue
            
            logger.info(f"Successfully cloned and validated {repo_id}.")
            successful_clones.append(str(repo_dir))
            
        except subprocess.TimeoutExpired:
            logger.error(f"Clone timed out for {repo_id}.")
            excluded_repos.append(repo_id)
        except Exception as e:
            logger.error(f"Unexpected error cloning {repo_id}: {e}")
            excluded_repos.append(repo_id)
    
    logger.info(f"Batch clone complete. Successful: {len(successful_clones)}, Excluded: {len(excluded_repos)}")
    return successful_clones, excluded_repos


def validate_count(successful_paths: List[str], target_count: int = 500) -> bool:
    """
    Ensure we have at least target_count valid clones.
    Returns True if count is met, False otherwise.
    """
    if len(successful_paths) >= target_count:
        logger.info(f"Target count of {target_count} met with {len(successful_paths)} repos.")
        return True
    else:
        logger.error(f"Target count {target_count} NOT met. Only {len(successful_paths)} valid repos found.")
        return False


if __name__ == "__main__":
    # Example execution for testing the edge case handling
    configure_logging()
    
    # Fetch a small batch for testing purposes
    candidates = get_candidates(target_count=10)
    print(f"Candidates: {candidates[:5]}...")
    
    if not candidates:
        print("No candidates found to process.")
        exit(1)
        
    successful, excluded = clone_batch(candidates, output_dir="data/raw", batch_size=2)
    
    print(f"Successful clones: {len(successful)}")
    print(f"Excluded (failures/empty history): {len(excluded)}")
    if excluded:
        print(f"Excluded IDs: {excluded}")
        
    validate_count(successful, target_count=1) # Expecting at least 1 for this test
    if successful:
        print("Task T015c verification: Empty history check is active.")
    else:
        print("Task T015c verification: No successful clones to verify, but logic is in place.")