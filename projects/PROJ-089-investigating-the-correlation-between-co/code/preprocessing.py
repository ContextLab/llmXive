"""
Preprocessing module for filtering and preparing metrics data.

Implements:
- Filtering non-source code files
- Excluding files with avg_loc < threshold
- Generating parameterized datasets for sensitivity analysis
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from config import get_config_summary, ensure_directories
from utils import get_logger

# Source file extensions
SOURCE_EXTENSIONS = {
    # Python
    '.py',
    # Java
    '.java',
    # JavaScript/TypeScript
    '.js', '.jsx', '.ts', '.tsx',
    # Go
    '.go',
    # Rust
    '.rs',
    # C/C++
    '.c', '.cpp', '.cc', '.h', '.hpp',
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
    # R
    '.r', '.R',
    # Julia
    '.jl',
    # Shell
    '.sh', '.bash',
    # HTML/CSS (often counted in web projects)
    '.html', '.htm', '.css', '.scss', '.sass', '.less',
    # Config files that might be analyzed
    '.yaml', '.yml', '.json', '.xml', '.toml', '.ini', '.cfg',
    # SQL
    '.sql',
    # Markdown (sometimes included in documentation debt)
    '.md', '.rst', '.txt',
}

# Directories to exclude
EXCLUDED_DIRS = {
    'node_modules', '__pycache__', '.git', '.svn', '.hg',
    'venv', 'env', '.env', 'dist', 'build', 'target',
    'vendor', 'third_party', 'external', 'libs',
    '.idea', '.vscode', '.settings', '.pytest_cache',
    'coverage', 'htmlcov', '.tox', '.mypy_cache',
}

# Directories to exclude based on name patterns
EXCLUDED_DIR_PATTERNS = {
    'test', 'tests', 'spec', 'specs', 'benchmark', 'bench',
    'example', 'examples', 'sample', 'samples',
    'mock', 'mocks', 'fixture', 'fixtures',
    'generated', 'gen', 'out', 'output',
}

logger = get_logger(__name__)

def is_source_file(file_path: str) -> bool:
    """
    Check if a file is a source code file based on extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file has a recognized source code extension
    """
    path = Path(file_path)
    return path.suffix.lower() in SOURCE_EXTENSIONS

def should_exclude_dir(dir_name: str) -> bool:
    """
    Check if a directory should be excluded from analysis.
    
    Args:
        dir_name: Name of the directory
        
    Returns:
        True if the directory should be excluded
    """
    dir_lower = dir_name.lower()
    if dir_lower in EXCLUDED_DIRS:
        return True
    if any(pattern in dir_lower for pattern in EXCLUDED_DIR_PATTERNS):
        return True
    return False

def filter_non_source_files(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out non-source code files from the dataset.
    
    Args:
        df: DataFrame with a 'file_path' column
        
    Returns:
        Filtered DataFrame containing only source files
    """
    if df.empty:
        logger.warning("Input DataFrame is empty")
        return df
    
    if 'file_path' not in df.columns:
        raise ValueError("DataFrame must contain 'file_path' column")
    
    # Filter by extension
    mask_extension = df['file_path'].apply(lambda x: is_source_file(str(x)))
    
    # Filter by directory
    def has_excluded_dir(path_str):
        path = Path(path_str)
        for parent in path.parents:
            if should_exclude_dir(parent.name):
                return True
        return False
    
    mask_dir = ~df['file_path'].apply(has_excluded_dir)
    
    combined_mask = mask_extension & mask_dir
    filtered_df = df[combined_mask].copy()
    
    logger.info(
        f"Filtered {len(df) - len(filtered_df)} non-source files "
        f"(from {len(df)} to {len(filtered_df)} rows)"
    )
    
    return filtered_df

def apply_loc_threshold(df: pd.DataFrame, min_loc: int) -> pd.DataFrame:
    """
    Filter out files with avg_loc below the specified threshold.
    
    Args:
        df: DataFrame with 'avg_loc' column
        min_loc: Minimum lines of code threshold
        
    Returns:
        Filtered DataFrame
    """
    if df.empty:
        logger.warning("Input DataFrame is empty")
        return df
    
    if 'avg_loc' not in df.columns:
        raise ValueError("DataFrame must contain 'avg_loc' column")
    
    filtered_df = df[df['avg_loc'] >= min_loc].copy()
    
    logger.info(
        f"Applied LOC threshold >= {min_loc}: "
        f"filtered {len(df) - len(filtered_df)} files "
        f"(from {len(df)} to {len(filtered_df)} rows)"
    )
    
    return filtered_df

def generate_parameterized_datasets(
    input_df: pd.DataFrame,
    thresholds: List[int] = [5, 10, 20]
) -> Dict[int, pd.DataFrame]:
    """
    Generate parameterized datasets for sensitivity analysis with different LOC thresholds.
    
    Args:
        input_df: DataFrame with raw metrics
        thresholds: List of LOC thresholds to apply
        
    Returns:
        Dictionary mapping threshold to filtered DataFrame
    """
    datasets = {}
    
    for threshold in thresholds:
        logger.info(f"Generating dataset for LOC threshold = {threshold}")
        filtered_df = apply_loc_threshold(input_df.copy(), threshold)
        datasets[threshold] = filtered_df
    
    return datasets

def save_datasets(
    datasets: Dict[int, pd.DataFrame],
    output_dir: Path,
    base_filename: str = "unified_metrics"
) -> List[Path]:
    """
    Save parameterized datasets to CSV files.
    
    Args:
        datasets: Dictionary of threshold -> DataFrame
        output_dir: Output directory path
        base_filename: Base name for output files
        
    Returns:
        List of output file paths
    """
    output_paths = []
    
    for threshold, df in datasets.items():
        filename = f"{base_filename}_loc_{threshold}.csv"
        output_path = output_dir / filename
        
        df.to_csv(output_path, index=False)
        output_paths.append(output_path)
        
        logger.info(f"Saved dataset (threshold={threshold}): {output_path} "
                    f"({len(df)} rows)")
    
    return output_paths

def validate_raw_metrics(df: pd.DataFrame) -> bool:
    """
    Validate that required raw metric columns exist and are non-null.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if validation passes
        
    Raises:
        ValueError if validation fails
    """
    required_columns = [
        'total_lines_changed',
        'debt_score',
        'avg_loc',
        'contributor_count'
    ]
    
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
        
        null_count = df[col].isna().sum()
        if null_count > 0:
            raise ValueError(
                f"Column '{col}' has {null_count} null values. "
                "All raw metrics must be non-null."
            )
        
        # Check for negative values where not expected
        if col in ['total_lines_changed', 'debt_score', 'avg_loc']:
            if (df[col] < 0).any():
                raise ValueError(
                    f"Column '{col}' contains negative values, which is unexpected."
                )
    
    logger.info("Raw metrics validation passed")
    return True

def run_preprocessing(
    input_path: Path,
    output_dir: Path,
    thresholds: List[int] = [5, 10, 20]
) -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline.
    
    Args:
        input_path: Path to input CSV with raw metrics
        output_dir: Directory to save output files
        thresholds: LOC thresholds for sensitivity analysis
        
    Returns:
        Dictionary with processing results
    """
    logger.info(f"Starting preprocessing from {input_path}")
    
    # Ensure output directory exists
    ensure_directories([output_dir])
    
    # Load input data
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Validate raw metrics
    validate_raw_metrics(df)
    
    # Step 1: Filter non-source files
    df_filtered = filter_non_source_files(df)
    
    # Step 2: Generate parameterized datasets
    datasets = generate_parameterized_datasets(df_filtered, thresholds)
    
    # Step 3: Save all datasets
    output_paths = save_datasets(datasets, output_dir)
    
    # Prepare results summary
    results = {
        'input_rows': len(df),
        'after_filter_rows': len(df_filtered),
        'datasets_generated': len(datasets),
        'thresholds': thresholds,
        'output_files': [str(p) for p in output_paths],
        'dataset_sizes': {k: len(v) for k, v in datasets.items()},
    }
    
    logger.info(f"Preprocessing complete. Results: {results}")
    return results

def main():
    """Main entry point for preprocessing script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Preprocess metrics data: filter files and generate sensitivity datasets'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/raw/static_analysis_metrics.csv'),
        help='Input CSV file with raw metrics'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('data/processed'),
        help='Output directory for processed datasets'
    )
    parser.add_argument(
        '--thresholds',
        type=int,
        nargs='+',
        default=[5, 10, 20],
        help='LOC thresholds for sensitivity analysis'
    )
    
    args = parser.parse_args()
    
    try:
        results = run_preprocessing(
            input_path=args.input,
            output_dir=args.output_dir,
            thresholds=args.thresholds
        )
        
        print("Preprocessing completed successfully!")
        print(f"Input rows: {results['input_rows']}")
        print(f"Filtered rows: {results['after_filter_rows']}")
        print(f"Datasets generated: {results['datasets_generated']}")
        print("Output files:")
        for f in results['output_files']:
            print(f"  - {f}")
            
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == '__main__':
    main()
