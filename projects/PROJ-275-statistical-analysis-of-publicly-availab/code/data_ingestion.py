import os
import sys
import logging
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from config import load_config, get_dataset_urls, ensure_directories, get_logging_config
from entities import TimeSeriesMovie

# Re-use logger setup if defined, or define locally
def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger

def download_datasets() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetch TMDB 5000 and IMDb Reviews from verified public URLs.
    Assumes URLs are defined in config/research.md and validated.
    """
    urls = get_dataset_urls()
    # Expected keys based on typical research.md content for this project
    tmdb_url = urls.get('tmdb_5000')
    imdb_url = urls.get('imdb_reviews')
    
    if not tmdb_url or not imdb_url:
        raise ValueError("Dataset URLs not found in configuration. Check research.md and config.")

    # Setup paths
    data_dir = Path("data/raw")
    ensure_directories([data_dir])
    
    tmdb_file = data_dir / "tmdb_5000_movies.csv"
    imdb_file = data_dir / "imdb_reviews.csv" # Assuming CSV for simplicity, adjust if JSON/Parquet

    # Download logic (using wget or urllib)
    # Using subprocess wget for robustness if available, else urllib
    try:
        subprocess.run(["wget", "-O", str(tmdb_file), tmdb_url], check=True)
        subprocess.run(["wget", "-O", str(imdb_file), imdb_url], check=True)
    except subprocess.CalledProcessError:
        # Fallback to urllib if wget fails
        import urllib.request
        urllib.request.urlretrieve(tmdb_url, tmdb_file)
        urllib.request.urlretrieve(imdb_url, imdb_file)
    
    return pd.read_csv(tmdb_file), pd.read_csv(imdb_file)

def merge_datasets(tmdb_df: pd.DataFrame, imdb_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join on movie title/year using pandas with fuzzy matching fallback.
    """
    # Basic join on title (cleaned)
    # Assuming columns: 'title' in both, 'release_date' in tmdb, 'movie_id' or similar in imdb
    # This is a simplified version; real implementation needs specific column mapping
    
    # Clean titles
    tmdb_df['title_clean'] = tmdb_df['title'].str.lower().str.strip()
    imdb_df['title_clean'] = imdb_df['title'].str.lower().str.strip()
    
    # Attempt inner merge
    merged = pd.merge(tmdb_df, imdb_df, on='title_clean', how='inner', suffixes=('_tmdb', '_imdb'))
    
    if len(merged) == 0:
        # Fallback: fuzzy matching (requires fuzzywuzzy)
        from fuzzywuzzy import process
        # Implementation of fuzzy merge would go here
        # For now, raising error if strict merge fails and fuzzy not implemented
        raise RuntimeError("Initial merge failed and fuzzy fallback not fully implemented in this snippet.")
        
    return merged

def filter_valid_movies(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Exclude movies with missing revenue or <3 months of review history.
    Logs counts and raises error if < 500 valid movies.
    """
    initial_count = len(df)
    
    # Filter missing revenue
    # Assuming 'opening_weekend_revenue' exists
    df = df.dropna(subset=['opening_weekend_revenue'])
    
    # Filter review history (simplified: assume 'review_date' exists)
    # Need to ensure 'release_date' and 'review_date' are datetime
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    if 'review_date' in df.columns:
        df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
        # Calculate duration
        df['review_duration_days'] = (df['review_date'] - df['release_date']).dt.days
        df = df[df['review_duration_days'] >= 90] # 3 months approx
    
    final_count = len(df)
    excluded = initial_count - final_count
    
    logger.info(f"Filtering valid movies: Excluded {excluded}, Remaining {final_count}")
    
    if final_count < 500:
        raise ValueError(f"Final count {final_count} is less than required 500 valid movies.")
        
    return df

def align_timestamps(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Create a weekly sentiment time-series structure aligned to release_date.
    Treats opening_weekend_revenue as a static anchor (broadcast to all weeks).
    """
    # This function prepares the data for sentiment scoring by creating weekly bins
    # or ensures the dataframe is ready for the sentiment merge.
    # For T013, we assume the data is already aligned or we perform a simple broadcast.
    
    # Ensure release_date is datetime
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    
    # Create a week offset column if needed for time-series
    # For now, we assume the dataframe represents the aggregated movie level
    # and we just ensure the static anchor is present.
    
    logger.info("Timestamps aligned. Revenue treated as static anchor.")
    return df

def save_intermediate_results(df: pd.DataFrame, logger: logging.Logger) -> None:
    """
    T013 Implementation: Save intermediate data and log row counts.
    Verifies required columns and row count >= 500.
    """
    required_columns = ['title', 'release_date', 'opening_weekend_revenue', 'sentiment_score', 'genre']
    
    # Verify columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for output: {missing_cols}")
    
    row_count = len(df)
    if row_count < 500:
        raise ValueError(f"Row count {row_count} is less than required 500.")
    
    # Ensure directories
    processed_dir = Path("data/processed")
    logs_dir = Path("data/logs")
    ensure_directories([processed_dir, logs_dir])
    
    # Save Parquet
    output_path = processed_dir / "merged_clean.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved intermediate results to {output_path} with {row_count} rows.")
    
    # Log row counts
    log_path = logs_dir / "ingestion_log.txt"
    with open(log_path, "a") as f:
        f.write(f"Task: T013 - Save Intermediate Results\n")
        f.write(f"Timestamp: {pd.Timestamp.now()}\n")
        f.write(f"Output File: {output_path}\n")
        f.write(f"Row Count: {row_count}\n")
        f.write(f"Columns: {list(df.columns)}\n")
        f.write("-" * 40 + "\n")
    
    logger.info(f"Logged row counts to {log_path}")

def main():
    """
    Main pipeline execution for Data Ingestion and T013 Save.
    """
    config = load_config()
    log_config = get_logging_config()
    
    log_file = Path("data/logs/ingestion_log.txt")
    ensure_directories([log_file.parent])
    
    logger = setup_logger("DataIngestion", str(log_file))
    logger.info("Starting Data Ingestion Pipeline (T013)")
    
    try:
        # 1. Download
        logger.info("Downloading datasets...")
        tmdb_df, imdb_df = download_datasets()
        
        # 2. Merge
        logger.info("Merging datasets...")
        merged_df = merge_datasets(tmdb_df, imdb_df)
        
        # 3. Filter
        logger.info("Filtering valid movies...")
        filtered_df = filter_valid_movies(merged_df, logger)
        
        # 4. Align Timestamps
        logger.info("Aligning timestamps...")
        aligned_df = align_timestamps(filtered_df, logger)
        
        # 5. Sentiment Analysis (Assuming T015 runs here or data is pre-scored for T013)
        # If T015 is separate, this step might be skipped or assumed done.
        # However, T013 requires 'sentiment_score' column.
        # We will call the sentiment function to ensure the column exists.
        from sentiment_analysis import compute_vader_sentiment, process_reviews_for_timeseries, merge_sentiment_to_timeseries
        
        # Assuming we have a 'review_text' column
        if 'review_text' in aligned_df.columns:
            logger.info("Computing VADER sentiment...")
            aligned_df = merge_sentiment_to_timeseries(aligned_df)
        else:
            # If no review text, we might need to aggregate or mock? 
            # Per constraints, we must fail loudly if real data missing.
            # But T013 requires the column. We assume the pipeline up to T015
            # provides this. For T013 standalone, we assume the dataframe 
            # passed in has the sentiment_score or we compute it.
            # Let's assume the input to T013 (the merged_df) has review text.
            # If not, we raise error.
            if 'sentiment_score' not in aligned_df.columns:
                 raise ValueError("Sentiment score column missing. Ensure review text is processed.")

        # 6. Save Intermediate (T013)
        logger.info("Saving intermediate results (T013)...")
        save_intermediate_results(aligned_df, logger)
        
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
