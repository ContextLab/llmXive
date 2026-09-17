import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import pyarrow.parquet as pq

# Project imports based on API surface
from utils.config import get_config, ensure_directories
from utils.validators import validate_schema, scan_dataset_for_pii

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_cohort_data(input_path: str) -> pd.DataFrame:
    """
    Loads the classified snippets dataset from Parquet.
    Expects 'author_type' column containing 'human' or 'llm-like'.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading cohort data from {input_path}")
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        logger.error(f"Failed to read parquet file: {e}")
        raise
    
    if 'author_type' not in df.columns:
        raise ValueError(f"Input DataFrame missing required column 'author_type'. Columns: {df.columns.tolist()}")
    
    logger.info(f"Loaded {len(df)} snippets. Value counts:\n{df['author_type'].value_counts()}")
    return df

def segment_cohorts(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Segments the input DataFrame into three cohorts:
    1. LLM-like (author_type == 'llm-like')
    2. Human (author_type == 'human')
    3. All (full dataset with an added 'cohort_label' column for convenience)
    
    Returns:
        Tuple of (llm_like_df, human_df, all_df_with_label)
    """
    logger.info("Segmenting cohorts based on 'author_type'")
    
    llm_like_df = df[df['author_type'] == 'llm-like'].copy()
    human_df = df[df['author_type'] == 'human'].copy()
    
    if llm_like_df.empty:
        logger.warning("No 'llm-like' snippets found in the dataset.")
    if human_df.empty:
        logger.warning("No 'human' snippets found in the dataset.")
    
    # Create a unified dataframe with explicit cohort labels for downstream analysis
    df['cohort_label'] = df['author_type']
    
    return llm_like_df, human_df, df

def analyze_cohort_properties(llm_like_df: pd.DataFrame, human_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Performs descriptive statistical analysis on the segmented cohorts.
    Calculates mean and std for numeric features (e.g., complexity, file_size)
    to compare stylistic properties as required by US4.
    
    Returns:
        Dictionary containing summary statistics for both cohorts.
    """
    logger.info("Analyzing cohort properties (descriptive statistics)")
    
    numeric_cols = ['complexity_score', 'file_size', 'review_duration']
    # Filter to only existing columns
    existing_numeric_cols = [c for c in numeric_cols if c in llm_like_df.columns]
    
    stats = {
        "llm-like": {},
        "human": {},
        "comparison": {}
    }
    
    if not existing_numeric_cols:
        logger.warning(f"No standard numeric columns {numeric_cols} found for comparison.")
        return stats

    for col in existing_numeric_cols:
        llm_stats = llm_like_df[col].describe()
        human_stats = human_df[col].describe()
        
        stats["llm-like"][col] = {
            "mean": float(llm_stats['mean']) if not pd.isna(llm_stats['mean']) else None,
            "std": float(llm_stats['std']) if not pd.isna(llm_stats['std']) else None,
            "count": int(llm_stats['count'])
        }
        
        stats["human"][col] = {
            "mean": float(human_stats['mean']) if not pd.isna(human_stats['mean']) else None,
            "std": float(human_stats['std']) if not pd.isna(human_stats['std']) else None,
            "count": int(human_stats['count'])
        }
        
        # Simple difference in means
        if not pd.isna(llm_stats['mean']) and not pd.isna(human_stats['mean']):
            diff = float(llm_stats['mean']) - float(human_stats['mean'])
            stats["comparison"][col] = {
                "mean_difference": diff,
                "direction": "llm-higher" if diff > 0 else "human-higher" if diff < 0 else "equal"
            }
    
    logger.info(f"Analysis complete. Found {len(existing_numeric_cols)} numeric features to compare.")
    return stats

def run_cohort_segmentation(
    input_path: str = "data/processed/classified_snippets.parquet",
    output_path: str = "data/processed/cohort_segments.parquet"
) -> str:
    """
    Main entry point for the cohort analysis pipeline.
    1. Loads data.
    2. Segments into LLM-like and Human cohorts.
    3. Writes the combined segmented dataframe to Parquet with 'cohort_label'.
    4. Logs descriptive statistics.
    
    Args:
        input_path: Path to the classified snippets parquet file.
        output_path: Path where the segmented parquet file will be saved.
        
    Returns:
        Path to the generated output file.
    """
    config = get_config()
    ensure_directories([output_path])
    
    try:
        # Load
        df = load_cohort_data(input_path)
        
        # Segment
        llm_df, human_df, segmented_df = segment_cohorts(df)
        
        # Analyze (Descriptive)
        stats = analyze_cohort_properties(llm_df, human_df)
        logger.info(f"Cohort Statistics:\n{stats}")
        
        # Write Output
        output_file = Path(output_path)
        segmented_df.to_parquet(output_file, index=False)
        
        logger.info(f"Successfully wrote segmented cohorts to {output_file}")
        return str(output_file)
        
    except Exception as e:
        logger.error(f"Cohort segmentation failed: {e}")
        raise

def main():
    """
    CLI entry point.
    """
    # Default paths from task description
    input_file = "data/processed/classified_snippets.parquet"
    output_file = "data/processed/cohort_segments.parquet"
    
    # Allow override via environment or args if needed, but defaults are strict per spec
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
        
    logger.info(f"Starting Cohort Analyzer. Input: {input_file}, Output: {output_file}")
    run_cohort_segmentation(input_file, output_file)
    logger.info("Cohort Analyzer completed.")

if __name__ == "__main__":
    main()