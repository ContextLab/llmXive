import subprocess
import json
import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Import logging utility from project structure
try:
    from utils.logger import get_logger
except ImportError:
    # Fallback for standalone execution or different import context
    import logging
    logger = logging.getLogger(__name__)
    def get_logger(name):
        return logging.getLogger(name)

# Import config if needed for path resolution, though task focuses on logic
try:
    from utils.config import get_path
except ImportError:
    get_path = None

logger = get_logger(__name__)

def run_git_command(command: List[str], cwd: str) -> Tuple[Optional[str], Optional[str], int]:
    """
    Execute a git command in the specified directory.
    Returns (stdout, stderr, return_code).
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        logger.error(f"Git command timed out: {' '.join(command)}")
        return None, "Command timed out", -1
    except Exception as e:
        logger.error(f"Error running git command: {e}")
        return None, str(e), -1

def checkout_commit(repo_path: str, commit_sha: str) -> bool:
    """
    Checkout a specific commit SHA in the repository.
    Returns True if successful, False otherwise.
    """
    stdout, stderr, code = run_git_command(["git", "checkout", commit_sha], repo_path)
    if code != 0:
        logger.warning(f"Failed to checkout commit {commit_sha}: {stderr}")
        return False
    logger.info(f"Successfully checked out commit {commit_sha}")
    return True

def get_commits_for_file(repo_path: str, file_path: str, max_commits: int = 100) -> List[str]:
    """
    Get the list of commit SHAs that modified a specific file.
    """
    stdout, stderr, code = run_git_command(
        ["git", "log", f"--max-count={max_commits}", "--format=%H", "--", file_path],
        repo_path
    )
    if code != 0:
        logger.warning(f"Failed to get commits for {file_path}: {stderr}")
        return []
    
    commits = [line.strip() for line in stdout.strip().split('\n') if line.strip()]
    return commits

def get_blame_authorship(repo_path: str, file_path: str) -> Dict[str, int]:
    """
    Get line counts attributed to each author for a file using git blame.
    Returns a dictionary mapping author name to line count.
    """
    stdout, stderr, code = run_git_command(
        ["git", "blame", "--line-porcelain", "--", file_path],
        repo_path
    )
    if code != 0:
        logger.warning(f"Failed to blame {file_path}: {stderr}")
        return {}
    
    author_counts = {}
    current_author = None
    
    for line in stdout.split('\n'):
        if line.startswith('author '):
            current_author = line[7:].strip()
        elif current_author and line.startswith('\t'):
            # This is a line of code attributed to current_author
            author_counts[current_author] = author_counts.get(current_author, 0) + 1
    
    return author_counts

def calculate_gini_coefficient(values: List[float]) -> Optional[float]:
    """
    Calculate the Gini coefficient for a list of values.
    Returns None if values are empty or invalid.
    """
    if not values or len(values) == 0:
        return None
    
    # Handle case where all values are zero
    if sum(values) == 0:
        return 0.0
    
    n = len(values)
    values = sorted(values)
    
    # Gini coefficient calculation
    index = list(range(1, n + 1))
    gini = (2 * sum(i * x for i, x in zip(index, values)) - (n + 1) * sum(values)) / (n * sum(values))
    
    return gini

def extract_file_metrics(repo_path: str, file_path: str, target_commit: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Extract ownership metrics for a specific file.
    Handles edge cases: missing history, non-Python/Java files.
    """
    # Edge Case: Check file extension
    if not file_path.endswith(('.py', '.java')):
        logger.warning(f"Skipping non-Python/Java file: {file_path}")
        return {
            "file": file_path,
            "gini_coefficient": None,
            "developer_count": None,
            "total_lines": None,
            "status": "skipped_invalid_extension"
        }

    # Edge Case: Check if file exists in repo
    full_path = os.path.join(repo_path, file_path)
    if not os.path.exists(full_path):
        logger.warning(f"File not found in repository: {file_path}")
        return {
            "file": file_path,
            "gini_coefficient": None,
            "developer_count": None,
            "total_lines": None,
            "status": "skipped_file_missing"
        }

    # Temporarily checkout target commit if provided
    original_branch = None
    if target_commit:
        # Get current branch to restore later
        stdout, _, code = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_path)
        if code == 0:
            original_branch = stdout.strip()
        
        if not checkout_commit(repo_path, target_commit):
            logger.error(f"Could not checkout {target_commit} for file {file_path}")
            return {
                "file": file_path,
                "gini_coefficient": None,
                "developer_count": None,
                "total_lines": None,
                "status": "error_checkout_failed"
            }

    try:
        # Get blame authorship
        author_counts = get_blame_authorship(repo_path, file_path)
        
        if not author_counts:
            logger.warning(f"No authorship data found for {file_path} (possibly empty or binary)")
            return {
                "file": file_path,
                "gini_coefficient": None,
                "developer_count": 0,
                "total_lines": 0,
                "status": "no_authorship_data"
            }

        values = list(author_counts.values())
        gini = calculate_gini_coefficient(values)
        
        return {
            "file": file_path,
            "gini_coefficient": gini,
            "developer_count": len(author_counts),
            "total_lines": sum(values),
            "status": "success"
        }
    finally:
        # Restore original branch/state if we checked out a commit
        if target_commit and original_branch:
            run_git_command(["git", "checkout", original_branch], repo_path)

def extract_repo_metrics(repo_path: str, max_files: int = 50, target_commit: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract aggregate ownership metrics for a repository.
    Calculates LOC-weighted Gini coefficient across all relevant files.
    """
    logger.info(f"Starting extraction for repository: {repo_path}")
    
    # Edge Case: Check if directory is a git repo
    if not os.path.exists(os.path.join(repo_path, ".git")):
        logger.error(f"Path is not a git repository: {repo_path}")
        return {
            "repo": repo_path,
            "status": "error_not_git_repo",
            "metrics": None
        }

    # Get list of Python and Java files
    python_files = []
    java_files = []
    
    for root, _, files in os.walk(repo_path):
        # Skip hidden directories and common non-code directories
        if any(part.startswith('.') or part in ['node_modules', 'venv', '__pycache__'] for part in root.split(os.sep)):
            continue
        
        for f in files:
            if f.endswith('.py'):
                python_files.append(os.path.relpath(os.path.join(root, f), repo_path))
            elif f.endswith('.java'):
                java_files.append(os.path.relpath(os.path.join(root, f), repo_path))
    
    all_files = python_files + java_files
    
    if not all_files:
        logger.warning(f"No Python or Java files found in {repo_path}")
        return {
            "repo": repo_path,
            "status": "warning_no_source_files",
            "metrics": None
        }

    # Limit files if necessary
    if len(all_files) > max_files:
        logger.info(f"Limiting analysis to first {max_files} files out of {len(all_files)}")
        all_files = all_files[:max_files]

    # Temporarily checkout target commit
    original_branch = None
    if target_commit:
        stdout, _, code = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_path)
        if code == 0:
            original_branch = stdout.strip()
        if not checkout_commit(repo_path, target_commit):
            logger.error(f"Could not checkout {target_commit} for repo metrics")
            return {
                "repo": repo_path,
                "status": "error_checkout_failed",
                "metrics": None
            }

    try:
        file_metrics = []
        total_loc = 0
        total_devs = 0
        
        # Aggregate data for Gini calculation
        # We want LOC-weighted Gini of commit distribution? 
        # The task says "LOC-weighted Gini coefficient of commit distribution"
        # But T012 says "using git blame to attribute lines".
        # Standard approach: Sum lines per author across all files -> Gini of author lines.
        
        global_author_lines = {}
        
        for file_path in all_files:
            metrics = extract_file_metrics(repo_path, file_path, target_commit)
            if metrics and metrics.get("status") == "success":
                file_metrics.append(metrics)
                total_loc += metrics["total_lines"]
                total_devs += metrics["developer_count"]
                
                # Aggregate for global Gini
                # We need to get the author counts for this file to aggregate
                # Re-calling blame is inefficient, but extract_file_metrics doesn't return the map.
                # Let's optimize: extract_file_metrics should ideally return the map, 
                # but to keep changes minimal and focused on T014 (edge cases), 
                # we will re-calculate blame for aggregation or modify extract_file_metrics slightly.
                # Actually, let's just aggregate the counts we already have if we modify the function slightly?
                # No, T014 is about edge cases. I will re-run blame for aggregation to be safe and accurate.
                
                author_counts = get_blame_authorship(repo_path, file_path)
                for author, lines in author_counts.items():
                    global_author_lines[author] = global_author_lines.get(author, 0) + lines
        
        # Calculate Global Gini
        global_gini = calculate_gini_coefficient(list(global_author_lines.values())) if global_author_lines else None
        
        # Unique developers across the repo (union)
        unique_devs = len(global_author_lines)
        
        return {
            "repo": repo_path,
            "status": "success",
            "metrics": {
                "gini_coefficient": global_gini,
                "unique_developers": unique_devs,
                "total_lines_analyzed": total_loc,
                "files_analyzed": len(file_metrics),
                "file_details": file_metrics
            }
        }
    finally:
        if target_commit and original_branch:
            run_git_command(["git", "checkout", original_branch], repo_path)

def save_metrics_to_json(metrics: Dict[str, Any], output_path: str) -> bool:
    """
    Save metrics to a JSON file.
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Metrics saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")
        return False

def main():
    """
    Main entry point for testing the extractor.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract git ownership metrics")
    parser.add_argument("--repo", required=True, help="Path to git repository")
    parser.add_argument("--commit", help="Specific commit SHA to analyze")
    parser.add_argument("--output", default="data/processed/ownership_metrics.json", help="Output JSON path")
    parser.add_argument("--max-files", type=int, default=50, help="Max files to analyze")
    
    args = parser.parse_args()
    
    metrics = extract_repo_metrics(args.repo, max_files=args.max_files, target_commit=args.commit)
    save_metrics_to_json(metrics, args.output)

if __name__ == "__main__":
    main()