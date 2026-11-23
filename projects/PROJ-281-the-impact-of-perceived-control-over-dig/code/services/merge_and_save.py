"""
Merge and Save service for the llmXive automated science pipeline.

This module handles the merging of anxiety scoring results and control proxy results,
and saves the final analysis dataset.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple
from code.config import CONFIG

logger = logging.getLogger(__name__)


def load_scoring_results() -> pd.DataFrame:
    """
    Load pre-filtered anxiety scoring results.
    
    Reads from data/processed/scoring_results.csv which contains:
    - text
    - anxiety_score
    - confidence_score
    - post_id (added during scoring pipeline)
    
    Returns:
        DataFrame with scoring results
        
    Raises:
        FileNotFoundError: If the scoring results file does not exist
        ValueError: If required columns are missing
    """
    scoring_path = CONFIG.PROCESSED_DATA_DIR / "scoring_results.csv"
    
    if not scoring_path.exists():
        raise FileNotFoundError(
            f"Scoring results file not found: {scoring_path}. "
            "Ensure T017 (anxiety scoring) has completed successfully."
        )
    
    df = pd.read_csv(scoring_path)
    
    required_columns = ['post_id', 'anxiety_score', 'confidence_score']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(
            f"Scoring results missing required columns: {missing_columns}"
        )
    
    logger.info(f"Loaded {len(df)} rows from scoring results")
    return df


def load_proxy_results() -> pd.DataFrame:
    """
    Load extracted control proxy results.
    
    Reads from data/processed/proxy_results.csv which contains:
    - post_id
    - user_id
    - control_proxy
    - timestamp_regularity
    
    Returns:
        DataFrame with proxy results
        
    Raises:
        FileNotFoundError: If the proxy results file does not exist
        ValueError: If required columns are missing
    """
    proxy_path = CONFIG.PROCESSED_DATA_DIR / "proxy_results.csv"
    
    if not proxy_path.exists():
        raise FileNotFoundError(
            f"Proxy results file not found: {proxy_path}. "
            "Ensure T026 (proxy extraction) has completed successfully."
        )
    
    df = pd.read_csv(proxy_path)
    
    required_columns = ['post_id', 'user_id', 'control_proxy', 'timestamp_regularity']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(
            f"Proxy results missing required columns: {missing_columns}"
        )
    
    logger.info(f"Loaded {len(df)} rows from proxy results")
    return df


def merge_datasets(
    scoring_df: pd.DataFrame,
    proxy_df: pd.DataFrame,
    join_key: str = 'post_id'
) -> pd.DataFrame:
    """
    Merge scoring and proxy datasets on the specified join key.
    
    This function performs an inner join to keep only posts that have
    both anxiety scores and control proxies.
    
    Args:
        scoring_df: DataFrame with anxiety scoring results
        proxy_df: DataFrame with control proxy results
        join_key: Column name to join on (default: 'post_id')
        
    Returns:
        Merged DataFrame with columns from both datasets
        
    Raises:
        ValueError: If join_key is not present in both DataFrames
    """
    if join_key not in scoring_df.columns:
        raise ValueError(f"Join key '{join_key}' not found in scoring results")
    if join_key not in proxy_df.columns:
        raise ValueError(f"Join key '{join_key}' not found in proxy results")
    
    # Inner join to keep only matched posts
    merged_df = pd.merge(
        scoring_df,
        proxy_df,
        on=join_key,
        how='inner'
    )
    
    logger.info(
        f"Merged datasets: {len(scoring_df)} scoring rows + "
        f"{len(proxy_df)} proxy rows = {len(merged_df)} matched rows"
    )
    
    # Log any dropped rows
    dropped_count = len(scoring_df) + len(proxy_df) - len(merged_df)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows due to missing matches")
    
    return merged_df


def save_final_analysis(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the final merged analysis dataset.
    
    Args:
        df: Merged DataFrame to save
        output_path: Optional custom output path. Defaults to CONFIG.PROCESSED_DATA_DIR / "final_analysis.csv"
        
    Returns:
        Path to the saved file
        
    Raises:
        ValueError: If the DataFrame is empty
    """
    if output_path is None:
        output_path = CONFIG.PROCESSED_DATA_DIR / "final_analysis.csv"
    
    if df.empty:
        raise ValueError("Cannot save empty DataFrame. No data to merge.")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved final analysis to {output_path} ({len(df)} rows)")
    
    return output_path


def run_merge_and_save_pipeline() -> Path:
    """
    Execute the full merge and save pipeline (T032).
    
    This function:
    1. Loads pre-filtered scoring results (T017 output)
    2. Loads proxy results (T026 output)
    3. Merges the datasets on post_id
    4. Saves the final analysis to data/processed/final_analysis.csv
    
    Returns:
        Path to the saved final_analysis.csv file
        
    Raises:
        FileNotFoundError: If input files are missing
        ValueError: If merge produces no results
    """
    logger.info("Starting merge and save pipeline (T032)")
    
    # Load input datasets (already filtered by previous stages)
    scoring_df = load_scoring_results()
    proxy_df = load_proxy_results()
    
    # Merge datasets
    merged_df = merge_datasets(scoring_df, proxy_df)
    
    # Save final output
    output_path = save_final_analysis(merged_df)
    
    logger.info("Merge and save pipeline completed successfully")
    return output_path


def main():
    """CLI entry point for merge and save pipeline."""
    import sys
    from code.config import setup_logging
    
    setup_logging(logging.INFO)
    
    try:
        output_path = run_merge_and_save_pipeline()
        print(f"Final analysis saved to: {output_path}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Merge and save pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
