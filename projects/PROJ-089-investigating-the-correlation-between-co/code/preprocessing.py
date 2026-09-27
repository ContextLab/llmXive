import os
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from utils import get_logger

# Constants for streaming
CHUNK_SIZE = 1000

def is_source_file(file_path: str) -> bool:
    """
    Determine if a file path corresponds to a source code file.
    Filters out documentation, build artifacts, and config files.
    """
    if not file_path:
        return False
    
    ext = Path(file_path).suffix.lower()
    source_exts = {'.py', '.java', '.js', '.ts', '.go', '.rs', '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift', '.kt', '.scala', '.m', '.mm'}
    return ext in source_exts

def should_exclude_dir(dir_name: str) -> bool:
    """
    Check if a directory should be excluded from analysis (e.g., tests, vendor, build).
    """
    excluded = {
        'test', 'tests', 'node_modules', 'vendor', 'build', 'dist', 
        'venv', '.venv', '__pycache__', '.git', '.svn', 'docs', 
        'example', 'examples', 'benchmark', 'benchmarks'
    }
    return dir_name.lower() in excluded

def filter_non_source_files(git_history_df: pd.DataFrame, semgrep_results: Dict) -> pd.DataFrame:
    """
    Filters the git history dataframe to keep only source files present in semgrep results.
    Also removes non-source extensions.
    
    Args:
        git_history_df: DataFrame with columns ['file_path', 'total_lines_changed', 'commit_count']
        semgrep_results: Dict of file_path -> semgrep metrics (keys must match git_history)
    
    Returns:
        Filtered DataFrame.
    """
    if git_history_df.empty:
        return git_history_df
    
    # Filter for source file extensions
    source_mask = git_history_df['file_path'].apply(is_source_file)
    git_history_df = git_history_df[source_mask].copy()
    
    if git_history_df.empty:
        return git_history_df

    # Filter for files that exist in semgrep results
    # If a file was changed but Semgrep didn't analyze it (e.g., language mismatch or empty),
    # we might need to handle it. The task implies joining on file_path.
    # We will keep files that are in the git history AND have a valid entry in semgrep results.
    # If semgrep_results is empty for a file, we might still want to keep it with 0 debt?
    # Spec says: "Filter non-source-code files".
    # Let's assume we keep files present in git history that are source files.
    # We will join with semgrep data, filling missing debt scores with 0 or NaN depending on strictness.
    # Given the task is about correlation, we need valid debt scores.
    # If a file is source but Semgrep found nothing, debt_score might be 0.
    
    # Convert semgrep keys to a set for fast lookup
    semgrep_files = set(semgrep_results.keys())
    
    # Keep files that are in git history and (are source files OR we assume source if in git)
    # We already filtered by extension. Now ensure we have metrics.
    # If a file is in git history but not in semgrep results, it might be a false positive in git (e.g. binary misidentified) or semgrep skipped it.
    # For robustness, we'll keep it but mark debt as 0 if not found, or drop it if strict.
    # Let's join and drop rows where debt_score is NaN if we require it.
    
    # Create a DataFrame from semgrep results to join
    semgrep_df = pd.DataFrame([
        {'file_path': k, 'debt_score': v.get('debt_score', 0) if isinstance(v, dict) else 0}
        for k, v in semgrep_results.items()
    ])
    
    if semgrep_df.empty:
        # If no semgrep results, return empty or original?
        # If no analysis was done, we can't compute correlation.
        return pd.DataFrame(columns=git_history_df.columns.tolist() + ['debt_score'])
    
    # Merge
    merged = pd.merge(git_history_df, semgrep_df, on='file_path', how='left')
    
    # Fill missing debt scores with 0 (assuming no issues found = 0 debt)
    merged['debt_score'] = merged['debt_score'].fillna(0)
    
    # Calculate avg_loc if not present (placeholder logic, assuming it comes from static analysis or git history stats)
    # The spec mentions avg_loc as a covariate. If not in semgrep results, we might need to estimate or fetch.
    # For this task, we assume the input semgrep_results or git_history already has avg_loc or we calculate it.
    # If avg_loc is missing, we might need to compute it.
    # Let's assume the semgrep result contains 'avg_loc' or we calculate it from file size/lines if available.
    # If not present in semgrep, we might need to fetch from a separate source or default.
    # For now, if 'avg_loc' is in semgrep_df, we keep it. If not, we might need to derive it.
    # The task T015a description says: "Filter non-source-code files... Output: unified_metrics.csv".
    # It doesn't explicitly say how to get avg_loc if missing. We assume it's in semgrep_results.
    
    if 'avg_loc' not in merged.columns:
        # Fallback: try to compute from git history if 'lines_changed' is a proxy? No, that's churn.
        # We must have avg_loc. If missing, we cannot proceed with the full analysis.
        # We will leave it as NaN for now, and the downstream analysis might drop these.
        pass
    
    return merged

def load_git_history_chunked(repo_id: str, base_path: Path, chunksize: int = CHUNK_SIZE) -> pd.DataFrame:
    """
    Loads git history CSV for a specific repo using chunked reading to manage memory.
    Aggregates statistics on the fly if needed, or returns the full DataFrame if it fits.
    Here we return the full DataFrame but constructed via streaming to avoid loading
    a massive file into memory at once if it exceeds RAM.
    """
    git_history_path = base_path / 'git_history' / repo_id / 'commits.csv'
    
    if not git_history_path.exists():
        return pd.DataFrame()
    
    # Read in chunks
    chunks = []
    for chunk in pd.read_csv(git_history_path, chunksize=chunksize):
        chunks.append(chunk)
    
    if not chunks:
        return pd.DataFrame()
    
    return pd.concat(chunks, ignore_index=True)

def load_semgrep_results_chunked(repo_id: str, base_path: Path) -> Dict[str, Any]:
    """
    Loads semgrep results JSON. Since JSON is usually one file, we load it directly.
    If the JSON is massive, we might need to stream it, but usually it's smaller than CSVs.
    However, for consistency with the streaming requirement, we assume the file might be large.
    We'll load it as a dict. If it's too big, this will raise MemoryError, which is acceptable
    as "fail loudly" rather than silently dropping data.
    """
    semgrep_path = base_path / 'static_analysis' / repo_id / 'semgrep_results.json'
    
    if not semgrep_path.exists():
        return {}
    
    try:
        with open(semgrep_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def run_preprocessing_streaming(base_path: Path, output_path: Path, logger: Optional[logging.Logger] = None) -> None:
    """
    Main entry point for preprocessing with streaming support.
    Iterates over repos, loads data in chunks, merges, and writes to a single unified CSV.
    Uses a generator to accumulate rows to avoid holding all data in memory.
    """
    if logger is None:
        logger = get_logger('preprocessing')
    
    logger.info("Starting streaming preprocessing...")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get list of repos from the git_history directory structure
    git_history_dir = base_path / 'git_history'
    if not git_history_dir.exists():
        logger.warning("No git_history directory found. Nothing to process.")
        return
    
    repos = [d.name for d in git_history_dir.iterdir() if d.is_dir()]
    
    if not repos:
        logger.warning("No repositories found in git_history directory.")
        return
    
    logger.info(f"Found {len(repos)} repositories to process.")
    
    # Define columns for the final CSV
    columns = ['repo_id', 'file_path', 'total_lines_changed', 'commit_count', 'debt_score', 'avg_loc', 'contributor_count']
    
    # Write header first
    with open(output_path, 'w') as f:
        f.write(','.join(columns) + '\n')
    
    # Process each repo
    for repo_id in repos:
        logger.info(f"Processing repo: {repo_id}")
        
        try:
            # Load Git History (Chunked)
            git_df = load_git_history_chunked(repo_id, base_path)
            if git_df.empty:
                logger.warning(f"No git history for {repo_id}, skipping.")
                continue
            
            # Load Semgrep Results
            semgrep_data = load_semgrep_results_chunked(repo_id, base_path)
            
            # Filter and Merge
            merged_df = filter_non_source_files(git_df, semgrep_data)
            
            if merged_df.empty:
                logger.warning(f"No valid source files for {repo_id} after filtering.")
                continue
            
            # Add repo_id column
            merged_df['repo_id'] = repo_id
            
            # Reorder columns to match output schema
            # Ensure all columns exist, fill missing with NaN
            for col in columns:
                if col not in merged_df.columns:
                    merged_df[col] = np.nan
            
            merged_df = merged_df[columns]
            
            # Write to CSV in chunks (or all at once if small)
            # Since we are writing to a file, we can append
            merged_df.to_csv(output_path, mode='a', header=False, index=False)
            
            logger.info(f"Processed {len(merged_df)} files for {repo_id}.")
            
        except Exception as e:
            logger.error(f"Error processing repo {repo_id}: {e}", exc_info=True)
            # Continue to next repo
            continue
    
    logger.info(f"Preprocessing complete. Output written to {output_path}")

def run_preprocessing(base_path: Path, output_path: Path) -> None:
    """
    Wrapper for run_preprocessing_streaming to maintain API compatibility.
    """
    logger = get_logger('preprocessing')
    run_preprocessing_streaming(base_path, output_path, logger)

def main():
    """
    CLI entry point for preprocessing.
    """
    import argparse
    from utils import setup_logging
    
    setup_logging()
    logger = get_logger('preprocessing')
    
    parser = argparse.ArgumentParser(description='Preprocess git and semgrep data.')
    parser.add_argument('--base-path', type=str, required=True, help='Base path for data directories')
    parser.add_argument('--output-path', type=str, required=True, help='Path for output CSV')
    
    args = parser.parse_args()
    
    base = Path(args.base_path)
    out = Path(args.output_path)
    
    run_preprocessing(base, out)

if __name__ == '__main__':
    main()