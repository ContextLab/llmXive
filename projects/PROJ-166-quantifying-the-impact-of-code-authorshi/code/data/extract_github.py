import os
import sys
import subprocess
import tempfile
import shutil
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import multiprocessing
from multiprocessing import Manager

from config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/extract_github.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
MAX_WORKERS = 2
MEMORY_LIMIT_GB = 6
TIME_LIMIT_SECONDS = 6 * 3600  # 6 hours
SHALLOW_SINCE_DATE = "2015-01-01"
MIN_AUTHORS_THRESHOLD = 0  # Trigger fallback if authors <= this

def check_memory_usage() -> bool:
    """Check if current memory usage is below the limit."""
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        # Parse available memory (simplified for Linux)
        for line in meminfo.splitlines():
            if line.startswith('MemAvailable:'):
                available_kb = int(line.split()[1])
                available_gb = available_kb / (1024 * 1024)
                return available_gb > MEMORY_LIMIT_GB
        # Fallback: assume OK if we can't parse
        return True
    except Exception as e:
        logger.warning(f"Could not check memory usage: {e}")
        return True

def check_cloc_version() -> bool:
    """Verify cloc version >= 1.88."""
    try:
        result = subprocess.run(['cloc', '--version'], capture_output=True, text=True, check=True)
        version_str = result.stdout.strip()
        # Extract version number (e.g., "cloc 1.90")
        parts = version_str.split()
        if len(parts) >= 2:
            version = parts[1]
            major, minor = map(int, version.split('.')[:2])
            if major > 1 or (major == 1 and minor >= 88):
                return True
        logger.error(f"cloc version too old or unparseable: {version_str}")
        return False
    except FileNotFoundError:
        logger.error("cloc not found in PATH")
        return False
    except Exception as e:
        logger.error(f"Error checking cloc version: {e}")
        return False

def run_command(cmd: List[str], cwd: Optional[str] = None, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def shallow_clone(repo_url: str, target_dir: str, since_date: str) -> bool:
    """Perform a shallow clone with --shallow-since."""
    cmd = [
        'git', 'clone', '--depth', '1',
        '--shallow-since', since_date,
        '--no-single-branch',
        repo_url, target_dir
    ]
    logger.info(f"Attempting shallow clone of {repo_url} since {since_date}")
    rc, out, err = run_command(cmd)
    if rc != 0:
        logger.warning(f"Shallow clone failed for {repo_url}: {err}")
        return False
    return True

def full_clone(repo_url: str, target_dir: str) -> bool:
    """Perform a full clone."""
    cmd = ['git', 'clone', repo_url, target_dir]
    logger.info(f"Performing full clone of {repo_url}")
    rc, out, err = run_command(cmd)
    if rc != 0:
        logger.error(f"Full clone failed for {repo_url}: {err}")
        return False
    return True

def parse_git_log(repo_dir: str) -> List[str]:
    """Parse git log to extract unique authors with ≥1 line of code committed."""
    cmd = ['git', 'log', '--format=%aN', '--numstat']
    rc, out, err = run_command(cmd, cwd=repo_dir)
    if rc != 0:
        logger.warning(f"git log failed in {repo_dir}: {err}")
        return []

    authors = set()
    current_author = None
    lines_added = 0

    for line in out.splitlines():
        if line.startswith('Author:'):
            # This shouldn't happen with --format=%aN, but handle just in case
            continue
        if line == '' and current_author:
            # End of a commit block
            if lines_added > 0:
                authors.add(current_author)
            current_author = None
            lines_added = 0
            continue

        # Detect author line (git log --format=%aN prints just the name)
        if not line.startswith('\t') and not line.startswith('#') and line.strip():
            # It's an author name
            current_author = line.strip()
            lines_added = 0
            continue

        # It's a numstat line: <added>\t<removed>\t<file>
        if line.startswith('\t') and current_author:
            parts = line.split('\t')
            if len(parts) >= 2:
                try:
                    added = int(parts[0]) if parts[0] != '-' else 0
                    lines_added += added
                except ValueError:
                    pass

    # Don't forget the last author
    if current_author and lines_added > 0:
        authors.add(current_author)

    return list(authors)

def run_cloc(repo_dir: str) -> Optional[float]:
    """Run cloc --by-file and return total KLOC (excluding comments)."""
    cmd = ['cloc', '--by-file', '--quiet', repo_dir]
    rc, out, err = run_command(cmd, cwd=repo_dir)
    if rc != 0:
        logger.warning(f"cloc failed for {repo_dir}: {err}")
        return None

    # cloc output format:
    # URL or repo name
    # ...
    # SUM: <files> <blank> <comment> <code>
    # We need the total code lines from the SUM line
    total_code = 0
    for line in out.splitlines():
        if line.startswith('SUM:'):
            parts = line.split()
            # Expected: SUM: <files> <blank> <comment> <code>
            if len(parts) >= 5:
                try:
                    total_code = int(parts[4])
                except ValueError:
                    pass
            break

    kloc = total_code / 1000.0
    return kloc

def process_repo(repo_info: Dict[str, Any], start_time: float) -> Optional[Dict[str, Any]]:
    """Process a single repository: shallow clone, check authors, fallback if needed, run cloc."""
    repo_url = repo_info['url']
    logger.info(f"Processing {repo_url}")

    # Check time limit
    elapsed = time.time() - start_time
    if elapsed > TIME_LIMIT_SECONDS:
        logger.error(f"Time limit exceeded ({elapsed}s > {TIME_LIMIT_SECONDS}s). Aborting {repo_url}.")
        return None

    # Check memory
    if not check_memory_usage():
        logger.error(f"Memory limit exceeded. Aborting {repo_url}.")
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = os.path.join(tmpdir, "repo")
        authors = []
        kloc = None

        # Try shallow clone first
        if not shallow_clone(repo_url, repo_dir, SHALLOW_SINCE_DATE):
            logger.warning(f"Shallow clone failed for {repo_url}, skipping.")
            return None

        # Parse authors
        authors = parse_git_log(repo_dir)
        logger.info(f"Shallow clone found {len(authors)} authors for {repo_url}")

        # Fallback logic: if 0 authors, try full clone
        if len(authors) <= MIN_AUTHORS_THRESHOLD:
            logger.warning(f"Shallow clone returned 0 authors for {repo_url}. Triggering full clone fallback.")
            # Remove the shallow clone directory
            shutil.rmtree(repo_dir)
            
            # Perform full clone
            if not full_clone(repo_url, repo_dir):
                logger.error(f"Full clone failed for {repo_url}. Skipping.")
                return None
            
            # Re-parse authors from full clone
            authors = parse_git_log(repo_dir)
            logger.info(f"Full clone found {len(authors)} authors for {repo_url} (fallback triggered)")
            if len(authors) <= MIN_AUTHORS_THRESHOLD:
                logger.warning(f"Full clone also returned 0 authors for {repo_url}. Skipping.")
                return None

        # Run cloc
        kloc = run_cloc(repo_dir)
        if kloc is None:
            logger.warning(f"cloc failed for {repo_url}. Skipping.")
            return None

        return {
            'url': repo_url,
            'unique_authors': len(authors),
            'raw_line_count': int(kloc * 1000),
            'kloc': kloc
        }

def worker_wrapper(args: Tuple[Dict[str, Any], float, Manager]) -> Optional[Dict[str, Any]]:
    """Wrapper for multiprocessing to handle shared state if needed."""
    repo_info, start_time, _ = args
    return process_repo(repo_info, start_time)

def main():
    """Main entry point for the GitHub extraction pipeline."""
    ensure_directories()
    
    if not check_cloc_version():
        logger.error("cloc version check failed. Exiting.")
        sys.exit(1)

    # Load target list
    target_list_path = Path('data/raw/target_list.csv')
    if not target_list_path.exists():
        logger.error(f"Target list not found at {target_list_path}. Run generate_target_list.py first.")
        sys.exit(1)

    import pandas as pd
    df = pd.read_csv(target_list_path)
    repos = df.to_dict('records')
    logger.info(f"Loaded {len(repos)} repositories from target list.")

    start_time = time.time()
    results = []

    # Process with multiprocessing
    # Note: We pass start_time to each worker so they can check the global limit
    manager = Manager()
    args_list = [(repo, start_time, manager) for repo in repos]

    with multiprocessing.Pool(processes=MAX_WORKERS) as pool:
        # Use imap_unordered to process as results come in
        for result in pool.imap_unordered(worker_wrapper, args_list):
            if result is not None:
                results.append(result)
            # Check time limit periodically
            if time.time() - start_time > TIME_LIMIT_SECONDS:
                logger.error("Time limit reached during processing. Stopping.")
                break

    # Save results
    output_path = Path('data/processed/github_raw_metrics.csv')
    if results:
        result_df = pd.DataFrame(results)
        result_df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(results)} results to {output_path}")
    else:
        logger.warning("No results to save.")

    elapsed = time.time() - start_time
    logger.info(f"Pipeline completed in {elapsed:.2f} seconds.")

if __name__ == '__main__':
    main()