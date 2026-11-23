import os
import sys
import subprocess
import tempfile
import shutil
import logging
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from local utils module
from code.data.utils import run_command, parse_git_log, run_cloc
from code.config import ensure_directories

logger = logging.getLogger(__name__)

def check_memory_usage(threshold_gb: float = 1.0) -> bool:
    """
    Check current memory usage against a threshold.
    
    Args:
        threshold_gb: Memory threshold in gigabytes
        
    Returns:
        True if current memory usage is below threshold, False otherwise
    """
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    return mem_gb < threshold_gb

def shallow_clone(repo_url: str, target_dir: Path) -> bool:
    """
    Perform a shallow clone of a git repository.
    
    Args:
        repo_url: URL of the git repository
        target_dir: Directory path where the repository should be cloned
        
    Returns:
        True if clone was successful, False otherwise
    """
    cmd = ["git", "clone", "--depth=1", repo_url, str(target_dir)]
    stdout, stderr, code = run_command(cmd, timeout=300)
    
    if code != 0:
        logger.error(f"Failed to clone {repo_url}: {stderr}")
        return False
    
    return True

def parse_git_log_and_count_authors(repo_path: Path) -> int:
    """
    Parse git log to count unique authors in a repository.
    
    This function uses the parse_git_log utility to extract author emails
    and counts the number of unique authors.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        Number of unique authors
    """
    authors = parse_git_log(repo_path, format_str="%ae")
    unique_authors = len(set(authors))
    logger.debug(f"Found {unique_authors} unique authors in {repo_path}")
    return unique_authors

def run_cloc_on_clone(repo_path: Path) -> Dict[str, Any]:
    """
    Run cloc on a cloned repository and return metrics.
    
    This function uses the run_cloc utility to calculate lines of code
    and returns the results as a dictionary.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary with cloc results including total_lines, kloc, and success status
    """
    return run_cloc(repo_path)

def process_repo(repo_url: str, output_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Process a single repository: clone, parse authors, run cloc.
    
    Args:
        repo_url: URL of the repository to process
        output_dir: Directory for temporary clone storage
        
    Returns:
        Dictionary with metrics if successful, None if failed
    """
    # Check memory before cloning
    if not check_memory_usage():
        logger.critical(f"Memory usage too high, skipping {repo_url}")
        return None
    
    # Create a temporary directory for the clone
    clone_dir = output_dir / repo_url.split('/')[-1].replace('.git', '')
    clone_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Shallow clone
        if not shallow_clone(repo_url, clone_dir):
            logger.warning(f"Clone failed for {repo_url}, skipping")
            return None
        
        # Check memory again after clone
        if not check_memory_usage():
            logger.critical(f"Memory usage too high after clone, skipping {repo_url}")
            return None
        
        # Parse git log for unique authors
        unique_authors = parse_git_log_and_count_authors(clone_dir)
        
        # Run cloc
        cloc_results = run_cloc_on_clone(clone_dir)
        
        if not cloc_results['success']:
            logger.warning(f"cloc failed for {repo_url}, excluding from analysis")
            return None
        
        # Calculate authorship diversity
        kloc = cloc_results['kloc']
        if kloc > 0:
            authorship_diversity = unique_authors / kloc
        else:
            authorship_diversity = 0.0
        
        return {
            'url': repo_url,
            'unique_authors': unique_authors,
            'raw_line_count': cloc_results['total_lines'],
            'kloc': kloc,
            'authorship_diversity': authorship_diversity,
            'processing_status': 'success'
        }
    
    except Exception as e:
        logger.error(f"Error processing {repo_url}: {e}")
        return None
    finally:
        # Cleanup: remove the clone directory
        if clone_dir.exists():
            shutil.rmtree(clone_dir, ignore_errors=True)

def main():
    """
    Main entry point for the GitHub data extraction pipeline.
    
    Reads target list from data/raw/target_list.csv, processes each repository,
    and writes results to data/processed/github_raw_metrics.csv.
    """
    logging.basicConfig(level=logging.INFO)
    ensure_directories()
    
    target_list_path = Path("data/raw/target_list.csv")
    output_path = Path("data/processed/github_raw_metrics.csv")
    tmp_clone_paths_path = Path("data/processed/tmp_clone_paths.txt")
    
    if not target_list_path.exists():
        logger.error(f"Target list not found: {target_list_path}")
        sys.exit(1)
    
    import pandas as pd
    
    # Load target list
    df_targets = pd.read_csv(target_list_path)
    logger.info(f"Loaded {len(df_targets)} repositories from target list")
    
    results = []
    successful_clones = []
    
    # Process sequentially
    for idx, row in df_targets.iterrows():
        repo_url = row['url']
        logger.info(f"Processing [{idx+1}/{len(df_targets)}]: {repo_url}")
        
        result = process_repo(repo_url, Path("data/processed/tmp_clones"))
        
        if result:
            results.append(result)
            successful_clones.append(repo_url)
        else:
            # Record failure status
            results.append({
                'url': repo_url,
                'unique_authors': None,
                'raw_line_count': None,
                'kloc': None,
                'authorship_diversity': None,
                'processing_status': 'error_skip'
            })
    
    # Save results
    if results:
        df_results = pd.DataFrame(results)
        df_results.to_csv(output_path, index=False)
        logger.info(f"Saved {len(results)} results to {output_path}")
    else:
        logger.warning("No successful results to save")
    
    # Save successful clone paths (for cleanup verification if needed)
    with open(tmp_clone_paths_path, 'w') as f:
        for path in successful_clones:
            f.write(f"{path}\n")
    
    logger.info(f"Pipeline completed. Successfully processed: {len(successful_clones)}")

if __name__ == "__main__":
    main()
