import os
import sys
import logging
from pathlib import Path
import pandas as pd
from src.reports.generate import load_dimension_results, classify_dimension_status, generate_dimension_viability_report
from src.utils import get_logger, ensure_directories

def main():
    """
    T018: Generate final dimension viability report.
    
    Reads dimension results (from T016/T020), classifies status (from T017),
    and writes the final viability CSV to data/dimension_viability.csv.
    
    Schema: [dimension, pearson_r, lower_ci, upper_ci, status, adjusted_p]
    """
    logger = get_logger("T018_Viability_Report")
    logger.info("Starting T018: Generating dimension viability report")
    
    # Ensure output directory exists
    ensure_directories()
    output_path = Path("data/dimension_viability.csv")
    
    try:
        # Load dimension results (should contain pearson_r, lower_ci, upper_ci, adjusted_p)
        # This data is produced by T016 (correlations) and T020 (permutation correction)
        dim_results = load_dimension_results()
        
        if dim_results is None or dim_results.empty:
            logger.error("No dimension results found. Did T016 and T020 run successfully?")
            logger.error("Expected file: data/dimension_metrics.csv")
            sys.exit(1)
        
        logger.info(f"Loaded {len(dim_results)} dimension results")
        
        # Validate required columns
        required_cols = ['dimension', 'pearson_r', 'lower_ci', 'upper_ci', 'adjusted_p']
        missing_cols = [col for col in required_cols if col not in dim_results.columns]
        
        if missing_cols:
            logger.error(f"Missing required columns in dimension results: {missing_cols}")
            logger.error("Ensure T016 and T020 have written their outputs correctly.")
            sys.exit(1)
        
        # Classify dimension status (feature-sufficient vs VLM-required)
        # This uses the logic from T017:
        # - feature-sufficient: r >= 0.85
        # - VLM-required: lower 95% CI < 0.70
        # - ambiguous: otherwise
        dim_results['status'] = dim_results.apply(classify_dimension_status, axis=1)
        
        logger.info("Dimension status classification complete")
        
        # Generate final viability report
        viability_df = generate_dimension_viability_report(dim_results)
        
        # Write to disk
        viability_df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote viability report to {output_path}")
        logger.info(f"Report contains {len(viability_df)} dimensions")
        
        # Print summary
        status_counts = viability_df['status'].value_counts()
        logger.info("Status distribution:")
        for status, count in status_counts.items():
            logger.info(f"  {status}: {count}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        logger.error("Ensure T016 and T020 have completed successfully.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating viability report: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
