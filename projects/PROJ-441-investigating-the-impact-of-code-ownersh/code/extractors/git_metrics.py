"""
Git Metrics Extraction Module.

Implements the extraction of socio-technical ownership metrics from git repositories,
specifically focusing on the LOC-weighted Gini coefficient of commit distribution.
"""
import subprocess
import json
import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Local imports matching API surface
from utils.logger import get_logger
from utils.config import get_path

logger = get_logger(__name__)


@dataclass
class OwnershipMetrics:
    """Data structure for ownership metrics."""
    repo_url: str
    commit_sha: str
    total_commits: int
    unique_developers: int
    gini_coefficient: float
    file_path: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary."""
        return asdict(self)


def run_git_command(cmd: List[str], cwd: Optional[str] = None, timeout: int = 300) -> Tuple[str, str, int]:
    """
    Execute a git command and return stdout, stderr, and return code.

    Args:
        cmd: List of command arguments.
        cwd: Working directory for the command.
        timeout: Command execution timeout in seconds.

    Returns:
        Tuple of (stdout, stderr, return_code).
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        logger.error(f"Git command timed out: {' '.join(cmd)}")
        return "", "Command timed out", -1
    except Exception as e:
        logger.error(f"Error running git command: {e}")
        return "", str(e), -1


def checkout_commit(repo_path: Path, commit_sha: str) -> bool:
    """
    Checkout a specific commit SHA in the repository.

    Args:
        repo_path: Path to the git repository.
        commit_sha: The commit SHA to checkout.

    Returns:
        True if successful, False otherwise.
    """
    stdout, stderr, code = run_git_command(["git", "checkout", commit_sha], cwd=str(repo_path))
    if code != 0:
        logger.warning(f"Failed to checkout commit {commit_sha}: {stderr}")
        return False
    logger.debug(f"Successfully checked out commit {commit_sha}")
    return True


def get_commits_for_file(repo_path: Path, file_path: str, since: Optional[str] = None, until: Optional[str] = None) -> List[str]:
    """
    Get list of commit SHAs that modified a specific file.

    Args:
        repo_path: Path to the git repository.
        file_path: Relative path to the file within the repo.
        since: Start date filter (optional).
        until: End date filter (optional).

    Returns:
        List of commit SHAs.
    """
    cmd = ["git", "log", "--pretty=format:%H", "--follow", "--", file_path]
    if since:
        cmd.insert(2, f"--since={since}")
    if until:
        cmd.insert(2, f"--until={until}")

    stdout, _, code = run_git_command(cmd, cwd=str(repo_path))
    if code != 0:
        return []
    return [line.strip() for line in stdout.strip().split('\n') if line.strip()]


def get_blame_authorship(repo_path: Path, file_path: str, commit_sha: str) -> Dict[str, int]:
    """
    Get line attribution (blame) for a file at a specific commit.

    Args:
        repo_path: Path to the git repository.
        file_path: Relative path to the file.
        commit_sha: Commit SHA to blame against.

    Returns:
        Dictionary mapping author email to line count.
    """
    # Ensure we are at the correct commit
    if not checkout_commit(repo_path, commit_sha):
        logger.error(f"Could not checkout {commit_sha} for blame analysis")
        return {}

    cmd = ["git", "blame", "--line-porcelain", file_path]
    stdout, stderr, code = run_git_command(cmd, cwd=str(repo_path))

    if code != 0:
        logger.warning(f"Git blame failed for {file_path} at {commit_sha}: {stderr}")
        return {}

    author_counts: Dict[str, int] = {}
    current_author = None

    for line in stdout.split('\n'):
        if line.startswith('author '):
            # Extract author email if available, otherwise use name
            # Format: "author Name <email>"
            parts = line.split('>', 1)
            if len(parts) == 2:
                author_name = parts[0].replace('author ', '').strip()
                # Use the full string (Name <email>) as key to distinguish authors
                current_author = author_name
            else:
                current_author = line.replace('author ', '').strip()
        elif current_author and not line.startswith(('author-mail', 'author-time', 'author-tz', 'summary', 'filename', 'previous')):
            # If it's not a metadata line and we have an author, it's likely a line content line
            # However, git blame porcelain has many lines per commit.
            # A safer way is to parse the "author-mail" specifically.
            pass

    # Re-parsing strategy: Use author-mail for uniqueness
    author_counts = {}
    current_author = None
    lines_in_current_commit = 0

    # Reset and parse properly
    for line in stdout.split('\n'):
        if line.startswith('author-mail '):
            author = line.replace('author-mail ', '').strip()
            if current_author and lines_in_current_commit > 0:
                author_counts[current_author] = author_counts.get(current_author, 0) + lines_in_current_commit
            current_author = author
            lines_in_current_commit = 0
        elif line.startswith('filename'):
            # New file in blame (shouldn't happen in single file blame usually, but good safety)
            pass
        elif not line.startswith(('author ', 'author-time ', 'author-tz ', 'summary ', 'previous ', 'repeated', 'boundary')):
            # If we are in a block, this line counts as 1 line of code attributed to current author
            # But we need to be careful: the first line of a block is the commit hash line.
            # The standard porcelain output starts with <commit> <parent>...
            # Then metadata lines.
            # We need to count the actual lines of code.
            # Actually, the easiest way is to count lines where we have an author-mail and the line is NOT metadata.
            # But the structure is: <hash> <1> <author> <date> ... \n <line>
            # The line content is usually the last line before the next hash or EOF.
            pass

    # Let's use a more robust parsing for git blame --line-porcelain
    # It outputs: <sha> <1> <author> <time> <tz> <filename> \n <line>
    # Wait, --line-porcelain is verbose.
    # Let's use a simpler approach: count lines per author using a regex or specific markers.
    # Actually, let's just iterate and count lines.
    
    # Re-implementation of parsing:
    author_counts = {}
    current_author = None
    line_count = 0
    in_commit_block = False

    lines = stdout.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('author-mail '):
            if current_author and line_count > 0:
                author_counts[current_author] = author_counts.get(current_author, 0) + line_count
            current_author = line.replace('author-mail ', '').strip()
            line_count = 0
            in_commit_block = True
        elif line.startswith('filename'):
            pass # File name line
        elif line.startswith('summary'):
            pass # Summary line
        elif line.startswith('previous'):
            pass # Previous commit line
        elif line.startswith('boundary'):
            pass # Boundary commit
        elif line.startswith('author '):
            pass # Author name
        elif line.startswith('author-time'):
            pass
        elif line.startswith('author-tz'):
            pass
        elif line.startswith('\t'):
            # This is the actual line of code (starts with tab in porcelain)
            if current_author:
                line_count += 1
        elif len(line) == 40 and all(c in '0123456789abcdef' for c in line):
            # Start of a new commit block (SHA)
            # If we had a current author, save the count
            if current_author and line_count > 0:
                author_counts[current_author] = author_counts.get(current_author, 0) + line_count
            current_author = None
            line_count = 0
            in_commit_block = False
        else:
            # Fallback for lines that might be part of the content if format varies
            if in_commit_block and current_author and not line.startswith(('author', 'filename', 'summary', 'previous', 'boundary', 'author-mail', 'author-time', 'author-tz')):
                # Check if it's a content line (usually indented or just text)
                # In strict porcelain, content lines start with tab.
                # But if we missed the tab check, we might count metadata.
                # Let's be strict: only count if it looks like code or is a continuation.
                pass
        i += 1

    # Don't forget the last block
    if current_author and line_count > 0:
        author_counts[current_author] = author_counts.get(current_author, 0) + line_count

    return author_counts


def calculate_gini_coefficient(values: List[float]) -> float:
    """
    Calculate the Gini coefficient for a list of values.

    The Gini coefficient is a measure of statistical dispersion intended to
    represent the income inequality or wealth inequality within a nation or
    any other group of people. In this context, it measures the inequality
    of code ownership (LOC distribution).

    Formula: G = (2 * sum(i * x_i) - (n + 1) * sum(x_i)) / (n * sum(x_i))
    where x_i are the sorted values.

    Args:
        values: List of numeric values (e.g., lines of code per developer).

    Returns:
        Gini coefficient between 0 and 1.
    """
    if not values or sum(values) == 0:
        return 0.0

    sorted_values = sorted(values)
    n = len(sorted_values)
    total_sum = sum(sorted_values)
    cumulative_sum = 0
    weighted_sum = 0

    for i, val in enumerate(sorted_values):
        cumulative_sum += val
        weighted_sum += (i + 1) * val

    gini = (2 * weighted_sum - (n + 1) * total_sum) / (n * total_sum)
    return max(0.0, min(1.0, gini))


def extract_file_metrics(repo_path: Path, file_path: str, commit_sha: str) -> Optional[OwnershipMetrics]:
    """
    Extract ownership metrics for a specific file at a specific commit.

    Args:
        repo_path: Path to the git repository.
        file_path: Relative path to the file.
        commit_sha: The commit SHA to analyze.

    Returns:
        OwnershipMetrics object or None if extraction fails.
    """
    logger.info(f"Extracting metrics for {file_path} at {commit_sha}")

    # Get blame authorship
    author_lines = get_blame_authorship(repo_path, file_path, commit_sha)
    if not author_lines:
        logger.warning(f"No blame data found for {file_path} at {commit_sha}")
        return None

    total_lines = sum(author_lines.values())
    unique_devs = len(author_lines)

    # Calculate Gini based on lines of code (LOC) per developer
    loc_values = list(author_lines.values())
    gini = calculate_gini_coefficient(loc_values)

    return OwnershipMetrics(
        repo_url=str(repo_path),
        commit_sha=commit_sha,
        total_commits=1, # For file level, we are analyzing one snapshot
        unique_developers=unique_devs,
        gini_coefficient=gini,
        file_path=file_path
    )


def extract_repo_metrics(repo_url: str, commit_sha: str, file_pattern: str = "*.py") -> List[OwnershipMetrics]:
    """
    Extract ownership metrics for all matching files in a repository at a specific commit.

    Args:
        repo_url: URL of the git repository.
        commit_sha: The commit SHA to analyze.
        file_pattern: Glob pattern for files to include (default: *.py).

    Returns:
        List of OwnershipMetrics objects.
    """
    logger.info(f"Extracting repo metrics for {repo_url} at {commit_sha}")

    # Create a temporary directory for the clone
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / "repo"
        
        # Clone the repository
        logger.info(f"Cloning {repo_url} to {repo_path}")
        stdout, stderr, code = run_git_command(["git", "clone", "--depth", "1", repo_url, str(repo_path)])
        
        if code != 0:
            logger.error(f"Failed to clone repository: {stderr}")
            return []

        # Checkout the specific commit
        # Note: --depth 1 might not have the full history needed for deep commits if not the latest.
        # For this implementation, we assume the commit is in the shallow history or we fetch.
        # To be safe, let's fetch the specific commit.
        stdout, stderr, code = run_git_command(["git", "fetch", "origin", commit_sha], cwd=str(repo_path))
        if code != 0:
            # Fallback: try direct checkout (might work if commit is in shallow)
            pass
        
        if not checkout_commit(repo_path, commit_sha):
            logger.error(f"Failed to checkout {commit_sha} after fetch")
            return []

        # Find matching files
        cmd = ["git", "ls-files", file_pattern]
        stdout, _, code = run_git_command(cmd, cwd=str(repo_path))
        
        if code != 0:
            return []

        files = [f.strip() for f in stdout.split('\n') if f.strip()]
        metrics_list = []

        for file_path in files:
            metric = extract_file_metrics(repo_path, file_path, commit_sha)
            if metric:
                metrics_list.append(metric)

        return metrics_list


def save_metrics_to_json(metrics_list: List[OwnershipMetrics], output_path: str) -> None:
    """
    Serialize and save ownership metrics to a JSON file.

    Args:
        metrics_list: List of OwnershipMetrics objects.
        output_path: Path to the output JSON file.
    """
    if not metrics_list:
        logger.warning("No metrics to save.")
        # Ensure the file is created even if empty, to indicate the run completed
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        return

    # Convert to dict
    data = [m.to_dict() for m in metrics_list]

    # Ensure directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

    logger.info(f"Saved {len(metrics_list)} metrics to {output_path}")


def main():
    """
    Main entry point for the git metrics extraction script.
    This function demonstrates the workflow and ensures the output file is created.
    """
    # Example usage with a real public repository
    # Using a small, stable repo for demonstration: https://github.com/pandas-dev/pandas
    # Note: In a real pipeline, this would be driven by data_loader.py
    
    sample_repo = "https://github.com/pandas-dev/pandas"
    sample_commit = "v2.0.0" # A known stable tag
    output_file = "data/processed/ownership_metrics.json"

    logger.info("Starting Git Metrics Extraction (Demo Mode)")
    
    metrics = extract_repo_metrics(sample_repo, sample_commit, "*.py")
    
    if metrics:
        save_metrics_to_json(metrics, output_file)
        logger.info(f"Extraction complete. Output saved to {output_file}")
    else:
        logger.error("No metrics extracted. Check logs for errors.")
        # Create an empty file to indicate the run finished (even with no data)
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump([], f)

if __name__ == "__main__":
    main()