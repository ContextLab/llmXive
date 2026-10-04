"""
Optimized Main Pipeline Entry Point for CPU-Only Execution.

This module provides an optimized version of the main pipeline that:
1. Enforces CPU-only execution
2. Implements memory-efficient processing
3. Uses chunked processing for large datasets
4. Optimizes data structures for performance
5. Implements proper garbage collection

This is the recommended entry point for production runs on CPU-only systems.
"""
import os
import sys
import gc
import traceback
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import optimization utilities
from utils.cpu_optimization import (
    validate_cpu_only_environment,
    optimize_memory_usage,
    chunked_dataframe_iterator,
    set_random_seed,
    ensure_numpy_arrays_contiguous,
    force_gc_collect,
    monitor_memory_usage,
    validate_no_gpu_acceleration
)

# Import core pipeline components
from config import ensure_directories, get_config_dict
from preprocess.structural import run_structural_pipeline, save_structural_metrics_to_csv
from preprocess.functional import run_functional_pipeline, assign_states_and_calculate_metrics
from analysis.correlation import run_correlation_analysis
from reports.generate_report import generate_final_report

# Set environment for CPU-only
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

def log_memory_usage(step: str) -> None:
    """Log current memory usage for monitoring."""
    mem_stats = monitor_memory_usage()
    print(f"[MEMORY] {step}: {mem_stats}")

def process_subject_optimized(subject_id: str, 
                              config: Dict[str, Any],
                              exclude_list: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Process a single subject with memory optimizations.

    Args:
        subject_id: Subject identifier
        config: Configuration dictionary
        exclude_list: List of subject IDs to exclude

    Returns:
        Dict[str, Any]: Processing results for the subject
    """
    if exclude_list and subject_id in exclude_list:
        return {'subject_id': subject_id, 'status': 'excluded'}

    try:
        # Validate CPU environment before processing
        validate_cpu_only_environment()
        
        # Initialize subject processing
        log_memory_usage(f"Starting subject {subject_id}")
        
        # Process structural metrics
        structural_result = run_structural_pipeline(
            subject_id=subject_id,
            config=config,
            optimize_memory=True
        )
        
        # Force garbage collection after structural processing
        force_gc_collect()
        log_memory_usage(f"After structural processing for {subject_id}")
        
        # Process functional metrics
        functional_result = run_functional_pipeline(
            subject_id=subject_id,
            config=config,
            optimize_memory=True
        )
        
        # Force garbage collection after functional processing
        force_gc_collect()
        log_memory_usage(f"After functional processing for {subject_id}")
        
        # Combine results
        result = {
            'subject_id': subject_id,
            'status': 'success',
            'structural': structural_result,
            'functional': functional_result
        }
        
        return result
        
    except Exception as e:
        error_msg = f"Error processing subject {subject_id}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        
        return {
            'subject_id': subject_id,
            'status': 'error',
            'error': str(e)
        }
    finally:
        # Ensure cleanup after each subject
        gc.collect()

def aggregate_metrics_to_csv(results: List[Dict[str, Any]], 
                             output_path: str) -> None:
    """
    Aggregate processing results to CSV with memory optimization.

    Args:
        results: List of processing result dictionaries
        output_path: Path for output CSV file
    """
    if not results:
        print("[WARNING] No results to aggregate")
        return

    # Convert to DataFrame with optimization
    df = pd.DataFrame(results)
    df_optimized = optimize_memory_usage(df, low_precision=True)
    
    # Save to CSV
    df_optimized.to_csv(output_path, index=False)
    print(f"[INFO] Aggregated metrics saved to {output_path}")

def run_optimized_pipeline(config_path: Optional[str] = None) -> bool:
    """
    Run the entire pipeline with CPU optimizations.

    Args:
        config_path: Optional path to configuration file

    Returns:
        bool: True if pipeline completed successfully
    """
    try:
        # Validate environment
        print("[INFO] Validating CPU-only environment...")
        validate_cpu_only_environment()
        print("[INFO] Environment validation passed")
        
        # Load configuration
        config = get_config_dict(config_path)
        ensure_directories(config)
        
        # Set random seeds
        set_random_seed(config.get('random_seed', 42))
        
        # Initialize tracking
        all_results = []
        exclude_list = []
        
        # Get subject list (this would typically come from data loader)
        # For now, we'll assume subjects are in data/raw/
        raw_data_dir = Path(config['data_raw_dir'])
        if not raw_data_dir.exists():
            print(f"[ERROR] Raw data directory not found: {raw_data_dir}")
            return False
        
        # Process each subject with optimizations
        subject_dirs = [d for d in raw_data_dir.iterdir() if d.is_dir()]
        total_subjects = len(subject_dirs)
        
        print(f"[INFO] Processing {total_subjects} subjects with CPU optimizations...")
        
        for idx, subject_dir in enumerate(subject_dirs):
            subject_id = subject_dir.name
            print(f"[INFO] Processing subject {idx+1}/{total_subjects}: {subject_id}")
            
            # Process subject
            result = process_subject_optimized(subject_id, config, exclude_list)
            
            if result['status'] == 'error':
                exclude_list.append(subject_id)
                continue
            
            all_results.append(result)
            
            # Periodic garbage collection
            if (idx + 1) % 5 == 0:
                force_gc_collect()
                log_memory_usage(f"Checkpoint after {idx+1} subjects")
        
        # Aggregate results
        if all_results:
            output_path = Path(config['data_processed_dir']) / 'structural_metrics.csv'
            aggregate_metrics_to_csv(all_results, str(output_path))
            
            # Generate final report
            report_path = Path(config['data_processed_dir']) / 'final_report.json'
            generate_final_report(config, str(report_path))
        
        print("[INFO] Pipeline completed successfully")
        return True
        
    except Exception as e:
        print(f"[ERROR] Pipeline failed: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        # Final cleanup
        force_gc_collect()
        log_memory_usage("Final cleanup")

def main():
    """Main entry point for the optimized pipeline."""
    print("=" * 60)
    print("LLMXive Optimized Pipeline (CPU-Only)")
    print("=" * 60)
    
    # Run optimized pipeline
    success = run_optimized_pipeline()
    
    if success:
        print("[SUCCESS] Pipeline completed successfully")
        sys.exit(0)
    else:
        print("[FAILURE] Pipeline failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
