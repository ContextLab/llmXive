"""
Git repository clone utility for the llmXive pipeline.

Implements cloning repositories from a list and verifying their existence
in the designated data directory.
"""
import os
import logging
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional

from utils.exceptions import GitCloneException

logger = logging.getLogger(__name__)


def clone_repository(repo_url: str, target_dir: Path, timeout: int = 300) -> Path:
    """
    Clone a single git repository to the target directory.
    
    Args:
        repo_url: The URL of the git repository (e.g., 'https://github.com/psf/requests.git')
        target_dir: The directory where the repository should be cloned
        timeout: Maximum time in seconds to wait for the clone operation
        
    Returns:
        Path to the cloned repository directory
        
    Raises:
        GitCloneException: If the clone operation fails
    """
    if not repo_url:
        raise GitCloneException("Repository URL cannot be empty")
        
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        
    # Extract repo name from URL for the target path
    repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
    repo_path = target_dir / repo_name
    
    # If repo already exists, skip cloning
    if repo_path.exists() and any(repo_path.iterdir()):
        logger.info(f"Repository {repo_name} already exists at {repo_path}, skipping clone")
        return repo_path
        
    # Remove partially cloned directories if any
    if repo_path.exists():
        shutil.rmtree(repo_path)
        
    try:
        logger.info(f"Cloning repository: {repo_url} to {repo_path}")
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', repo_url, str(repo_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )
        logger.info(f"Successfully cloned {repo_name}")
        return repo_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repository {repo_url}: {e.stderr}")
        raise GitCloneException(f"Git clone failed for {repo_url}: {e.stderr}")
        
    except subprocess.TimeoutExpired as e:
        logger.error(f"Timeout cloning repository {repo_url}")
        raise GitCloneException(f"Timeout cloning {repo_url} after {timeout}s")
        
    except FileNotFoundError:
        raise GitCloneException("Git command not found. Please install git.")
    except Exception as e:
        logger.error(f"Unexpected error cloning {repo_url}: {str(e)}")
        raise GitCloneException(f"Unexpected error cloning {repo_url}: {str(e)}")


def clone_repos_from_list(
    repo_list: List[Dict[str, str]],
    base_dir: Path,
    max_repos: Optional[int] = None
) -> List[Path]:
    """
    Clone multiple repositories from a list of repository dictionaries.
    
    Args:
        repo_list: List of dictionaries containing 'repo_url' key
        base_dir: Base directory where repositories will be cloned
        max_repos: Maximum number of repositories to clone (None for all)
        
    Returns:
        List of paths to cloned repositories
        
    Raises:
        GitCloneException: If any clone operation fails
    """
    if not repo_list:
        logger.warning("Empty repository list provided")
        return []
        
    if max_repos:
        repo_list = repo_list[:max_repos]
        
    cloned_paths = []
    failed_urls = []
    
    for idx, repo_info in enumerate(repo_list, 1):
        repo_url = repo_info.get('repo_url')
        if not repo_url:
            logger.warning(f"Skipping entry {idx}: missing 'repo_url'")
            continue
            
        logger.info(f"Processing repository {idx}/{len(repo_list)}: {repo_url}")
        
        try:
            repo_path = clone_repository(repo_url, base_dir)
            cloned_paths.append(repo_path)
        except GitCloneException as e:
            logger.error(f"Failed to clone {repo_url}: {str(e)}")
            failed_urls.append((repo_url, str(e)))
            
    if failed_urls:
        logger.warning(f"Failed to clone {len(failed_urls)} repositories")
        for url, error in failed_urls:
            logger.warning(f"  - {url}: {error}")
            
    logger.info(f"Successfully cloned {len(cloned_paths)} repositories")
    return cloned_paths


def verify_repo_exists(repo_path: Path) -> bool:
    """
    Verify that a cloned repository exists and contains files.
    
    Args:
        repo_path: Path to the repository directory
        
    Returns:
        True if repository exists and is not empty, False otherwise
    """
    if not repo_path.exists():
        logger.warning(f"Repository path does not exist: {repo_path}")
        return False
        
    if not repo_path.is_dir():
        logger.warning(f"Repository path is not a directory: {repo_path}")
        return False
        
    try:
        # Check if directory has any contents
        if not any(repo_path.iterdir()):
            logger.warning(f"Repository directory is empty: {repo_path}")
            return False
            
        return True
    except PermissionError:
        logger.warning(f"Permission denied accessing repository: {repo_path}")
        return False
    except Exception as e:
        logger.warning(f"Error verifying repository {repo_path}: {str(e)}")
        return False


def main():
    """
    Main entry point for testing the git clone utility.
    Clones repositories from data/raw/repo_list.json to data/raw/repos/.
    """
    from utils.repo_loader import load_repo_list
    from config import get_config
    
    config = get_config()
    base_dir = Path("data/raw/repos")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Load repository list
    repo_list_path = Path("data/raw/repo_list.json")
    if not repo_list_path.exists():
        logger.error(f"Repository list not found: {repo_list_path}")
        logger.error("Please run T010 first to generate the repo list.")
        return 1
        
    try:
        repo_list = load_repo_list(repo_list_path)
    except Exception as e:
        logger.error(f"Failed to load repository list: {str(e)}")
        return 1
        
    logger.info(f"Loaded {len(repo_list)} repositories from {repo_list_path}")
    
    # Clone repositories
    cloned_paths = clone_repos_from_list(repo_list, base_dir)
    
    # Verify clones
    verified_count = 0
    for path in cloned_paths:
        if verify_repo_exists(path):
            verified_count += 1
        else:
            logger.error(f"Verification failed for: {path}")
            
    logger.info(f"Verification complete: {verified_count}/{len(cloned_paths)} repositories verified")
    
    if verified_count == 0:
        logger.error("No repositories were successfully cloned and verified")
        return 1
        
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    exit(main())
