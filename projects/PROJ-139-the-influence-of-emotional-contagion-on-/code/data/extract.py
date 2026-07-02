import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from code.utils.logging_config import get_logger

# Ensure the logger is configured before use
logger = get_logger("extract")

def load_downloaded_data(data_dir: Path) -> pd.DataFrame:
    """
    Load the combined raw data from the downloaded JSON files.
    Expects files in data_dir/raw/ matching *.json or a specific merged file.
    """
    # Check for the standard merged file first, or glob for raw files
    merged_path = data_dir / "raw" / "merged_reddit_data.json"
    if merged_path.exists():
        logger.info(f"Loading merged data from {merged_path}")
        with open(merged_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        # Fallback to globbing if merged file doesn't exist yet (e.g. during dev)
        raw_dir = data_dir / "raw"
        if not raw_dir.exists():
            logger.warning(f"Raw data directory {raw_dir} does not exist.")
            return pd.DataFrame()
        
        json_files = list(raw_dir.glob("*.json"))
        if not json_files:
            logger.warning(f"No JSON files found in {raw_dir}")
            return pd.DataFrame()

        all_records = []
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_records.extend(data)
                    elif isinstance(data, dict):
                        all_records.append(data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON in {file_path}: {e}")
        
        data = all_records

    df = pd.DataFrame(data)
    
    # Standardize column names if they vary slightly
    # Expected: post_id, author, timestamp, body, subreddit, thread_id, etc.
    # Normalize 'created_utc' to 'timestamp' if present
    if 'created_utc' in df.columns and 'timestamp' not in df.columns:
        df['timestamp'] = df['created_utc']
    
    return df

def extract_seed_posts(df: pd.DataFrame, n_seeds: int = 3) -> pd.DataFrame:
    """
    Identify threads with decision points and extract the first N=3 top-level posts as seed posts.
    Flags threads with <3 top-level posts with reason code SEED_INSUFFICIENT.
    
    Args:
        df: DataFrame containing raw thread data.
        n_seeds: Number of seed posts to extract per thread (default 3).
        
    Returns:
        DataFrame of extracted seed posts.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty result.")
        return pd.DataFrame()

    # Ensure we have a thread identifier
    if 'thread_id' not in df.columns:
        logger.error("Input DataFrame missing 'thread_id' column.")
        return pd.DataFrame()

    seed_posts = []
    excluded_threads = []

    # Group by thread_id
    for thread_id, group in df.groupby('thread_id'):
        # Sort by timestamp to get chronological order
        # Fallback to index if timestamp missing or NaT
        if 'timestamp' in group.columns:
            sorted_group = group.sort_values('timestamp')
        else:
            sorted_group = group

        # Filter for top-level posts (parent_id is None or null or thread_id itself depending on schema)
        # Assuming 'parent_id' column exists. If not, we might need to infer from 'depth' or similar.
        # Common Reddit schema: parent_id is null for top-level, or equals thread_id.
        top_level_mask = group['parent_id'].isna() | (group['parent_id'] == thread_id)
        
        top_level_posts = sorted_group[top_level_mask].head(n_seeds)

        if len(top_level_posts) < n_seeds:
            excluded_threads.append({
                'thread_id': thread_id,
                'reason': 'SEED_INSUFFICIENT',
                'available_seeds': len(top_level_posts)
            })
            # Log the exclusion
            logger.debug(f"Thread {thread_id} excluded: SEED_INSUFFICIENT (found {len(top_level_posts)})")
        else:
            # Select the first N posts
            selected_posts = top_level_posts.head(n_seeds)
            seed_posts.append(selected_posts)

    if seed_posts:
        result_df = pd.concat(seed_posts, ignore_index=True)
    else:
        result_df = pd.DataFrame()

    # Log exclusions if any
    if excluded_threads:
        exclusions_df = pd.DataFrame(excluded_threads)
        exclusions_path = Path("data/processed/exclusions.log")
        exclusions_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to log file as JSON lines or simple text
        with open(exclusions_path, 'a', encoding='utf-8') as f:
            for exc in excluded_threads:
                f.write(json.dumps(exc) + "\n")
        
        logger.info(f"Logged {len(excluded_threads)} excluded threads to {exclusions_path}")

    return result_df

def validate_metadata_completeness(df: pd.DataFrame, required_fields: List[str] = None, threshold: float = 0.95) -> Dict[str, Any]:
    """
    Validates that metadata (timestamp, author, comment ID) is complete for >= 95% of extracted threads.
    
    Args:
        df: DataFrame of extracted posts.
        required_fields: List of field names that must be present and non-null. Defaults to ['post_id', 'author', 'timestamp'].
        threshold: Minimum required completeness ratio (default 0.95).
        
    Returns:
        Dictionary with validation results:
            - 'passed': bool
            - 'completeness': dict mapping field to ratio
            - 'missing_count': int
            - 'total_count': int
            - 'details': list of rows with missing data (if any)
    """
    if df.empty:
        logger.warning("Input DataFrame is empty for validation.")
        return {
            'passed': False,
            'completeness': {},
            'missing_count': 0,
            'total_count': 0,
            'details': []
        }

    if required_fields is None:
        required_fields = ['post_id', 'author', 'timestamp']

    # Check which required fields actually exist in the dataframe
    existing_fields = [f for f in required_fields if f in df.columns]
    missing_schema_fields = [f for f in required_fields if f not in df.columns]

    if missing_schema_fields:
        logger.error(f"Required fields missing from schema: {missing_schema_fields}")
        return {
            'passed': False,
            'completeness': {f: 0.0 for f in required_fields},
            'missing_count': len(df),
            'total_count': len(df),
            'details': [],
            'error': f"Missing schema fields: {missing_schema_fields}"
        }

    total_rows = len(df)
    completeness = {}
    missing_rows_mask = pd.Series([False] * total_rows)

    for field in existing_fields:
        # Count non-null and non-empty strings
        non_null = df[field].notna()
        non_empty = df[field].astype(str).str.strip() != ""
        valid = non_null & non_empty
        completeness[field] = valid.sum() / total_rows if total_rows > 0 else 0.0
        
        # Track rows missing this specific field
        missing_rows_mask = missing_rows_mask | (~valid)

    missing_count = missing_rows_mask.sum()
    overall_completeness = (total_rows - missing_count) / total_rows if total_rows > 0 else 0.0

    passed = overall_completeness >= threshold

    # Collect details of missing rows for logging
    missing_details = []
    if missing_count > 0:
        missing_df = df[missing_rows_mask]
        # Limit details to first 10 for the report
        for idx, row in missing_df.head(10).iterrows():
            missing_details.append({
                'index': idx,
                'missing_fields': [f for f in existing_fields if not (row[f] is not None and str(row[f]).strip() != "")]
            })

    result = {
        'passed': passed,
        'completeness': completeness,
        'missing_count': missing_count,
        'total_count': total_rows,
        'overall_completeness': overall_completeness,
        'details': missing_details
    }

    logger.info(f"Metadata Validation: {overall_completeness:.2%} complete (Threshold: {threshold:.0%}). Passed: {passed}")
    if not passed:
        logger.warning(f"Validation FAILED. Missing metadata in {missing_count} rows.")

    return result

def run_extraction(data_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Orchestrates the extraction pipeline:
    1. Load raw data.
    2. Extract seed posts.
    3. Validate metadata completeness.
    
    Args:
        data_dir: Path to the raw data directory.
        output_dir: Path to save processed outputs.
        
    Returns:
        Dictionary with extraction results and validation status.
    """
    logger.info("Starting extraction pipeline...")
    
    # 1. Load Data
    raw_df = load_downloaded_data(data_dir)
    if raw_df.empty:
        logger.error("No data loaded. Aborting extraction.")
        return {'status': 'failed', 'reason': 'No data loaded'}

    # 2. Extract Seed Posts
    seed_df = extract_seed_posts(raw_df)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    seeds_path = output_dir / "seed_posts.csv"
    if not seed_df.empty:
        seed_df.to_csv(seeds_path, index=False)
        logger.info(f"Saved {len(seed_df)} seed posts to {seeds_path}")
    else:
        logger.warning("No seed posts extracted.")

    # 3. Validate Metadata
    validation_result = validate_metadata_completeness(seed_df)

    # Save validation report
    report_path = output_dir / "validation_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(validation_result, f, indent=2, default=str)
    
    logger.info(f"Validation report saved to {report_path}")

    return {
        'status': 'success' if validation_result['passed'] else 'warning',
        'seed_count': len(seed_df),
        'validation': validation_result,
        'output_path': str(seeds_path)
    }

def main():
    """
    Entry point for the extraction script.
    Expects data to be in data/raw/ and outputs to data/processed/.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"
    output_dir = data_dir / "processed"
    
    result = run_extraction(data_dir, output_dir)
    
    if result['status'] == 'failed':
        logger.error("Extraction failed.")
        exit(1)
    elif result['status'] == 'warning':
        logger.warning("Extraction completed with validation warnings.")
        exit(0) # Still exit 0 as the code ran, but validation failed
    else:
        logger.info("Extraction completed successfully.")
        exit(0)

if __name__ == "__main__":
    main()