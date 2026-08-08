"""
Script to execute Task T024: Save correlation results to CSV.

This script:
1. Loads the correlation results from src/correlation.py analysis
2. Validates the required columns are present
3. Saves the results to data/processed/correlation_results.csv
4. Logs the operation and verifies file creation

Usage:
    python scripts/run_t024_save_results.py
"""
import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import load_config
from src.correlation import run_correlation_analysis
from src.correlation_io import save_correlation_results

def main():
    """Main entry point for T024."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Task T024: Save correlation results")
    
    # Load configuration
    config = load_config()
    logger.info(f"Loaded configuration: DATA_PROCESSED={config['DATA_PROCESSED']}")
    
    # Define input and output paths
    cleaned_data_path = Path(config['DATA_PROCESSED']) / 'cleaned_microbiome_sleep.csv'
    output_path = Path(config['DATA_PROCESSED']) / 'correlation_results.csv'
    
    # Check if input file exists
    if not cleaned_data_path.exists():
        logger.error(f"Input file not found: {cleaned_data_path}")
        logger.error("T016 (cleaned data generation) must complete before T024.")
        # Create a blocked report as per requirements
        import pandas as pd
        blocked_df = pd.DataFrame({
            'r': [None],
            'p': [None],
            'q': [None],
            'is_moderate': [False],
            'is_meaningful': [False],
            'status': ['blocked'],
            'reason': ['No verified data source found']
        })
        save_correlation_results(blocked_df, output_path=str(output_path), force=True)
        logger.info(f"Created blocked report at {output_path}")
        return 1
    
    try:
        # Run correlation analysis (which loads data, computes diversity, runs correlation)
        logger.info(f"Loading and analyzing data from {cleaned_data_path}")
        correlation_df = run_correlation_analysis(
            input_path=str(cleaned_data_path),
            output_path=None  # We handle saving separately
        )
        
        if correlation_df is None or len(correlation_df) == 0:
            logger.warning("Correlation analysis returned empty results.")
            # Create blocked report if no data was available
            import pandas as pd
            blocked_df = pd.DataFrame({
                'r': [None],
                'p': [None],
                'q': [None],
                'is_moderate': [False],
                'is_meaningful': [False],
                'status': ['blocked'],
                'reason': ['No significant data available for correlation']
            })
            save_correlation_results(blocked_df, output_path=str(output_path), force=True)
            logger.info(f"Created blocked report at {output_path}")
            return 0
        
        # Save results
        logger.info(f"Saving correlation results to {output_path}")
        saved_path = save_correlation_results(
            correlation_df,
            output_path=str(output_path),
            force=True
        )
        
        # Verification
        if not saved_path.exists():
            logger.error(f"Failed to create output file: {saved_path}")
            return 1
        
        # Verify columns
        required_cols = ['r', 'p', 'q', 'is_moderate', 'is_meaningful', 'status']
        actual_cols = list(correlation_df.columns)
        missing_cols = [col for col in required_cols if col not in actual_cols]
        
        if missing_cols:
            logger.error(f"Missing required columns in output: {missing_cols}")
            return 1
        
        logger.info(f"Successfully saved {len(correlation_df)} correlation results to {saved_path}")
        logger.info(f"Columns: {actual_cols}")
        
        # Log summary
        meaningful_count = correlation_df['is_meaningful'].sum()
        moderate_count = correlation_df['is_moderate'].sum()
        logger.info(f"Summary: {meaningful_count} meaningful, {moderate_count} moderate correlations found")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        # Create blocked report
        import pandas as pd
        blocked_df = pd.DataFrame({
            'r': [None],
            'p': [None],
            'q': [None],
            'is_moderate': [False],
            'is_meaningful': [False],
            'status': ['blocked'],
            'reason': [str(e)]
        })
        save_correlation_results(blocked_df, output_path=str(output_path), force=True)
        logger.info(f"Created blocked report at {output_path}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T024: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)