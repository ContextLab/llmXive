import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from utils.config import get_project_root, get_data_processed_path, get_output_path

logger = logging.getLogger(__name__)

def log_hypothesis_rejection(test_name: str, p_value: float, threshold: float = 0.01, 
                             effect_size: Optional[float] = None, 
                             details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a single null hypothesis rejection event.
    
    Args:
        test_name: Name of the statistical test performed
        p_value: Calculated p-value
        threshold: Significance threshold (default 0.01)
        effect_size: Optional effect size metric
        details: Optional dictionary of additional context
    """
    if p_value < threshold:
        rejection_msg = (
            f"NULL HYPOTHESIS REJECTED: {test_name} | "
            f"p-value={p_value:.6e} < {threshold} | "
            f"Effect size={effect_size:.4f}" if effect_size is not None else
            f"NULL HYPOTHESIS REJECTED: {test_name} | p-value={p_value:.6e} < {threshold}"
        )
        logger.warning(rejection_msg)
        
        # Log additional details if provided
        if details:
            for key, value in details.items():
                logger.info(f"  {key}: {value}")

def log_all_rejections_from_results(results_file: str, threshold: float = 0.01) -> List[Dict[str, Any]]:
    """
    Read a statistical results CSV file and log all null hypothesis rejections.
    
    Args:
        results_file: Path to the CSV file containing statistical results
        threshold: Significance threshold (default 0.01)
        
    Returns:
        List of dictionaries containing rejection details
    """
    project_root = get_project_root()
    processed_path = get_data_processed_path()
    
    # Determine full path
    if not os.path.isabs(results_file):
        # Check if it's in the processed directory or root
        possible_paths = [
            processed_path / results_file,
            project_root / results_file,
            project_root / "data" / "processed" / results_file
        ]
        results_path = next((p for p in possible_paths if p.exists()), None)
    else:
        results_path = Path(results_file)
        
    if not results_path or not results_path.exists():
        logger.error(f"Results file not found: {results_file}")
        return []
        
    rejections = []
    
    try:
        df = pd.read_csv(results_path)
        
        # Identify p-value columns (common naming patterns)
        p_value_cols = [col for col in df.columns if 'p_value' in col.lower() or 'p-value' in col.lower()]
        test_name_cols = [col for col in df.columns if 'test' in col.lower() or 'metric' in col.lower() or 'property' in col.lower()]
        
        if not p_value_cols:
            logger.warning(f"No p-value columns found in {results_file}. Columns: {list(df.columns)}")
            return rejections
            
        logger.info(f"Processing {len(df)} results from {results_file}")
        logger.info(f"Found p-value columns: {p_value_cols}")
        
        for idx, row in df.iterrows():
            for p_col in p_value_cols:
                try:
                    p_val = float(row[p_col])
                    if p_val < threshold:
                        # Extract test name from row or column headers
                        test_name = "Unknown"
                        for t_col in test_name_cols:
                            if t_col in df.columns and pd.notna(row[t_col]):
                                test_name = f"{row[t_col]} ({p_col})"
                                break
                                
                        effect_size = None
                        effect_cols = [col for col in df.columns if 'effect' in col.lower() or 'coeff' in col.lower()]
                        for e_col in effect_cols:
                            if pd.notna(row[e_col]):
                                effect_size = float(row[e_col])
                                break
                                
                        details = {
                            "row_index": idx,
                            "p_value_column": p_col
                        }
                        
                        log_hypothesis_rejection(
                            test_name=test_name,
                            p_value=p_val,
                            threshold=threshold,
                            effect_size=effect_size,
                            details=details
                        )
                        
                        rejections.append({
                            "test_name": test_name,
                            "p_value": p_val,
                            "threshold": threshold,
                            "effect_size": effect_size,
                            "row_index": idx
                        })
                except (ValueError, TypeError):
                    continue
                    
    except Exception as e:
        logger.error(f"Error processing results file {results_file}: {str(e)}")
        raise
        
    logger.info(f"Total rejections logged: {len(rejections)}")
    return rejections

def main() -> None:
    """
    Main entry point for logging hypothesis rejections.
    Reads statistical results and logs all p < 0.01 rejections.
    """
    # Setup logging if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    project_root = get_project_root()
    processed_path = get_data_processed_path()
    
    # Default results file from T025
    results_file = processed_path / "statistical_results.csv"
    
    if not results_file.exists():
        logger.error(f"Statistical results file not found: {results_file}")
        logger.info("Please ensure T025 has been completed and data/processed/statistical_results.csv exists.")
        return
        
    logger.info(f"Starting hypothesis rejection logging for {results_file}")
    
    rejections = log_all_rejections_from_results(str(results_file), threshold=0.01)
    
    # Log summary
    logger.info("=" * 60)
    logger.info(f"SUMMARY: {len(rejections)} null hypotheses rejected at p < 0.01")
    logger.info("=" * 60)
    
    # Optionally save rejection summary to a file
    if rejections:
        summary_path = processed_path / "hypothesis_rejections_log.csv"
        pd.DataFrame(rejections).to_csv(summary_path, index=False)
        logger.info(f"Rejection summary saved to: {summary_path}")

if __name__ == "__main__":
    main()