"""
Compliance Reporting Module for Photo-Fries Rearrangement Study.

Implements T017b: Aggregates validation results from T017a to produce
a compliance report ensuring >= 95% of runs meet all tolerances.

Dependency: Runs after T017a (validation.py produces validation_flags.json).

Output:
    data/processed/compliance_report.json
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from project API surface
try:
    from config import get_processed_data_path, ensure_directories
except ImportError:
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(BASE_DIR))
    from code.config import get_processed_data_path, ensure_directories

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Compliance thresholds per SC-004
COMPLIANCE_THRESHOLD = 0.95  # >= 95% of runs must be compliant

class ComplianceError(Exception):
    """Raised when compliance cannot be assessed or threshold not met."""
    pass

def load_validation_flags(filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load validation flags from T017a output.
    
    Args:
        filepath: Path to validation_flags.json. If None, uses default from config.
    
    Returns:
        List of validation flag records.
    
    Raises:
        FileNotFoundError: If validation_flags.json does not exist.
    """
    if filepath is None:
        processed_path = get_processed_data_path()
        filepath = processed_path / "validation_flags.json"
    
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(
            f"Validation flags file not found: {filepath}. "
            f"Please run T017a (validation.py) first to generate validation_flags.json."
        )
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, dict):
        # If it's a dict with 'flags' key, extract the list
        if 'flags' in data:
            return data['flags']
        # If it's a dict with a 'validation_records' or similar key
        elif 'validation_records' in data:
            return data['validation_records']
        # Otherwise treat the dict values as records if they're list-like
        else:
            return [data]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected format in validation_flags.json: {type(data)}")

def assess_compliance(flags: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Assess overall compliance based on validation flags.
    
    Computes:
    - Percentage of runs within all tolerances
    - Breakdown by tolerance category
    - Pass/fail status against COMPLIANCE_THRESHOLD
    
    Args:
        flags: List of validation flag records from T017a.
    
    Returns:
        Dictionary with compliance metrics and assessment.
    """
    if not flags:
        raise ComplianceError("No validation flags provided for compliance assessment.")
    
    total_runs = len(flags)
    
    # Count compliant runs (all flags pass)
    compliant_runs = 0
    temperature_compliant = 0
    humidity_compliant = 0
    dielectric_compliant = 0
    
    failed_runs = []
    
    for flag_record in flags:
        # Extract compliance status from the flag record
        # Expected structure: {run_id, temperature_ok, humidity_ok, dielectric_ok, ...}
        
        run_id = flag_record.get('run_id', 'unknown')
        
        temp_ok = flag_record.get('temperature_ok', False)
        humidity_ok = flag_record.get('humidity_ok', False)
        dielectric_ok = flag_record.get('dielectric_ok', False)
        
        # A run is compliant if ALL checks pass
        if temp_ok and humidity_ok and dielectric_ok:
            compliant_runs += 1
        else:
            failed_runs.append({
                'run_id': run_id,
                'temperature_ok': temp_ok,
                'humidity_ok': humidity_ok,
                'dielectric_ok': dielectric_ok
            })
        
        # Count individual category compliance
        if temp_ok:
            temperature_compliant += 1
        if humidity_ok:
            humidity_compliant += 1
        if dielectric_ok:
            dielectric_compliant += 1
    
    # Calculate compliance percentage
    compliance_percentage = compliant_runs / total_runs if total_runs > 0 else 0.0
    
    # Determine pass/fail
    compliant = compliance_percentage >= COMPLIANCE_THRESHOLD
    
    assessment = {
        "total_runs": total_runs,
        "compliant_runs": compliant_runs,
        "non_compliant_runs": total_runs - compliant_runs,
        "compliance_percentage": compliance_percentage,
        "compliance_threshold": COMPLIANCE_THRESHOLD,
        "status": "PASS" if compliant else "FAIL",
        "category_breakdown": {
            "temperature_compliant_runs": temperature_compliant,
            "humidity_compliant_runs": humidity_compliant,
            "dielectric_compliant_runs": dielectric_compliant
        },
        "failed_runs": failed_runs if not compliant else [],
        "assessment_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return assessment

def generate_compliance_report(assessment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a complete compliance report.
    
    Args:
        assessment: Output from assess_compliance().
    
    Returns:
        Complete compliance report with recommendations.
    """
    report = {
        "report_type": "compliance_report",
        "report_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "compliance_assessment": assessment,
        "requirement_reference": {
            "spec_requirement": "SC-004",
            "requirement_text": "Environmental parameters logged within tolerance for >=95% of runs"
        }
    }
    
    # Add recommendations based on assessment
    if assessment['status'] == 'PASS':
        report['recommendation'] = (
            f"Compliance requirement met. {assessment['compliance_percentage']:.1%} of runs "
            f"({assessment['compliant_runs']}/{assessment['total_runs']}) meet all environmental tolerances."
        )
    else:
        report['recommendation'] = (
            f"COMPLIANCE FAILURE. Only {assessment['compliance_percentage']:.1%} of runs "
            f"({assessment['compliant_runs']}/{assessment['total_runs']}) meet all environmental tolerances. "
            f"Threshold is {assessment['compliance_threshold']:.1%}. "
            f"Review failed runs and adjust environmental controls."
        )
        
        # Identify most common failure mode
        failed_count = len(assessment['failed_runs'])
        if failed_count > 0:
            temp_failures = sum(1 for r in assessment['failed_runs'] if not r['temperature_ok'])
            humidity_failures = sum(1 for r in assessment['failed_runs'] if not r['humidity_ok'])
            dielectric_failures = sum(1 for r in assessment['failed_runs'] if not r['dielectric_ok'])
            
            failure_modes = []
            if temp_failures > 0:
                failure_modes.append(f"temperature ({temp_failures} runs)")
            if humidity_failures > 0:
                failure_modes.append(f"humidity ({humidity_failures} runs)")
            if dielectric_failures > 0:
                failure_modes.append(f"dielectric constant ({dielectric_failures} runs)")
            
            if failure_modes:
                report['primary_failure_modes'] = failure_modes
    
    return report

def write_compliance_report(report: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Write compliance report to JSON file.
    
    Args:
        report: Compliance report dictionary.
        output_path: Path to output file. If None, uses default from config.
    
    Returns:
        Path to written file.
    """
    if output_path is None:
        processed_path = get_processed_data_path()
        output_path = processed_path / "compliance_report.json"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Compliance report written to {output_path}")
    return output_path

def run_compliance_reporting(validation_flags_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Execute the full compliance reporting pipeline.
    
    Args:
        validation_flags_path: Optional path to validation_flags.json.
    
    Returns:
        The generated compliance report.
    
    Raises:
        ComplianceError: If compliance assessment fails.
        FileNotFoundError: If validation_flags.json not found.
    """
    logger.info("Starting compliance reporting pipeline (T017b).")
    
    try:
        # Load validation flags from T017a
        flags = load_validation_flags(validation_flags_path)
        logger.info(f"Loaded {len(flags)} validation flag records.")
        
        # Assess compliance
        assessment = assess_compliance(flags)
        logger.info(f"Compliance assessment: {assessment['compliance_percentage']:.1%} compliant "
                   f"({assessment['compliant_runs']}/{assessment['total_runs']} runs).")
        
        # Generate report
        report = generate_compliance_report(assessment)
        
        # Write report
        output_path = write_compliance_report(report)
        
        logger.info(f"Compliance reporting complete. Status: {assessment['status']}")
        
        return report
        
    except FileNotFoundError as e:
        logger.error(f"Data error: {e}")
        raise
    except ComplianceError as e:
        logger.error(f"Compliance assessment error: {e}")
        raise

def main():
    """CLI entry point for compliance reporting."""
    parser = argparse.ArgumentParser(
        description="Aggregate validation results and produce compliance report (T017b)."
    )
    parser.add_argument(
        "--validation-flags",
        type=str,
        default=None,
        help="Path to validation_flags.json from T017a. If not provided, uses default location."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output compliance_report.json. If not provided, uses default location."
    )
    
    args = parser.parse_args()
    
    try:
        ensure_directories()
        
        validation_flags_path = Path(args.validation_flags) if args.validation_flags else None
        report = run_compliance_reporting(validation_flags_path)
        
        output_path = Path(args.output) if args.output else None
        if output_path:
            write_compliance_report(report, output_path)
        else:
            write_compliance_report(report)
        
        # Print summary to stdout
        assessment = report['compliance_assessment']
        print(f"\nCompliance Report Summary:")
        print(f"  Status: {assessment['status']}")
        print(f"  Compliant Runs: {assessment['compliant_runs']}/{assessment['total_runs']}")
        print(f"  Compliance: {assessment['compliance_percentage']:.1%}")
        print(f"  Threshold: {assessment['compliance_threshold']:.1%}")
        print(f"\n{report['recommendation']}")
        
        return 0 if assessment['status'] == 'PASS' else 1
        
    except Exception as e:
        logger.error(f"Compliance reporting failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
