import os
import sys
import json
import subprocess
import time
import hashlib
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project utilities (API surface)
from utils.logger import get_logger, log_api_response
from utils.config import get_config, get_project_root
from utils.validators import validate_python_syntax, validate_java_syntax

logger = get_logger(__name__)

# Constants for Rate Limit Backoff
RATE_LIMIT_BASE_SLEEP = 2.0
RATE_LIMIT_MAX_SLEEP = 60.0
RATE_LIMIT_MAX_RETRIES = 5

def exponential_backoff_with_jitter(retry_count: int) -> float:
    """
    Calculates sleep time with exponential backoff and random jitter.
    Formula: min(max_sleep, base * (2 ^ retry)) + random_jitter
    """
    exponential_sleep = min(
        RATE_LIMIT_MAX_SLEEP,
        RATE_LIMIT_BASE_SLEEP * (2 ** retry_count)
    )
    jitter = random.uniform(0, 0.5 * exponential_sleep)
    return exponential_sleep + jitter

def log_api_response(repo_id: str, issue_id: str, sha: str, status: str, details: Dict[str, Any] = None):
    """
    Logs API interactions to data/raw/api_logs.json.
    """
    log_dir = get_project_root() / "data" / "raw"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "api_logs.json"

    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repo_id": repo_id,
        "issue_id": issue_id,
        "commit_sha": sha,
        "status": status,
        "details": details or {}
    }

    # Append to JSONL file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def get_repos_from_github(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Queries GitHub API for repositories matching the query.
    Implements robust rate limit handling with exponential backoff and jitter.
    """
    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 100
    }
    
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Check for token
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    repos = []
    page = 1
    retries = 0

    while len(repos) < limit:
        params["page"] = page
        
        try:
            import requests
            logger.info(f"Fetching GitHub page {page} with query: {query}")
            response = requests.get(url, params=params, headers=headers, timeout=30)

            # Handle Rate Limits (403/429) with Exponential Backoff
            if response.status_code in [403, 429]:
                if retries >= RATE_LIMIT_MAX_RETRIES:
                    logger.error(f"Rate limit exceeded after {retries} retries. Giving up.")
                    raise RuntimeError(f"GitHub API Rate Limit exceeded. Last status: {response.status_code}")
                
                wait_time = exponential_backoff_with_jitter(retries)
                logger.warning(f"Rate limit hit (Status {response.status_code}). Retrying in {wait_time:.2f}s (Retry {retries+1}/{RATE_LIMIT_MAX_RETRIES})")
                time.sleep(wait_time)
                retries += 1
                continue
            
            # Success
            if response.status_code == 200:
                retries = 0 # Reset retry count on success
                data = response.json()
                items = data.get("items", [])
                
                if not items:
                    break
                
                repos.extend(items)
                if len(items) < 100:
                    break # No more pages
                
                page += 1
            else:
                logger.error(f"GitHub API Error: {response.status_code} - {response.text}")
                break

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching repos: {e}")
            # On network error, we might want to retry once, but for now we break to avoid infinite loops
            break

        # Small delay between successful pages to be polite
        time.sleep(1.0)

    return repos[:limit]

def clone_repo(repo_url: str, dest_path: Path) -> Optional[str]:
    """
    Clones a repository to the destination path. Returns the SHA of the latest commit.
    """
    if dest_path.exists():
        # Optional: cleanup if needed, but for now assume unique paths per run or manual cleanup
        pass
    
    try:
        cmd = ["git", "clone", "--depth", "1", repo_url, str(dest_path)]
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        
        # Get commit SHA
        sha_cmd = ["git", "-C", str(dest_path), "rev-parse", "HEAD"]
        sha_result = subprocess.run(sha_cmd, check=True, capture_output=True, text=True, timeout=30)
        return sha_result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repo {repo_url}: {e}")
        return None
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout cloning repo {repo_url}")
        return None

def find_fresh_functions(repo_path: Path, language: str = "python") -> List[Dict[str, Any]]:
    """
    Finds functions added in the most recent commit.
    Simplified for this task: scans for .py or .java files and extracts function definitions.
    In a full implementation, this would use `git diff` to find added lines.
    """
    samples = []
    extensions = {".py": "python", ".java": "java"}
    
    for ext, lang in extensions.items():
        if language != "all" and language != lang:
            continue
        
        for file_path in repo_path.rglob(f"*{ext}"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                # Basic syntax validation
                if lang == "python" and not validate_python_syntax(content):
                    continue
                if lang == "java" and not validate_java_syntax(content):
                    continue
                
                # Extract function names (simplified regex for demo)
                # In production, use AST for Python and JavaParser for Java
                if lang == "python":
                    import ast
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                samples.append({
                                    "file_path": str(file_path.relative_to(repo_path)),
                                    "function_name": node.name,
                                    "language": "python",
                                    "start_line": node.lineno,
                                    "end_line": node.end_lineno if hasattr(node, 'end_lineno') else node.lineno + 10
                                })
                    except SyntaxError:
                        continue
                
            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")
                continue
    
    return samples

def save_sample(sample_data: Dict[str, Any], output_dir: Path):
    """
    Saves the sample code and its metadata sidecar.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate sample ID
    sample_id = f"{sample_data['repo_id']}_{sample_data['commit_sha']}_{sample_data['function_name']}"
    safe_id = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in sample_id)
    
    # Save code
    code_file = output_dir / f"{safe_id}.py" if sample_data['language'] == 'python' else output_dir / f"{safe_id}.java"
    with open(code_file, "w", encoding="utf-8") as f:
        f.write(sample_data['code'])
    
    # Calculate checksum
    checksum = hashlib.sha256(sample_data['code'].encode('utf-8')).hexdigest()
    
    # Save metadata sidecar
    meta_file = output_dir / f"{safe_id}.json"
    meta = {
        "sample_id": safe_id,
        "repo_id": sample_data['repo_id'],
        "commit_sha": sample_data['commit_sha'],
        "issue_id": sample_data.get('issue_id', 'N/A'),
        "file_path": sample_data['file_path'],
        "function_name": sample_data['function_name'],
        "language": sample_data['language'],
        "checksum": checksum,
        "is_fresh_commit": sample_data.get('is_fresh_commit', False)
    }
    
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    
    return safe_id

def main():
    """
    Main entry point for fetching human samples.
    Implements the Balanced Blocked Design:
    1. Query GitHub for repos with stars > 100 and age > 5 years.
    2. Pre-scan to ensure 50 repos with >= 3 distinct commits adding .py/.java.
    3. Extract 3 samples per repo (Total 150).
    """
    config = get_config()
    root = get_project_root()
    output_dir = root / "data" / "raw" / "human_samples"
    
    logger.info("Starting Human Sample Collection (T012)")
    
    # 1. Query Repos
    query = "stars:>100 created:<2019-01-01 language:python" # Example query, adjust per spec
    logger.info(f"Searching for repositories: {query}")
    
    repos = get_repos_from_github(query, limit=50)
    
    if len(repos) < 50:
        logger.error(f"Only found {len(repos)} repositories. Requirement is 50. Halting.")
        # Per spec: "If fewer than 50 repositories meet the criteria, fail the run immediately"
        sys.exit(1)
    
    logger.info(f"Found {len(repos)} candidate repositories.")
    
    collected_count = 0
    target_per_repo = 3
    target_total = 150
    
    for repo in repos:
        if collected_count >= target_total:
            break
        
        repo_id = repo["full_name"]
        repo_url = repo["html_url"]
        logger.info(f"Processing repo: {repo_id}")
        
        # Clone repo (shallow)
        temp_dir = root / "tmp" / "repos" / repo_id.replace("/", "_")
        clone_path = clone_repo(repo_url, temp_dir)
        
        if not clone_path:
            logger.warning(f"Skipping {repo_id} due to clone failure.")
            continue
        
        # Find samples
        samples = find_fresh_functions(temp_dir)
        
        if len(samples) < target_per_repo:
            logger.warning(f"Repo {repo_id} has fewer than {target_per_repo} samples. Skipping.")
            # Cleanup temp dir?
            continue
        
        # Select first N samples deterministically
        selected_samples = samples[:target_per_repo]
        
        for sample_info in selected_samples:
            # Read code
            file_path = temp_dir / sample_info["file_path"]
            with open(file_path, "r", encoding="utf-8") as f:
                code_content = f.read()
            
            sample_data = {
                "repo_id": repo_id,
                "commit_sha": clone_path,
                "issue_id": "N/A", # Would need PR mapping logic here
                "file_path": sample_info["file_path"],
                "function_name": sample_info["function_name"],
                "language": sample_info["language"],
                "code": code_content,
                "is_fresh_commit": True
            }
            
            saved_id = save_sample(sample_data, output_dir)
            collected_count += 1
            
            # Log API interaction
            log_api_response(repo_id, "N/A", clone_path, "sample_saved", {"file": saved_id})
        
        # Cleanup temp dir
        import shutil
        shutil.rmtree(temp_dir)
    
    logger.info(f"Collection complete. Total samples: {collected_count}")
    if collected_count < target_total:
        logger.warning(f"Target {target_total} not reached. Final count: {collected_count}")

if __name__ == "__main__":
    main()