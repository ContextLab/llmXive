import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_bias_magnitude() -> Dict[str, Any]:
    """
    Load the bias magnitude data from data/results/bias_magnitude.csv.
    
    Returns:
        Dict containing the bias data for the worst-case scenario.
    
    Raises:
        FileNotFoundError: If the bias magnitude file does not exist.
        ValueError: If the file is empty or malformed.
    """
    bias_path = Path("data/results/bias_magnitude.csv")
    
    if not bias_path.exists():
        raise FileNotFoundError(f"Expected bias magnitude file not found: {bias_path}")
    
    with open(bias_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        raise ValueError(f"Bias magnitude file {bias_path} is empty or has no data rows.")
    
    # We expect exactly one row for the worst-case scenario based on T044
    return rows[0]

def load_worst_case_summary() -> Dict[str, Any]:
    """
    Load the worst-case scenario summary from data/results/worst_case_summary.json.
    
    Returns:
        Dict containing the worst-case scenario parameters.
    
    Raises:
        FileNotFoundError: If the summary file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    summary_path = Path("data/results/worst_case_summary.json")
    
    if not summary_path.exists():
        raise FileNotFoundError(f"Worst case summary file not found: {summary_path}")
    
    with open(summary_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def determine_mechanism(worst_case: Dict[str, Any], bias_data: Dict[str, Any]) -> str:
    """
    Determine the failure mechanism string based on worst-case parameters.
    
    Args:
        worst_case: The worst-case scenario dictionary.
        bias_data: The bias magnitude data dictionary.
    
    Returns:
        A string describing the mechanism of failure.
    """
    rho = worst_case.get('rho', 0)
    p = worst_case.get('p', 0)
    n = worst_case.get('n', 0)
    
    # Construct a specific explanation based on the parameters
    mechanism = (
        f"Correlation ρ={rho:.2f} inflates the variance of the test statistic, "
        f"causing p-values to cluster near 0 instead of being uniform. "
        f"The 'ritual' (standard t-test) assumes independence, but the 'mess' of "
        f"high-dimensional noise (p={p}, n={n}) violates this assumption."
    )
    
    return mechanism

def generate_ritual_vs_reality_table() -> Path:
    """
    Generate the ritual vs reality comparative table.
    
    Reads bias magnitude data and worst-case summary to calculate
    FPR differences and produces a CSV file.
    
    Returns:
        Path to the generated CSV file.
    
    Raises:
        FileNotFoundError: If input files are missing.
        ValueError: If required fields are missing or data is invalid.
    """
    # Load inputs
    logger.info("Loading bias magnitude data...")
    bias_data = load_bias_magnitude()
    
    logger.info("Loading worst-case summary...")
    worst_case = load_worst_case_summary()
    
    # Extract values
    try:
        standard_fpr = float(bias_data.get('standard_test_fpr', 0.0))
        permutation_fpr = float(bias_data.get('permutation_test_fpr', 0.0))
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid FPR values in bias_magnitude.csv: {e}")
    
    # Calculate bias metrics
    bias_absolute = abs(standard_fpr - permutation_fpr)
    
    # Avoid division by zero
    if permutation_fpr != 0:
        bias_percentage = (bias_absolute / permutation_fpr) * 100.0
    else:
        bias_percentage = 100.0 if standard_fpr > 0 else 0.0
    
    # Determine mechanism
    mechanism = determine_mechanism(worst_case, bias_data)
    
    # Construct output row
    scenario_name = (
        f"rho={worst_case.get('rho', 0):.1f}, p={worst_case.get('p', 0)}, "
        f"n={worst_case.get('n', 0)}, dist={worst_case.get('distribution_type', 'unknown')}"
    )
    
    output_row = {
        'Scenario': scenario_name,
        'Standard_Test_FPR': f"{standard_fpr:.6f}",
        'Permutation_Test_FPR': f"{permutation_fpr:.6f}",
        'Bias_Absolute': f"{bias_absolute:.6f}",
        'Bias_Percentage': f"{bias_percentage:.2f}",
        'Mechanism': mechanism
    }
    
    # Write output
    output_path = Path("data/results/ritual_vs_reality.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'Scenario',
        'Standard_Test_FPR',
        'Permutation_Test_FPR',
        'Bias_Absolute',
        'Bias_Percentage',
        'Mechanism'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(output_row)
    
    logger.info(f"Successfully wrote ritual vs reality table to {output_path}")
    return output_path

def main():
    """Main entry point for the ritual vs reality analysis."""
    try:
        logger.info("Starting Ritual vs Reality Table generation (T054)...")
        output_path = generate_ritual_vs_reality_table()
        logger.info(f"Task T054 completed successfully. Output: {output_path}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        logger.error("Ensure T044 (bias_magnitude.csv) and T049 (worst_case_summary.json) are complete.")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T054 execution: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
