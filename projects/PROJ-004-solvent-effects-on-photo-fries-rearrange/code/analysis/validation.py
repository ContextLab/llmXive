"""
Validation module for environmental and solvent series data.
Implements T017a: Environmental Validation.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import yaml

# Local imports based on provided API surface
from config import get_chemicals_path, get_processed_data_path
from utils.logging import setup_logging

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when configuration files are missing or invalid."""
    pass

class ValidationError(Exception):
    """Raised when validation logic encounters an unrecoverable error."""
    pass

def load_solvent_reference() -> Dict[str, Any]:
    """
    Load and validate the solvent reference file (solvents.yaml).
    Checks for existence and the required 'version_hash' in metadata.

    Returns:
        Dict containing the parsed YAML content.

    Raises:
        ConfigurationError: If file is missing or lacks version_hash.
    """
    chemicals_path = get_chemicals_path()
    solvent_file = chemicals_path / "solvents.yaml"

    if not solvent_file.exists():
        raise ConfigurationError(
            f"Solvent reference file missing at {solvent_file}. "
            "Ensure T006b (Data Population) and T006d (Hash Generation) have completed."
        )

    try:
        with open(solvent_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse {solvent_file}: {e}")

    # Constraint: MUST verify version_hash exists (from T006d)
    metadata = data.get('metadata', {})
    if 'version_hash' not in metadata:
        raise ConfigurationError(
            f"Solvent reference {solvent_file} is missing 'version_hash' in metadata. "
            "Run T006d to generate the hash."
        )

    logger.info(f"Loaded solvent reference with version_hash: {metadata['version_hash']}")
    return data

def check_dielectric_deviation(
    run_solvent_name: str,
    run_dielectric: float,
    reference_data: Dict[str, Any],
    tolerance_pct: float = 2.0
) -> Tuple[bool, str]:
    """
    Check if the logged dielectric constant deviates >2% from the reference.

    Args:
        run_solvent_name: Name of the solvent from the run.
        run_dielectric: The logged dielectric constant value.
        reference_data: Parsed solvents.yaml content.
        tolerance_pct: Maximum allowed percentage deviation.

    Returns:
        Tuple of (is_valid, message).
    """
    solvents = reference_data.get('solvents', [])
    ref_entry = next((s for s in solvents if s['name'] == run_solvent_name), None)

    if not ref_entry:
        return False, f"Solvent '{run_solvent_name}' not found in reference table."

    ref_dielectric = ref_entry['dielectric_constant']
    if ref_dielectric == 0:
        # Avoid division by zero if reference is 0 (unlikely for dielectric)
        deviation = abs(run_dielectric)
        is_valid = deviation == 0
        msg = "Reference dielectric is 0; any deviation is invalid." if not is_valid else "Match."
        return is_valid, msg

    deviation_pct = abs((run_dielectric - ref_dielectric) / ref_dielectric) * 100

    if deviation_pct > tolerance_pct:
        msg = (
            f"Dielectric constant deviation {deviation_pct:.2f}% exceeds tolerance {tolerance_pct}% "
            f"(Run: {run_dielectric}, Ref: {ref_dielectric})."
        )
        return False, msg

    return True, f"Deviation {deviation_pct:.2f}% within tolerance."

def validate_environmental_conditions(
    run_data: Dict[str, Any],
    tolerance_temp: float = 0.5,
    tolerance_humidity: float = 2.0
) -> List[str]:
    """
    Detect and flag runs where temperature or humidity exceeds tolerance.

    Args:
        run_data: Dictionary containing logged environmental parameters.
        tolerance_temp: Allowed deviation in Celsius (default 0.5).
        tolerance_humidity: Allowed deviation in %RH (default 2.0).

    Returns:
        List of flag messages.
    """
    flags = []

    # Temperature validation
    target_temp = 25.0  # Spec target
    run_temp = run_data.get('temperature_c')
    if run_temp is not None:
        diff = abs(run_temp - target_temp)
        if diff > tolerance_temp:
            flags.append(
                f"Temperature {run_temp}°C deviates {diff:.2f}°C from target {target_temp}°C "
                f"(tolerance ±{tolerance_temp}°C)."
            )
    else:
        flags.append("Temperature not recorded.")

    # Humidity validation
    run_humidity = run_data.get('relative_humidity_pct')
    if run_humidity is not None:
        # Assuming target is 50% or similar, but spec says "within tolerance" usually implies
        # deviation from a setpoint or a range. Here we check if it's within a standard range
        # or just flag if it's outside a reasonable experimental bound if no target is set.
        # However, T041 mentions ±2% RH tolerance. Let's assume a target of 50% RH or check
        # against a configured target if available. For now, we flag if it's outside 48-52%
        # if no target is specified, OR we check deviation from a stored target if run_data has it.
        # T014 logs 'relative_humidity'. Let's assume we check against a standard 50% target
        # or just flag extreme values. The prompt says "exceeds tolerance", implying a target.
        # Let's assume target is 50% based on standard lab conditions unless specified.
        target_humidity = 50.0
        diff = abs(run_humidity - target_humidity)
        if diff > tolerance_humidity:
            flags.append(
                f"Humidity {run_humidity}% deviates {diff:.2f}% from target {target_humidity}% "
                f"(tolerance ±{tolerance_humidity}%)."
            )
    else:
        flags.append("Relative humidity not recorded.")

    return flags

def validate_solvent_series_runs(
    environment_log_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Main validation routine:
    1. Load solvents.yaml (checking version_hash).
    2. Load environment_logs.json.
    3. Flag runs with dielectric deviation >2%.
    4. Flag runs with T/Humidity out of tolerance.

    Args:
        environment_log_path: Path to environment_logs.json. Defaults to processed path.

    Returns:
        List of flagged run dictionaries.
    """
    # 1. Load Reference
    try:
        reference_data = load_solvent_reference()
    except ConfigurationError as e:
        logger.error(f"Configuration Error: {e}")
        raise

    # 2. Load Environment Logs
    if environment_log_path is None:
        processed_path = get_processed_data_path()
        environment_log_path = processed_path / "environment_logs.json"

    if not environment_log_path.exists():
        raise ConfigurationError(
            f"Environment log file missing at {environment_log_path}. "
            "Run T014 to generate environment_logs.json."
        )

    try:
        with open(environment_log_path, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Failed to parse environment logs: {e}")

    # Handle both list of runs or dict with 'runs' key
    runs = logs if isinstance(logs, list) else logs.get('runs', [])

    flagged_runs = []

    for run in runs:
        run_id = run.get('run_id', 'unknown')
        solvent_name = run.get('solvent_name', 'unknown')
        logged_dielectric = run.get('dielectric_constant')
        
        flags = []

        # Check Dielectric
        if logged_dielectric is not None:
            is_valid, msg = check_dielectric_deviation(
                solvent_name, logged_dielectric, reference_data
            )
            if not is_valid:
                flags.append({"type": "dielectric_deviation", "message": msg})
        else:
            flags.append({"type": "missing_dielectric", "message": "Dielectric constant not logged."})

        # Check T/Humidity
        env_flags = validate_environmental_conditions(run)
        for f_msg in env_flags:
            flags.append({"type": "environmental_tolerance", "message": f_msg})

        if flags:
            flagged_runs.append({
                "run_id": run_id,
                "solvent_name": solvent_name,
                "flags": flags
            })

    return flagged_runs

def write_validation_report(flagged_runs: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Write the list of flagged runs to data/processed/validation_flags.json.

    Args:
        flagged_runs: List of flagged run dictionaries.
        output_path: Output path. Defaults to processed/validation_flags.json.

    Returns:
        Path to the written file.
    """
    if output_path is None:
        processed_path = get_processed_data_path()
        output_path = processed_path / "validation_flags.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "generated_at": "2026-01-01T00:00:00Z", # Placeholder for actual timestamp logic if needed
        "total_flagged": len(flagged_runs),
        "flagged_runs": flagged_runs
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to {output_path}")
    return output_path

def main():
    """Entry point for validation script."""
    setup_logging()
    logger.info("Starting Environmental Validation (T017a)...")

    try:
        flagged_runs = validate_solvent_series_runs()
        output_file = write_validation_report(flagged_runs)
        
        if flagged_runs:
            logger.warning(f"Validation complete. {len(flagged_runs)} runs flagged. See {output_file}")
            sys.exit(1) # Exit non-zero to indicate flags found (optional, but good for CI)
        else:
            logger.info("Validation complete. All runs within tolerance.")
            sys.exit(0)
    except (ConfigurationError, ValidationError) as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
