"""
Data validator to check for critical variables and run completeness.
Implements T010: Exclude run if critical variables missing.

Logic:
- Exclude run if critical variables (throughput, latency) are missing.
- Proceed with reduced model ONLY if non-critical covariates are missing.
"""
import logging
from typing import List, Dict, Any, Tuple
from orchestrator.logger import get_logger

logger = get_logger(__name__)

# Critical variables that must be present for a run to be valid for analysis
CRITICAL_VARS = {"throughput_ops", "latency_ms"}

# Non-critical covariates that can be missing (reduced model)
NON_CRITICAL_VARS = {"cpu_utilization_pct", "packet_loss_rate", "node_heterogeneity_score"}

def validate_data_completeness(run_data: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Check for critical variables in the run data.
    
    Args:
        run_data: List of dictionaries representing execution run records.
                 Each record should contain metric keys like 'throughput_ops', 
                 'latency_ms', etc.
    
    Returns:
        Tuple[bool, str]: (is_valid, reason)
        - is_valid: True if critical variables are present, False otherwise.
        - reason: Human-readable explanation of the validation result.
    
    Logic:
        1. If run_data is empty, return False (exclude run).
        2. Check if ANY record in the run has 'throughput_ops' and 'latency_ms'.
        3. If either critical variable is missing across ALL records:
           - Return False with reason listing missing critical variables.
        4. If critical variables are present but non-critical covariates are missing:
           - Return True with warning about reduced model.
        5. If all expected variables are present:
           - Return True with success message.
    """
    if not run_data:
        return False, "Run data is empty. Excluding run."

    # Track presence of critical and non-critical variables across the dataset
    has_throughput = False
    has_latency = False
    missing_non_critical = set()

    # Check each record for variable presence
    for record in run_data:
        if "throughput_ops" in record and record["throughput_ops"] is not None:
            has_throughput = True
        if "latency_ms" in record and record["latency_ms"] is not None:
            has_latency = True
        
        # Track non-critical variables that are missing in this record
        for var in NON_CRITICAL_VARS:
            if var not in record or record[var] is None:
                missing_non_critical.add(var)

    # Check critical variables first - if missing, exclude the run
    if not has_throughput or not has_latency:
        missing_critical = []
        if not has_throughput:
            missing_critical.append("throughput_ops")
        if not has_latency:
            missing_critical.append("latency_ms")
        
        reason = (
            f"Critical variables missing: {', '.join(missing_critical)}. "
            f"Run excluded from analysis (SC-006)."
        )
        logger.warning(reason)
        return False, reason

    # Critical variables are present - check for non-critical gaps
    if missing_non_critical:
        reason = (
            f"Non-critical covariates missing: {', '.join(missing_non_critical)}. "
            f"Proceeding with reduced model. Critical variables (throughput_ops, latency_ms) present."
        )
        logger.info(reason)
        return True, reason

    # All good
    reason = "Data validation passed. All critical and non-critical variables present."
    logger.info(reason)
    return True, reason

def get_missing_variables(run_data: List[Dict[str, Any]]) -> Tuple[set, set]:
    """
    Helper function to identify exactly which variables are missing.
    
    Args:
        run_data: List of dictionaries representing execution run records.
    
    Returns:
        Tuple[set, set]: (missing_critical, missing_non_critical)
    """
    if not run_data:
        return set(), set()

    present_critical = set()
    present_non_critical = set()

    for record in run_data:
        for var in CRITICAL_VARS:
            if var in record and record[var] is not None:
                present_critical.add(var)
        for var in NON_CRITICAL_VARS:
            if var in record and record[var] is not None:
                present_non_critical.add(var)

    missing_critical = CRITICAL_VARS - present_critical
    missing_non_critical = NON_CRITICAL_VARS - present_non_critical

    return missing_critical, missing_non_critical
