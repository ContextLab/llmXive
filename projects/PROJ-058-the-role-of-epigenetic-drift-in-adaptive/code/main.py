"""
Main orchestrator for the epigenetic drift analysis pipeline.

This module coordinates the execution of all pipeline stages while
enforcing memory limits and runtime constraints.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

from config import get_env_int, ensure_directories, set_seed
from memory_monitor import (
    check_memory_usage,
    cleanup_memory,
    enforce_memory_limit,
    reduce_dataframe_memory,
    MEMORY_LIMIT_BYTES
)

# Import pipeline modules
from preprocess.rna_seq import process_rna_seq
from preprocess.methyl import process_methyl_data
from preprocess.filter_genes import filter_genes_by_variance_and_missing
from analysis.correlation import run_correlation_analysis
from analysis.timescale_align import run_timescale_alignment
from analysis.sensitivity import run_sensitivity_analysis
from analysis.stability_check import perform_stability_check
from analysis.stressor_stratification import run_stressor_stratification
from viz.plots import run_viz_analysis

# Configure logging
logger = logging.getLogger(__name__)

# Runtime constraints
MAX_RUNTIME_SECONDS = get_env_int("MAX_RUNTIME_SECONDS", 6 * 3600)  # 6 hours
MEMORY_LIMIT_BYTES = get_env_int("MEMORY_LIMIT_BYTES", 2 * 1024 * 1024 * 1024)  # 2GB

def setup_logging() -> logging.Logger:
    """
    Configure pipeline logging.
    
    Returns:
        Configured logger instance.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "pipeline.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def check_halt_signal() -> bool:
    """
    Check if a halt signal exists from discovery phase.
    
    Returns:
        True if pipeline should halt, False otherwise.
    """
    status_file = Path("output/discovery_status.json")
    
    if not status_file.exists():
        logger.warning("Discovery status file not found. Assuming no halt signal.")
        return False
    
    try:
        with open(status_file, "r") as f:
            status = json.load(f)
        
        if status.get("halt_signal", False):
            logger.error("Halt signal detected from discovery phase. Stopping pipeline.")
            logger.error(f"Reason: {status.get('reason', 'Unknown')}")
            return True
    
    except Exception as e:
        logger.error(f"Error reading discovery status: {e}")
        return True
    
    return False

def run_rna_seq_pipeline() -> pd.DataFrame:
    """
    Execute RNA-seq preprocessing pipeline with memory monitoring.
    
    Returns:
        Processed RNA-seq variance data.
    """
    logger.info("Starting RNA-seq preprocessing pipeline")
    start_time = time.time()
    
    try:
        result = process_rna_seq()
        
        # Optimize memory usage
        result = reduce_dataframe_memory(result)
        cleanup_memory()
        
        elapsed = time.time() - start_time
        logger.info(f"RNA-seq pipeline completed in {elapsed:.2f} seconds")
        
        if not check_memory_usage():
            raise MemoryError("Memory limit exceeded during RNA-seq processing")
        
        return result
    
    except Exception as e:
        logger.error(f"RNA-seq pipeline failed: {e}")
        raise

def run_methyl_pipeline() -> pd.DataFrame:
    """
    Execute methylation preprocessing pipeline with memory monitoring.
    
    Returns:
        Processed methylation variance data.
    """
    logger.info("Starting methylation preprocessing pipeline")
    start_time = time.time()
    
    try:
        result = process_methyl_data()
        
        # Optimize memory usage
        result = reduce_dataframe_memory(result)
        cleanup_memory()
        
        elapsed = time.time() - start_time
        logger.info(f"Methylation pipeline completed in {elapsed:.2f} seconds")
        
        if not check_memory_usage():
            raise MemoryError("Memory limit exceeded during methylation processing")
        
        return result
    
    except Exception as e:
        logger.error(f"Methylation pipeline failed: {e}")
        raise

def unify_results(rna_df: pd.DataFrame, methyl_df: pd.DataFrame) -> pd.DataFrame:
    """
    Unify RNA-seq and methylation variance data into a single matrix.
    
    Args:
        rna_df: Processed RNA-seq variance data
        methyl_df: Processed methylation variance data
    
    Returns:
        Unified variance matrix.
    """
    logger.info("Unifying RNA-seq and methylation variance data")
    
    # Filter genes with zero variance in both layers
    combined = filter_genes_by_variance_and_missing(rna_df, methyl_df)
    
    # Optimize memory
    combined = reduce_dataframe_memory(combined)
    cleanup_memory()
    
    # Save unified results
    output_path = Path("data/processed/variance_matrix.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_path, index=False)
    
    logger.info(f"Unified variance matrix saved to {output_path}")
    logger.info(f"Matrix shape: {combined.shape}")
    
    return combined

def run_correlation_analysis(variance_matrix: pd.DataFrame) -> Dict[str, Any]:
    """
    Execute correlation analysis between epigenetic and expression variance.
    
    Args:
        variance_matrix: Unified variance matrix
    
    Returns:
        Correlation analysis results.
    """
    logger.info("Starting correlation analysis")
    start_time = time.time()
    
    try:
        results = run_correlation_analysis(variance_matrix)
        
        elapsed = time.time() - start_time
        logger.info(f"Correlation analysis completed in {elapsed:.2f} seconds")
        
        if not check_memory_usage():
            raise MemoryError("Memory limit exceeded during correlation analysis")
        
        return results
    
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        raise

def run_timescale_alignment(variance_matrix: pd.DataFrame) -> Dict[str, Any]:
    """
    Execute timescale alignment analysis.
    
    Args:
        variance_matrix: Unified variance matrix
    
    Returns:
        Timescale alignment results.
    """
    logger.info("Starting timescale alignment analysis")
    start_time = time.time()
    
    try:
        results = run_timescale_alignment(variance_matrix)
        
        elapsed = time.time() - start_time
        logger.info(f"Timescale alignment completed in {elapsed:.2f} seconds")
        
        if not check_memory_usage():
            raise MemoryError("Memory limit exceeded during timescale alignment")
        
        return results
    
    except Exception as e:
        logger.error(f"Timescale alignment failed: {e}")
        raise

def run_sensitivity_analysis(correlation_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute sensitivity analysis across generation thresholds.
    
    Args:
        correlation_results: Correlation analysis results
    
    Returns:
        Sensitivity analysis results.
    """
    logger.info("Starting sensitivity analysis")
    start_time = time.time()
    
    try:
        results = run_sensitivity_analysis(correlation_results)
        
        elapsed = time.time() - start_time
        logger.info(f"Sensitivity analysis completed in {elapsed:.2f} seconds")
        
        if not check_memory_usage():
            raise MemoryError("Memory limit exceeded during sensitivity analysis")
        
        return results
    
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

def run_stability_check(sensitivity_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform stability check on sensitivity results.
    
    Args:
        sensitivity_results: Sensitivity analysis results
    
    Returns:
        Stability check results.
    """
    logger.info("Starting stability check")
    start_time = time.time()
    
    try:
        results = perform_stability_check(sensitivity_results)
        
        elapsed = time.time() - start_time
        logger.info(f"Stability check completed in {elapsed:.2f} seconds")
        
        if not check_memory_usage():
            raise MemoryError("Memory limit exceeded during stability check")
        
        return results
    
    except Exception as e:
        logger.error(f"Stability check failed: {e}")
        raise

def run_stressor_stratification(variance_matrix: pd.DataFrame) -> Dict[str, Any]:
    """
    Execute stressor stratification analysis.
    
    Args:
        variance_matrix: Unified variance matrix
    
    Returns:
        Stressor stratification results.
    """
    logger.info("Starting stressor stratification analysis")
    start_time = time.time()
    
    try:
        results = run_stressor_stratification(variance_matrix)
        
        elapsed = time.time() - start_time
        logger.info(f"Stressor stratification completed in {elapsed:.2f} seconds")
        
        if not check_memory_usage():
            raise MemoryError("Memory limit exceeded during stressor stratification")
        
        return results
    
    except Exception as e:
        logger.error(f"Stressor stratification failed: {e}")
        raise

def generate_final_report(
    correlation_results: Dict[str, Any],
    timescale_results: Dict[str, Any],
    sensitivity_results: Dict[str, Any],
    stability_results: Dict[str, Any],
    stressor_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate final consolidated report.
    
    Args:
        correlation_results: Correlation analysis results
        timescale_results: Timescale alignment results
        sensitivity_results: Sensitivity analysis results
        stability_results: Stability check results
        stressor_results: Stressor stratification results
    
    Returns:
        Final consolidated report.
    """
    logger.info("Generating final report")
    
    final_report = {
        "correlation_analysis": correlation_results,
        "timescale_alignment": timescale_results,
        "sensitivity_analysis": sensitivity_results,
        "stability_check": stability_results,
        "stressor_stratification": stressor_results,
        "pipeline_metadata": {
            "memory_limit_bytes": MEMORY_LIMIT_BYTES,
            "max_runtime_seconds": MAX_RUNTIME_SECONDS
        }
    }
    
    output_path = Path("output/final_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(final_report, f, indent=2, default=str)
    
    logger.info(f"Final report saved to {output_path}")
    
    return final_report

@enforce_memory_limit
def main() -> None:
    """
    Main pipeline execution with memory and runtime monitoring.
    """
    logger.info("Starting epigenetic drift analysis pipeline")
    logger.info(f"Memory limit: {MEMORY_LIMIT_BYTES / (1024**3):.2f} GB")
    logger.info(f"Max runtime: {MAX_RUNTIME_SECONDS / 3600:.2f} hours")
    
    pipeline_start = time.time()
    
    try:
        # Setup
        set_seed(42)
        ensure_directories()
        logger = setup_logging()
        
        # Check halt signal
        if check_halt_signal():
            logger.error("Pipeline halted due to discovery phase failure")
            sys.exit(1)
        
        # Run RNA-seq pipeline
        rna_data = run_rna_seq_pipeline()
        
        # Run methylation pipeline
        methyl_data = run_methyl_pipeline()
        
        # Unify results
        variance_matrix = unify_results(rna_data, methyl_data)
        
        # Run correlation analysis
        correlation_results = run_correlation_analysis(variance_matrix)
        
        # Run timescale alignment
        timescale_results = run_timescale_alignment(variance_matrix)
        
        # Run sensitivity analysis
        sensitivity_results = run_sensitivity_analysis(correlation_results)
        
        # Run stability check
        stability_results = run_stability_check(sensitivity_results)
        
        # Run stressor stratification
        stressor_results = run_stressor_stratification(variance_matrix)
        
        # Generate final report
        final_report = generate_final_report(
            correlation_results,
            timescale_results,
            sensitivity_results,
            stability_results,
            stressor_results
        )
        
        # Run visualization
        run_viz_analysis(variance_matrix, final_report)
        
        # Check runtime
        elapsed = time.time() - pipeline_start
        logger.info(f"Pipeline completed successfully in {elapsed:.2f} seconds")
        
        if elapsed > MAX_RUNTIME_SECONDS:
            logger.warning(f"Pipeline exceeded max runtime: {elapsed:.2f} > {MAX_RUNTIME_SECONDS}")
        
        if not check_memory_usage():
            logger.error("Memory limit exceeded at pipeline completion")
            sys.exit(1)
    
    except MemoryError as e:
        logger.error(f"Memory error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        cleanup_memory()
        elapsed = time.time() - pipeline_start
        logger.info(f"Pipeline execution time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    main()
