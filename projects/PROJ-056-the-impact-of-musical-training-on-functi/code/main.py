"""
Main entry point for the llmXive project: The Impact of Musical Training on Functional Connectivity.

Supports two modes:
- verification: Runs the pipeline on synthetic data to verify code integrity (T008 generator).
- analysis: Runs the pipeline on real data (requires external data source availability).
"""
import argparse
import sys
import os
from pathlib import Path
import logging
import traceback

# Add project root to path for imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, configure_logger
from utils.memory_monitor import check_memory_limit, get_current_memory_mb, MemoryLimitExceeded
from data.models import ValidationError
from data.synthetic_generator import generate_synthetic_dataset
from data.download import load_data
from data.preprocess import run_preprocessing_pipeline
from analysis.connectivity import compute_connectivity_matrices
from analysis.stats import run_group_comparison, run_nbs_analysis
from analysis.correlation import run_correlation_analysis
from analysis.sensitivity import run_sensitivity_analysis

logger = get_logger(__name__)

def run_verification_mode():
    """
    Executes the pipeline using synthetic data for verification purposes.
    """
    logger.info("Starting Verification Mode...")
    logger.info("Generating synthetic dataset...")
    
    try:
        # Generate synthetic data if not present or force regeneration
        # T008 synthetic_generator is responsible for this logic
        synthetic_data_path = generate_synthetic_dataset(n_subjects=100, output_dir="data/processed")
        logger.info(f"Synthetic data generated at: {synthetic_data_path}")
        
        # Load data using the standard loader (T014)
        # In verification mode, load_data should delegate to the synthetic generator if file missing
        df_subjects = load_data(path=synthetic_data_path, mode='verification')
        
        # Preprocessing (T015, T016, T018)
        logger.info("Running preprocessing pipeline...")
        cleaned_df = run_preprocessing_pipeline(df_subjects, mode='verification')
        
        # Connectivity (T024)
        logger.info("Computing connectivity matrices...")
        # This step might be skipped in a minimal verification or run on a subset
        # For T010, we ensure the entry point calls it
        matrices = compute_connectivity_matrices(cleaned_df, mode='verification')
        
        # Group Comparison (T026, T027, T028, T029a)
        logger.info("Running group comparison statistics...")
        stats_results = run_group_comparison(cleaned_df, matrices)
        nbs_results = run_nbs_analysis(cleaned_df, matrices)
        
        # Correlation (T035)
        logger.info("Running correlation analysis...")
        corr_results = run_correlation_analysis(cleaned_df, matrices)
        
        # Sensitivity (T037)
        logger.info("Running sensitivity analysis...")
        sens_results = run_sensitivity_analysis(corr_results)
        
        logger.info("Verification Mode completed successfully.")
        return True

    except MemoryLimitExceeded as e:
        logger.error(f"Memory limit exceeded: {e}")
        return False
    except ValidationError as e:
        logger.error(f"Data validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Verification Mode failed with unexpected error: {e}")
        traceback.print_exc()
        return False

def run_analysis_mode():
    """
    Executes the pipeline using real data.
    """
    logger.info("Starting Analysis Mode...")
    logger.warning("Analysis Mode requires real data sources (ABCD/HCP).")
    
    try:
        # Check memory before heavy lifting
        check_memory_limit()
        
        # Attempt to load real data
        # T014 logic: If mode='analysis' and path invalid, raise DataAccessException
        # We assume a default path or CLI arg for real data
        data_path = os.environ.get('REAL_DATA_PATH', 'data/raw/abcd_subset.csv')
        
        if not os.path.exists(data_path):
            raise FileNotFoundError(
                f"Data Source Missing: Real data required for Analysis Mode at {data_path}. "
                "Set REAL_DATA_PATH environment variable to the location of the real dataset."
            )
        
        logger.info(f"Loading real data from: {data_path}")
        df_subjects = load_data(path=data_path, mode='analysis')
        
        # Preprocessing
        logger.info("Running preprocessing pipeline on real data...")
        cleaned_df = run_preprocessing_pipeline(df_subjects, mode='analysis')
        
        # Connectivity
        logger.info("Computing connectivity matrices on real data...")
        matrices = compute_connectivity_matrices(cleaned_df, mode='analysis')
        
        # Group Comparison
        logger.info("Running group comparison statistics...")
        stats_results = run_group_comparison(cleaned_df, matrices)
        nbs_results = run_nbs_analysis(cleaned_df, matrices)
        
        # Correlation
        logger.info("Running correlation analysis...")
        corr_results = run_correlation_analysis(cleaned_df, matrices)
        
        # Sensitivity
        logger.info("Running sensitivity analysis...")
        sens_results = run_sensitivity_analysis(corr_results)
        
        logger.info("Analysis Mode completed successfully.")
        return True

    except MemoryLimitExceeded as e:
        logger.error(f"Memory limit exceeded: {e}")
        return False
    except ValidationError as e:
        logger.error(f"Data validation failed: {e}")
        return False
    except FileNotFoundError as e:
        logger.error(f"Data Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Analysis Mode failed with unexpected error: {e}")
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Main entry point for the Musical Training Connectivity Study."
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['verification', 'analysis'],
        required=True,
        help="Mode of operation: 'verification' (synthetic data) or 'analysis' (real data)."
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help="Logging verbosity level."
    )
    
    args = parser.parse_args()
    
    # Configure logging
    configure_logger(level=args.log_level)
    
    logger.info(f"Project started in {args.mode} mode.")
    logger.info(f"Current memory usage: {get_current_memory_mb():.2f} MB")
    
    success = False
    if args.mode == 'verification':
        success = run_verification_mode()
    elif args.mode == 'analysis':
        success = run_analysis_mode()
    
    if success:
        logger.info("Pipeline execution finished successfully.")
        sys.exit(0)
    else:
        logger.error("Pipeline execution failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()