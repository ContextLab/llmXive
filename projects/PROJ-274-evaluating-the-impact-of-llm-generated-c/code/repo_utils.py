"""
Repository utilities for fetching, pinning, and streaming codebases.
Implements T024: Codebase fetching (<=500 files) and commit pinning logic.
"""
import os
import subprocess
import hashlib
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Generator, Iterable
from pathlib import Path

# Configure logging for this module
logger = logging.getLogger(__name__)

# Constants
MAX_FILES_LIMIT = 500
GIT_TIMEOUT = 300  # seconds

class DataFetchError(Exception):
    """Raised when real data fetching fails."""
    pass

def ensure_dirs(output_dir: str) -> None:
    """Ensure the output directory exists."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

def clone_or_fetch_repo(repo_url: str, commit_hash: str, output_dir: str) -> str:
    """
    Clone a repository and checkout a specific commit.
    Returns the path to the checked-out directory.
    
    Args:
        repo_url: URL of the git repository
        commit_hash: Specific commit hash to pin to
        output_dir: Directory to clone into
        
    Returns:
        Path to the checked-out repository directory
        
    Raises:
        DataFetchError: If the repository cannot be fetched or commit not found
    """
    ensure_dirs(output_dir)
    repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
    repo_path = os.path.join(output_dir, repo_name)
    
    # Check if repo already exists
    if os.path.exists(repo_path):
        logger.info(f"Repository {repo_name} already exists at {repo_path}")
    else:
        logger.info(f"Cloning repository {repo_url}...")
        try:
            subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, repo_path],
                check=True,
                timeout=GIT_TIMEOUT,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise DataFetchError(f"Failed to clone repository {repo_url}: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise DataFetchError(f"Timeout cloning repository {repo_url}")
    
    # Checkout specific commit
    logger.info(f"Checking out commit {commit_hash}...")
    try:
        result = subprocess.run(
            ['git', '-C', repo_path, 'fetch', 'origin', commit_hash],
            check=True,
            timeout=GIT_TIMEOUT,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        raise DataFetchError(f"Failed to fetch commit {commit_hash}: {e.stderr}")
    
    try:
        result = subprocess.run(
            ['git', '-C', repo_path, 'checkout', commit_hash],
            check=True,
            timeout=GIT_TIMEOUT,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        raise DataFetchError(f"Failed to checkout commit {commit_hash}: {e.stderr}")
    
    # Verify commit hash matches
    try:
        result = subprocess.run(
            ['git', '-C', repo_path, 'rev-parse', 'HEAD'],
            check=True,
            timeout=GIT_TIMEOUT,
            capture_output=True,
            text=True
        )
        actual_hash = result.stdout.strip()
        if not actual_hash.startswith(commit_hash):
            raise DataFetchError(f"Commit hash mismatch: expected {commit_hash}, got {actual_hash}")
    except subprocess.CalledProcessError as e:
        raise DataFetchError(f"Failed to verify commit hash: {e.stderr}")
    
    logger.info(f"Successfully pinned to commit {actual_hash}")
    return repo_path

def get_repo_files(repo_path: str, max_files: int = MAX_FILES_LIMIT) -> Tuple[List[str], int]:
    """
    Get list of files in the repository, respecting the max_files limit.
    
    Args:
        repo_path: Path to the repository
        max_files: Maximum number of files to return
        
    Returns:
        Tuple of (list of file paths, total file count)
        
    Raises:
        DataFetchError: If file count exceeds limit
    """
    if not os.path.isdir(repo_path):
        raise DataFetchError(f"Repository path does not exist: {repo_path}")
    
    all_files = []
    for root, _, files in os.walk(repo_path):
        # Skip common non-code directories
        if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', 'venv', '.tox']):
            continue
        for file in files:
            # Skip binary files and common non-text files
            if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.exe', '.dll', '.so')):
                continue
            all_files.append(os.path.join(root, file))
    
    total_count = len(all_files)
    
    if total_count > max_files:
        raise DataFetchError(
            f"Repository has {total_count} files, exceeding limit of {max_files}. "
            f"Please select a smaller repository or adjust the limit."
        )
    
    # Sort for deterministic ordering
    all_files.sort()
    return all_files, total_count

def generate_checksum(file_path: str) -> str:
    """
    Generate SHA-256 checksum for a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hex digest of the file's SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def log_pinned_repo(repo_url: str, commit_hash: str, repo_path: str, output_file: str) -> None:
    """
    Log the pinned repository information to a JSON file.
    
    Args:
        repo_url: Original repository URL
        commit_hash: Pinned commit hash
        repo_path: Local path to the repository
        output_file: Path to the output JSON file
    """
    ensure_dirs(os.path.dirname(output_file))
    
    repo_info = {
        "repo_url": repo_url,
        "commit_hash": commit_hash,
        "repo_path": repo_path,
        "pinned_at": subprocess.run(
            ['git', '-C', repo_path, 'log', '-1', '--format=%ci'],
            capture_output=True,
            text=True
        ).stdout.strip() if os.path.exists(repo_path) else "unknown"
    }
    
    with open(output_file, 'w') as f:
        json.dump(repo_info, f, indent=2)
    
    logger.info(f"Pinned repository logged to {output_file}")

def stream_repo_content(repo_path: str, file_list: List[str]) -> Generator[Tuple[str, str], None, None]:
    """
    Stream file contents from the repository.
    
    Args:
        repo_path: Path to the repository
        file_list: List of file paths to stream
        
    Yields:
        Tuples of (relative_path, content)
    """
    for file_path in file_list:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(file_path, repo_path)
                yield rel_path, content
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            continue

def construct_llm_prompt_stream(repo_name: str, file_stream: Iterable[Tuple[str, str]], max_tokens: Optional[int] = None) -> str:
    """
    Construct an LLM prompt from streamed repository content.
    
    Args:
        repo_name: Name of the repository
        file_stream: Iterable of (relative_path, content) tuples
        max_tokens: Optional maximum token limit (approximate)
        
    Returns:
        Formatted prompt string
    """
    prompt_parts = [f"Repository: {repo_name}\n\n"]
    token_count = 0
    estimated_chars_per_token = 4
    
    for rel_path, content in file_stream:
        file_prompt = f"--- File: {rel_path} ---\n{content}\n\n"
        estimated_tokens = len(file_prompt) / estimated_chars_per_token
        
        if max_tokens and token_count + estimated_tokens > max_tokens:
            logger.warning(f"Token limit reached at {token_count}/{max_tokens}, stopping stream")
            break
        
        prompt_parts.append(file_prompt)
        token_count += estimated_tokens
    
    return "".join(prompt_parts)

def main():
    """Main entry point for testing repo_utils functionality."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Repository utilities for code fetching and pinning')
    parser.add_argument('--repo', required=True, help='Repository URL')
    parser.add_argument('--commit', required=True, help='Commit hash to pin to')
    parser.add_argument('--output-dir', default='data/raw/repos', help='Output directory for cloned repo')
    parser.add_argument('--log-file', default='data/raw/pinned_repo.json', help='Path to log pinned repo info')
    
    args = parser.parse_args()
    
    try:
        # Clone and checkout
        repo_path = clone_or_fetch_repo(args.repo, args.commit, args.output_dir)
        
        # Get file list
        files, count = get_repo_files(repo_path)
        logger.info(f"Found {count} files in repository")
        
        # Log pinned repo
        log_pinned_repo(args.repo, args.commit, repo_path, args.log_file)
        
        # Verify checksum of a sample file
        if files:
            sample_file = files[0]
            checksum = generate_checksum(sample_file)
            logger.info(f"Sample file checksum: {checksum}")
        
        logger.info("Repository fetching and pinning completed successfully")
        
    except DataFetchError as e:
        logger.error(f"Data fetch error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
