import os
import subprocess
import logging
import time
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import re

# Local imports matching API surface
from config import get_cutoff_date, get_depth_limit, get_repo_list, get_github_token, get_output_dir
from utils.backoff import fetch_with_backoff, handle_github_rate_limit
from utils.path_normalizer import normalize_path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def clone_repository(repo_url: str, repo_name: str, depth: int) -> Tuple[bool, Optional[str]]:
    """Clone a repository with specified depth."""
    repo_path = Path(get_output_dir()) / "raw" / repo_name
    
    if repo_path.exists():
        logger.info(f"Repository {repo_name} already exists, skipping clone.")
        return True, str(repo_path)

    try:
        cmd = ["git", "clone", "--depth", str(depth), "--single-branch", repo_url, str(repo_path)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Successfully cloned {repo_name}")
        return True, str(repo_path)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone {repo_name}: {e.stderr}")
        return False, str(e.stderr)

def verify_commit_count(repo_path: str, min_commits: int = 1000) -> Tuple[bool, int]:
    """Verify the repository has at least min_commits."""
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        count = int(result.stdout.strip())
        if count < min_commits:
            logger.warning(f"Repo {repo_path} has only {count} commits (< {min_commits}). Skipping.")
            return False, count
        return True, count
    except subprocess.CalledProcessError as e:
        logger.error(f"Error counting commits in {repo_path}: {e}")
        return False, 0

def parse_commit_history(repo_path: str, output_csv: Path) -> bool:
    """Parse git log to extract author, timestamp, and file_path."""
    try:
        # Get all commits with file changes
        # Format: hash|author|timestamp|file_path
        cmd = [
            "git", "log", "--pretty=format:%H|%an|%ai",
            "--name-only",
            "--no-merges"
        ]
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, check=True)
        
        lines = result.stdout.strip().split('\n')
        current_hash, current_author, current_time = None, None, None
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['commit_hash', 'author', 'timestamp', 'file_path', 'line_count'])
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        current_hash = parts[0]
                        current_author = parts[1]
                        current_time = parts[2]
                else:
                    # This is a file path
                    if current_hash and current_author and current_time:
                        file_path = line
                        # Estimate line count (simplified: 0 for now, can be improved with git diff)
                        # For validation purposes, we just need to ensure the file path exists in history
                        writer.writerow([current_hash, current_author, current_time, file_path, 0])
                        
        logger.info(f"Saved commit history to {output_csv}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error parsing commit history for {repo_path}: {e}")
        return False

def fetch_github_issues(repo_owner: str, repo_name: str, cutoff_date: str) -> List[Dict[str, Any]]:
    """Fetch issues from GitHub API."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues?state=all&since={cutoff_date}"
    headers = {"Authorization": f"token {get_github_token()}"}
    
    issues = []
    try:
        response = fetch_with_backoff(url, headers=headers)
        if response.status_code == 200:
            issues = response.json()
        else:
            logger.error(f"Failed to fetch issues for {repo_owner}/{repo_name}: {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching issues: {e}")
    
    return issues

def save_issues_to_csv(issues: List[Dict[str, Any]], output_csv: Path):
    """Save issues to CSV."""
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['issue_id', 'title', 'state', 'created_at', 'body', 'labels'])
        for issue in issues:
            writer.writerow([
                issue.get('id'),
                issue.get('title'),
                issue.get('state'),
                issue.get('created_at'),
                issue.get('body', ''),
                ';'.join([label['name'] for label in issue.get('labels', [])])
            ])

def process_issues_for_repo(issues: List[Dict[str, Any]], repo_path: str, output_csv: Path) -> bool:
    """Process issues and link to modules using path normalization."""
    try:
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['issue_id', 'linked_file', 'normalized_path'])
            
            for issue in issues:
                body = issue.get('body', '')
                issue_id = issue.get('id')
                
                # Simple heuristic: look for file paths in issue body
                # This is a placeholder; real implementation would use more sophisticated NLP
                potential_paths = re.findall(r'[a-zA-Z0-9_/\-\.]+\.(py|js|ts|java|c|cpp|h|hpp)', body)
                
                for path in potential_paths:
                    normalized = normalize_path(path)
                    writer.writerow([issue_id, path, normalized])
                    
        return True
    except Exception as e:
        logger.error(f"Error processing issues: {e}")
        return False

def validate_dataset_variable_fit(csv_path: Path) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the dataset contains the necessary variables for analysis:
    - committers (authors)
    - timestamps
    - file paths
    - line counts (or ability to derive them)
    
    Returns (is_valid, details_dict)
    """
    if not csv_path.exists():
        logger.error(f"Validation failed: File {csv_path} does not exist.")
        return False, {"reason": "file_not_found"}
    
    required_columns = {'commit_hash', 'author', 'timestamp', 'file_path'}
    valid = True
    details = {"missing_columns": [], "issues": []}
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                logger.error(f"Validation failed: {csv_path} is empty or has no headers.")
                return False, {"reason": "empty_file"}
            
            # Check required columns
            missing = required_columns - set(reader.fieldnames)
            if missing:
                valid = False
                details["missing_columns"] = list(missing)
                details["issues"].append(f"Missing required columns: {missing}")
            
            # Check for data quality
            row_count = 0
            unique_authors = set()
            unique_files = set()
            has_line_counts = 'line_count' in reader.fieldnames
            
            for row in reader:
                row_count += 1
                
                # Validate author
                if not row.get('author') or row['author'].strip() == '':
                    details["issues"].append(f"Row {row_count}: Missing author")
                
                # Validate timestamp (basic check)
                if not row.get('timestamp') or not re.match(r'\d{4}-\d{2}-\d{2}', row['timestamp']):
                    details["issues"].append(f"Row {row_count}: Invalid timestamp format")
                
                # Validate file path
                if not row.get('file_path') or row['file_path'].strip() == '':
                    details["issues"].append(f"Row {row_count}: Missing file_path")
                
                unique_authors.add(row.get('author'))
                unique_files.add(row.get('file_path'))
            
            if row_count == 0:
                valid = False
                details["issues"].append("No data rows found")
            
            if len(unique_authors) == 0:
                valid = False
                details["issues"].append("No unique committers found")
            
            if len(unique_files) == 0:
                valid = False
                details["issues"].append("No unique file paths found")
            
            details["row_count"] = row_count
            details["unique_authors"] = len(unique_authors)
            details["unique_files"] = len(unique_files)
            details["has_line_counts"] = has_line_counts
            
            if not valid:
                logger.warning(f"Validation failed for {csv_path}: {details['issues']}")
            else:
                logger.info(f"Validation passed for {csv_path}: {row_count} rows, {len(unique_authors)} authors, {len(unique_files)} files")
            
            return valid, details
            
    except Exception as e:
        logger.error(f"Error validating {csv_path}: {e}")
        return False, {"reason": "error_reading_file", "error": str(e)}

def clone_repositories() -> List[Dict[str, Any]]:
    """Clone all repositories from config."""
    repo_list = get_repo_list()
    depth = get_depth_limit()
    results = []
    
    for repo_info in repo_list:
        repo_url = repo_info.get('url')
        repo_name = repo_info.get('name')
        
        logger.info(f"Processing {repo_name}...")
        success, repo_path = clone_repository(repo_url, repo_name, depth)
        
        if not success:
            results.append({"name": repo_name, "status": "clone_failed", "path": None})
            continue
        
        # Verify commit count
        valid, count = verify_commit_count(repo_path, min_commits=1000)
        if not valid:
            results.append({"name": repo_name, "status": "insufficient_commits", "count": count, "path": repo_path})
            continue
        
        results.append({"name": repo_name, "status": "cloned", "path": repo_path, "commit_count": count})
    
    return results

def process_all_repos():
    """Main entry point to process all repositories."""
    output_dir = get_output_dir()
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(output_dir, "raw")).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(output_dir, "intermediate")).mkdir(parents=True, exist_ok=True)
    
    clone_results = clone_repositories()
    
    for repo_data in clone_results:
        if repo_data.get("status") != "cloned":
            continue
        
        repo_name = repo_data["name"]
        repo_path = repo_data["path"]
        intermediate_dir = Path(output_dir) / "intermediate"
        
        # Parse commit history
        commits_csv = intermediate_dir / f"{repo_name}_commits.csv"
        if parse_commit_history(repo_path, commits_csv):
            # Validate dataset variable fit
            is_valid, details = validate_dataset_variable_fit(commits_csv)
            if not is_valid:
                logger.warning(f"Skipping {repo_name} due to validation failure: {details}")
                continue
            
            # Further processing (issues, etc.) would go here
            logger.info(f"Successfully processed {repo_name}")
        else:
            logger.error(f"Failed to parse commit history for {repo_name}")

def main():
    """Main function to run the data collection pipeline."""
    logger.info("Starting data collection pipeline...")
    process_all_repos()
    logger.info("Data collection pipeline finished.")

if __name__ == "__main__":
    main()