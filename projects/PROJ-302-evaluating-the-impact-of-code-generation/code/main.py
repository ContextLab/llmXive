import os
import sys
import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import get_config, ensure_directories
from analysis.matching import run_propensity_matching, check_balance
from analysis.sensitivity import run_sensitivity_analysis
from security.pii_scanner import run_pii_scan_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_matching_gate() -> bool:
    """
    Check if propensity matching gate passed.
    
    Returns:
        True if matching was successful, False otherwise
    """
    failure_report_path = Path('data/processed/matching_failure_report.json')
    
    if failure_report_path.exists():
        with open(failure_report_path) as f:
            report = json.load(f)
            if report.get('status') == 'failed':
                logger.error("Matching gate failed: SMD > 0.1 after retries")
                return False
    
    return True

def check_sensitivity_gate() -> bool:
    """
    Check if sensitivity analysis gate passed.
    
    Returns:
        True if sensitivity analysis was consistent, False otherwise
    """
    sensitivity_summary_path = Path('data/processed/sensitivity_summary.json')
    
    if not sensitivity_summary_path.exists():
        logger.warning("Sensitivity summary not found, assuming pass")
        return True
    
    with open(sensitivity_summary_path) as f:
        summary = json.load(f)
        consistent = summary.get('consistent', True)
        
        if not consistent:
            logger.error("Sensitivity gate failed: Consistency < 80%")
            return False
    
    return True

def check_pii_gate() -> bool:
    """
    Check if PII scan gate passed.
    
    Returns:
        True if no critical PII found, False otherwise
    """
    pii_report_path = Path('data/processed/pii_scan_report.json')
    
    if not pii_report_path.exists():
        logger.warning("PII report not found, running scan...")
        # Run PII scan on code directory
        result = run_pii_scan_pipeline(
            scan_paths=[Path('code')],
            output_dir=Path('data/processed'),
            block_on_critical=True
        )
        return result['status'] == 'passed'
    
    with open(pii_report_path) as f:
        report = json.load(f)
        
        if report['status'] == 'failed':
            logger.error("PII gate failed: Critical PII detected")
            return False
    
    return True

def check_runtime_gate(start_time: float) -> bool:
    """
    Check if runtime is within the 6-hour limit.
    
    Args:
        start_time: Pipeline start timestamp
    
    Returns:
        True if within time limit, False otherwise
    """
    max_runtime_seconds = 6 * 60 * 60  # 6 hours
    elapsed = time.time() - start_time
    
    if elapsed > max_runtime_seconds:
        logger.error(f"Runtime gate failed: {elapsed:.2f}s > {max_runtime_seconds}s")
        return False
    
    return True

def write_runtime_report(start_time: float, pipeline_name: str = 'main'):
    """
    Write runtime report to disk.
    
    Args:
        start_time: Pipeline start timestamp
        pipeline_name: Name of the pipeline
    """
    end_time = time.time()
    duration = end_time - start_time
    
    report = {
        'pipeline_name': pipeline_name,
        'start_time': datetime.fromtimestamp(start_time).isoformat(),
        'end_time': datetime.fromtimestamp(end_time).isoformat(),
        'duration_seconds': duration,
        'duration_hours': duration / 3600
    }
    
    report_path = Path('data/processed/runtime_report.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Runtime report written to {report_path}")
    return report

def run_pipeline():
    """
    Run the complete analysis pipeline with all gates.
    
    Returns:
        True if pipeline completed successfully, False otherwise
    """
    start_time = time.time()
    logger.info("Starting main analysis pipeline")
    
    # Ensure directories exist
    ensure_directories()
    
    # Gate 1: PII Security Check
    logger.info("Running PII security gate...")
    if not check_pii_gate():
        logger.error("Pipeline halted: PII security gate failed")
        write_runtime_report(start_time)
        return False
    
    # Gate 2: Matching Gate
    logger.info("Checking matching gate...")
    if not check_matching_gate():
        logger.error("Pipeline halted: Matching gate failed")
        write_runtime_report(start_time)
        return False
    
    # Gate 3: Sensitivity Gate
    logger.info("Checking sensitivity gate...")
    if not check_sensitivity_gate():
        logger.error("Pipeline halted: Sensitivity gate failed")
        write_runtime_report(start_time)
        return False
    
    # Gate 4: Runtime Gate
    logger.info("Checking runtime gate...")
    if not check_runtime_gate(start_time):
        logger.error("Pipeline halted: Runtime gate failed")
        write_runtime_report(start_time)
        return False
    
    logger.info("All gates passed. Pipeline completed successfully.")
    write_runtime_report(start_time)
    return True

def main():
    """Main entry point for the pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run the main analysis pipeline')
    parser.add_argument('--skip-pii-check', action='store_true', help='Skip PII security check')
    parser.add_argument('--skip-matching-check', action='store_true', help='Skip matching gate check')
    parser.add_argument('--skip-sensitivity-check', action='store_true', help='Skip sensitivity gate check')
    parser.add_argument('--skip-runtime-check', action='store_true', help='Skip runtime gate check')
    
    args = parser.parse_args()
    
    # Override gates if requested
    global check_pii_gate, check_matching_gate, check_sensitivity_gate, check_runtime_gate
    
    if args.skip_pii_check:
        check_pii_gate = lambda: True
    if args.skip_matching_check:
        check_matching_gate = lambda: True
    if args.skip_sensitivity_check:
        check_sensitivity_gate = lambda: True
    if args.skip_runtime_check:
        check_runtime_gate = lambda _: True
    
    success = run_pipeline()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
