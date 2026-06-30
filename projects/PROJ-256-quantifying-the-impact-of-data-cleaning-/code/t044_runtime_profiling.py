"""
Task T044: Add runtime profiling/logging to monitor execution time and identify bottlenecks.

This script demonstrates the integration of profiling into the pipeline.
It wraps key pipeline functions to collect execution metrics and generates
a report identifying bottlenecks.
"""
import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from profiler import (
    profile_function,
    profile_block,
    run_cprofile,
    save_profile_report,
    identify_bottlenecks,
    reset_profile_data,
    logger
)
from utils import setup_logging
from config import get_config

def wrap_pipeline_functions():
    """
    Demonstrate wrapping of existing pipeline functions with profiling.
    In a real scenario, these would be applied to the actual functions
    in analysis.py, cleaning.py, etc.
    """
    logger.info("WRAPPING_PIPELINE_FUNCTIONS: Demonstrating profiler integration")
    
    # Example: Wrap a hypothetical data loading function
    @profile_function
    def mock_data_loading():
        """Simulates a data loading operation."""
        import time
        time.sleep(0.2)  # Simulate I/O delay
        return {"rows": 1000, "columns": 10}
    
    # Example: Wrap a hypothetical analysis function
    @profile_function
    def mock_analysis(data):
        """Simulates a statistical analysis operation."""
        import time
        time.sleep(0.3)  # Simulate computation
        return {"p_value": 0.03, "effect_size": 0.5}
    
    # Execute wrapped functions
    with profile_block("data_acquisition_phase"):
        data = mock_data_loading()
        logger.info(f"Data loaded: {data}")
    
    with profile_block("analysis_phase"):
        result = mock_analysis(data)
        logger.info(f"Analysis result: {result}")
    
    return data, result

def generate_profiling_report(output_path: str = "data/processed/profiling_summary.json"):
    """
    Generate a comprehensive profiling report.
    
    Args:
        output_path: Path to save the JSON report.
    """
    logger.info(f"GENERATING_PROFILING_REPORT: {output_path}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Collect metrics
    bottlenecks = identify_bottlenecks(threshold_seconds=0.1)
    total_duration = sum(item.get("duration_seconds", 0) for item in profiling_data)
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_operations": len(profiling_data),
        "total_duration_seconds": total_duration,
        "average_duration_seconds": total_duration / len(profiling_data) if profiling_data else 0,
        "bottlenecks": [
            {
                "name": item.get("function") or item.get("block"),
                "duration_seconds": item.get("duration_seconds"),
                "status": item.get("status")
            }
            for item in bottlenecks
        ],
        "all_executions": profiling_data
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"PROFILING_REPORT_SAVED: {output_path}")
    return report

# Global storage for this script's execution
profiling_data = []

def main():
    """Main entry point for the profiling task."""
    # Initialize logging
    setup_logging()
    logger.info("T044: Starting runtime profiling task")
    
    # Reset previous data
    reset_profile_data()
    
    # Run wrapped pipeline functions
    data, result = wrap_pipeline_functions()
    
    # Generate report
    report_path = "data/processed/profiling_summary.json"
    report = generate_profiling_report(report_path)
    
    # Also save the raw profile data from the profiler module
    profiler_report_path = save_profile_report("data/processed/profile_report.json")
    
    logger.info("T044: Profiling task completed successfully")
    print(f"Profiling report saved to: {report_path}")
    print(f"Raw profile data saved to: {profiler_report_path}")
    print(f"Total operations profiled: {report['total_operations']}")
    print(f"Bottlenecks identified: {len(report['bottlenecks'])}")

if __name__ == "__main__":
    main()
