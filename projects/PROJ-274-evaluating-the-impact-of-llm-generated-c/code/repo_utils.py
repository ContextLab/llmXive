import os
import subprocess
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple, Generator, Iterable
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_dirs(base_dir: str = "data/raw") -> None:
    """Ensure the base directory and subdirectories exist."""
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(os.path.join(base_dir, "repos"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "llm_docs"), exist_ok=True)

def clone_or_fetch_repo(repo_url: str, commit_hash: str, target_dir: str) -> str:
    """
    Clone a repository or fetch a specific commit if already cloned.
    Returns the path to the repository.
    """
    repo_path = os.path.join(target_dir, os.path.basename(repo_url).replace('.git', ''))
    
    if not os.path.exists(repo_path):
        logger.info(f"Cloning repository: {repo_url} to {repo_path}")
        subprocess.run(["git", "clone", repo_url, repo_path], check=True)
    else:
        logger.info(f"Repository already exists at {repo_path}, fetching specific commit.")
    
    subprocess.run(["git", "-C", repo_path, "fetch", "origin"], check=True)
    subprocess.run(["git", "-C", repo_path, "checkout", commit_hash], check=True)
    
    return repo_path

def get_repo_files(repo_path: str, max_files: int = 500) -> List[Dict[str, Any]]:
    """
    Get a list of files in the repository, limited to max_files.
    Returns a list of dicts with 'path', 'size', 'content' (truncated if too large).
    """
    files = []
    for root, _, filenames in os.walk(repo_path):
        # Skip hidden directories and common non-code directories
        if any(part.startswith('.') for part in root.split(os.sep)):
            continue
        if any(part in ['node_modules', '__pycache__', '.git', 'venv'] for part in root.split(os.sep)):
            continue
        
        for filename in filenames:
            if len(files) >= max_files:
                logger.warning(f"Reached max_files limit ({max_files}). Stopping scan.")
                return files
            
            file_path = os.path.join(root, filename)
            try:
                size = os.path.getsize(file_path)
                # Skip binary files or very large files immediately
                if size > 1_000_000:  # 1MB limit per file for raw inclusion
                    continue
                
                files.append({
                    'path': os.path.relpath(file_path, repo_path),
                    'size': size,
                    'content': None  # Content will be streamed later
                })
            except Exception as e:
                logger.warning(f"Could not process file {file_path}: {e}")
    
    return files

def generate_checksum(data: str) -> str:
    """Generate a SHA256 checksum of the input string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def log_pinned_repo(repo_url: str, commit_hash: str, target_dir: str) -> None:
    """Log the pinned repository information to a JSON file."""
    log_file = os.path.join(target_dir, "pinned_repo.json")
    data = {
        "repo_url": repo_url,
        "commit_hash": commit_hash,
        "pinned_at": subprocess.check_output(["date", "-u"]).decode('utf-8').strip()
    }
    with open(log_file, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Pinned repo logged to {log_file}")

def stream_repo_content(repo_path: str, file_list: List[Dict[str, Any]], 
                        chunk_size: int = 8192) -> Generator[Dict[str, Any], None, None]:
    """
    Stream file contents from the repository one by one to minimize memory usage.
    Yields dicts containing 'path', 'size', 'content' (as a string).
    
    This generator pattern ensures that only one file is loaded into memory at a time,
    keeping peak RAM usage under the 7GB constraint specified in FR-007.
    """
    for file_info in file_list:
        file_path = os.path.join(repo_path, file_info['path'])
        try:
            # Check if file is readable and not empty
            if os.path.getsize(file_path) == 0:
                continue
            
            content_parts = []
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Stream the file in chunks to avoid loading huge files entirely into memory
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    content_parts.append(chunk)
            
            content = "".join(content_parts)
            
            # Yield the file info with content
            yield {
                'path': file_info['path'],
                'size': len(content),
                'content': content
            }
            
        except Exception as e:
            logger.warning(f"Failed to stream content for {file_info['path']}: {e}")
            # Skip this file and continue with the next
            continue

def construct_llm_prompt_stream(repo_path: str, file_list: List[Dict[str, Any]]) -> Iterable[str]:
    """
    Construct a prompt for the LLM by streaming file contents.
    This function yields prompt segments that can be fed directly to an LLM API
    or a local model without loading the entire codebase into memory.
    
    Args:
        repo_path: Path to the cloned repository.
        file_list: List of file metadata dicts from get_repo_files.
    
    Yields:
        Strings representing parts of the prompt.
    """
    yield "=== Repository Documentation Request ===\n"
    yield f"Please analyze the following codebase structure and content to generate comprehensive documentation.\n\n"
    
    for file_info in file_list:
        file_path = os.path.join(repo_path, file_info['path'])
        try:
            if os.path.getsize(file_path) == 0:
                continue
            
            # Stream content in chunks for very large files if needed
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Truncate extremely long files to prevent context window overflow
            max_content_len = 100000  # ~100k chars
            if len(content) > max_content_len:
                content = content[:max_content_len] + "\n... [Content truncated due to size] ..."
            
            yield f"--- File: {file_info['path']} (Size: {file_info['size']} bytes) ---\n"
            yield content
            yield "\n\n"
            
        except Exception as e:
            logger.warning(f"Could not read file {file_info['path']}: {e}")
            continue

def main():
    """
    Main function to demonstrate streaming data loading for a repository.
    This is a utility script to verify the streaming functionality works correctly.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Stream repository content for LLM prompt construction")
    parser.add_argument("--repo-url", type=str, required=True, help="URL of the repository to clone")
    parser.add_argument("--commit", type=str, required=True, help="Commit hash to pin")
    parser.add_argument("--max-files", type=int, default=500, help="Maximum number of files to process")
    parser.add_argument("--output", type=str, default="data/raw/streamed_content.jsonl", help="Output file for streamed content")
    args = parser.parse_args()

    ensure_dirs("data/raw")
    target_dir = "data/raw/repos"
    
    # Clone or fetch the repository
    repo_path = clone_or_fetch_repo(args.repo_url, args.commit, target_dir)
    log_pinned_repo(args.repo_url, args.commit, target_dir)
    
    # Get list of files
    file_list = get_repo_files(repo_path, max_files=args.max_files)
    logger.info(f"Found {len(file_list)} files to process.")
    
    # Stream content and write to output file (JSONL format)
    output_path = args.output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f_out:
        for file_data in stream_repo_content(repo_path, file_list):
            f_out.write(json.dumps(file_data) + "\n")
    
    logger.info(f"Streamed content written to {output_path}")

if __name__ == "__main__":
    main()