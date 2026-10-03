"""
Generate sensitivity report for conformal prediction thresholds.

This script analyzes the trade-off between prediction interval width
and observed coverage error across a range of coverage levels.

Output: results/sensitivity_report.csv
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
from stats.significance import run_sensitivity_analysis
from utils.logger import get_logger

# Ensure paths are set up
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_conformal_results() -> pd.DataFrame:
    """
    Load conformal prediction results from the per_sample_errors.csv file.
    
    Returns:
        DataFrame with conformal prediction results.
        
    Raises:
        FileNotFoundError: If the required input file does not exist.
    """
    input_path = Path("results/per_sample_errors.csv")
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please run the pipeline first to generate per_sample_errors.csv."
        )
    
    logger = get_logger()
    logger.info(f"Loading conformal results from {input_path}")
    df = pd.read_csv(input_path)
    
    # Filter for conformal method results only
    # Assuming 'method' column contains the method name
    conformal_df = df[df['method'].str.lower().str.contains('conformal', na=False)]
    
    if conformal_df.empty:
        raise ValueError(
            "No conformal prediction results found in per_sample_errors.csv. "
            "Ensure the pipeline ran conformal methods."
        )
    
    logger.info(f"Loaded {len(conformal_df)} conformal prediction results")
    return conformal_df

def main():
    """
    Main entry point for generating the sensitivity report.
    
    Loads conformal results, runs sensitivity analysis, and saves the report.
    """
    logger = get_logger()
    logger.info("Starting sensitivity report generation")
    
    try:
        # Load conformal results
        conformal_results = load_conformal_results()
        
        # Define coverage range: 0.80 to 0.99 with step 0.01
        coverage_range = [round(i * 0.01, 2) for i in range(80, 100)]
        logger.info(f"Analyzing coverage levels: {coverage_range}")
        
        # Run sensitivity analysis
        # This function should analyze the trade-off between coverage and width
        sensitivity_results = run_sensitivity_analysis(
            conformal_results, 
            coverage_range
        )
        
        # Save results to CSV
        output_path = Path("results/sensitivity_report.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure the DataFrame has the required columns
        required_columns = ['coverage_level', 'avg_width', 'observed_coverage_error']
        if not all(col in sensitivity_results.columns for col in required_columns):
            logger.error(f"Missing required columns in sensitivity results. "
                       f"Expected: {required_columns}")
            raise ValueError("Sensitivity analysis results missing required columns")
        
        # Save to CSV
        sensitivity_results.to_csv(output_path, index=False)
        logger.info(f"Sensitivity report saved to {output_path}")
        
        # Print summary
        logger.info("Sensitivity analysis summary:")
        logger.info(sensitivity_results.to_string(index=False))
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during sensitivity analysis: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
