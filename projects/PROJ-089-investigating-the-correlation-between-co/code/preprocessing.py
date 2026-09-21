import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from config import get_config_summary

logger = logging.getLogger(__name__)

# Source file extensions by language
SOURCE_EXTENSIONS = {
    # Python
    '.py',
    # Java
    '.java',
    # JavaScript/TypeScript
    '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    # Go
    '.go',
    # Rust
    '.rs',
    # C/C++
    '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx',
    # Ruby
    '.rb',
    # PHP
    '.php',
    # Swift
    '.swift',
    # Kotlin
    '.kt', '.kts',
    # Scala
    '.scala',
    # Shell
    '.sh', '.bash', '.zsh',
    # SQL
    '.sql',
    # HTML/CSS
    '.html', '.htm', '.css', '.scss', '.sass', '.less',
    # Config (often counted as source in some contexts, but excluding for strictness unless specified)
    # '.yaml', '.yml', '.json', '.xml', '.toml'
}

# Directories to exclude from analysis
EXCLUDED_DIRS = {
    'node_modules', '__pycache__', '.git', '.svn', '.hg',
    'venv', '.venv', 'env', '.env',
    'build', 'dist', 'target', 'out',
    'test', 'tests', 'spec', 'specs',
    '__tests__', '__mocks__',
    '.idea', '.vscode',
    'docs', 'documentation',
    'examples', 'sample', 'samples',
    'vendor', 'third_party',
    'migrations', 'alembic',
}

def is_source_file(file_path: str) -> bool:
    """
    Check if a file is a source code file based on its extension.
    """
    if not file_path:
        return False
    path_obj = Path(file_path)
    return path_obj.suffix.lower() in SOURCE_EXTENSIONS

def should_exclude_dir(dir_path: str) -> bool:
    """
    Check if a directory should be excluded from analysis.
    """
    if not dir_path:
        return False
    # Check if any part of the path is in the exclusion list
    parts = Path(dir_path).parts
    return any(part.lower() in EXCLUDED_DIRS for part in parts)

def filter_non_source_files(git_metrics_path: Path, semgrep_metrics_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Filter non-source-code files from Git history and Static Analysis outputs.
    
    Inputs:
      - git_metrics_path: Directory containing commits.csv for each repo
      - semgrep_metrics_path: Directory containing semgrep_results.json for each repo
      - output_path: Path to save the filtered metrics CSV
    
    Returns:
      - DataFrame of filtered metrics
    """
    logger.info(f"Starting filtering of non-source files. Input: {git_metrics_path}, {semgrep_metrics_path}")
    
    if not git_metrics_path.exists():
        raise FileNotFoundError(f"Git metrics directory not found: {git_metrics_path}")
    if not semgrep_metrics_path.exists():
        raise FileNotFoundError(f"Semgrep metrics directory not found: {semgrep_metrics_path}")
    
    # Collect all filtered data
    all_data = []
    
    # Process Git History
    git_df_list = []
    for repo_dir in git_metrics_path.iterdir():
        if repo_dir.is_dir():
            commits_file = repo_dir / "commits.csv"
            if commits_file.exists():
                try:
                    df = pd.read_csv(commits_file)
                    # Ensure file_path column exists
                    if 'file_path' in df.columns:
                        # Filter for source files only
                        source_mask = df['file_path'].apply(is_source_file)
                        # Also filter out paths containing excluded directories
                        dir_mask = ~df['file_path'].apply(lambda p: should_exclude_dir(p))
                        filtered_df = df[source_mask & dir_mask]
                        if not filtered_df.empty:
                            filtered_df['repo_id'] = repo_dir.name
                            git_df_list.append(filtered_df)
                    else:
                        logger.warning(f"commits.csv missing 'file_path' column in {commits_file}")
                except Exception as e:
                    logger.error(f"Error processing {commits_file}: {e}")
    
    if git_df_list:
        git_df = pd.concat(git_df_list, ignore_index=True)
    else:
        git_df = pd.DataFrame(columns=['file_path', 'total_lines_changed', 'commit_count', 'repo_id'])
    
    # Process Semgrep Results
    semgrep_df_list = []
    for repo_dir in semgrep_metrics_path.iterdir():
        if repo_dir.is_dir():
            results_file = repo_dir / "semgrep_results.json"
            if results_file.exists():
                try:
                    with open(results_file, 'r') as f:
                        data = json.load(f)
                    
                    # Expected structure: list of results or dict with results
                    # Assuming structure: {"results": [{"path": "...", "code_smells": N, ...}, ...]}
                    # Or flat list if processed differently
                    results = data.get('results', data) if isinstance(data, dict) else data
                    
                    if isinstance(results, list):
                        rows = []
                        for item in results:
                            if isinstance(item, dict) and 'path' in item:
                                rows.append(item)
                        
                        if rows:
                            df = pd.DataFrame(rows)
                            # Standardize column names if necessary
                            # Assuming 'path' is the file path
                            if 'path' in df.columns:
                                df.rename(columns={'path': 'file_path'}, inplace=True)
                                # Filter for source files
                                source_mask = df['file_path'].apply(is_source_file)
                                dir_mask = ~df['file_path'].apply(lambda p: should_exclude_dir(p))
                                filtered_df = df[source_mask & dir_mask]
                                
                                if not filtered_df.empty:
                                    # Ensure numeric columns exist, fill NaN with 0
                                    numeric_cols = ['code_smells', 'cc', 'debt_score'] # Adjust based on actual output
                                    for col in numeric_cols:
                                        if col not in filtered_df.columns:
                                            filtered_df[col] = 0
                                        else:
                                            filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce').fillna(0)
                                    
                                    filtered_df['repo_id'] = repo_dir.name
                                    semgrep_df_list.append(filtered_df)
                except Exception as e:
                    logger.error(f"Error processing {results_file}: {e}")
    
    if semgrep_df_list:
        semgrep_df = pd.concat(semgrep_df_list, ignore_index=True)
    else:
        semgrep_df = pd.DataFrame(columns=['file_path', 'code_smells', 'cc', 'debt_score', 'repo_id'])
    
    # Merge Git and Semgrep data on repo_id and file_path
    if not git_df.empty and not semgrep_df.empty:
        merged_df = pd.merge(git_df, semgrep_df, on=['repo_id', 'file_path'], how='outer')
    elif not git_df.empty:
        merged_df = git_df
    elif not semgrep_df.empty:
        merged_df = semgrep_df
    else:
        logger.warning("No data found after filtering. Creating empty DataFrame.")
        merged_df = pd.DataFrame(columns=['repo_id', 'file_path', 'total_lines_changed', 'commit_count', 'code_smells', 'cc', 'debt_score'])
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Filtered metrics saved to {output_path}. Rows: {len(merged_df)}")
    
    return merged_df

def run_preprocessing():
    """
    Main entry point for the preprocessing phase.
    Reads raw data from data/raw/, filters non-source files, and saves to data/processed/.
    """
    config = get_config_summary()
    raw_git_path = Path(config['paths']['raw_git'])
    raw_semgrep_path = Path(config['paths']['raw_semgrep'])
    output_path = Path(config['paths']['processed']) / "filtered_metrics.csv"
    
    logger.info("Running preprocessing: Filtering non-source files...")
    try:
        df = filter_non_source_files(raw_git_path, raw_semgrep_path, output_path)
        logger.info(f"Preprocessing complete. Output: {output_path}")
        return df
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    run_preprocessing()
