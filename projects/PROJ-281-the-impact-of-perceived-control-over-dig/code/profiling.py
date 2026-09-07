"""
Performance profiling module for the llmXive pipeline.

This module implements runtime and memory profiling to verify that the pipeline
executes within the specified constraints:
- Runtime: < 6 hours (SC-004)
- Memory: < 7 GB RAM (Free-tier constraint)

It also checks for discrepancies between Plan.md and Spec SC-004 regarding
the hard 6-hour limit.
"""
import argparse
import json
import logging
import resource
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Ensure we can import from the project root
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import CONFIG, get_config_value
from code.main import run_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/profiling_run.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants from Config (SC-004)
RUNTIME_LIMIT_HOURS = get_config_value('RUNTIME_LIMIT_HOURS', default=6)
MEMORY_LIMIT_GB = 7.0  # Free-tier constraint
RUNTIME_LIMIT_SECONDS = RUNTIME_LIMIT_HOURS * 3600

def get_memory_usage_gb() -> float:
    """
    Get current memory usage in GB using resource module (Unix/Linux/Mac).
    Falls back to 0.0 on Windows where resource is not available.
    """
    try:
        # rusage.ru_maxrss is in KB on Unix, bytes on some systems
        # On Linux: ru_maxrss is in KB
        mem_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return mem_kb / (1024 * 1024)  # Convert KB to GB
    except Exception as e:
        logger.warning(f"Could not retrieve memory usage: {e}")
        return 0.0

def get_peak_memory_gb() -> float:
    """
    Get peak memory usage since process start in GB.
    Uses the same resource call as get_memory_usage_gb but represents the peak.
    """
    return get_memory_usage_gb()

def check_plan_spec_discrepancy() -> Optional[str]:
    """
    Check for discrepancies between Plan.md's 'Compute Feasibility Note'
    and Spec SC-004 (hard 6h limit).
    
    Returns a discrepancy message if found, None otherwise.
    """
    plan_path = Path("plan.md")
    spec_path = Path("specs/001-perceived-control-anxiety/spec.md")
    
    discrepancy_msg = None
    
    if plan_path.exists():
        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                plan_content = f.read().lower()
            
            # Look for conflicting statements in Plan.md
            if 'compute feasibility' in plan_content or 'compute budget' in plan_content:
                # Check if it mentions a different limit than 6 hours
                if '8 hours' in plan_content or '12 hours' in plan_content or '24 hours' in plan_content:
                    discrepancy_msg = "DISCREPANCY: Plan.md mentions a compute budget different from Spec SC-004's hard 6-hour limit."
        
        except Exception as e:
            logger.warning(f"Could not read plan.md for discrepancy check: {e}")
    
    if spec_path.exists():
        try:
            with open(spec_path, 'r', encoding='utf-8') as f:
                spec_content = f.read()
            
            # Verify SC-004 exists and mentions 6h
            if 'sc-004' in spec_content.lower() and '6' in spec_content:
                logger.info("Spec SC-004 with 6-hour limit confirmed.")
            else:
                logger.warning("Could not confirm Spec SC-004 6-hour limit in spec.md")
                
        except Exception as e:
            logger.warning(f"Could not read spec.md: {e}")
    
    return discrepancy_msg

def run_profiling_pipeline() -> Dict[str, Any]:
    """
    Execute the full pipeline with profiling enabled.
    
    Returns a dictionary with:
    - runtime_seconds: Actual runtime
    - peak_memory_gb: Peak memory usage
    - status: 'passed' or 'failed'
    - errors: List of error messages
    - discrepancy_note: Any Plan vs Spec discrepancy found
    """
    results = {
        'timestamp': datetime.now().isoformat(),
        'runtime_seconds': 0.0,
        'peak_memory_gb': 0.0,
        'status': 'pending',
        'errors': [],
        'discrepancy_note': None,
        'limits': {
            'runtime_hours': RUNTIME_LIMIT_HOURS,
            'memory_gb': MEMORY_LIMIT_GB
        }
    }
    
    # Check for Plan vs Spec discrepancy first
    discrepancy = check_plan_spec_discrepancy()
    if discrepancy:
        results['discrepancy_note'] = discrepancy
        logger.warning(discrepancy)
    
    logger.info(f"Starting pipeline profiling (Limit: {RUNTIME_LIMIT_HOURS}h, {MEMORY_LIMIT_GB}GB)")
    
    start_time = time.time()
    initial_memory = get_memory_usage_gb()
    
    try:
        # Run the pipeline
        logger.info("Executing pipeline...")
        run_pipeline()
        
        end_time = time.time()
        results['runtime_seconds'] = end_time - start_time
        results['peak_memory_gb'] = get_peak_memory_gb()
        
        # Validate against limits
        runtime_hours = results['runtime_seconds'] / 3600
        memory_gb = results['peak_memory_gb']
        
        errors = []
        if runtime_hours > RUNTIME_LIMIT_HOURS:
            errors.append(f"Runtime {runtime_hours:.2f}h exceeds limit of {RUNTIME_LIMIT_HOURS}h")
        
        if memory_gb > MEMORY_LIMIT_GB:
            errors.append(f"Memory {memory_gb:.2f}GB exceeds limit of {MEMORY_LIMIT_GB}GB")
        
        if errors:
            results['status'] = 'failed'
            results['errors'] = errors
            logger.error(f"Profiling FAILED: {'; '.join(errors)}")
        else:
            results['status'] = 'passed'
            logger.info(f"Profiling PASSED: Runtime {runtime_hours:.2f}h, Memory {memory_gb:.2f}GB")
            
    except Exception as e:
        end_time = time.time()
        results['runtime_seconds'] = end_time - start_time
        results['errors'].append(f"Pipeline execution failed: {str(e)}")
        results['status'] = 'failed'
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
    
    return results

def save_report(results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save profiling results to a JSON file.
    
    Args:
        results: Profiling results dictionary
        output_path: Optional custom output path (default: data/processed/profiling_report.json)
    
    Returns:
        Path to the saved report
    """
    if output_path is None:
        output_path = Path("data/processed/profiling_report.json")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Profiling report saved to {output_path}")
    return output_path

def main():
    """
    Entry point for the profiling script.
    """
    parser = argparse.ArgumentParser(description="Profile pipeline performance")
    parser.add_argument('--output', type=str, default=None,
                      help='Output path for profiling report')
    args = parser.parse_args()
    
    output_path = Path(args.output) if args.output else None
    
    results = run_profiling_pipeline()
    save_report(results, output_path)
    
    # Exit with error code if profiling failed
    if results['status'] == 'failed':
        logger.error("Profiling failed. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("Profiling completed successfully.")
        sys.exit(0)

if __name__ == '__main__':
    main()
