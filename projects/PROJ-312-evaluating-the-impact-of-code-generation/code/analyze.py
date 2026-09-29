import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

import pandas as pd
import numpy as np
from scipy import stats

# Custom Exceptions defined in this module
class SampleSizeError(Exception):
    """Raised when sample size is insufficient for statistical analysis."""
    pass

class SignificanceError(Exception):
    """Raised when statistical significance thresholds are not met or logic fails."""
    pass

class DataQualityError(Exception):
    """Raised when data quality checks fail."""
    pass

# --- Data Loading Functions ---

def load_processed_data(filepath: str) -> pd.DataFrame:
    """
    Loads the processed PR turnaround data from a CSV file.
    Input: data/processed/pr_turnaround.csv (from T018b)
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    
    logging.info(f"Loading processed data from {filepath}")
    df = pd.read_csv(path)
    
    # Ensure turnaround_hours is numeric
    df['turnaround_hours'] = pd.to_numeric(df['turnaround_hours'], errors='coerce')
    df = df.dropna(subset=['turnaround_hours'])
    
    return df

def load_repos(filepath: str) -> List[Dict[str, Any]]:
    """
    Loads the list of repositories from the raw data file.
    Input: data/raw/repos.json (from T012a)
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Repo metadata file not found: {filepath}")
    
    logging.info(f"Loading repo metadata from {filepath}")
    with open(path, 'r') as f:
        data = json.load(f)
    
    return data

def filter_excluded_repos(df: pd.DataFrame, repos: List[Dict[str, Any]], excluded_repos_path: str) -> pd.DataFrame:
    """
    Filters the dataframe to exclude repositories listed in excluded_repos.txt.
    Input: data/processed/excluded_repos.txt (from T014)
    Fallback: If file is missing, assumes no exclusions and logs a warning.
    """
    excluded_set = set()
    excluded_path = Path(excluded_repos_path)
    
    if excluded_path.exists():
        logging.info(f"Loading excluded repositories from {excluded_repos_path}")
        with open(excluded_path, 'r') as f:
            for line in f:
                repo_name = line.strip()
                if repo_name:
                    excluded_set.add(repo_name)
    else:
        logging.warning(f"Excluded repos file not found at {excluded_repos_path}. Assuming no exclusions.")
    
    if not excluded_set:
        return df
    
    logging.info(f"Filtering out {len(excluded_set)} repositories.")
    # Filter rows where repo_name is NOT in the excluded set
    filtered_df = df[~df['repo_name'].isin(excluded_set)]
    
    original_count = len(df)
    new_count = len(filtered_df)
    logging.info(f"Filtered {original_count - new_count} rows based on excluded repos.")
    
    return filtered_df

# --- Statistical Calculation Functions ---

def calculate_medians(values: List[float]) -> Dict[str, float]:
    """
    Calculates the median of a list of values.
    """
    if not values:
        return {'median': None}
    return {'median': float(np.median(values))}

def calculate_descriptive_statistics(values: List[float], label: str) -> Dict[str, Any]:
    """
    Calculates descriptive statistics for a group of values.
    Returns: Dict containing mean, median, std (SD), quartiles (Q1, Q2, Q3), count.
    """
    if not values:
        return {
            'label': label,
            'count': 0,
            'mean': None,
            'median': None,
            'std': None,
            'q1': None,
            'q2': None,
            'q3': None
        }
    
    arr = np.array(values)
    return {
        'label': label,
        'count': int(len(arr)),
        'mean': float(np.mean(arr)),
        'median': float(np.median(arr)),
        'std': float(np.std(arr, ddof=1)), # Sample standard deviation
        'q1': float(np.percentile(arr, 25)),
        'q2': float(np.percentile(arr, 50)), # Median
        'q3': float(np.percentile(arr, 75))
    }

def save_descriptive_statistics(stats: Dict[str, Any], filepath: str) -> None:
    """
    Saves the descriptive statistics to a JSON file.
    Output: data/processed/descriptive_statistics.json
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"Saving descriptive statistics to {filepath}")
    with open(path, 'w') as f:
        json.dump(stats, f, indent=2)

# --- Main Execution Logic ---

def main():
    """
    Main entry point for T023a: Calculate descriptive statistics.
    1. Load processed data (pr_turnaround.csv).
    2. Load repos and excluded repos list.
    3. Filter out excluded repos.
    4. Split data into AI and Non-AI groups.
    5. Calculate descriptive stats (mean, median, SD, quartiles).
    6. Save results to JSON.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/pipeline.log')
        ]
    )
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / 'data' / 'processed'
    
    input_csv = data_dir / 'pr_turnaround.csv'
    excluded_repos_file = data_dir / 'excluded_repos.txt'
    repos_file = project_root / 'data' / 'raw' / 'repos.json'
    output_json = data_dir / 'descriptive_statistics.json'
    
    try:
        # 1. Load Processed Data
        df = load_processed_data(str(input_csv))
        logging.info(f"Loaded {len(df)} PR records.")
        
        # 2. Load Repos and Filter Excluded
        if repos_file.exists():
            repos = load_repos(str(repos_file))
        else:
            repos = []
            logging.warning(f"Repo file {repos_file} not found, skipping exclusion filter based on repo list.")
        
        filtered_df = filter_excluded_repos(df, repos, str(excluded_repos_file))
        
        # 3. Split into AI and Non-AI groups
        # Assuming column 'is_ai_assisted' exists (created in T015/T018b)
        if 'is_ai_assisted' not in filtered_df.columns:
            raise KeyError("Column 'is_ai_assisted' not found in processed data. Check T015 implementation.")
        
        ai_group = filtered_df[filtered_df['is_ai_assisted'] == 1]['turnaround_hours'].tolist()
        non_ai_group = filtered_df[filtered_df['is_ai_assisted'] == 0]['turnaround_hours'].tolist()
        
        logging.info(f"AI Group size: {len(ai_group)}")
        logging.info(f"Non-AI Group size: {len(non_ai_group)}")
        
        if len(ai_group) == 0 and len(non_ai_group) == 0:
            raise DataQualityError("No valid data found after filtering. Check input data and exclusion logic.")
        
        # 4. Calculate Descriptive Statistics
        stats_ai = calculate_descriptive_statistics(ai_group, "AI-Assisted")
        stats_non_ai = calculate_descriptive_statistics(non_ai_group, "Non-AI")
        
        result = {
            "analysis_type": "descriptive_statistics",
            "groups": {
                "ai": stats_ai,
                "non_ai": stats_non_ai
            }
        }
        
        # 5. Save Results
        save_descriptive_statistics(result, str(output_json))
        logging.info("Descriptive statistics calculation completed successfully.")
        
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        sys.exit(1)
    except KeyError as e:
        logging.error(f"Data structure error: {e}")
        sys.exit(1)
    except DataQualityError as e:
        logging.error(f"Data quality issue: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error during analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()