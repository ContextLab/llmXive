"""
Module to log null hypothesis rejection flags for statistical tests.

This module provides functionality to log instances where null hypotheses
are rejected (p < 0.01) during statistical analysis, providing a clear
audit trail of significant findings.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from utils.config import get_project_root, get_data_processed_path, get_output_path
from utils.logging import get_pipeline_logger

logger = get_pipeline_logger(__name__)


def log_hypothesis_rejection(
    test_name: str,
    property_name: str,
    metric_name: str,
    p_value: float,
    effect_size: Optional[float] = None,
    sample_size: Optional[int] = None,
    correction_applied: str = "bonferroni",
    logger_instance: Optional[logging.Logger] = None
) -> None:
    """
    Log a null hypothesis rejection event.
    
    Args:
        test_name: Name of the statistical test performed
        property_name: Galaxy property being tested
        metric_name: Halo shape metric being tested
        p_value: The p-value from the test
        effect_size: Optional effect size measure
        sample_size: Optional sample size used in the test
        correction_applied: Type of multiple comparison correction applied
        logger_instance: Logger instance to use (defaults to module logger)
    """
    if logger_instance is None:
        logger_instance = logger
    
    # Log the rejection event
    rejection_msg = (
        f"NULL HYPOTHESIS REJECTED: {test_name} test for "
        f"property='{property_name}' vs metric='{metric_name}' "
        f"with p-value={p_value:.6e} (< 0.01 threshold)"
    )
    
    if effect_size is not None:
        rejection_msg += f", effect_size={effect_size:.4f}"
    
    if sample_size is not None:
        rejection_msg += f", n={sample_size}"
    
    rejection_msg += f" (correction: {correction_applied})"
    
    logger_instance.warning(rejection_msg)
    
    # Also log to a dedicated rejection log file
    project_root = get_project_root()
    rejection_log_path = project_root / "data" / "logs" / "rejections.log"
    rejection_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(rejection_log_path, "a") as f:
        f.write(f"{rejection_msg}\n")


def log_all_rejections_from_results(
    results_file: str,
    p_threshold: float = 0.01,
    logger_instance: Optional[logging.Logger] = None
) -> List[Dict[str, Any]]:
    """
    Scan statistical results and log all null hypothesis rejections.
    
    Args:
        results_file: Path to the CSV file containing statistical results
        p_threshold: P-value threshold for rejection (default 0.01)
        logger_instance: Logger instance to use
        
    Returns:
        List of dictionaries containing rejection details
    """
    if logger_instance is None:
        logger_instance = logger
    
    project_root = get_project_root()
    results_path = project_root / "data" / "processed" / results_file
    
    if not results_path.exists():
        logger_instance.error(f"Results file not found: {results_path}")
        return []
    
    try:
        df = pd.read_csv(results_path)
    except Exception as e:
        logger_instance.error(f"Failed to read results file: {e}")
        return []
    
    # Identify columns containing p-values
    p_value_cols = [col for col in df.columns if 'p_value' in col.lower()]
    
    if not p_value_cols:
        logger_instance.warning("No p-value columns found in results file")
        return []
    
    rejections = []
    
    for _, row in df.iterrows():
        for p_col in p_value_cols:
            p_value = row[p_col]
            if pd.notna(p_value) and p_value < p_threshold:
                # Extract context from row
                test_name = row.get('test_name', 'unknown')
                property_name = row.get('galaxy_property', 'unknown')
                metric_name = row.get('shape_metric', 'unknown')
                effect_size = row.get('effect_size', None)
                sample_size = row.get('sample_size', None)
                correction = row.get('correction_method', 'bonferroni')
                
                rejection_entry = {
                    'test_name': test_name,
                    'property_name': property_name,
                    'metric_name': metric_name,
                    'p_value': p_value,
                    'effect_size': effect_size,
                    'sample_size': sample_size,
                    'correction_method': correction,
                    'p_threshold': p_threshold
                }
                
                rejections.append(rejection_entry)
                log_hypothesis_rejection(
                    test_name=test_name,
                    property_name=property_name,
                    metric_name=metric_name,
                    p_value=p_value,
                    effect_size=effect_size,
                    sample_size=sample_size,
                    correction_applied=correction,
                    logger_instance=logger_instance
                )
    
    logger_instance.info(f"Logged {len(rejections)} null hypothesis rejections")
    return rejections


def main():
    """
    Main entry point for logging hypothesis rejections.
    
    This function scans the statistical results file and logs all
    instances where the null hypothesis was rejected (p < 0.01).
    """
    logger_instance = get_pipeline_logger(__name__)
    logger_instance.info("Starting hypothesis rejection logging")
    
    try:
        # Default to the main statistical results file
        results_file = "statistical_results.csv"
        
        rejections = log_all_rejections_from_results(
            results_file=results_file,
            p_threshold=0.01,
            logger_instance=logger_instance
        )
        
        # Summary
        if rejections:
            logger_instance.info(
                f"Found {len(rejections)} significant results (p < 0.01). "
                f"Details logged to data/logs/rejections.log"
            )
        else:
            logger_instance.info("No null hypothesis rejections found at p < 0.01 threshold")
            
    except Exception as e:
        logger_instance.error(f"Error during hypothesis rejection logging: {e}")
        raise


if __name__ == "__main__":
    main()