"""
Task T040: Calculate Family-Wise Error Rate (FWER) and verify correction effectiveness.

This module reads the statistics from results/stats.csv (produced by T039),
calculates the Family-Wise Error Rate (FWER) based on the corrected p-values,
and updates the results/stats.csv file with the FWER metric.

FWER is the probability of making one or more false discoveries (Type I errors)
among all the hypotheses tested.
"""
import os
import sys
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.exceptions import DataError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RESULTS_DIR = PROJECT_ROOT / "results"
STATS_CSV_PATH = RESULTS_DIR / "stats.csv"

def load_stats_csv(path: Path) -> List[Dict[str, Any]]:
    """Load existing statistics from CSV."""
    if not path.exists():
        raise DataError(f"Stats file not found: {path}. Ensure T039 has run.")
    
    rows = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats where appropriate
            processed_row = {}
            for k, v in row.items():
                try:
                    processed_row[k] = float(v)
                except (ValueError, TypeError):
                    processed_row[k] = v
            rows.append(processed_row)
    return rows

def calculate_fwer(corrected_p_values: List[float]) -> float:
    """
    Calculate the Family-Wise Error Rate (FWER).
    
    FWER is the probability of at least one Type I error.
    If we assume independence or use the max-statistic approach,
    FWER can be estimated as 1 - product(1 - corrected_p_i) for all i.
    However, in the context of reporting a single metric for the experiment,
    we often report the maximum corrected p-value or the probability that
    any null hypothesis is rejected when it is true.
    
    Here, we calculate the empirical FWER estimate based on the provided
    corrected p-values. If we treat the corrected p-values as the probability
    of error for each test, the FWER (probability of >=1 error) under
    independence is 1 - product(1 - p_i).
    
    Alternatively, if the correction method (e.g., Bonferroni) was applied
    correctly to control FWER at level alpha, the FWER is bounded by alpha.
    We will calculate the empirical FWER estimate: 1 - prod(1 - p_corrected).
    
    Args:
        corrected_p_values: List of corrected p-values for each metric.
    
    Returns:
        Estimated FWER.
    """
    if not corrected_p_values:
        return 0.0
    
    # Ensure values are in [0, 1]
    valid_p_values = [max(0.0, min(1.0, p)) for p in corrected_p_values]
    
    # Calculate probability of NO errors: product(1 - p_i)
    prob_no_error = 1.0
    for p in valid_p_values:
        prob_no_error *= (1.0 - p)
    
    # FWER = 1 - P(no errors)
    fwer = 1.0 - prob_no_error
    return fwer

def verify_correction_effectiveness(fwer: float, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Verify if the correction was effective in controlling FWER below alpha.
    
    Args:
        fwer: Calculated Family-Wise Error Rate.
        alpha: Significance level (default 0.05).
    
    Returns:
        Dict with verification results.
    """
    is_effective = fwer <= alpha
    return {
        "fwer": fwer,
        "alpha": alpha,
        "is_effective": is_effective,
        "message": f"FWER ({fwer:.6f}) {'is' if is_effective else 'is NOT'} controlled below alpha ({alpha})."
    }

def update_stats_csv(path: Path, fwer: float, verification: Dict[str, Any]) -> None:
    """
    Update the stats.csv file to include the FWER metric row.
    
    The existing CSV should have columns: metric, observed_value, p_value, 
    corrected_p_value, vif_score, fwer.
    
    We will append a new row for the 'fwer' metric itself, or update an existing
    summary row if present. For simplicity, we append a new row.
    """
    fieldnames = ['metric', 'observed_value', 'p_value', 'corrected_p_value', 'vif_score', 'fwer']
    
    # Read existing rows
    rows = []
    if path.exists():
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or fieldnames
            for row in reader:
                rows.append(row)
    
    # Prepare new row for FWER
    new_row = {
        'metric': 'fwer',
        'observed_value': f"{fwer:.6f}",
        'p_value': "",  # FWER is a rate, not a p-value in the traditional sense
        'corrected_p_value': "", 
        'vif_score': "",
        'fwer': f"{fwer:.6f}"
    }
    
    # Add verification info to the row (optional, or just rely on the fwer column)
    # We'll stick to the defined schema.
    
    rows.append(new_row)
    
    # Write back
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Updated {path} with FWER metric.")

def main():
    """Main entry point for T040."""
    logger.info("Starting T040: Calculate Family-Wise Error Rate (FWER).")
    
    if not STATS_CSV_PATH.exists():
        logger.error(f"Stats file not found: {STATS_CSV_PATH}.")
        logger.error("Ensure T039 (Bonferroni/Holm correction) has completed successfully.")
        raise DataError("Missing stats.csv from previous step.")
    
    try:
        stats = load_stats_csv(STATS_CSV_PATH)
        
        # Extract corrected p-values from the stats
        # We look for rows that have a 'corrected_p_value' column with a numeric value
        corrected_p_values = []
        for row in stats:
            c_p_val = row.get('corrected_p_value')
            if c_p_val is not None and isinstance(c_p_val, (int, float)) and not (isinstance(c_p_val, float) and c_p_val != c_p_val): # check for NaN
                corrected_p_values.append(float(c_p_val))
            elif isinstance(c_p_val, str):
                try:
                    val = float(c_p_val)
                    corrected_p_values.append(val)
                except ValueError:
                    pass
        
        if not corrected_p_values:
            logger.warning("No corrected p-values found in stats.csv. FWER calculation skipped.")
            # Still create a row indicating this? Or just exit?
            # Let's calculate FWER as 0 if no tests were corrected, or handle as error.
            # Assuming if no tests, FWER is 0.
            fwer = 0.0
        else:
            fwer = calculate_fwer(corrected_p_values)
        
        verification = verify_correction_effectiveness(fwer)
        
        logger.info(f"Calculated FWER: {fwer:.6f}")
        logger.info(f"Verification: {verification['message']}")
        
        update_stats_csv(STATS_CSV_PATH, fwer, verification)
        
        logger.info("T040 completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during T040 execution: {e}")
        raise

if __name__ == "__main__":
    main()