import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.lib import config
from src.services.analysis import run_full_analysis, calculate_spearman_correlation, perform_linear_regression, apply_multiple_comparison_correction

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_analysis_data() -> Dict[str, Any]:
    """
    Loads the processed dataset required for statistical analysis.
    In a real pipeline, this would load from data/processed/final_analysis_dataset.parquet.
    For this task, we assume the analysis service can access the data or we simulate
    the input structure expected by the analysis functions if the file is missing.
    
    However, per strict constraints, we must use real data. 
    This function attempts to load the final dataset. If it doesn't exist, 
    it raises an error rather than fabricating data.
    """
    data_path = Path(config.PROCESSED_DATA_DIR) / "final_analysis_dataset.parquet"
    
    if not data_path.exists():
        logger.error(f"Required dataset not found at {data_path}. "
                     "Please ensure User Story 1 and 2 are completed and the dataset is generated.")
        raise FileNotFoundError(f"Dataset file not found: {data_path}")
    
    import pandas as pd
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded dataset with {len(df)} rows from {data_path}")
    return df

def run_statistical_analysis(df: Any, correction_method: str = "fdr_bh") -> Dict[str, Any]:
    """
    Runs the full statistical analysis pipeline on the provided dataframe.
    Returns a dictionary containing all metrics, coefficients, and p-values.
    """
    logger.info("Starting statistical analysis...")
    
    # Run the full analysis which includes correlation, regression, and correction
    # The run_full_analysis function is expected to return a comprehensive dict
    # based on the API surface provided in src/services/analysis.py
    
    try:
        results = run_full_analysis(df, correction_method=correction_method)
        logger.info("Statistical analysis completed successfully.")
        return results
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

def save_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Saves the statistical metrics to a JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, default=str)
    
    logger.info(f"Metrics saved to {output_file}")

def main():
    """
    Main entry point for saving statistical metrics.
    1. Loads the processed dataset.
    2. Runs the statistical analysis (Spearman, Regression, Correction).
    3. Saves the results to artifacts/results/statistical_metrics.json.
    """
    logger.info("Starting save_statistical_metrics pipeline...")
    
    try:
        # Load data
        df = load_analysis_data()
        
        # Determine correction method (default to FDR-BH as per typical scientific practice)
        # This could be made CLI-arg driven if needed, but tasks.md implies a standard run
        correction_method = "fdr_bh" 
        
        # Run analysis
        metrics = run_statistical_analysis(df, correction_method=correction_method)
        
        # Define output path
        output_path = str(Path(config.ARTIFACTS_DIR) / "results" / "statistical_metrics.json")
        
        # Save results
        save_metrics(metrics, output_path)
        
        logger.info("Pipeline finished successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()