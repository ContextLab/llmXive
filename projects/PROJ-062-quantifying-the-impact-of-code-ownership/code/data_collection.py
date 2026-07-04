import os
import subprocess
import sys
import time
import logging
import shutil
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Add parent to path for imports if running as script
if __name__ == "__main__" and "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))
elif "code" not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging_utils import get_logger, configure_logging
from utils.api_utils import fetch_with_backoff, retry_with_exponential_backoff
from utils.path_utils import normalize_path
from utils.memory_utils import clear_memory, check_memory_limit

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"
DEFAULT_TIMEOUT = 30

logger = get_logger(__name__)

def clone_repository(repo_url: str, target_dir: Path, depth: int = 1000) -> bool:
    """Clone a repository with shallow history."""
    try:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        
        cmd = [
            "git", "clone", "--depth", str(depth),
            "--single-branch", repo_url, str(target_dir)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to clone {repo_url}: {result.stderr}")
            return False
        
        logger.info(f"Successfully cloned {repo_url} to {target_dir}")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout cloning {repo_url}")
        return False
    except Exception as e:
        logger.error(f"Error cloning {repo_url}: {e}")
        return False

def get_commit_count(repo_path: Path) -> int:
    """Get the number of commits in the repository."""
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
        return 0
    except Exception as e:
        logger.error(f"Error getting commit count for {repo_path}: {e}")
        return 0

def verify_repository(repo_path: Path, min_commits: int = 1000) -> bool:
    """Verify repository has sufficient commits."""
    count = get_commit_count(repo_path)
    if count < min_commits:
        logger.warning(f"Repository {repo_path} has only {count} commits (min: {min_commits})")
        return False
    return True

def parse_commit_logs(repo_path: Path, cutoff_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Parse commit logs to extract ownership data."""
    commits = []
    try:
        cmd = ["git", "log", "--format=%H|%an|%ae|%aI|%s", "--numstat"]
        if cutoff_date:
            cmd.extend(["--since", cutoff_date.isoformat()])
        
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to parse commits: {result.stderr}")
            return []
        
        output = result.stdout
        current_commit = None
        
        for line in output.split('\n'):
            if not line.strip():
                continue
            
            if '|' in line and len(line.split('|')) >= 5:
                parts = line.split('|')
                current_commit = {
                    "hash": parts[0],
                    "author_name": parts[1],
                    "author_email": parts[2],
                    "date": parts[3],
                    "subject": parts[4],
                    "files": []
                }
            elif current_commit and '\t' in line:
                file_parts = line.split('\t')
                if len(file_parts) >= 3:
                    added = int(file_parts[0]) if file_parts[0] != '-' else 0
                    deleted = int(file_parts[1]) if file_parts[1] != '-' else 0
                    filepath = file_parts[2]
                    current_commit["files"].append({
                        "path": filepath,
                        "added": added,
                        "deleted": deleted
                    })
            
            if current_commit and current_commit["files"]:
                commits.append(current_commit)
                current_commit = None
        
        return commits
    except Exception as e:
        logger.error(f"Error parsing commit logs: {e}")
        return []

def get_repo_owner_name(repo_url: str) -> Optional[Tuple[str, str]]:
    """Extract owner and repo name from GitHub URL."""
    try:
        # Handle both https and git@ formats
        if repo_url.startswith("https://github.com/"):
            parts = repo_url.rstrip('/').split('/')
            if len(parts) >= 2:
                owner = parts[-2]
                repo = parts[-1].replace('.git', '')
                return owner, repo
        elif repo_url.startswith("git@github.com:"):
            parts = repo_url.split(':')
            if len(parts) >= 2:
                path_part = parts[1].rstrip('/').split('/')
                if len(path_part) >= 2:
                    owner = path_part[-2]
                    repo = path_part[-1].replace('.git', '')
                    return owner, repo
        return None
    except Exception as e:
        logger.error(f"Error parsing repo URL: {e}")
        return None

def fetch_issues_for_repo(owner: str, repo: str, since: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch issues and PRs from GitHub API with exponential backoff."""
    issues = []
    page = 1
    per_page = 100
    
    base_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues"
    params = {
        "state": "all",
        "per_page": per_page,
        "page": page,
        "filter": "all"
    }
    
    if since:
        params["since"] = since
    
    while True:
        params["page"] = page
        try:
            response = fetch_with_backoff(base_url, params=params)
            if not response:
                break
            
            data = response.json()
            if not data:
                break
            
            for item in data:
                # Skip pull requests (they are included in issues endpoint)
                if "pull_request" in item:
                    continue
                
                issues.append({
                    "issue_number": item.get("number"),
                    "title": item.get("title"),
                    "state": item.get("state"),
                    "created_at": item.get("created_at"),
                    "closed_at": item.get("closed_at"),
                    "user": item.get("user", {}).get("login"),
                    "labels": [l.get("name") for l in item.get("labels", [])],
                    "repository_url": item.get("repository_url"),
                    "html_url": item.get("html_url")
                })
            
            if len(data) < per_page:
                break
            
            page += 1
            time.sleep(1)  # Rate limit compliance
            
        except Exception as e:
            logger.error(f"Error fetching issues page {page}: {e}")
            break
    
    return issues

def fetch_bug_data_for_commit(repo_path: Path, repo_url: str, cutoff_date: datetime) -> List[Dict[str, Any]]:
    """
    Fetch bug data associated with commits in the repository.
    Uses GitHub Issues API to find issues/PRs that might be linked to code changes.
    """
    owner_name = get_repo_owner_name(repo_url)
    if not owner_name:
        logger.warning(f"Could not extract owner/repo from {repo_url}")
        return []
    
    owner, repo = owner_name
    logger.info(f"Fetching bug data for {owner}/{repo}")
    
    # Fetch issues since the cutoff date (T+1 window for bug tracking)
    # We look for bugs reported after the analysis window
    since_date = cutoff_date.isoformat()
    issues = fetch_issues_for_repo(owner, repo, since=since_date)
    
    bug_data = []
    
    # Also fetch issues that might have been created before but closed after T
    # This is a heuristic: we consider an issue a "bug" if it's closed and labeled as bug
    # or if the title contains common bug keywords
    if not issues:
        # Try fetching all issues without date filter if none found
        issues = fetch_issues_for_repo(owner, repo)
    
    for issue in issues:
        # Heuristic: Consider closed issues with 'bug' label or keywords as bugs
        is_bug = False
        if issue.get("state") == "closed":
            labels = issue.get("labels", [])
            if "bug" in [l.lower() for l in labels]:
                is_bug = True
            elif any(kw in issue.get("title", "").lower() for kw in ["bug", "fix", "error", "crash", "issue"]):
                is_bug = True
        
        if is_bug:
            # Try to link issue to specific files via commit messages or body
            # For now, we'll store the issue metadata and link later via proximity heuristic
            bug_entry = {
                "issue_id": issue.get("issue_number"),
                "title": issue.get("title"),
                "state": issue.get("state"),
                "created_at": issue.get("created_at"),
                "closed_at": issue.get("closed_at"),
                "is_bug": is_bug,
                "labels": issue.get("labels"),
                "html_url": issue.get("html_url")
            }
            bug_data.append(bug_entry)
    
    logger.info(f"Found {len(bug_data)} potential bugs for {owner}/{repo}")
    return bug_data

def collect_repository_data(
    repo_url: str, 
    output_dir: Path, 
    cutoff_date: datetime,
    min_commits: int = 1000
) -> Optional[Dict[str, Any]]:
    """
    Main function to collect all data for a repository.
    1. Clone repo
    2. Parse commits
    3. Fetch bug data
    """
    repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
    repo_dir = output_dir / repo_name
    
    # Step 1: Clone
    if not clone_repository(repo_url, repo_dir, depth=1000):
        return None
    
    # Step 2: Verify commit count
    if not verify_repository(repo_dir, min_commits):
        shutil.rmtree(repo_dir)
        return None
    
    # Step 3: Parse commits
    commits = parse_commit_logs(repo_dir, cutoff_date)
    if not commits:
        logger.warning(f"No commits found for {repo_url}")
        shutil.rmtree(repo_dir)
        return None
    
    # Step 4: Fetch bug data
    bugs = fetch_bug_data_for_commit(repo_dir, repo_url, cutoff_date)
    
    # Step 5: Memory cleanup
    clear_memory()
    
    return {
        "repo_url": repo_url,
        "repo_name": repo_name,
        "commit_count": len(commits),
        "commits": commits,
        "bugs": bugs,
        "cutoff_date": cutoff_date.isoformat()
    }

def run_data_collection(
    repo_list: List[str], 
    output_dir: Path, 
    cutoff_date: datetime,
    min_commits: int = 1000
) -> List[Dict[str, Any]]:
    """
    Run data collection for a list of repositories.
    Returns list of collected data dictionaries.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    
    for repo_url in repo_list:
        logger.info(f"Processing {repo_url}")
        try:
            data = collect_repository_data(repo_url, output_dir, cutoff_date, min_commits)
            if data:
                results.append(data)
        except Exception as e:
            logger.error(f"Failed to process {repo_url}: {e}")
            continue
    
    return results

def main():
    """Entry point for data collection script."""
    # Configure logging
    configure_logging()
    
    # Example usage (can be overridden by command line args in a full implementation)
    repo_list = [
        "https://github.com/psf/requests",
        "https://github.com/pallets/flask",
        "https://github.com/django/django",
        "https://github.com/psf/black",
        "https://github.com/pytest-dev/pytest",
        "https://github.com/pandas-dev/pandas",
        "https://github.com/scikit-learn/scikit-learn",
        "https://github.com/pytest-dev/pluggy"
    ]
    
    # Set a cutoff date (e.g., 1 year ago)
    cutoff_date = datetime(2023, 1, 1)
    
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = run_data_collection(repo_list, output_dir, cutoff_date)
    
    logger.info(f"Successfully collected data for {len(results)} repositories")
    
    # Save results to intermediate storage
    intermediate_dir = Path("data/intermediate")
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    
    with open(intermediate_dir / "raw_data.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Raw data saved to {intermediate_dir / 'raw_data.json'}")

if __name__ == "__main__":
    main()