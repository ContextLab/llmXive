"""
Memory Profiling Script for llmXive Pipeline (T059)

This script runs the pipeline with memory profiling enabled to identify
peak memory usage points, specifically during:
1. RDKit descriptor calculation (T014)
2. Dataset merging (T016a)

Output: data/memory_profile.log
"""
import os
import sys
import time
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Try to import memory_profiler, install if missing
try:
    from memory_profiler import memory_usage
    from memory_profiler import profile
except ImportError:
    print("ERROR: memory_profiler is not installed. Please install it via pip install memory-profiler")
    sys.exit(1)

# Project imports
from config import get_config, ensure_directories
from ingest import main as run_ingest, fetch_fda_drugs, check_degradation_columns, filter_valid_records
from descriptors import main as run_descriptors, calculate_descriptors_batch
from standardize import main as run_standardize
from analysis import main as run_analysis
from viz import main as run_viz
from report import main as run_report
from logging_config import setup_logging, get_logger

# Setup logging
logger = setup_logging()
logger = get_logger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def run_pipeline_with_profiling() -> Dict[str, Any]:
    """
    Run the full pipeline with memory profiling enabled.
    Returns a dictionary with memory usage statistics.
    """
    project_root = get_project_root()
    config = get_config()
    ensure_directories()

    memory_profile = {
        "pipeline_stages": {},
        "peak_memory_mb": 0,
        "total_duration_seconds": 0,
        "start_time": None,
        "end_time": None,
        "errors": []
    }

    start_time = time.time()
    memory_profile["start_time"] = start_time

    try:
        # Stage 1: Data Ingestion (T012, T016a)
        logger.info("Starting memory profiling for Data Ingestion stage...")
        try:
            # We need to profile the actual fetch and merge operations
            # Since run_ingest() is a full pipeline runner, we profile specific functions
            def ingest_stage():
                # Fetch FDA drugs
                df_structural = fetch_fda_drugs()
                # Filter valid records
                df_filtered = filter_valid_records(df_structural)
                return df_filtered

            # Run with memory profiling
            mem_usage, df_filtered = memory_usage((ingest_stage,), retval=True, interval=0.1, timeout=60)
            peak_ingest = max(mem_usage) if mem_usage else 0
            
            memory_profile["pipeline_stages"]["ingestion"] = {
                "peak_memory_mb": peak_ingest,
                "records_processed": len(df_filtered) if df_filtered is not None else 0,
                "status": "success"
            }
            memory_profile["peak_memory_mb"] = max(memory_profile["peak_memory_mb"], peak_ingest)
            
        except Exception as e:
            logger.error(f"Ingestion stage failed: {str(e)}")
            memory_profile["pipeline_stages"]["ingestion"] = {
                "peak_memory_mb": 0,
                "status": "failed",
                "error": str(e)
            }
            memory_profile["errors"].append(f"Ingestion: {str(e)}")

        # Stage 2: Descriptor Calculation (T014)
        logger.info("Starting memory profiling for Descriptor Calculation stage...")
        try:
            # Load the processed structural data
            structural_path = project_root / "data" / "processed" / "structural_subset.csv"
            if structural_path.exists():
                import pandas as pd
                df_structural = pd.read_csv(structural_path)
                
                def descriptor_stage():
                    # Calculate descriptors for all molecules
                    # This is the memory-intensive part
                    descriptors = calculate_descriptors_batch(df_structural["SMILES"].tolist())
                    return descriptors
                
                # Profile descriptor calculation
                mem_usage, descriptors = memory_usage((descriptor_stage,), retval=True, interval=0.1, timeout=300)
                peak_descriptor = max(mem_usage) if mem_usage else 0
                
                memory_profile["pipeline_stages"]["descriptors"] = {
                    "peak_memory_mb": peak_descriptor,
                    "molecules_processed": len(descriptors) if descriptors else 0,
                    "status": "success"
                }
                memory_profile["peak_memory_mb"] = max(memory_profile["peak_memory_mb"], peak_descriptor)
            else:
                logger.warning("Structural subset not found, skipping descriptor profiling")
                memory_profile["pipeline_stages"]["descriptors"] = {
                    "peak_memory_mb": 0,
                    "status": "skipped",
                    "reason": "No structural_subset.csv found"
                }
                
        except Exception as e:
            logger.error(f"Descriptor stage failed: {str(e)}")
            memory_profile["pipeline_stages"]["descriptors"] = {
                "peak_memory_mb": 0,
                "status": "failed",
                "error": str(e)
            }
            memory_profile["errors"].append(f"Descriptors: {str(e)}")

        # Stage 3: Standardization (T021)
        logger.info("Starting memory profiling for Standardization stage...")
        try:
            def standardize_stage():
                # Run standardization
                run_standardize()
                return True
            
            mem_usage, result = memory_usage((standardize_stage,), retval=True, interval=0.1, timeout=60)
            peak_standardize = max(mem_usage) if mem_usage else 0
            
            memory_profile["pipeline_stages"]["standardization"] = {
                "peak_memory_mb": peak_standardize,
                "status": "success"
            }
            memory_profile["peak_memory_mb"] = max(memory_profile["peak_memory_mb"], peak_standardize)
            
        except Exception as e:
            logger.error(f"Standardization stage failed: {str(e)}")
            memory_profile["pipeline_stages"]["standardization"] = {
                "peak_memory_mb": 0,
                "status": "failed",
                "error": str(e)
            }
            memory_profile["errors"].append(f"Standardization: {str(e)}")

        # Stage 4: Analysis (T022-T025)
        logger.info("Starting memory profiling for Analysis stage...")
        try:
            def analysis_stage():
                run_analysis()
                return True
            
            mem_usage, result = memory_usage((analysis_stage,), retval=True, interval=0.1, timeout=120)
            peak_analysis = max(mem_usage) if mem_usage else 0
            
            memory_profile["pipeline_stages"]["analysis"] = {
                "peak_memory_mb": peak_analysis,
                "status": "success"
            }
            memory_profile["peak_memory_mb"] = max(memory_profile["peak_memory_mb"], peak_analysis)
            
        except Exception as e:
            logger.error(f"Analysis stage failed: {str(e)}")
            memory_profile["pipeline_stages"]["analysis"] = {
                "peak_memory_mb": 0,
                "status": "failed",
                "error": str(e)
            }
            memory_profile["errors"].append(f"Analysis: {str(e)}")

    except Exception as e:
        logger.error(f"Pipeline profiling failed: {str(e)}")
        memory_profile["errors"].append(f"Pipeline: {str(e)}")
    
    finally:
        end_time = time.time()
        memory_profile["end_time"] = end_time
        memory_profile["total_duration_seconds"] = end_time - start_time

    return memory_profile

def save_memory_profile(profile: Dict[str, Any], output_path: Path) -> None:
    """Save the memory profile to a log file."""
    with open(output_path, 'w') as f:
        json.dump(profile, f, indent=2)
    logger.info(f"Memory profile saved to {output_path}")

def main():
    """Main entry point for memory profiling."""
    logger.info("Starting memory profiling for llmXive pipeline (T059)")
    
    project_root = get_project_root()
    output_path = project_root / "data" / "memory_profile.log"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run profiling
    profile = run_pipeline_with_profiling()
    
    # Save results
    save_memory_profile(profile, output_path)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("MEMORY PROFILING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Duration: {profile['total_duration_seconds']:.2f} seconds")
    logger.info(f"Peak Memory Usage: {profile['peak_memory_mb']:.2f} MB")
    logger.info(f"Pipeline Stages Profiled: {len(profile['pipeline_stages'])}")
    
    for stage, data in profile['pipeline_stages'].items():
        status = data.get('status', 'unknown')
        peak = data.get('peak_memory_mb', 0)
        logger.info(f"  - {stage}: {status} (Peak: {peak:.2f} MB)")
    
    if profile['errors']:
        logger.warning(f"Errors encountered: {len(profile['errors'])}")
        for error in profile['errors']:
            logger.warning(f"  - {error}")
    
    logger.info("=" * 60)
    logger.info("Memory profiling complete. Results saved to data/memory_profile.log")
    
    return 0 if not profile['errors'] else 1

if __name__ == "__main__":
    sys.exit(main())
