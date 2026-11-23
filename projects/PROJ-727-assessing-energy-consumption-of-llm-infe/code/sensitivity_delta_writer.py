"""
Sensitivity Delta Writer (Task T024b)

Implements FR-012: Writes the sensitivity comparison results (original p-value vs. perturbed p-value, delta, robustness flag)
to data/processed/sensitivity_delta.csv.

This module depends on the sensitivity analysis logic in code/sensitivity_analysis.py which produces the necessary
original and perturbed ANOVA results.
"""
import os
import pandas as pd
import numpy as np
from code.config import DATA_PROCESSED_DIR
from code.sensitivity_analysis import load_data, perturb_energy_values, run_anova_on_data

def calculate_sensitivity_delta(original_p_value: float, perturbed_p_value: float) -> float:
    """
    Calculate the absolute delta between original and perturbed p-values.
    
    Args:
        original_p_value: P-value from the original dataset ANOVA.
        perturbed_p_value: P-value from the perturbed dataset ANOVA.
        
    Returns:
        Absolute difference between the two p-values.
    """
    return abs(original_p_value - perturbed_p_value)

def determine_robustness(delta: float, threshold: float = 0.1) -> str:
    """
    Determine robustness flag based on the delta.
    
    Args:
        delta: The absolute difference in p-values.
        threshold: Threshold for robustness (default 0.1). If delta < threshold, it's robust.
        
    Returns:
        'Robust' if delta < threshold, otherwise 'Sensitive'.
    """
    return "Robust" if delta < threshold else "Sensitive"

def write_sensitivity_comparison(
    original_p_value: float,
    perturbed_p_value: float,
    delta: float,
    robustness: str,
    output_path: str
) -> None:
    """
    Write the sensitivity comparison results to a CSV file.
    
    Args:
        original_p_value: Original ANOVA p-value.
        perturbed_p_value: Perturbed ANOVA p-value.
        delta: Absolute difference between p-values.
        robustness: 'Robust' or 'Sensitive' flag.
        output_path: Path to the output CSV file.
    """
    df = pd.DataFrame([{
        'original_p_value': original_p_value,
        'perturbed_p_value': perturbed_p_value,
        'delta_p_value': delta,
        'robustness_flag': robustness
    }])
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    print(f"Sensitivity comparison results written to {output_path}")

def main() -> None:
    """
    Main entry point for T024b:
    1. Load original data.
    2. Run ANOVA on original data to get original p-value.
    3. Perturb energy values by ±10%.
    4. Run ANOVA on perturbed data to get perturbed p-value.
    5. Calculate delta and robustness.
    6. Write results to data/processed/sensitivity_delta.csv.
    """
    # Ensure output directory exists
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    output_path = os.path.join(DATA_PROCESSED_DIR, "sensitivity_delta.csv")
    
    # 1. Load original data
    print("Loading original data...")
    original_df = load_data()
    
    if original_df is None or original_df.empty:
        raise RuntimeError("Failed to load original data for sensitivity analysis.")
        
    # 2. Run ANOVA on original data
    print("Running ANOVA on original data...")
    original_result = run_anova_on_data(original_df)
    original_p_value = original_result.pvalue
    print(f"Original ANOVA p-value: {original_p_value}")
    
    # 3. Perturb energy values by ±10%
    print("Perturbing energy values by ±10%...")
    perturbed_df = perturb_energy_values(original_df, perturbation_percent=10)
    
    if perturbed_df is None or perturbed_df.empty:
        raise RuntimeError("Failed to generate perturbed dataset.")
        
    # 4. Run ANOVA on perturbed data
    print("Running ANOVA on perturbed data...")
    perturbed_result = run_anova_on_data(perturbed_df)
    perturbed_p_value = perturbed_result.pvalue
    print(f"Perturbed ANOVA p-value: {perturbed_p_value}")
    
    # 5. Calculate delta and robustness
    delta = calculate_sensitivity_delta(original_p_value, perturbed_p_value)
    robustness = determine_robustness(delta)
    print(f"Delta p-value: {delta}, Robustness: {robustness}")
    
    # 6. Write results
    write_sensitivity_comparison(
        original_p_value,
        perturbed_p_value,
        delta,
        robustness,
        output_path
    )

if __name__ == "__main__":
    main()
