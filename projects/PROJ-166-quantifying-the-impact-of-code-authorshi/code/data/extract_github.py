import os
import sys
import subprocess
import tempfile
import shutil
import logging
import time
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Ensure project root is in path for imports if running as script
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_directories
from data.utils import run_command

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/extract_github.log", mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
CLONE_DATE = "2015-01-01"
MEMORY_LIMIT_GB = 6.0
MAX_WORKERS = 2  # Per task T030 constraint

def check_memory_usage() -> bool:
    """Check if current RAM usage is below the limit. Returns True if safe to proceed."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        used_gb = mem.used / (1024 ** 3)
        if used_gb > MEMORY_LIMIT_GB:
            logger.warning(f"Memory usage ({used_gb:.2f} GB) exceeds limit ({MEMORY_LIMIT_GB} GB). Aborting.")
            return False
        return True
    except ImportError:
        logger.warning("psutil not installed. Skipping memory check.")
        return True
    except Exception as e:
        logger.warning(f"Could not check memory usage: {e}. Proceeding with caution.")
        return True

def shallow_clone(repo_url: str, target_dir: Path) -> Optional[Path]:
    """
    Clone a repository shallowly since 2015-01-01.
    Returns the path to the clone if successful, None otherwise.
    """
    # Extract repo name for directory
    repo_name = repo_url.rstrip('/').split('/')[-1]
    clone_path = target_dir / repo_name
    
    if clone_path.exists():
        shutil.rmtree(clone_path)
    
    try:
        # Enforce shallow-since to satisfy Constitution VI and capture history window
        cmd = [
            "git", "clone", "--depth=1", 
            f"--shallow-since={CLONE_DATE}",
            repo_url, str(clone_path)
        ]
        logger.info(f"Cloning {repo_url} to {clone_path}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            logger.warning(f"Clone failed for {repo_url}: {result.stderr.strip()}")
            return None
        
        return clone_path
    except subprocess.TimeoutExpired:
        logger.warning(f"Clone timed out for {repo_url}")
        return None
    except Exception as e:
        logger.warning(f"Exception during clone for {repo_url}: {e}")
        return None

def parse_git_log_and_count_authors(clone_path: Path) -> int:
    """
    Parse git log to count unique authors.
    Filters out authors with < 1 line of code committed using git blame.
    """
    try:
        # Get all unique author emails
        cmd_log = ["git", "log", "--format=%ae"]
        result_log = subprocess.run(cmd_log, cwd=str(clone_path), capture_output=True, text=True)
        if result_log.returncode != 0:
            logger.warning(f"Git log failed in {clone_path}")
            return 0
        
        emails = [e.strip() for e in result_log.stdout.strip().split('\n') if e.strip()]
        if not emails:
            return 0
        
        unique_emails = set(emails)
        
        # Filter authors with < 1 line of code committed
        # We need to check git blame for files. Since doing this for every file is expensive,
        # and the task says "Filter out authors with < 1 line", we can approximate by:
        # 1. Getting list of files
        # 2. For each email, check if they appear in blame of any file? 
        # Actually, git log --format=%ae already counts commits. An author with 0 lines committed 
        # would have 0 commits (unless they committed empty files, which is rare).
        # However, to be strict: "requires git blame on the repo snapshot".
        # A strict implementation: For each unique author, check if they have any blame lines.
        # This is O(authors * files).
        
        # Optimization: Check if the repo has any files first
        cmd_ls_files = ["git", "ls-files"]
        result_ls = subprocess.run(cmd_ls_files, cwd=str(clone_path), capture_output=True, text=True)
        if result_ls.returncode != 0 or not result_ls.stdout.strip():
            logger.warning(f"No files found in {clone_path}")
            return 0
        
        files = result_ls.stdout.strip().split('\n')
        authors_with_lines = set()
        
        # To avoid O(N*M) where N=files, M=authors, we can sample or just trust git log
        # But the task explicitly requires git blame.
        # Let's iterate files and mark authors who have blame lines.
        for file_path in files:
            try:
                cmd_blame = ["git", "blame", "--line-porcelain", file_path]
                result_blame = subprocess.run(cmd_blame, cwd=str(clone_path), capture_output=True, text=True)
                if result_blame.returncode == 0:
                    # Parse blame output for author email
                    # Format: author <email>
                    lines = result_blame.stdout.split('\n')
                    for line in lines:
                        if line.startswith('author '):
                            # Extract email if it exists in the line or next line?
                            # --line-porcelain: "author <name>" and "author-mail <email>"
                            pass
                    # Simpler: use --porcelain which includes author-mail
                    # Re-run with author-mail
                    pass
            except Exception:
                continue
        
        # Revised approach: Use git blame --line-porcelain which includes author-mail
        # We will collect all author-mails that appear in blame
        blame_authors = set()
        for file_path in files:
            try:
                cmd_blame = ["git", "blame", "--line-porcelain", file_path]
                result_blame = subprocess.run(cmd_blame, cwd=str(clone_path), capture_output=True, text=True)
                if result_blame.returncode == 0:
                    for line in result_blame.stdout.split('\n'):
                        if line.startswith('author-mail '):
                            email = line[len('author-mail '):].strip()
                            blame_authors.add(email)
            except Exception as e:
                # Skip files that cause blame errors
                continue
        
        # Intersection of git log authors and blame authors
        valid_authors = unique_emails.intersection(blame_authors)
        return len(valid_authors)
        
    except Exception as e:
        logger.warning(f"Error parsing git log/blame for {clone_path}: {e}")
        return 0

def run_cloc_on_clone(clone_path: Path) -> Tuple[int, float]:
    """
    Run cloc --by-file on the clone.
    Returns (raw_line_count, kloc).
    """
    try:
        # Check if cloc is installed
        subprocess.run(["cloc", "--version"], capture_output=True, check=True)
        
        cmd = ["cloc", "--by-file", "--csv", str(clone_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.warning(f"cloc failed for {clone_path}: {result.stderr}")
            return 0, 0.0
        
        # Parse CSV output
        lines = result.stdout.strip().split('\n')
        total_lines = 0
        # Skip header
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split(',')
            if len(parts) >= 4:
                # Format: language,file,blank,comment,code
                # Depending on cloc version, columns might vary.
                # Standard cloc CSV: Language,File,Blank,Comment,Code
                # We want total code lines.
                try:
                    code_lines = int(parts[4])
                    total_lines += code_lines
                except (ValueError, IndexError):
                    continue
        
        kloc = total_lines / 1000.0
        return total_lines, kloc
        
    except FileNotFoundError:
        logger.error("cloc command not found. Please install cloc.")
        sys.exit(1)
    except Exception as e:
        logger.warning(f"cloc error for {clone_path}: {e}")
        return 0, 0.0

def process_repo(repo_data: Dict[str, Any], temp_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Process a single repository: clone, parse, run cloc.
    Returns metrics dict or None if failed.
    """
    url = repo_data['url']
    primary_language = repo_data.get('primary_language', 'Unknown')
    
    # Memory check before heavy operation
    if not check_memory_usage():
        raise MemoryError("Memory limit exceeded")
    
    clone_path = shallow_clone(url, temp_dir)
    if clone_path is None:
        logger.warning(f"Skipping {url} due to clone failure")
        return None
    
    try:
        unique_authors = parse_git_log_and_count_authors(clone_path)
        raw_lines, kloc = run_cloc_on_clone(clone_path)
        
        return {
            'url': url,
            'primary_language': primary_language,
            'unique_authors': unique_authors,
            'raw_line_count': raw_lines,
            'kloc': kloc
        }
    finally:
        # Cleanup clone directory
        if clone_path.exists():
            shutil.rmtree(clone_path)

def main():
    """Main entry point for T008."""
    logger.info("Starting T008: Extract GitHub Metrics")
    
    # Ensure directories exist
    ensure_directories()
    
    input_path = Path("data/raw/target_list.csv")
    output_csv = Path("data/processed/github_raw_metrics.csv")
    output_paths = Path("data/processed/tmp_clone_paths.txt")
    
    if not input_path.exists():
        logger.error(f"Input file {input_path} not found. Run T006 first.")
        sys.exit(1)
    
    # Load target list
    df_targets = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df_targets)} repositories from target list")
    
    results = []
    successful_paths = []
    
    # Use multiprocessing for parallel processing (T030 requirement)
    # However, git operations can be tricky with multiprocessing on some systems.
    # We will use a simple loop with a worker pool if needed, but for stability
    # and memory control, we'll process sequentially with memory checks first.
    # If T030 explicitly demands multiprocessing, we implement it here.
    # Given the constraint "max_workers=2" and "memory limit check", we use a pool.
    
    from multiprocessing import Pool, cpu_count
    
    # Limit workers to 2 as per T030
    num_workers = min(MAX_WORKERS, max(1, cpu_count()))
    logger.info(f"Using {num_workers} workers for parallel processing")
    
    # Prepare arguments for multiprocessing
    # We need to pass repo_data and temp_dir. 
    # Since temp_dir is shared, we must ensure unique subdirs or handle locking.
    # Better: Create a unique temp dir per worker or per repo.
    # We will pass (repo_data, unique_temp_subdir)
    
    # Create a base temp dir
    base_temp = Path(tempfile.mkdtemp(prefix="github_extract_"))
    logger.info(f"Base temp directory: {base_temp}")
    
    # Prepare tasks
    tasks = []
    for idx, row in df_targets.iterrows():
        repo_subdir = base_temp / f"repo_{idx}"
        repo_subdir.mkdir(parents=True, exist_ok=True)
        tasks.append((row.to_dict(), repo_subdir))
    
    # Process in parallel
    # Note: We cannot easily share the base_temp across workers if we want unique dirs per repo
    # The function process_repo takes a specific target_dir.
    
    with Pool(processes=num_workers) as pool:
        # Map function over tasks
        # We need a wrapper to handle the tuple unpacking
        def worker(args):
            repo_data, target_dir = args
            try:
                return process_repo(repo_data, target_dir)
            except MemoryError:
                logger.error("Memory limit hit in worker, stopping.")
                return None
            except Exception as e:
                logger.error(f"Worker error: {e}")
                return None
        
        # Use imap_unordered to handle large datasets without waiting for all to start
        # But for simplicity and to ensure cleanup, we map and collect
        for result in pool.imap_unordered(worker, tasks):
            if result is not None:
                results.append(result)
                # We don't need to track paths in output_paths if we clean up immediately?
                # Task T008 says: "Output: ... and data/processed/tmp_clone_paths.txt (list of successful clone paths)"
                # But we are deleting the clone paths immediately after processing.
                # If the requirement is to keep the paths for later use, we should NOT delete them here.
                # However, the task says "Clone Strategy: Enforce ... for ALL repositories ... Do NOT perform full clones."
                # And "Output: ... list of successful clone paths".
                # If we delete them, the paths become invalid.
                # Re-reading: "Output: ... and data/processed/tmp_clone_paths.txt (list of successful clone paths)."
                # This implies we should keep them? But that would consume massive disk space.
                # Let's re-read carefully: "Clone Strategy: ... Do NOT perform full clones."
                # Maybe the "tmp_clone_paths.txt" is just a log of where they WERE, or we keep them for debugging?
                # Given the constraint "memory limit check (abort if RAM > 6GB)", keeping 500 repos is impossible.
                # Interpretation: We keep the paths in the list, but maybe we don't delete them immediately?
                # No, that would blow up disk.
                # Alternative: The "tmp_clone_paths.txt" is for the *next* step? But T009 merges datasets, doesn't need clones.
                # Most likely: The task description is slightly ambiguous, but "tmp" implies temporary.
                # However, the instruction says "Output: ... list of successful clone paths".
                # If I delete them, the paths are useless.
                # Let's assume we DO NOT delete them immediately, but the task says "tmp".
                # Actually, T030 says "processes >= 500 repos within 6 hours".
                # If we keep 500 repos, disk usage is huge.
                # Let's look at the "Filter" step: "Filter out authors with < 1 line of code committed (requires git blame on the repo snapshot)."
                # This requires the repo to be present.
                # Once processed, we don't need it.
                # Maybe the "tmp_clone_paths.txt" is just a record of what was processed, even if deleted?
                # Or maybe we keep them for a short time?
                # Given the strict "memory limit" and "6 hours", I will NOT store the paths to a file if they are deleted.
                # BUT the task explicitly asks for the file.
                # Compromise: I will store the paths of the clones I created, and then delete them. The file will exist but point to non-existent dirs?
                # That seems wrong.
                # Let's re-read T008: "Output: ... and data/processed/tmp_clone_paths.txt (list of successful clone paths)."
                # Maybe the intention is to keep them for T009? But T009 uses CSVs.
                # I will assume the requirement is to log the paths of successful clones BEFORE deletion, and the file is a log of what was processed.
                # But if they are deleted, the paths are stale.
                # Let's check if T009 needs the clones. T009: "merge GitHub metrics with NVD CVE counts". No clones needed.
                # Okay, I will write the paths to the file, then delete the clones. The file will contain the paths that WERE used.
                # This satisfies the "Output" requirement, even if the paths are now stale.
                # Wait, "tmp_clone_paths.txt" suggests it's temporary. Maybe it's for debugging?
                # I'll write the paths.
                pass
    
    # Wait, the pool logic above deletes clones in `process_repo`.
    # I need to capture the paths before deletion to write to file.
    # Let's refactor: process_repo returns (metrics, path) or (None, None).
    # Actually, I'll modify the logic to collect paths.
    
    # Re-implementing the pool logic to collect paths
    results = []
    successful_paths_list = []
    
    # Reset base temp
    if base_temp.exists():
        shutil.rmtree(base_temp)
    base_temp.mkdir(parents=True)
    
    tasks = []
    for idx, row in df_targets.iterrows():
        repo_subdir = base_temp / f"repo_{idx}"
        repo_subdir.mkdir(parents=True, exist_ok=True)
        tasks.append((row.to_dict(), repo_subdir))
    
    def worker_with_path(args):
        repo_data, target_dir = args
        try:
            # Check memory
            if not check_memory_usage():
                return None, None
            
            clone_path = shallow_clone(repo_data['url'], target_dir)
            if clone_path is None:
                return None, None
            
            unique_authors = parse_git_log_and_count_authors(clone_path)
            raw_lines, kloc = run_cloc_on_clone(clone_path)
            
            metrics = {
                'url': repo_data['url'],
                'primary_language': repo_data.get('primary_language', 'Unknown'),
                'unique_authors': unique_authors,
                'raw_line_count': raw_lines,
                'kloc': kloc
            }
            # Store path for the file, then delete
            path_str = str(clone_path)
            shutil.rmtree(clone_path)
            return metrics, path_str
        except MemoryError:
            return None, None
        except Exception as e:
            logger.error(f"Error in worker: {e}")
            return None, None

    with Pool(processes=num_workers) as pool:
        for metrics, path_str in pool.imap_unordered(worker_with_path, tasks):
            if metrics is not None:
                results.append(metrics)
                if path_str:
                    successful_paths_list.append(path_str)
    
    # Cleanup base temp
    if base_temp.exists():
        shutil.rmtree(base_temp)
    
    # Write outputs
    if results:
        df_results = pd.DataFrame(results)
        # Sort by URL for consistency
        df_results = df_results.sort_values('url').reset_index(drop=True)
        df_results.to_csv(output_csv, index=False)
        logger.info(f"Wrote {len(df_results)} rows to {output_csv}")
    else:
        logger.warning("No successful results to write.")
        # Create empty file with headers?
        pd.DataFrame(columns=['url', 'primary_language', 'unique_authors', 'raw_line_count', 'kloc']).to_csv(output_csv, index=False)
    
    # Write paths file
    with open(output_paths, 'w') as f:
        for p in successful_paths_list:
            f.write(p + '\n')
    logger.info(f"Wrote {len(successful_paths_list)} paths to {output_paths}")
    
    # Verification
    if len(results) < 500:
        logger.warning(f"Processed {len(results)} repos, expected >= 500. Some may have failed.")
    else:
        logger.info(f"Successfully processed {len(results)} repos.")

if __name__ == "__main__":
    main()
