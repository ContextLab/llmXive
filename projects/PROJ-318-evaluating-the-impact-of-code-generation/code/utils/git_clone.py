"""
Git repository clone utility for the llmXive research pipeline.
Clones repositories from a list into the data/raw/repos directory.
"""
import os
import logging
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional

from utils.exceptions import GitCloneException
from utils.repo_loader import load_repo_list

logger = logging.getLogger(__name__)

def clone_repository(repo_url: str, target_dir: Path, repo_slug: str) -> bool:
    """
    Clones a single Git repository to the specified target directory.

    Args:
        repo_url: The URL of the Git repository to clone.
        target_dir: The directory where the repository should be cloned.
        repo_slug: The slug/identifier for the repository (used for directory naming).

    Returns:
        True if cloning was successful, False otherwise.

    Raises:
        GitCloneException: If the clone operation fails.
    """
    repo_path = target_dir / repo_slug
    
    # If directory already exists, remove it to ensure a fresh clone
    if repo_path.exists():
        logger.info(f"Removing existing directory: {repo_path}")
        shutil.rmtree(repo_path)
    
    logger.info(f"Cloning {repo_url} to {repo_path}")
    
    try:
        # Use git clone with depth 1 to save bandwidth/time if possible
        # We don't need full history for code extraction
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(repo_path)],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout per repo
        )
        
        if result.returncode != 0:
            error_msg = f"Failed to clone {repo_url}: {result.stderr}"
            logger.error(error_msg)
            raise GitCloneException(error_msg)
        
        logger.info(f"Successfully cloned {repo_url}")
        return True
        
    except subprocess.TimeoutExpired:
        error_msg = f"Timeout cloning {repo_url}"
        logger.error(error_msg)
        raise GitCloneException(error_msg)
    except FileNotFoundError:
        error_msg = "Git command not found. Please ensure Git is installed and in PATH."
        logger.error(error_msg)
        raise GitCloneException(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error cloning {repo_url}: {str(e)}"
        logger.error(error_msg)
        raise GitCloneException(error_msg)

def clone_repos_from_list(
    repo_list_path: Path, 
    target_dir: Path,
    max_repos: Optional[int] = None
) -> List[dict]:
    """
    Clones repositories from a JSON list file.

    Args:
        repo_list_path: Path to the JSON file containing repository information.
        target_dir: Base directory where repositories will be cloned.
        max_repos: Maximum number of repositories to clone (None for all).

    Returns:
        List of dictionaries containing clone results with keys:
        - repo_slug: Identifier for the repository
        - success: Boolean indicating if clone was successful
        - error: Error message if failed, None otherwise

    Raises:
        GitCloneException: If repo list file is missing or invalid.
    """
    if not repo_list_path.exists():
        raise GitCloneException(f"Repository list file not found: {repo_list_path}")
    
    repos = load_repo_list(repo_list_path)
    
    if max_repos:
        repos = repos[:max_repos]
    
    results = []
    target_dir.mkdir(parents=True, exist_ok=True)
    
    for repo in repos:
        repo_slug = repo.get('repo_slug', repo.get('repo_name', 'unknown'))
        repo_url = repo.get('repo_url')
        
        if not repo_url:
            logger.warning(f"Skipping repo {repo_slug} - no URL found")
            results.append({
                'repo_slug': repo_slug,
                'success': False,
                'error': 'No URL found'
            })
            continue
        
        try:
            success = clone_repository(repo_url, target_dir, repo_slug)
            results.append({
                'repo_slug': repo_slug,
                'success': success,
                'error': None
            })
        except GitCloneException as e:
            results.append({
                'repo_slug': repo_slug,
                'success': False,
                'error': str(e)
            })
        
    return results

def verify_repo_exists(repo_dir: Path) -> bool:
    """
    Verifies that a cloned repository directory exists and contains a .git folder.

    Args:
        repo_dir: Path to the repository directory.

    Returns:
        True if the repository exists and is valid, False otherwise.
    """
    git_dir = repo_dir / '.git'
    return repo_dir.exists() and git_dir.exists() and git_dir.is_dir()

def main():
    """
    Main entry point for cloning repositories from the frozen list.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    repo_list_path = project_root / 'data' / 'raw' / 'frozen_repo_list.json'
    target_dir = project_root / 'data' / 'raw' / 'repos'
    
    logger.info(f"Starting repository cloning process")
    logger.info(f"Repo list: {repo_list_path}")
    logger.info(f"Target directory: {target_dir}")
    
    try:
        results = clone_repos_from_list(repo_list_path, target_dir)
        
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        logger.info(f"Cloning complete: {success_count}/{total_count} successful")
        
        for result in results:
            status = "SUCCESS" if result['success'] else "FAILED"
            logger.info(f"  {result['repo_slug']}: {status}")
            if not result['success'] and result['error']:
                logger.info(f"    Error: {result['error']}")
        
        # Verify all successful clones
        for result in results:
            if result['success']:
                repo_path = target_dir / result['repo_slug']
                if not verify_repo_exists(repo_path):
                    logger.error(f"Verification failed for {result['repo_slug']}")
                    result['success'] = False
                    result['error'] = "Verification failed after clone"
        
        # Return exit code based on success
        if success_count == total_count:
            logger.info("All repositories cloned successfully")
            return 0
        else:
            logger.warning(f"Some repositories failed to clone: {total_count - success_count} failed")
            return 1
            
    except GitCloneException as e:
        logger.error(f"Critical error during cloning: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
