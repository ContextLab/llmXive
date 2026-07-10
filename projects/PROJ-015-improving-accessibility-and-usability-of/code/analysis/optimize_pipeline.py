"""
Pipeline Optimization Script

Orchestrates the application of performance optimizations across the analysis pipeline.
This script replaces inefficient loops with vectorized operations and caches results.
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

from config.settings import get_settings
from utils.logger import get_logger
from utils.perf_optimizer import (
    optimize_dataframe_loading,
    run_vectorized_statistical_tests,
    StatisticalCache,
    profile_execution
)
from analysis.data_cleaner import DataCleaner
from analysis.stat_utils import StatUtils

logger = get_logger(__name__)
cache = StatisticalCache()


@profile_execution
def optimized_cleaning_pipeline(raw_dir: str, output_dir: str) -> pd.DataFrame:
    """
    Runs the data cleaning pipeline with memory optimizations.
    """
    cleaner = DataCleaner()
    # Assuming cleaner has a method to load and clean
    # We wrap the loading in our optimizer
    cleaned_df = cleaner.load_and_clean(raw_dir, output_dir)
    
    # Post-load optimization: ensure dtypes are efficient
    for col in cleaned_df.select_dtypes(include=['object']).columns:
        cleaned_df[col] = cleaned_df[col].astype('category')
    
    return cleaned_df


@profile_execution
def optimized_analysis_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Runs statistical analysis using vectorized methods and caching.
    """
    # Check cache first
    cached_result = cache.get("analysis_pipeline", df)
    if cached_result is not None:
        logger.info("Retrieved analysis from cache.")
        return cached_result

    # Perform vectorized stats
    # Example: Compare Completion Time across Interface Types
    if 'completion_time' in df.columns and 'interface_type' in df.columns:
        stats_results = run_vectorized_statistical_tests(df, 'completion_time', 'interface_type')
        
        # Create a summary DataFrame
        summary_df = pd.DataFrame([stats_results])
        cache.set("analysis_pipeline", df, summary_df)
        return summary_df
    
    logger.warning("No standard metrics found for vectorized analysis.")
    return pd.DataFrame()


def main():
    """
    Main entry point for the optimized pipeline.
    """
    settings = get_settings()
    raw_dir = settings.data_raw_dir
    processed_dir = settings.data_processed_dir

    logger.info("Starting Optimized Pipeline Execution...")

    # 1. Load and Clean
    try:
        cleaned_data = optimized_cleaning_pipeline(raw_dir, processed_dir)
        logger.info(f"Cleaning complete. Rows: {len(cleaned_data)}")
    except FileNotFoundError:
        logger.error("Raw data directory not found. Cannot proceed.")
        return
    except Exception as e:
        logger.error(f"Cleaning pipeline failed: {e}")
        return

    # 2. Analysis
    try:
        analysis_results = optimized_analysis_pipeline(cleaned_data)
        logger.info("Analysis complete.")
        
        # Save results
        output_path = Path(processed_dir) / "optimized_analysis_results.csv"
        analysis_results.to_csv(output_path, index=False)
        logger.info(f"Results saved to {output_path}")
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}")
        return

    logger.info("Optimized pipeline execution finished successfully.")


if __name__ == "__main__":
    main()
