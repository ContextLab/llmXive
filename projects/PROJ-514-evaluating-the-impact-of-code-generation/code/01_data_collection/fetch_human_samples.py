"""
Fetch human-written code samples from GitHub repositories.

Implements the 'Balanced Blocked Design' from plan.md:
- Select 50 public GitHub repositories (>=100 stars, >=5 years history).
- Extract 3 "fresh" functions per repo (total 150).
- Use `git log --diff-filter=A` to find commits introducing functions.
- Save files to `data/raw/human_samples/` with metadata JSON sidecars.
"""

import os
import sys
import json
import subprocess
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
HUMAN_SAMPLES_DIR = DATA_RAW_DIR / "human_samples"
API_LOG_FILE = DATA_RAW_DIR / "api_logs.json"

# Ensure output directories exist
HUMAN_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
GITHUB_API_BASE = "https://api.github.com"
# Search for repos: public, created before 5 years ago, stars >= 100, language Python or Java
# We limit to Python for this implementation to ensure syntax validation works consistently
# unless we add Java support later.
SEARCH_QUERY = "language:Python stars:>=100 pushed:<2019-01-01"
REPO_COUNT_TARGET = 50
SAMPLES_PER_REPO = 3

# Logging
from utils.logger import get_logger
logger = get_logger(__name__)

from utils.config import get_project_root
from utils.validators import validate_python_syntax

def log_api_response(endpoint: str, status_code: int, data: Any = None):
    """Log API interactions to api_logs.json."""
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoint": endpoint,
        "status_code": status_code,
        "data_preview": str(data)[:200] if data else None
    }

    logs = []
    if API_LOG_FILE.exists():
        try:
            with open(API_LOG_FILE, 'r') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []

    logs.append(log_entry)
    with open(API_LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

def get_repos_from_github(query: str, count: int) -> List[Dict[str, Any]]:
    """
    Query GitHub API for repositories matching the criteria.
    Returns a list of repo metadata dicts.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-Research-Agent"
    }
    
    repos = []
    page = 1
    per_page = 100
    
    while len(repos) < count:
        url = f"{GITHUB_API_BASE}/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(per_page, count - len(repos)),
            "page": page
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            log_api_response(url, response.status_code, response.json())
            
            if response.status_code != 200:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                # If rate limited, wait and retry
                if response.status_code == 403:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                return repos
            
            data = response.json()
            items = data.get("items", [])
            if not items:
                break
            
            repos.extend(items)
            page += 1
            
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            break
    
    return repos[:count]

def clone_repo(repo_url: str, clone_path: Path) -> Optional[str]:
    """
    Clone a repository and return the SHA of the latest commit.
    Returns None if cloning fails.
    """
    try:
        # Clone with depth 1 for speed, but we need full history for --diff-filter=A
        # So we do a shallow clone then fetch full history for the specific commit
        # Actually, for --diff-filter=A we need the full history.
        # Let's do a full clone but with no checkout to save space initially
        subprocess.run(
            ["git", "clone", "--no-checkout", "--depth=1", repo_url, str(clone_path)],
            check=True,
            capture_output=True,
            timeout=120
        )
        
        # Fetch full history
        subprocess.run(
            ["git", "fetch", "--unshallow"],
            cwd=clone_path,
            check=True,
            capture_output=True,
            timeout=300
        )
        
        # Get latest commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=clone_path,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git clone/fetch failed for {repo_url}: {e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        logger.error(f"Git operation timed out for {repo_url}")
        return None

def find_fresh_functions(repo_path: Path, count: int) -> List[Dict[str, Any]]:
    """
    Find functions added in commits (diff-filter=A).
    Returns list of dicts with function info.
    """
    functions = []
    
    try:
        # Get all commits that added files (diff-filter=A)
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--name-only", "--pretty=format:%H", "--", "*.py"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        lines = result.stdout.strip().split('\n')
        current_commit = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if it's a commit hash (40 hex chars)
            if len(line) == 40 and all(c in '0123456789abcdef' for c in line):
                current_commit = line
            elif current_commit and line.endswith('.py'):
                # This is a file added in current_commit
                # Get the function definitions in this file at this commit
                try:
                    # Checkout the file at this commit
                    file_content = subprocess.run(
                        ["git", "show", f"{current_commit}:{line}"],
                        cwd=repo_path,
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    ).stdout
                    
                    # Parse functions from the file content
                    import ast
                    try:
                        tree = ast.parse(file_content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                # Check if this is a top-level function or method
                                # We'll take all functions for now
                                functions.append({
                                    "commit_sha": current_commit,
                                    "file_path": line,
                                    "function_name": node.name,
                                    "start_line": node.lineno,
                                    "end_line": node.end_lineno if hasattr(node, 'end_lineno') else node.lineno + 10,
                                    "content": file_content
                                })
                                
                                if len(functions) >= count:
                                    return functions
                    except SyntaxError:
                        # Skip files with syntax errors
                        continue
                        
                except subprocess.CalledProcessError:
                    continue
                
                if len(functions) >= count:
                    break
                
        return functions
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git log failed: {e.stderr}")
        return []
    except subprocess.TimeoutExpired:
        logger.error("Git log timed out")
        return []

def save_sample(sample_data: Dict[str, Any], sample_id: str):
    """
    Save a code sample and its metadata to disk.
    """
    # Sanitize sample_id for filename
    safe_id = sample_id.replace("/", "_").replace(":", "_")
    file_path = HUMAN_SAMPLES_DIR / f"{safe_id}.py"
    meta_path = HUMAN_SAMPLES_DIR / f"{safe_id}.json"
    
    # Save code
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(sample_data["content"])
    
    # Save metadata
    metadata = {
        "sample_id": sample_id,
        "source_type": "human",
        "repository_id": sample_data["repo_id"],
        "issue_id": sample_data.get("issue_id", "N/A"),
        "task_id": sample_data.get("task_id", "N/A"),
        "language": "python",
        "file_path": sample_data["file_path"],
        "function_name": sample_data["function_name"],
        "is_fresh_commit": True,
        "commit_sha": sample_data["commit_sha"],
        "repo_name": sample_data["repo_name"],
        "validation_status": "pending"
    }
    
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved sample: {sample_id} -> {file_path}")

def main():
    """
    Main entry point for fetching human samples.
    """
    logger.info("Starting human sample collection...")
    
    # Step 1: Get repositories
    logger.info(f"Querying GitHub for repositories matching: {SEARCH_QUERY}")
    repos = get_repos_from_github(SEARCH_QUERY, REPO_COUNT_TARGET)
    
    if not repos:
        logger.error("No repositories found. Exiting.")
        sys.exit(1)
    
    logger.info(f"Found {len(repos)} repositories.")
    
    all_samples = []
    repo_index = 0
    
    for repo in repos:
        if len(all_samples) >= REPO_COUNT_TARGET * SAMPLES_PER_REPO:
            break
        
        repo_id = repo["full_name"]
        repo_url = repo["html_url"]
        logger.info(f"Processing repo: {repo_id} (ID: {repo_index + 1}/{len(repos)})")
        
        # Create temp directory for clone
        temp_clone_path = PROJECT_ROOT / "temp_clones" / repo_id.replace("/", "_")
        temp_clone_path.mkdir(parents=True, exist_ok=True)
        
        # Clone repo
        clone_path = temp_clone_path / "repo"
        if clone_path.exists():
            import shutil
            shutil.rmtree(clone_path)
        
        commit_sha = clone_repo(repo_url, clone_path)
        if not commit_sha:
            logger.warning(f"Failed to clone {repo_id}, skipping.")
            repo_index += 1
            continue
        
        # Find fresh functions
        functions = find_fresh_functions(clone_path, SAMPLES_PER_REPO)
        
        for i, func in enumerate(functions):
            sample_id = f"{repo_id.replace('/', '__')}__{func['function_name']}_{i}"
            
            sample_data = {
                "repo_id": repo_id,
                "repo_name": repo["name"],
                "issue_id": "N/A",  # Would need to map commit to issue
                "task_id": "N/A",
                "file_path": func["file_path"],
                "function_name": func["function_name"],
                "commit_sha": func["commit_sha"],
                "content": func["content"]
            }
            
            # Validate syntax before saving
            if validate_python_syntax(func["content"]):
                save_sample(sample_data, sample_id)
                all_samples.append(sample_id)
                logger.info(f"  Saved function: {func['function_name']}")
            else:
                logger.warning(f"  Invalid Python syntax for {func['function_name']}, skipping.")
        
        # Cleanup clone
        import shutil
        if clone_path.exists():
            shutil.rmtree(clone_path)
        
        repo_index += 1
        
        # Rate limiting
        time.sleep(1)
    
    logger.info(f"Collection complete. Total samples: {len(all_samples)}")
    logger.info(f"Samples saved to: {HUMAN_SAMPLES_DIR}")
    
    # Log completion
    log_api_response("collection_complete", 200, {"total_samples": len(all_samples)})
    
    return len(all_samples)

if __name__ == "__main__":
    main()
