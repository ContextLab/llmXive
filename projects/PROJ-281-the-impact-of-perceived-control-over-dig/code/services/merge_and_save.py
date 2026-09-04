"""
Merge pre-filtered anxiety scores and control proxies into the final analysis dataset.

This module implements Task T032:
- Confirms that input data is pre-filtered (T016 confidence filtering already applied)
- Merges scoring_results.csv and proxy_results.csv on post_id
- Saves the final merged dataset to data/processed/final_analysis.csv
"""
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple
from code.config import CONFIG

logger = logging.getLogger(__name__)


def load_scoring_results(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the pre-filtered anxiety scoring results.
    
    Args:
        input_path: Path to scoring_results.csv. If None, uses CONFIG.PROCESSED_DIR.
        
    Returns:
        DataFrame with columns: text, anxiety_score, confidence_score, post_id (if present)
        
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If required columns are missing
    """
    if input_path is None:
        input_path = CONFIG.PROCESSED_DIR / "scoring_results.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Scoring results file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Verify required columns exist
    required_cols = {"text", "anxiety_score", "confidence_score"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Scoring results missing required columns: {missing}")
    
    # Confirm post_id exists for merging; if not, try to infer or raise
    if "post_id" not in df.columns:
        # Some datasets might not have post_id; we need it for merging with proxy results
        # If missing, we cannot merge properly. Raise an error.
        raise ValueError(
            "Scoring results must contain 'post_id' column for merging with proxy results. "
            "Ensure T013 (data ingestion) and T014a (preprocessing) preserved post_id."
        )
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df


def load_proxy_results(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the extracted control proxy results.
    
    Args:
        input_path: Path to proxy_results.csv. If None, uses CONFIG.PROCESSED_DIR.
        
    Returns:
        DataFrame with columns: post_id, user_id, control_proxy, timestamp_regularity
        
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If required columns are missing
    """
    if input_path is None:
        input_path = CONFIG.PROCESSED_DIR / "proxy_results.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Proxy results file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Verify required columns exist
    required_cols = {"post_id", "user_id", "control_proxy", "timestamp_regularity"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Proxy results missing required columns: {missing}")
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df


def merge_datasets(
    scores_df: pd.DataFrame,
    proxies_df: pd.DataFrame,
    join_key: str = "post_id"
) -> pd.DataFrame:
    """
    Merge scoring and proxy datasets on the specified key.
    
    This function performs an inner join to ensure only posts with both
    anxiety scores and control proxies are included in the final dataset.
    
    Args:
        scores_df: DataFrame from load_scoring_results()
        proxies_df: DataFrame from load_proxy_results()
        join_key: Column name to join on (default: "post_id")
        
    Returns:
        Merged DataFrame containing all columns from both inputs
        
    Raises:
        ValueError: If join key is missing from either dataset
    """
    if join_key not in scores_df.columns:
        raise ValueError(f"Join key '{join_key}' not found in scoring results")
    if join_key not in proxies_df.columns:
        raise ValueError(f"Join key '{join_key}' not found in proxy results")
    
    merged = pd.merge(
        scores_df,
        proxies_df,
        on=join_key,
        how="inner"  # Only include posts with both scores and proxies
    )
    
    logger.info(f"Merged dataset contains {len(merged)} rows (inner join on '{join_key}')")
    
    # Log join statistics
    score_count = len(scores_df)
    proxy_count = len(proxies_df)
    merged_count = len(merged)
    logger.info(
        f"Join stats: scores={score_count}, proxies={proxy_count}, "
        f"merged={merged_count} ({100*merged_count/score_count:.1f}% of scores retained)"
    )
    
    return merged


def save_final_analysis(
    merged_df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Path:
    """
    Save the final merged analysis dataset.
    
    Args:
        merged_df: Merged DataFrame from merge_datasets()
        output_path: Path to save the CSV. If None, uses CONFIG.PROCESSED_DIR.
        
    Returns:
        Path to the saved file
        
    Raises:
        IOError: If the file cannot be written
    """
    if output_path is None:
        output_path = CONFIG.PROCESSED_DIR / "final_analysis.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    merged_df.to_csv(output_path, index=False)
    
    logger.info(f"Saved final analysis dataset to {output_path} ({len(merged_df)} rows)")
    
    return output_path


def run_merge_and_save_pipeline(
    scoring_input: Optional[Path] = None,
    proxy_input: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Execute the full merge and save pipeline for Task T032.
    
    This function:
    1. Loads pre-filtered scoring results (from T017)
    2. Loads proxy results (from T026)
    3. Merges them on post_id
    4. Saves the final dataset to final_analysis.csv
    
    Args:
        scoring_input: Path to scoring_results.csv (optional)
        proxy_input: Path to proxy_results.csv (optional)
        output_path: Path to save final_analysis.csv (optional)
        
    Returns:
        Path to the saved final_analysis.csv file
        
    Raises:
        FileNotFoundError: If required input files are missing
        ValueError: If data validation fails
    """
    logger.info("Starting merge and save pipeline (T032)")
    
    # Load inputs
    scores_df = load_scoring_results(scoring_input)
    proxies_df = load_proxy_results(proxy_input)
    
    # Merge
    merged_df = merge_datasets(scores_df, proxies_df)
    
    # Save
    output = save_final_analysis(merged_df, output_path)
    
    logger.info("Merge and save pipeline completed successfully")
    return output


def main():
    """CLI entry point for T032 merge and save pipeline."""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Merge pre-filtered anxiety scores and control proxies into final analysis dataset."
    )
    parser.add_argument(
        "--scoring-input",
        type=Path,
        default=None,
        help="Path to scoring_results.csv (default: data/processed/scoring_results.csv)"
    )
    parser.add_argument(
        "--proxy-input",
        type=Path,
        default=None,
        help="Path to proxy_results.csv (default: data/processed/proxy_results.csv)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to save final_analysis.csv (default: data/processed/final_analysis.csv)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    try:
        output_path = run_merge_and_save_pipeline(
            scoring_input=args.scoring_input,
            proxy_input=args.proxy_input,
            output_path=args.output
        )
        print(f"Final analysis dataset saved to: {output_path}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
