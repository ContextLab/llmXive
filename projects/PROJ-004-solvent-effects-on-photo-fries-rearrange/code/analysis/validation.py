import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from config import get_processed_data_path, get_chemicals_path

logger = logging.getLogger(__name__)

def check_dielectric_deviation(run_data: Dict[str, Any], reference_data: Dict[str, Any], tolerance_percent: float = 2.0) -> Tuple[bool, float]:
    """
    Check if the logged dielectric constant deviates from the reference by more than tolerance_percent.
    
    Args:
        run_data: Dictionary containing 'dielectric_constant' key from the run log.
        reference_data: Dictionary containing 'dielectric_constant' key from solvents.yaml.
        tolerance_percent: Maximum allowed percentage deviation (default 2.0%).
    
    Returns:
        Tuple of (is_compliant, deviation_percent)
    """
    if 'dielectric_constant' not in run_data or 'dielectric_constant' not in reference_data:
        logger.warning("Missing dielectric constant data for comparison")
        return False, 0.0
    
    run_val = run_data['dielectric_constant']
    ref_val = reference_data['dielectric_constant']
    
    if ref_val == 0:
        logger.error("Reference dielectric constant is zero, cannot calculate percentage deviation")
        return False, float('inf')
    
    deviation = abs(run_val - ref_val) / abs(ref_val) * 100
    is_compliant = deviation <= tolerance_percent
    
    return is_compliant, deviation

def validate_solvent_series_runs(log_file_path: Path) -> List[Dict[str, Any]]:
    """
    Validate a series of solvent runs against environmental tolerances.
    
    This function reads environment logs and checks:
    1. Dielectric constant deviation (<= 2% from reference)
    2. Temperature tolerance (typically ±1°C or as defined in spec)
    3. Humidity tolerance (±2% RH as per Rosalind Franklin review)
    
    Args:
        log_file_path: Path to the environment logs JSON file.
    
    Returns:
        List of validation results for each run.
    """
    if not log_file_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_file_path}")
    
    with open(log_file_path, 'r') as f:
        logs = json.load(f)
    
    # Load reference solvent data
    ref_path = get_chemicals_path() / "solvents.yaml"
    import yaml
    with open(ref_path, 'r') as f:
        solvent_refs = yaml.safe_load(f)
    
    # Create lookup dict
    solvent_lookup = {s['name']: s for s in solvent_refs}
    
    results = []
    
    # Define tolerances (standard experimental tolerances)
    TEMP_TOLERANCE = 1.0  # ±1°C
    HUMIDITY_TOLERANCE = 2.0  # ±2% RH
    DIELECTRIC_TOLERANCE = 2.0  # ±2%
    
    for run in logs:
        run_id = run.get('run_id', 'unknown')
        solvent_name = run.get('solvent', 'unknown')
        
        validation_status = {
            'run_id': run_id,
            'solvent': solvent_name,
            'is_compliant': True,
            'flags': [],
            'metrics': {}
        }
        
        # Check Temperature
        temp = run.get('temperature_celsius')
        if temp is not None:
            # Assuming target is 25°C, but we check stability if target varies
            # For now, we check if it's within a reasonable range (24-26°C) or against a recorded target
            target_temp = run.get('target_temperature_celsius', 25.0)
            temp_dev = abs(temp - target_temp)
            validation_status['metrics']['temperature_deviation'] = temp_dev
            if temp_dev > TEMP_TOLERANCE:
                validation_status['is_compliant'] = False
                validation_status['flags'].append(f"Temperature deviation {temp_dev:.2f}°C exceeds tolerance ±{TEMP_TOLERANCE}°C")
        
        # Check Humidity
        humidity = run.get('relative_humidity_percent')
        if humidity is not None:
            target_humidity = run.get('target_relative_humidity_percent', 50.0)
            hum_dev = abs(humidity - target_humidity)
            validation_status['metrics']['humidity_deviation'] = hum_dev
            if hum_dev > HUMIDITY_TOLERANCE:
                validation_status['is_compliant'] = False
                validation_status['flags'].append(f"Humidity deviation {hum_dev:.2f}% RH exceeds tolerance ±{HUMIDITY_TOLERANCE}% RH")
        
        # Check Dielectric Constant
        if solvent_name in solvent_lookup:
            ref_solvent = solvent_lookup[solvent_name]
            is_dielectric_ok, dielectric_dev = check_dielectric_deviation(
                run, ref_solvent, tolerance_percent=DIELECTRIC_TOLERANCE
            )
            validation_status['metrics']['dielectric_deviation'] = dielectric_dev
            if not is_dielectric_ok:
                validation_status['is_compliant'] = False
                validation_status['flags'].append(f"Dielectric constant deviation {dielectric_dev:.2f}% exceeds tolerance ±{DIELECTRIC_TOLERANCE}%")
        else:
            logger.warning(f"Solvent {solvent_name} not found in reference data")
        
        results.append(validation_status)
    
    return results

def write_validation_report(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the validation report to a JSON file.
    
    Args:
        results: List of validation results from validate_solvent_series_runs.
        output_path: Path to write the report.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        'generated_at': str(pd.Timestamp.now(timezone.utc)),
        'total_runs': len(results),
        'compliant_runs': sum(1 for r in results if r['is_compliant']),
        'compliance_rate': sum(1 for r in results if r['is_compliant']) / len(results) * 100 if results else 0.0,
        'violations': [r for r in results if not r['is_compliant']],
        'details': results
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {output_path}")

def main() -> None:
    """
    Main entry point for running validation checks.
    Reads environment logs, validates against tolerances, and writes report.
    """
    import os
    import sys
    from datetime import datetime
    
    # Setup logging
    from utils.logging import setup_logging
    setup_logging()
    
    log_path = get_processed_data_path() / "environment_logs.json"
    report_path = get_processed_data_path() / "validation_report.json"
    
    if not log_path.exists():
        logger.error(f"Environment logs not found at {log_path}. Run environment logging first.")
        sys.exit(1)
    
    logger.info(f"Validating runs from {log_path}")
    
    try:
        results = validate_solvent_series_runs(log_path)
        write_validation_report(results, report_path)
        
        compliant = sum(1 for r in results if r['is_compliant'])
        total = len(results)
        logger.info(f"Validation complete: {compliant}/{total} runs compliant ({compliant/total*100:.1f}%)")
        
        if compliant < total:
            logger.warning("Some runs failed environmental compliance checks.")
            for r in results:
                if not r['is_compliant']:
                    logger.warning(f"Run {r['run_id']} ({r['solvent']}): {', '.join(r['flags'])}")
        
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()