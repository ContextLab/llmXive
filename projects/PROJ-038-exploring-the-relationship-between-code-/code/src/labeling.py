"""
Labeling module for Defects4J bug prediction research.

This module implements the logic to cross-reference commit metadata with file paths
to assign binary bug labels (is_buggy) to Java files.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LabelingError(Exception):
    """Custom exception for labeling errors."""
    pass

def load_commit_metadata(commit_file_path: str) -> Dict[str, Any]:
    """
    Load commit metadata from a JSON file.
    
    Args:
        commit_file_path: Path to the JSON file containing commit metadata.
        
    Returns:
        Dictionary containing commit metadata with keys:
        - commit_hash: str
        - files: List[str] (paths of files changed in the commit)
        
    Raises:
        LabelingError: If the file cannot be read or parsed.
    """
    try:
        with open(commit_file_path, 'r') as f:
            metadata = json.load(f)
        
        # Validate required fields
        if 'commit_hash' not in metadata:
            raise LabelingError("Missing 'commit_hash' in commit metadata")
        if 'files' not in metadata:
            raise LabelingError("Missing 'files' in commit metadata")
        if not isinstance(metadata['files'], list):
            raise LabelingError("'files' must be a list of strings")
        
        logger.info(f"Loaded commit metadata for {metadata['commit_hash']} with {len(metadata['files'])} files")
        return metadata
        
    except FileNotFoundError:
        raise LabelingError(f"Commit metadata file not found: {commit_file_path}")
    except json.JSONDecodeError as e:
        raise LabelingError(f"Invalid JSON in commit metadata file: {e}")
    except Exception as e:
        raise LabelingError(f"Error loading commit metadata: {e}")

def build_file_to_commit_map(
    project_id: str,
    commit_metadata: Dict[str, Any],
    java_files: List[str]
) -> Dict[str, Tuple[str, bool]]:
    """
    Build a mapping from file path to (commit_hash, is_buggy) tuple.
    
    Args:
        project_id: The Defects4J project ID (e.g., 'Lang-1').
        commit_metadata: Dictionary containing commit_hash and files list.
        java_files: List of Java file paths in the project.
        
    Returns:
        Dictionary mapping file paths to (commit_hash, is_buggy) tuples.
        - is_buggy=True if the file was changed in the bug-introduction commit
        - is_buggy=False if the file was not changed
    """
    commit_hash = commit_metadata['commit_hash']
    changed_files = set(commit_metadata['files'])
    
    file_to_label_map = {}
    
    for file_path in java_files:
        # Normalize paths for comparison (handle potential differences in separators)
        normalized_file = file_path.replace('\\', '/')
        is_buggy = normalized_file in changed_files
        file_to_label_map[file_path] = (commit_hash, is_buggy)
    
    buggy_count = sum(1 for _, (_, is_buggy) in file_to_label_map.items() if is_buggy)
    logger.info(f"Built file-to-commit map for {project_id}: {buggy_count} buggy files out of {len(java_files)} total")
    
    return file_to_label_map

def label_file(
    file_path: str,
    commit_metadata: Dict[str, Any]
) -> Tuple[str, bool]:
    """
    Determine if a single file is buggy based on commit metadata.
    
    Args:
        file_path: Path to the Java file.
        commit_metadata: Dictionary containing commit_hash and files list.
        
    Returns:
        Tuple of (commit_hash, is_buggy)
    """
    commit_hash = commit_metadata['commit_hash']
    changed_files = set(commit_metadata['files'])
    
    normalized_file = file_path.replace('\\', '/')
    is_buggy = normalized_file in changed_files
    
    return commit_hash, is_buggy

def label_dataframe(
    df: pd.DataFrame,
    commit_metadata: Dict[str, Any],
    file_path_column: str = 'file_path'
) -> pd.DataFrame:
    """
    Add bug labels to a DataFrame of Java files.
    
    Args:
        df: DataFrame containing file paths (must have 'file_path' column or specified column).
        commit_metadata: Dictionary containing commit_hash and files list.
        file_path_column: Name of the column containing file paths.
        
    Returns:
        DataFrame with additional columns: 'commit_hash' and 'is_buggy'
        
    Raises:
        LabelingError: If required columns are missing.
    """
    if file_path_column not in df.columns:
        raise LabelingError(f"Column '{file_path_column}' not found in DataFrame. Available columns: {list(df.columns)}")
    
    # Create a copy to avoid modifying the original
    labeled_df = df.copy()
    
    # Apply labeling function to each row
    results = labeled_df[file_path_column].apply(
        lambda path: label_file(path, commit_metadata)
    )
    
    labeled_df['commit_hash'] = [r[0] for r in results]
    labeled_df['is_buggy'] = [r[1] for r in results]
    
    buggy_count = labeled_df['is_buggy'].sum()
    total_count = len(labeled_df)
    logger.info(f"Labeled {total_count} files: {buggy_count} buggy ({buggy_count/total_count*100:.2f}%)")
    
    return labeled_df

def merge_metrics_and_labels(
    metrics_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    on_column: str = 'file_path'
) -> pd.DataFrame:
    """
    Merge metrics DataFrame with labels DataFrame.
    
    Args:
        metrics_df: DataFrame containing computed metrics (CC, Halstead, LOC, etc.)
        labels_df: DataFrame containing bug labels (commit_hash, is_buggy)
        on_column: Column name to join on (default: 'file_path')
        
    Returns:
        Merged DataFrame with both metrics and labels
        
    Raises:
        LabelingError: If required columns are missing or merge fails.
    """
    required_columns = [on_column]
    
    for col in required_columns:
        if col not in metrics_df.columns:
            raise LabelingError(f"Required column '{col}' not found in metrics DataFrame")
        if col not in labels_df.columns:
            raise LabelingError(f"Required column '{col}' not found in labels DataFrame")
    
    try:
        merged_df = pd.merge(
            metrics_df,
            labels_df[['commit_hash', 'is_buggy', on_column]],
            on=on_column,
            how='inner'
        )
        
        logger.info(f"Merged {len(metrics_df)} metrics with {len(labels_df)} labels: {len(merged_df)} rows")
        
        return merged_df
        
    except Exception as e:
        raise LabelingError(f"Failed to merge metrics and labels: {e}")

def main():
    """
    Main function to demonstrate labeling workflow.
    
    This function:
    1. Loads commit metadata from a JSON file
    2. Reads a metrics CSV file
    3. Labels the files based on commit changes
    4. Merges metrics with labels
    5. Outputs the final labeled dataset
    """
    # Configuration - these would typically come from command line args or config
    commit_metadata_path = os.environ.get('COMMIT_METADATA_PATH', 'data/raw/commit_metadata.json')
    metrics_csv_path = os.environ.get('METRICS_CSV_PATH', 'data/processed/metrics.csv')
    output_csv_path = os.environ.get('OUTPUT_CSV_PATH', 'data/processed/features.csv')
    
    logger.info(f"Starting labeling process...")
    logger.info(f"Commit metadata: {commit_metadata_path}")
    logger.info(f"Metrics CSV: {metrics_csv_path}")
    logger.info(f"Output CSV: {output_csv_path}")
    
    # Load commit metadata
    try:
        commit_metadata = load_commit_metadata(commit_metadata_path)
    except LabelingError as e:
        logger.error(f"Failed to load commit metadata: {e}")
        return 1
    
    # Load metrics DataFrame
    try:
        metrics_df = pd.read_csv(metrics_csv_path)
        logger.info(f"Loaded metrics DataFrame with {len(metrics_df)} rows")
    except Exception as e:
        logger.error(f"Failed to load metrics CSV: {e}")
        return 1
    
    # Label the files
    try:
        labeled_df = label_dataframe(metrics_df, commit_metadata)
    except LabelingError as e:
        logger.error(f"Failed to label files: {e}")
        return 1
    
    # Merge with original metrics (if needed - label_dataframe already adds labels)
    # For this implementation, label_dataframe returns the full labeled DataFrame
    final_df = labeled_df
    
    # Ensure output directory exists
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the final labeled dataset
    try:
        final_df.to_csv(output_csv_path, index=False)
        logger.info(f"Saved labeled dataset to {output_csv_path}")
        
        # Print summary statistics
        print(f"\nLabeling Summary:")
        print(f"  Total files: {len(final_df)}")
        print(f"  Buggy files: {final_df['is_buggy'].sum()}")
        print(f"  Clean files: {len(final_df) - final_df['is_buggy'].sum()}")
        print(f"  Bug rate: {final_df['is_buggy'].mean()*100:.2f}%")
        
    except Exception as e:
        logger.error(f"Failed to save labeled dataset: {e}")
        return 1
    
    logger.info("Labeling process completed successfully")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())