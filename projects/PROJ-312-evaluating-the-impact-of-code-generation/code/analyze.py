import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np
from scipy import stats

# Custom exceptions (defined locally or imported from utils if preferred,
# but keeping them here for self-containment as per existing API surface)
class SampleSizeError(Exception):
    pass

class SignificanceError(Exception):
    pass

class DataQualityError(Exception):
    pass

def load_processed_data(file_path: str) -> pd.DataFrame:
    """Load the processed PR turnaround data."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {file_path}")
    return pd.read_csv(path)

def load_repos(file_path: str) -> List[str]:
    """Load repository names from a text file (one per line)."""
    path = Path(file_path)
    if not path.exists():
        return []
    with open(path, 'r') as f:
        # Filter out empty lines
        return [line.strip() for line in f if line.strip()]

def filter_excluded_repos(df: pd.DataFrame, excluded_repos: List[str]) -> pd.DataFrame:
    """Filter the dataframe to exclude rows where repo_name is in the excluded list."""
    if not excluded_repos:
        return df
    return df[~df['repo_name'].isin(excluded_repos)]

def calculate_medians(df: pd.DataFrame, group_col: str = 'is_ai_assisted', value_col: str = 'turnaround_hours') -> Dict[str, float]:
    """Calculate median turnaround hours for AI and Non-AI groups."""
    if group_col not in df.columns or value_col not in df.columns:
        raise ValueError(f"Columns '{group_col}' or '{value_col}' not found in dataframe.")
    
    results = {}
    for val in df[group_col].unique():
        group_data = df[df[group_col] == val][value_col]
        if len(group_data) > 0:
            results[int(val)] = float(group_data.median())
        else:
            results[int(val)] = float(np.nan)
    return results

def calculate_descriptive_statistics(df: pd.DataFrame, group_col: str = 'is_ai_assisted', value_col: str = 'turnaround_hours') -> Dict[str, Dict[str, float]]:
    """
    Calculate descriptive statistics (mean, median, SD, quartiles) for AI and non-AI groups.
    
    Args:
        df: The dataframe containing the data.
        group_col: The column name indicating the group (AI vs Non-AI).
        value_col: The column name containing the values to analyze.
    
    Returns:
        A dictionary with keys 'AI' and 'Non-AI' (or 1 and 0) containing stats.
    """
    stats_dict = {}
    
    # Ensure numeric types
    df = df.copy()
    df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
    
    # Define group labels
    ai_label = 1
    non_ai_label = 0
    
    for label, name in [(ai_label, 'AI'), (non_ai_label, 'Non-AI')]:
        group_data = df[df[group_col] == label][value_col].dropna()
        
        if len(group_data) == 0:
            stats_dict[name] = {
                "count": 0,
                "mean": None,
                "median": None,
                "std": None,
                "q1": None,
                "q2": None,
                "q3": None
            }
            continue

        stats_dict[name] = {
            "count": int(len(group_data)),
            "mean": float(group_data.mean()),
            "median": float(group_data.median()),
            "std": float(group_data.std()),
            "q1": float(group_data.quantile(0.25)),
            "q2": float(group_data.quantile(0.50)),
            "q3": float(group_data.quantile(0.75))
        }
    
    return stats_dict

def save_descriptive_statistics(stats: Dict[str, Dict[str, float]], output_path: str):
    """Save descriptive statistics to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(stats, f, indent=2)

def main():
    """
    Main entry point for T023a: Calculate descriptive statistics.
    
    Prerequisites:
    - data/processed/pr_turnaround.csv (from T018b)
    - data/processed/excluded_repos.txt (from T014)
    
    Outputs:
    - data/processed/distribution_stats.json (Descriptive stats)
    - Note: Distribution characteristics (skewness, kurtosis, Shapiro-Wilk)
      are handled in T023c, but we ensure the structure here if needed.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    # Paths
    project_root = Path(__file__).resolve().parents[1]
    processed_data_path = project_root / "data" / "processed" / "pr_turnaround.csv"
    excluded_repos_path = project_root / "data" / "processed" / "excluded_repos.txt"
    output_stats_path = project_root / "data" / "processed" / "descriptive_stats.json"
    
    logger.info("Starting descriptive statistics calculation (T023a)...")
    
    # Load excluded repos
    try:
        excluded_repos = load_repos(str(excluded_repos_path))
        logger.info(f"Loaded {len(excluded_repos)} excluded repositories.")
    except FileNotFoundError:
        logger.warning(f"Excluded repos file not found: {excluded_repos_path}. Proceeding without exclusion.")
        excluded_repos = []
    
    # Load processed data
    try:
        df = load_processed_data(str(processed_data_path))
        logger.info(f"Loaded {len(df)} records from {processed_data_path}.")
    except FileNotFoundError:
        logger.error(f"Processed data file not found: {processed_data_path}.")
        sys.exit(1)
    
    # Filter excluded repos
    df_filtered = filter_excluded_repos(df, excluded_repos)
    logger.info(f"Filtered data: {len(df_filtered)} records remaining after excluding {len(excluded_repos)} repos.")
    
    if len(df_filtered) == 0:
        logger.error("No data remaining after filtering. Cannot calculate statistics.")
        sys.exit(1)
    
    # Calculate Descriptive Statistics
    desc_stats = calculate_descriptive_statistics(df_filtered, group_col='is_ai_assisted', value_col='turnaround_hours')
    
    logger.info(f"Calculated descriptive statistics for {len(desc_stats)} groups.")
    for group, stats in desc_stats.items():
        logger.info(f"Group {group}: Count={stats['count']}, Median={stats['median']}")
    
    # Save results
    save_descriptive_statistics(desc_stats, str(output_stats_path))
    logger.info(f"Descriptive statistics saved to {output_stats_path}")
    
    return desc_stats

if __name__ == "__main__":
    main()