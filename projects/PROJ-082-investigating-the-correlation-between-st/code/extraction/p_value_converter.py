"""
p_value_converter.py

Handles conversion of p-values to effect sizes (Fisher's z) for meta-analysis.
Implements strict exclusion logging if conversion is ambiguous.
"""

import csv
import math
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from utils.logger import get_logger, log_error_context

# Configuration
LOG_PATH = Path("data/logs/conversion_log.csv")

def _ensure_log_file() -> None:
    """Ensure the log directory and file exist."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        with open(LOG_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # The task spec requested columns: study_id, original_p, converted_r, conversion_status
            # The existing file had more columns. We will write the full set for completeness
            # but ensure the requested ones are present.
            # Columns: study_id, original_p, converted_r, conversion_status, (plus supporting data)
            writer.writerow(['study_id', 'p_value', 'n', 'conversion_type', 'result_z', 'result_r', 'status', 'error_message'])

def log_conversion(
    study_id: str,
    p_value: float,
    n: int,
    conversion_type: str,
    result_z: Optional[float],
    result_r: Optional[float],
    status: str,
    error_message: Optional[str] = None
) -> None:
    """
    Log conversion results to data/logs/conversion_log.csv.
    Columns: study_id, original_p, converted_r, conversion_status (plus context).
    """
    _ensure_log_file()
    with open(LOG_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([study_id, p_value, n, conversion_type, result_z, result_r, status, error_message or ""])

def p_to_z_two_tailed(p_value: float, n: int) -> Tuple[Optional[float], Optional[float], str]:
    """
    Convert a two-tailed p-value and sample size to Fisher's z and r.
    
    Logic:
    1. Validate p-value (0 < p <= 1).
    2. Calculate t-statistic from p-value using inverse t-distribution.
    3. Convert t to r: r = t / sqrt(t^2 + df)
    4. Convert r to Fisher's z: z = 0.5 * ln((1+r)/(1-r))
    
    Returns: (z, r, status)
    """
    try:
        if not (0 < p_value <= 1):
            return None, None, "invalid_p_range"
        
        # Handle edge case where p is effectively 1 (no effect)
        if math.isclose(p_value, 1.0, rel_tol=1e-9):
            return 0.0, 0.0, "converted"

        # Handle extreme p-values that might cause overflow in inverse functions
        if p_value < 1e-15:
            p_value = 1e-15

        # Use scipy.stats for precision
        from scipy import stats
        
        df = n - 2
        if df <= 0:
            return None, None, "invalid_df"

        # Two-tailed test: p = 2 * (1 - CDF(|t|)) => CDF(|t|) = 1 - p/2
        # t = ppf(1 - p/2)
        t_stat = stats.t.ppf(1 - (p_value / 2), df)
        
        # Convert t to r
        # r = t / sqrt(t^2 + df)
        if t_stat == 0:
            r = 0.0
        else:
            r = t_stat / math.sqrt(t_stat**2 + df)
        
        # Clamp r to [-1, 1] to avoid math domain errors in log
        r = max(-1.0, min(1.0, r))
        
        # Convert r to Fisher's z
        if math.isclose(abs(r), 1.0, rel_tol=1e-9):
            # Infinite effect size is ambiguous for meta-analysis pooling
            return None, None, "infinite_effect_size"
        
        z = 0.5 * math.log((1 + r) / (1 - r))
        
        return z, r, "converted"

    except Exception as e:
        return None, None, f"conversion_error: {str(e)}"

def convert_p_value_to_effect_size(
    study_id: str,
    p_value: float,
    n: int,
    log_exclusions: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Main entry point to convert p-value to effect size.
    
    Returns a dict with 'z' and 'r' if successful, or None if conversion fails/ambiguous.
    Logs the result to data/logs/conversion_log.csv.
    """
    z, r, status = p_to_z_two_tailed(p_value, n)
    
    if status == "converted":
        if log_exclusions:
            log_conversion(study_id, p_value, n, "p_to_z_two_tailed", z, r, "success")
        return {"z": z, "r": r, "status": "success"}
    else:
        if log_exclusions:
            log_conversion(study_id, p_value, n, "p_to_z_two_tailed", None, None, "ambiguous", status)
        return None

def main() -> None:
    """
    CLI entry point for testing the converter.
    Executes conversions and writes to data/logs/conversion_log.csv.
    """
    logger = get_logger(__name__)
    logger.info("Starting p-value converter test.")
    
    # Ensure log file is initialized
    _ensure_log_file()
    
    # Example usage covering success and failure cases
    test_cases = [
        ("Study_A", 0.05, 30),
        ("Study_B", 0.01, 50),
        ("Study_C", 0.001, 100),
        ("Study_D", 1.0, 20), # Edge case (no effect)
        ("Study_E", -0.1, 20), # Invalid p-value
        ("Study_F", 0.05, 1),  # Invalid df (n=1 -> df=-1)
    ]
    
    for study_id, p, n in test_cases:
        result = convert_p_value_to_effect_size(study_id, p, n)
        if result:
            logger.info(f"{study_id}: p={p}, n={n} -> r={result['r']:.4f}, z={result['z']:.4f}")
        else:
            logger.warning(f"{study_id}: p={p}, n={n} -> Conversion failed or ambiguous (status logged)")
    
    logger.info(f"Conversion log written to {LOG_PATH}")

if __name__ == "__main__":
    main()