"""
Final Gate Check (T057)

Verifies that:
1. data/gate_status.json exists and accurately reflects the Data Availability Gate outcome.
2. The pipeline logic correctly branched to either results_report.md or data_insufficiency_report.md.

This script is the final validation step before research_accepted transition.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def check_gate_status(gate_status_path: Path) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Check if gate_status.json exists and contains valid gate outcome.
    
    Returns:
        Tuple of (is_valid, gate_data, message)
    """
    if not gate_status_path.exists():
        return False, None, f"Gate status file not found: {gate_status_path}"
    
    try:
        with open(gate_status_path, 'r') as f:
            gate_data = json.load(f)
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON in gate status file: {e}"
    
    # Check required fields
    required_fields = ['gate_outcome', 'n_records', 'gate_passed']
    missing_fields = [field for field in required_fields if field not in gate_data]
    
    if missing_fields:
        return False, gate_data, f"Missing required fields in gate status: {missing_fields}"
    
    # Validate gate_outcome values
    valid_outcomes = ['PASS', 'FAIL', 'NO_DATA', 'NO_INTERSECTION']
    if gate_data['gate_outcome'] not in valid_outcomes:
        return False, gate_data, f"Invalid gate_outcome value: {gate_data['gate_outcome']}"
    
    # Validate gate_passed boolean
    if not isinstance(gate_data['gate_passed'], bool):
        return False, gate_data, "gate_passed must be a boolean"
    
    # Consistency check
    if gate_data['gate_passed'] and gate_data['gate_outcome'] == 'FAIL':
        return False, gate_data, "Inconsistent: gate_passed=True but gate_outcome=FAIL"
    
    if not gate_data['gate_passed'] and gate_data['gate_outcome'] == 'PASS':
        return False, gate_data, "Inconsistent: gate_passed=False but gate_outcome=PASS"
    
    return True, gate_data, f"Gate status valid: {gate_data['gate_outcome']} (N={gate_data['n_records']})"

def check_report_branching(
    project_root: Path,
    gate_passed: bool,
    gate_data: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Verify that the correct report was generated based on gate outcome.
    
    Args:
        project_root: Path to project root
        gate_passed: Boolean indicating if gate passed
        gate_data: Full gate status data
    
    Returns:
        Tuple of (is_valid, message)
    """
    results_report = project_root / 'results_report.md'
    insufficiency_report = project_root / 'data_insufficiency_report.md'
    
    if gate_passed:
        # Should have results_report.md
        if not results_report.exists():
            return False, f"Gate passed but results_report.md not found"
        
        # Should NOT have data_insufficiency_report.md (or it should be empty/placeholder)
        if insufficiency_report.exists():
            # Check if it's just a placeholder or if it has content
            size = insufficiency_report.stat().st_size
            if size > 100:  # Arbitrary threshold for "meaningful content"
                logger.warning(f"Gate passed but data_insufficiency_report.md exists with content ({size} bytes)")
                # This is a warning, not a failure - might be from a previous run
    
        # Verify results_report.md has meaningful content
        if results_report.stat().st_size == 0:
            return False, "results_report.md exists but is empty"
        
        # Check that results_report.md mentions the gate outcome
        with open(results_report, 'r') as f:
            content = f.read()
            if 'Data Availability Gate' not in content:
                logger.warning("results_report.md does not mention 'Data Availability Gate'")
            if str(gate_data['n_records']) not in content:
                logger.warning(f"results_report.md does not mention N={gate_data['n_records']}")
        
        return True, f"Correct branching: results_report.md generated for PASS (N={gate_data['n_records']})"
    
    else:
        # Should have data_insufficiency_report.md
        if not insufficiency_report.exists():
            return False, "Gate failed but data_insufficiency_report.md not found"
        
        # Should NOT have results_report.md (or it should be empty/placeholder)
        if results_report.exists():
            size = results_report.stat().st_size
            if size > 100:
                logger.warning(f"Gate failed but results_report.md exists with content ({size} bytes)")
        
        # Verify data_insufficiency_report.md has meaningful content
        if insufficiency_report.stat().st_size == 0:
            return False, "data_insufficiency_report.md exists but is empty"
        
        return True, f"Correct branching: data_insufficiency_report.md generated for FAIL (N={gate_data['n_records']})"

def main() -> int:
    """
    Main entry point for Final Gate Check.
    
    Returns:
        0 if all checks pass, 1 if any check fails
    """
    project_root = get_project_root()
    gate_status_path = project_root / 'data' / 'gate_status.json'
    
    logger.info("Starting Final Gate Check (T057)")
    logger.info(f"Project root: {project_root}")
    
    # Step 1: Check gate_status.json
    logger.info("Checking gate_status.json...")
    is_valid, gate_data, message = check_gate_status(gate_status_path)
    logger.info(message)
    
    if not is_valid:
        logger.error(f"Gate status check failed: {message}")
        return 1
    
    # Step 2: Check report branching
    logger.info("Checking report branching...")
    gate_passed = gate_data['gate_passed']
    is_valid, message = check_report_branching(project_root, gate_passed, gate_data)
    logger.info(message)
    
    if not is_valid:
        logger.error(f"Report branching check failed: {message}")
        return 1
    
    # Step 3: Final summary
    logger.info("=" * 60)
    logger.info("FINAL GATE CHECK PASSED")
    logger.info("=" * 60)
    logger.info(f"Gate Outcome: {gate_data['gate_outcome']}")
    logger.info(f"Records: {gate_data['n_records']}")
    logger.info(f"Gate Passed: {gate_data['gate_passed']}")
    logger.info(f"Branching: {'Results Report' if gate_passed else 'Insufficiency Report'}")
    logger.info("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
