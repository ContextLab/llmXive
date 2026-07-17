import os
import sys
import subprocess
import tempfile
import shutil
import logging
import time
import multiprocessing
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

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
SHALLOW_SINCE_DATE = "2015-01-01"
MIN_CLOC_VERSION = (1, 88)
MAX_MEMORY_GB = 6
MAX_WORKERS = 2

def check_memory_usage() -> bool:
    """Check if current memory usage is below the limit. Returns True if OK to proceed."""
    try:
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 * 1024)
        mem_gb = mem_mb / 1024
        if mem_gb > MAX_MEMORY_GB:
            logger.warning(f"Memory usage {mem_gb:.2f}GB exceeds limit {MAX_MEMORY_GB}GB. Aborting.")
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to check memory usage: {e}")
        return False

def check_cloc_version() -> bool:
    """Verify cloc version is >= 1.88."""
    try:
        result = subprocess.run(['cloc', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            logger.error("cloc command not found or failed.")
            return False
        
        version_str = result.stdout.split('\n')[0]
        parts = version_str.split()
        version_num_str = None
        for part in parts:
            if '.' in part:
                version_num_str = part
                break
        
        if not version_num_str:
            logger.error(f"Could not parse cloc version from: {version_str}")
            return False

        version_parts = version_num_str.split('.')
        if len(version_parts) < 2:
            logger.error(f"Invalid version format: {version_num_str}")
            return False

        major = int(version_parts[0])
        minor = int(version_parts[1])
        
        if (major, minor) >= MIN_CLOC_VERSION:
            logger.info(f"cloc version {major}.{minor} verified.")
            return True
        else:
            logger.error(f"cloc version {major}.{minor} is too old. Required >= {MIN_CLOC_VERSION[0]}.{MIN_CLOC_VERSION[1]}")
            return False
    except FileNotFoundError:
        logger.error("cloc executable not found in PATH. Please install cloc.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Timeout while checking cloc version.")
        return False
    except Exception as e:
        logger.error(f"Error checking cloc version: {e}")
        return False

def run_command(cmd: List[str], cwd: Optional[str] = None, timeout: int = 3600) -> Tuple[int, str, str]:
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
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out: {' '.join(cmd)}")
        return -1, "", str(e)
    except Exception as e:
        logger.error(f"Command failed: {' '.join(cmd)} - {e}")
        return -1, "", str(e)

def shallow_clone(repo_url: str, target_dir: Path) -> bool:
    """Perform a shallow clone since SHALLOW_SINCE_DATE."""
    cmd = [
        'git', 'clone', '--depth', '1', '--shallow-since', SHALLOW_SINCE_DATE,
        '--', repo_url, str(target_dir)
    ]
    logger.info(f"Shallow cloning {repo_url} since {SHALLOW_SINCE_DATE}...")
    rc, out, err = run_command(cmd)
    if rc == 0:
        return True
    else:
        logger.warning(f"Shallow clone failed for {repo_url}: {err}")
        return False

def full_clone(repo_url: str, target_dir: Path) -> bool:
    """Perform a full clone."""
    cmd = ['git', 'clone', '--', repo_url, str(target_dir)]
    logger.info(f"Performing full clone for {repo_url}...")
    rc, out, err = run_command(cmd)
    if rc == 0:
        return True
    else:
        logger.error(f"Full clone failed for {repo_url}: {err}")
        return False

def parse_git_log(repo_dir: Path) -> set:
    """
    Parse git log to find unique authors who committed at least 1 line of code.
    Returns a set of author emails/names.
    """
    cmd = [
        'git', '-C', str(repo_dir), 'log',
        '--pretty=format:%ae', # Author email
        '--numstat'
    ]
    rc, out, err = run_command(cmd, cwd=str(repo_dir), timeout=1800)
    if rc != 0:
        logger.warning(f"git log failed for {repo_dir}: {err}")
        return set()

    authors = set()
    current_author = None
    
    # Parse numstat output to attribute lines to authors
    # Format: <author> ... \n <add> <del> <file>
    lines = out.split('\n')
    for line in lines:
        if not line.strip():
            continue
        
        # Check if it's an author line (contains @ usually, or just email format)
        if '@' in line and not line.startswith('\t') and not line.startswith('#'):
            # It might be the author line if previous was empty or we are at start
            # But numstat output is: author_line \n numstat_lines...
            # The git log format used puts author on its own line.
            # Let's assume standard git log format: one line with email, then numstat lines starting with tab or numbers.
            current_author = line.strip()
            continue
        
        # If we have a current author and this line looks like numstat (starts with digit or tab)
        if current_author and (line.startswith('\t') or (line and line[0].isdigit())):
            parts = line.split()
            if len(parts) >= 3:
                # Add lines: parts[0] (add), parts[1] (del), parts[2] (file)
                # If parts[0] is '-' it means binary or unknown, skip for line count but author still committed
                add_lines = parts[0]
                if add_lines != '-':
                    try:
                        int(add_lines) # Just verify it's a number
                        authors.add(current_author)
                    except ValueError:
                        pass # Binary file or weird format, skip counting but author exists
                else:
                    # Even if binary, they committed something, so they count as an author
                    authors.add(current_author)
            else:
                # Maybe just a file path line or something weird, but if we have an author, they committed something
                authors.add(current_author)
        elif not line.startswith('\t') and not line[0].isdigit() and '@' not in line:
            # Could be a merge commit or other info, ignore
            pass
        
    # Re-approach: The previous logic is fragile. Let's use a simpler, robust method.
    # We want unique authors who committed >= 1 line of CODE (text).
    # Git log --numstat:
    # author_email
    # <add>\t<del>\t<file>
    # <add>\t<del>\t<file>
    # ...
    # (blank line between commits)
    
    authors = set()
    current_author = None
    
    lines = out.split('\n')
    for line in lines:
        if not line.strip():
            current_author = None
            continue
        
        # Detect author line: usually just the email if format is %ae
        # But sometimes git log output can be tricky.
        # Let's rely on the fact that numstat lines start with a number or tab.
        # If it's not a numstat line and not empty, it's likely the author.
        if not (line[0].isdigit() or line[0] == '\t'):
            # It's an author line (or header)
            current_author = line.strip()
            # If it's a valid email format, add it immediately? No, wait for numstat.
            continue
        
        if current_author:
            # It's a numstat line
            parts = line.split()
            if len(parts) >= 3:
                add = parts[0]
                if add != '-':
                    try:
                        int(add)
                        authors.add(current_author)
                    except ValueError:
                        pass
                else:
                    # Binary file: author committed, but we can't count lines.
                    # The requirement says "≥ 1 line of code committed".
                    # If it's a binary file, did they commit code? Maybe not.
                    # However, usually "author" implies they contributed.
                    # Let's be strict: only count if we see a numeric add.
                    # But if they ONLY committed binary, they might be excluded.
                    # Given "≥ 1 line of code", binary doesn't count as lines of code.
                    # So we only add if add is numeric.
                    pass
    return authors

def run_cloc(repo_dir: Path) -> Optional[int]:
    """
    Run cloc --by-file on the repo directory.
    Returns the total raw line count of code (excluding comments/blanks) if successful, else None.
    """
    # cloc output format:
    # Language | files | blank | comment | code
    # We need the sum of the 'code' column.
    # Or we can use --sum to get total directly? 
    # cloc --by-file returns per file. We need total.
    # Let's run cloc and parse the total line at the end.
    
    cmd = ['cloc', str(repo_dir), '--quiet', '--sum-sep', '|']
    # --quiet suppresses per-file output, but we need total.
    # Actually, cloc always prints a summary at the end.
    # Let's just run it and parse stdout.
    
    rc, out, err = run_command(cmd, cwd=str(repo_dir), timeout=1800)
    if rc != 0:
        logger.warning(f"cloc failed for {repo_dir}: {err}")
        return None

    total_lines = 0
    found_total = False
    
    for line in out.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Look for the total line. Usually starts with "SUM" or "total" or similar.
        # Or we can parse the last line if it has numbers.
        # cloc output example:
        #   language: code
        #   files: 10
        #   blank: 100
        #   comment: 50
        #   code: 1000
        #   (blank line)
        #   SUM: 10 100 50 1000
        
        # Let's try to find the line with "SUM" or "total" (case insensitive)
        if 'sum' in line.lower() or 'total' in line.lower():
            parts = line.split()
            # The last number is usually the code count
            for part in reversed(parts):
                if part.isdigit():
                    total_lines = int(part)
                    found_total = True
                    break
            if found_total:
                break
        
        # Fallback: if no SUM line, maybe the last line of numbers?
        # But cloc is consistent.
    
    if not found_total:
        # Maybe the output format is slightly different.
        # Let's try to parse the "code" line if present.
        for line in out.split('\n'):
            if 'code' in line.lower() and ':' in line:
                # e.g. "code: 1234" or "SUM: ... 1234"
                parts = line.split()
                for part in reversed(parts):
                    if part.isdigit():
                        total_lines = int(part)
                        found_total = True
                        break
                if found_total:
                    break

    if not found_total:
        logger.warning(f"Could not parse cloc output for {repo_dir}. Output: {out[:200]}...")
        return None

    return total_lines

def process_repo(repo_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single repository: clone, count authors, run cloc.
    Returns a dict with metrics or None if failed.
    """
    url = repo_entry.get('url')
    if not url:
        logger.error("Repository entry missing 'url'")
        return None

    logger.info(f"Processing {url}...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir) / "repo"
        
        # Try shallow clone
        if not shallow_clone(url, repo_dir):
            # T008b Fallback logic: If shallow returns 0 authors or fails, try full clone
            # Note: shallow_clone returns False if git command fails.
            # We need to check if it succeeded but returned 0 authors?
            # The shallow_clone function above returns True/False based on git exit code.
            # If it fails, we try full clone.
            logger.warning(f"Shallow clone failed for {url}, attempting full clone...")
            if not full_clone(url, repo_dir):
                logger.error(f"Full clone also failed for {url}. Skipping.")
                return None

        # Check authors
        try:
            unique_authors = parse_git_log(repo_dir)
            num_authors = len(unique_authors)
            logger.info(f"Found {num_authors} unique authors for {url}")
            
            if num_authors == 0:
                # T008b: If shallow clone resulted in 0 authors, try full clone?
                # We already tried full clone if shallow clone command failed.
                # But if shallow clone succeeded but had 0 authors (e.g. repo has no commits since 2015?),
                # we should try full clone.
                logger.warning(f"Shallow clone found 0 authors for {url}. Attempting full clone...")
                # Remove current dir and try full clone
                shutil.rmtree(repo_dir)
                if not full_clone(url, repo_dir):
                    logger.error(f"Full clone failed for {url} after 0 authors found. Skipping.")
                    return None
                
                # Re-parse authors
                unique_authors = parse_git_log(repo_dir)
                num_authors = len(unique_authors)
                logger.info(f"Full clone found {num_authors} unique authors for {url}")
                
                if num_authors == 0:
                    logger.warning(f"Full clone also found 0 authors for {url}. Skipping.")
                    return None
        except Exception as e:
            logger.error(f"Error parsing git log for {url}: {e}")
            return None

        # Run cloc
        try:
            raw_line_count = run_cloc(repo_dir)
            if raw_line_count is None:
                logger.warning(f"cloc failed for {url}. Skipping.")
                return None
            
            kloc = raw_line_count / 1000.0
        except Exception as e:
            logger.error(f"Error running cloc for {url}: {e}")
            return None

        return {
            'url': url,
            'unique_authors': num_authors,
            'raw_line_count': raw_line_count,
            'kloc': kloc
        }

def worker_wrapper(repo_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Wrapper for multiprocessing to handle memory checks."""
    if not check_memory_usage():
        return None
    return process_repo(repo_entry)

def main():
    """Main entry point."""
    ensure_directories()
    
    # Check prerequisites
    if not check_cloc_version():
        logger.error("cloc version check failed. Exiting.")
        sys.exit(1)

    # Load target list
    target_list_path = Path('data/raw/target_list.csv')
    if not target_list_path.exists():
        logger.error(f"Target list not found at {target_list_path}. Run T006 first.")
        sys.exit(1)

    df_target = pd.read_csv(target_list_path)
    logger.info(f"Loaded {len(df_target)} repositories from target list.")

    results = []
    
    # Process with multiprocessing
    # Use a pool with max_workers=2 as per T030
    with multiprocessing.Pool(processes=MAX_WORKERS) as pool:
        # We need to handle the case where the pool might hang or fail
        # Using imap_unordered for better memory management
        for i, result in enumerate(pool.imap_unordered(worker_wrapper, df_target.to_dict('records'))):
            if result is not None:
                results.append(result)
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i+1} repositories...")

    if not results:
        logger.error("No results generated. Exiting.")
        sys.exit(1)

    # Save results
    output_path = Path('data/processed/github_raw_metrics.csv')
    df_results = pd.DataFrame(results)
    
    # Ensure column order
    df_results = df_results[['url', 'unique_authors', 'raw_line_count', 'kloc']]
    
    df_results.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df_results)} records to {output_path}")

if __name__ == '__main__':
    main()
