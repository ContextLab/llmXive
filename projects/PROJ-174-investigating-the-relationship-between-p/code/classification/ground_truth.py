import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

# Add project root to path if running as script
if __name__ == "__main__" and "code" not in sys.path:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from config import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('code/logs/ground_truth.log')
    ]
)
logger = logging.getLogger(__name__)

def load_search_time_data(file_path: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Load search time data from the processed dataset.
    """
    if file_path is None:
        config = load_config()
        file_path = config.get('paths', {}).get('processed_data', 'data/processed/processed_data.csv')
    
    if not os.path.exists(file_path):
        logger.error(f"Search time data not found at {file_path}")
        return None
    
    try:
        df = pd.read_csv(file_path)
        if 'search_time' not in df.columns:
            logger.error("Search time data missing 'search_time' column.")
            return None
        logger.info(f"Loaded search time data from {file_path}: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load search time data: {e}")
        return None

def label_by_median_split(df: pd.DataFrame, target_col: str = 'search_time') -> pd.DataFrame:
    """
    Label data by median split of the target column.
    Returns a copy of the dataframe with a new 'ground_truth_label' column.
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    median_val = df[target_col].median()
    df_labeled = df.copy()
    df_labeled['ground_truth_label'] = (df_labeled[target_col] >= median_val).astype(int)
    
    logger.info(f"Labeled {len(df_labeled)} rows by median split (median={median_val:.4f})")
    return df_labeled

def save_labeled_data(df: pd.DataFrame, output_path: str = "data/processed/labeled_data.csv") -> bool:
    """
    Save the labeled dataframe to disk.
    """
    if df is None or df.empty:
        logger.error("Cannot save empty DataFrame.")
        return False
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Labeled data saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save labeled data: {e}")
        return False

def write_limitations_note(output_path: str = "results/limitations.md") -> bool:
    """
    Write a limitations note to results/limitations.md.
    """
    note_content = """# Limitations of Ground Truth

## Ground Truth Derivation
The ground truth labels for this study are derived from a **median split of search time**.
This is a relative measure and does not represent an absolute cognitive load metric.

## Implications
- **Predictive Validity**: Claims of predictive validity for absolute cognitive load are **removed**.
- **Interpretation**: Results should be interpreted as "Search-Time Estimation" rather than absolute cognitive load classification.
- **Stability**: The classification stability depends on the distribution of search times in the dataset.

## Caveat for Sensitivity Analysis
Any sensitivity analysis performed on these labels should be understood in the context of this relative measure.
"""
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'w') as f:
            f.write(note_content)
        logger.info(f"Limitations note written to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write limitations note: {e}")
        return False

def update_classification_metrics(metrics_df: pd.DataFrame, status: str = "UNVALIDATED") -> pd.DataFrame:
    """
    Update the classification metrics dataframe to set the status column.
    """
    if metrics_df is None or metrics_df.empty:
        return pd.DataFrame()
    
    df = metrics_df.copy()
    df['status'] = status
    logger.info(f"Updated classification metrics status to: {status}")
    return df

def main():
    """
    Main function to run the ground truth labeling pipeline.
    """
    logger.info("Starting Ground Truth Labeling Pipeline")
    
    # Load data
    df = load_search_time_data()
    if df is None:
        logger.error("Failed to load search time data. Aborting.")
        return False
    
    # Label by median split
    df_labeled = label_by_median_split(df)
    
    # Save labeled data
    if not save_labeled_data(df_labeled):
        logger.error("Failed to save labeled data. Aborting.")
        return False
    
    # Write limitations note
    write_limitations_note()
    
    # Update metrics if they exist (optional, called by evaluate.py)
    metrics_path = Path("results/classification_metrics.csv")
    if metrics_path.exists():
        try:
            metrics_df = pd.read_csv(metrics_path)
            metrics_df = update_classification_metrics(metrics_df, status="UNVALIDATED")
            metrics_df.to_csv(metrics_path, index=False)
            logger.info("Updated existing classification metrics with UNVALIDATED status.")
        except Exception as e:
            logger.warning(f"Could not update existing metrics: {e}")
    
    logger.info("Ground Truth Labeling Pipeline completed successfully.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)