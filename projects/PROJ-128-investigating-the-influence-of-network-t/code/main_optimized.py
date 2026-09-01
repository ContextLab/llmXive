"""
Optimized Main Pipeline Entry Point

This script runs the full pipeline with CPU-optimized settings,
ensuring no GPU calls are made and memory usage is minimized.
"""
import os
import sys
import gc
import traceback
import numpy as np
import pandas as pd
from pathlib import Path

# Import optimization utilities
from utils.cpu_optimization import (
    validate_no_gpu_acceleration,
    optimize_memory_usage,
    set_random_seed,
    force_gc_collect
)
from config import get_config_dict, ensure_directories
from preprocess.structural import run_structural_pipeline
from preprocess.functional import run_functional_pipeline
from analysis.correlation import run_correlation_analysis
from analysis.robustness import run_sensitivity_analysis
from reports.generate_report import generate_final_report
from reports.audit_associational_language import generate_audit_report

def main():
    """
    Main entry point for the optimized pipeline.
    """
    # 1. Validate CPU-only environment
    print("Validating CPU-only environment...")
    if not validate_no_gpu_acceleration():
        print("WARNING: GPU acceleration detected. Proceeding in CPU-only mode anyway, but results may be affected.")

    # 2. Set random seed for reproducibility
    config = get_config_dict()
    seed = config.get('RANDOM_SEED', 42)
    set_random_seed(seed)

    # 3. Ensure directories exist
    ensure_directories()

    # 4. Run Structural Pipeline
    print("Running Structural Pipeline...")
    try:
        structural_results = run_structural_pipeline()
        print(f"Structural metrics saved to {structural_results.get('output_path')}")
    except Exception as e:
        print(f"Error in Structural Pipeline: {e}")
        traceback.print_exc()
        return

    # 5. Run Functional Pipeline
    print("Running Functional Pipeline...")
    try:
        functional_results = run_functional_pipeline()
        print(f"Dynamic metrics saved to {functional_results.get('output_path')}")
    except Exception as e:
        print(f"Error in Functional Pipeline: {e}")
        traceback.print_exc()
        return

    # 6. Run Correlation Analysis
    print("Running Correlation Analysis...")
    try:
        correlation_results = run_correlation_analysis()
        print(f"Correlation results saved to {correlation_results.get('output_path')}")
    except Exception as e:
        print(f"Error in Correlation Analysis: {e}")
        traceback.print_exc()
        return

    # 7. Run Sensitivity Analysis
    print("Running Sensitivity Analysis...")
    try:
        sensitivity_results = run_sensitivity_analysis()
        print(f"Sensitivity results saved to {sensitivity_results.get('output_path')}")
    except Exception as e:
        print(f"Error in Sensitivity Analysis: {e}")
        traceback.print_exc()
        return

    # 8. Generate Final Report
    print("Generating Final Report...")
    try:
        report_path = generate_final_report()
        print(f"Final report saved to {report_path}")
    except Exception as e:
        print(f"Error generating Final Report: {e}")
        traceback.print_exc()
        return

    # 9. Audit Associational Language
    print("Auditing Associational Language...")
    try:
        audit_path = generate_audit_report()
        print(f"Audit report saved to {audit_path}")
    except Exception as e:
        print(f"Error in Associational Language Audit: {e}")
        traceback.print_exc()
        return

    # 10. Force garbage collection at the end
    collected = force_gc_collect()
    print(f"Garbage collection completed. Collected {collected} objects.")

    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
