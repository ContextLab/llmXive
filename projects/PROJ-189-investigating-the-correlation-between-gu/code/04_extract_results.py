"""
Module to extract results data from correlation analysis and model significance verification.
Implements extract_results_data() for US-3.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root / "code"))

from utils.logging import setup_logging, get_logger

# Configure logger
logger = setup_logging("extract_results")


def extract_results_data():
    """
    Read correlation results and significance verification data.
    
    Returns:
        dict: Dictionary containing:
            - 'correlations': DataFrame of significant correlations
            - 'significance': Dictionary with model significance verification results
            - 'summary': Dictionary with summary statistics
    
    Raises:
        FileNotFoundError: If required input files are missing
        ValueError: If input files are malformed or empty
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    correlation_path = project_root / "data" / "processed" / "correlation_results.csv"
    significance_path = project_root / "data" / "processed" / "significance_verification.json"
    
    # Validate input files exist
    if not correlation_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {correlation_path}. "
            "Ensure correlation analysis (T021-T025) has completed successfully."
        )
    if not significance_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {significance_path}. "
            "Ensure model significance verification (T037) has completed successfully."
        )
    
    logger.info(f"Loading correlation results from {correlation_path}")
    
    # Load correlation results
    try:
        correlations_df = pd.read_csv(correlation_path)
        
        # Validate required columns
        required_cols = ['genus', 'cognitive_score', 'rho', 'p_value', 'adj_p_value', 'interpretation']
        missing_cols = [col for col in required_cols if col not in correlations_df.columns]
        if missing_cols:
            raise ValueError(f"Correlation results missing required columns: {missing_cols}")
        
        # Validate data is not empty
        if correlations_df.empty:
            raise ValueError("Correlation results DataFrame is empty")
        
        logger.info(f"Loaded {len(correlations_df)} correlation results")
        
    except Exception as e:
        raise ValueError(f"Failed to load correlation results: {str(e)}")
    
    logger.info(f"Loading significance verification from {significance_path}")
    
    # Load significance verification
    try:
        with open(significance_path, 'r') as f:
            significance_data = json.load(f)
        
        # Validate required keys
        required_keys = ['threshold', 'r_squared', 'pass_status']
        missing_keys = [key for key in required_keys if key not in significance_data]
        if missing_keys:
            raise ValueError(f"Significance verification missing required keys: {missing_keys}")
        
        logger.info(f"Model significance verification: {significance_data['pass_status']}")
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse significance verification JSON: {str(e)}")
    except Exception as e:
        raise ValueError(f"Failed to load significance verification: {str(e)}")
    
    # Generate summary statistics
    significant_count = len(correlations_df[correlations_df['adj_p_value'] < 0.05])
    top_correlations = correlations_df.nlargest(5, 'abs_rho') if 'abs_rho' in correlations_df.columns else correlations_df.nlargest(5, 'rho')
    
    summary = {
        'total_correlations_tested': len(correlations_df),
        'significant_correlations': significant_count,
        'top_correlations_count': len(top_correlations),
        'model_significance_passed': significance_data['pass_status'],
        'model_r_squared': significance_data['r_squared'],
        'null_threshold': significance_data['threshold']
    }
    
    logger.info(f"Summary: {significant_count} significant correlations out of {len(correlations_df)} tested")
    
    return {
        'correlations': correlations_df,
        'significance': significance_data,
        'summary': summary
    }


def main():
    """Main entry point for script execution."""
    try:
        logger.info("Starting results extraction process")
        
        results = extract_results_data()
        
        # Log summary
        summary = results['summary']
        logger.info(f"Extraction complete: {summary}")
        
        # Return results for potential downstream use
        return results
        
    except Exception as e:
        logger.error(f"Results extraction failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()