"""
Preprocessing module for T015.

Filters non-source-code files, excludes files with avg_loc < 10 (default),
and generates parameterized datasets for sensitivity analysis with thresholds 5, 10, 20.

Outputs:
    data/processed/unified_metrics.csv (raw metrics)
    data/processed/unified_metrics_threshold_5.csv
    data/processed/unified_metrics_threshold_10.csv
    data/processed/unified_metrics_threshold_20.csv
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Import from existing project modules
from config import get_config_summary, ensure_directories
from utils import get_logger

# Define source code extensions
SOURCE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
    '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r', '.m', '.mm',
    '.pl', '.pm', '.sh', '.bash', '.zsh', '.fish', '.ps1', '.sql', '.html',
    '.css', '.scss', '.sass', '.less', '.vue', '.svelte', '.cs', '.fs', '.fsx'
}

# Non-source files patterns to exclude
EXCLUDED_DIRS = {
    'node_modules', 'venv', '.venv', '__pycache__', '.git', '.svn', '.hg',
    'dist', 'build', '.idea', '.vscode', 'target', 'out', 'bin', 'obj',
    'vendor', 'third_party', 'external', 'dependencies', 'test_data', 'fixtures'
}

EXCLUDED_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'Gemfile.lock',
    'Cargo.lock', 'composer.lock', 'poetry.lock', 'pipfile.lock',
    'requirements.txt', 'setup.py', 'pyproject.toml', 'Makefile', 'Dockerfile',
    'docker-compose.yml', '.gitignore', '.dockerignore', 'README.md', 'LICENSE',
    'CHANGELOG.md', 'CONTRIBUTING.md', 'setup.cfg', 'tox.ini', '.coveragerc'
}

def is_source_file(file_path: Path) -> bool:
    """Check if a file is a source code file based on extension and name."""
    if file_path.suffix.lower() not in SOURCE_EXTENSIONS:
        return False
    
    # Check if any parent directory is excluded
    for part in file_path.parts:
        if part in EXCLUDED_DIRS:
            return False
    
    # Check if the filename itself is excluded
    if file_path.name in EXCLUDED_FILES:
        return False
    
    return True

def filter_non_source_files(df: pd.DataFrame, file_path_column: str = 'file_path') -> pd.DataFrame:
    """Filter out non-source-code files from the dataframe."""
    valid_rows = []
    for idx, row in df.iterrows():
        file_path = Path(row[file_path_column])
        if is_source_file(file_path):
            valid_rows.append(row)
    
    return pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame(columns=df.columns)

def apply_loc_threshold(df: pd.DataFrame, threshold: int, loc_column: str = 'avg_loc') -> pd.DataFrame:
    """Filter files based on avg_loc threshold."""
    if loc_column not in df.columns:
        raise ValueError(f"Column '{loc_column}' not found in dataframe")
    
    return df[df[loc_column] >= threshold].copy()

def generate_parameterized_datasets(input_df: pd.DataFrame, thresholds: List[int] = [5, 10, 20]) -> Dict[int, pd.DataFrame]:
    """
    Generate datasets for sensitivity analysis with different LOC thresholds.
    
    Args:
        input_df: DataFrame with raw metrics
        thresholds: List of LOC thresholds to apply (default: [5, 10, 20])
    
    Returns:
        Dictionary mapping threshold value to filtered DataFrame
    """
    datasets = {}
    
    for threshold in thresholds:
        filtered_df = apply_loc_threshold(input_df, threshold)
        datasets[threshold] = filtered_df
    
    return datasets

def save_datasets(datasets: Dict[int, pd.DataFrame], output_dir: Path, base_filename: str = 'unified_metrics') -> List[str]:
    """
    Save parameterized datasets to CSV files.
    
    Args:
        datasets: Dictionary of threshold -> DataFrame
        output_dir: Directory to save files
        base_filename: Base name for output files
    
    Returns:
        List of paths to saved files
    """
    saved_files = []
    
    # Save the default dataset (threshold 10)
    if 10 in datasets:
        default_path = output_dir / f"{base_filename}.csv"
        datasets[10].to_csv(default_path, index=False)
        saved_files.append(str(default_path))
    
    # Save threshold-specific datasets
    for threshold, df in datasets.items():
        if threshold != 10:  # Already saved as default
            threshold_path = output_dir / f"{base_filename}_threshold_{threshold}.csv"
            df.to_csv(threshold_path, index=False)
            saved_files.append(str(threshold_path))
    
    return saved_files

def validate_raw_metrics(df: pd.DataFrame) -> bool:
    """
    Validate that the dataframe contains the required raw metrics columns.
    
    Required columns: total_lines_changed, debt_score, avg_loc, contributor_count
    """
    required_columns = ['total_lines_changed', 'debt_score', 'avg_loc', 'contributor_count']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required raw metric columns: {missing_columns}")
    
    # Check for non-null values in required columns
    for col in required_columns:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            logging.warning(f"Column '{col}' has {null_count} null values")
    
    return True

def run_preprocessing(input_file: str, output_dir: str, thresholds: List[int] = [5, 10, 20]) -> Dict[str, Any]:
    """
    Main preprocessing function.
    
    Args:
        input_file: Path to input unified_metrics.csv (raw metrics from static analysis)
        output_dir: Directory to save processed output files
        thresholds: List of LOC thresholds for sensitivity analysis
    
    Returns:
        Dictionary with execution results and statistics
    """
    logger = get_logger(__name__)
    
    # Ensure output directory exists
    ensure_directories()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load input data
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    logger.info(f"Loading input data from {input_file}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows")
    
    # Validate raw metrics
    validate_raw_metrics(df)
    
    # Filter non-source files
    logger.info("Filtering non-source-code files...")
    filtered_df = filter_non_source_files(df)
    logger.info(f"Filtered to {len(filtered_df)} source files (removed {len(df) - len(filtered_df)} non-source files)")
    
    # Generate parameterized datasets
    logger.info(f"Generating datasets for thresholds: {thresholds}")
    datasets = generate_parameterized_datasets(filtered_df, thresholds)
    
    # Save datasets
    logger.info("Saving datasets...")
    saved_files = save_datasets(datasets, output_path)
    
    # Prepare results summary
    results = {
        'input_file': str(input_path),
        'output_directory': str(output_path),
        'total_input_rows': len(df),
        'filtered_source_rows': len(filtered_df),
        'non_source_removed': len(df) - len(filtered_df),
        'thresholds_processed': thresholds,
        'output_files': saved_files,
        'datasets_summary': {
            threshold: len(df) for threshold, df in datasets.items()
        }
    }
    
    logger.info(f"Preprocessing complete. Saved {len(saved_files)} files.")
    logger.info(f"Dataset sizes by threshold: {results['datasets_summary']}")
    
    return results

def main():
    """Entry point for preprocessing script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess metrics data for sensitivity analysis')
    parser.add_argument('--input', type=str, default='data/processed/unified_metrics_raw.csv',
                      help='Input CSV file with raw metrics')
    parser.add_argument('--output', type=str, default='data/processed',
                      help='Output directory for processed files')
    parser.add_argument('--thresholds', type=int, nargs='+', default=[5, 10, 20],
                      help='LOC thresholds for sensitivity analysis')
    
    args = parser.parse_args()
    
    try:
        results = run_preprocessing(args.input, args.output, args.thresholds)
        print(f"Preprocessing completed successfully.")
        print(f"Output files: {results['output_files']}")
        print(f"Dataset sizes: {results['datasets_summary']}")
    except Exception as e:
        logging.error(f"Preprocessing failed: {e}")
        raise

if __name__ == '__main__':
    main()
