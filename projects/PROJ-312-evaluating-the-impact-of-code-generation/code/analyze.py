import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

import pandas as pd
import numpy as np

# Import from utils if needed (MIN_PR_THRESHOLD is there, though not used directly here)
# from utils import MIN_PR_THRESHOLD 

def setup_logging():
    """Configure logging for the analysis pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/pipeline.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

class SampleSizeError(Exception):
    """Raised when sample size is insufficient for statistical testing."""
    pass

class SignificanceError(Exception):
    """Raised when results are not statistically significant (if required)."""
    pass

class DataQualityError(Exception):
    """Raised when data quality thresholds are not met."""
    pass

def load_excluded_repos(excluded_path: str) -> List[str]:
    """Load list of excluded repository names from file."""
    if not os.path.exists(excluded_path):
        logging.getLogger(__name__).warning(f"Excluded repos file not found: {excluded_path}. Assuming no exclusions.")
        return []
    with open(excluded_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def filter_excluded_repos(df: pd.DataFrame, excluded_repos: List[str]) -> pd.DataFrame:
    """Remove rows belonging to excluded repositories."""
    if not excluded_repos:
        return df
    return df[~df['repo_name'].isin(excluded_repos)]

def load_processed_data(csv_path: str) -> pd.DataFrame:
    """Load the processed PR turnaround data."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Processed data file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    # Ensure turnaround_hours is numeric
    df['turnaround_hours'] = pd.to_numeric(df['turnaround_hours'], errors='coerce')
    # Drop rows with NaN turnaround_hours if any
    df = df.dropna(subset=['turnaround_hours'])
    return df

def load_repos(repos_path: str) -> List[Dict[str, Any]]:
    """Load repository metadata."""
    if not os.path.exists(repos_path):
        raise FileNotFoundError(f"Repos file not found: {repos_path}")
    with open(repos_path, 'r') as f:
        return json.load(f)

def calculate_medians(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate median stars and contributors from repo metadata if available."""
    # This function is a placeholder if metadata is loaded separately.
    # T017 saves this to repo_metadata.json, so we might load it there.
    # For now, returning empty dict or loading from file if path provided.
    return {}

def calculate_descriptive_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate descriptive stats for AI and non-AI groups."""
    stats = {}
    for group, name in [(df[df['is_ai_assisted'] == True], 'AI'), (df[df['is_ai_assisted'] == False], 'Non-AI')]:
        if len(group) == 0:
            stats[name] = {'count': 0, 'mean': None, 'median': None, 'std': None, 'q1': None, 'q3': None}
            continue
        stats[name] = {
            'count': int(len(group)),
            'mean': float(group['turnaround_hours'].mean()),
            'median': float(group['turnaround_hours'].median()),
            'std': float(group['turnaround_hours'].std()),
            'q1': float(group['turnaround_hours'].quantile(0.25)),
            'q3': float(group['turnaround_hours'].quantile(0.75))
        }
    return stats

def save_descriptive_statistics(stats: Dict[str, Any], output_path: str):
    """Save descriptive statistics to JSON."""
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)

def calculate_iqr_outliers(df: pd.DataFrame, group_col: str = 'is_ai_assisted', value_col: str = 'turnaround_hours') -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, int]]:
    """
    Calculate IQR outliers and separate clean vs full datasets.
    
    Returns:
      cleaned_df: DataFrame with outliers removed.
      full_df: Original DataFrame (for archival).
      outlier_counts: Dict with counts of outliers per group.
    """
    logger = logging.getLogger(__name__)
    full_df = df.copy()
    outlier_counts = {'AI': 0, 'Non-AI': 0}
    
    # Identify outliers per group
    mask_clean = pd.Series([True] * len(df), index=df.index)
    
    for is_ai, group_name in [(True, 'AI'), (False, 'Non-AI')]:
        group_data = df[df[group_col] == is_ai][value_col]
        
        if len(group_data) == 0:
            logger.info(f"No data found for {group_name} group. Skipping outlier calculation.")
            continue
        
        q1 = group_data.quantile(0.25)
        q3 = group_data.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Identify indices of outliers in this group
        outliers = group_data[(group_data < lower_bound) | (group_data > upper_bound)]
        outlier_indices = outliers.index
        
        count = len(outlier_indices)
        outlier_counts[group_name] = count
        logger.info(f"Found {count} outliers in {group_name} group (Q1={q1:.2f}, Q3={q3:.2f}, IQR={iqr:.2f}, Bounds=[{lower_bound:.2f}, {upper_bound:.2f}])")
        
        # Update mask to exclude these indices
        mask_clean.loc[outlier_indices] = False
    
    cleaned_df = full_df[mask_clean].reset_index(drop=True)
    
    logger.info(f"Total outliers removed: {sum(outlier_counts.values())}")
    logger.info(f"Cleaned dataset size: {len(cleaned_df)}")
    
    return cleaned_df, full_df, outlier_counts

def verify_outliers(df: pd.DataFrame, group_col: str = 'is_ai_assisted', value_col: str = 'turnaround_hours') -> bool:
    """Verify that no outliers remain in the dataframe."""
    for is_ai in [True, False]:
        group_data = df[df[group_col] == is_ai][value_col]
        if len(group_data) == 0:
            continue
        q1 = group_data.quantile(0.25)
        q3 = group_data.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = group_data[(group_data < lower_bound) | (group_data > upper_bound)]
        if len(outliers) > 0:
            logging.getLogger(__name__).error(f"Verification failed: {len(outliers)} outliers remain in {'AI' if is_ai else 'Non-AI'} group.")
            return False
    return True

def main():
    """Main execution for T024: IQR Outlier Calculation."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Paths
    project_root = Path(__file__).parent.parent
    input_csv = project_root / 'data' / 'processed' / 'pr_turnaround.csv'
    output_cleaned = project_root / 'data' / 'processed' / 'pr_turnaround_cleaned.csv'
    output_full = project_root / 'data' / 'processed' / 'pr_turnaround_full.csv'
    excluded_repos_file = project_root / 'data' / 'processed' / 'excluded_repos.txt'
    
    # 1. Load excluded repos
    excluded_repos = load_excluded_repos(str(excluded_repos_file))
    
    # 2. Load processed data
    try:
        df = load_processed_data(str(input_csv))
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed: {e}")
        sys.exit(1)
    
    # 3. Filter excluded repos
    df_filtered = filter_excluded_repos(df, excluded_repos)
    logger.info(f"Loaded {len(df)} rows, filtered to {len(df_filtered)} rows after excluding {len(excluded_repos)} repos.")
    
    if len(df_filtered) == 0:
        logger.error("No data remaining after filtering. Aborting.")
        sys.exit(1)
    
    # 4. Calculate IQR outliers and split data
    cleaned_df, full_df, outlier_counts = calculate_iqr_outliers(df_filtered)
    
    # 5. Save outputs
    cleaned_df.to_csv(output_cleaned, index=False)
    logger.info(f"Saved cleaned data (outliers removed) to {output_cleaned}")
    
    full_df.to_csv(output_full, index=False)
    logger.info(f"Saved full dataset (archival) to {output_full}")
    
    # 6. Verify no outliers remain in cleaned data
    if verify_outliers(cleaned_df):
        logger.info("Verification passed: No outliers remain in cleaned dataset.")
    else:
        logger.error("Verification failed: Outliers detected in cleaned dataset.")
        sys.exit(1)
    
    # 7. Save outlier counts for potential logging/reporting
    outlier_log = {
        'ai_outliers': outlier_counts['AI'],
        'non_ai_outliers': outlier_counts['Non-AI'],
        'total_removed': sum(outlier_counts.values()),
        'final_count': len(cleaned_df)
    }
    with open(project_root / 'data' / 'processed' / 'outlier_summary.json', 'w') as f:
        json.dump(outlier_log, f, indent=2)
        
    logger.info("T024 completed successfully.")

if __name__ == '__main__':
    main()
