import os
import csv
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.anova import AnovaRM
from code.config import DATA_PROCESSED_DIR

def load_data():
    """Load the aggregated energy results."""
    input_path = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Data file not found: {input_path}")
    return pd.read_csv(input_path)

def perturb_energy_values(df, perturbation_pct=0.10, seed=42):
    """
    Create a copy of the dataframe with energy values perturbed by +/- perturbation_pct.
    Uses a fixed seed for reproducibility.
    """
    np.random.seed(seed)
    df_perturbed = df.copy()
    
    # Generate random perturbations between -pct and +pct
    # We apply this to the 'energy_kwh' column
    if 'energy_kwh' not in df_perturbed.columns:
        raise ValueError("Dataset must contain 'energy_kwh' column for perturbation.")
    
    # Filter out nulls if any exist to avoid NaN propagation in perturbation math
    mask = df_perturbed['energy_kwh'].notna()
    
    # Calculate perturbation factors
    random_factors = 1.0 + np.random.uniform(-perturbation_pct, perturbation_pct, size=len(df_perturbed))
    
    # Apply perturbation only to valid rows
    df_perturbed.loc[mask, 'energy_kwh'] = df_perturbed.loc[mask, 'energy_kwh'] * random_factors[mask]
    
    return df_perturbed

def run_anova_on_data(df):
    """
    Run Repeated-Measures ANOVA on the provided dataframe.
    Returns the p-value from the ANOVA F-test.
    """
    if df.empty:
        return None

    # Ensure required columns exist
    required_cols = ['energy_kwh', 'model_id', 'problem_id']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DataFrame missing required columns for ANOVA: {required_cols}")

    # Drop rows with NaN in energy_kwh for the test
    df_clean = df.dropna(subset=['energy_kwh'])
    
    if len(df_clean) < 3:
        return None

    try:
        # Perform Repeated Measures ANOVA
        # 'model_id' is the within-subject factor, 'problem_id' is the subject
        anova_table = AnovaRM(
            df_clean, 
            depvar='energy_kwh', 
            subject='problem_id', 
            within=['model_id']
        ).fit()
        
        # Extract p-value for the 'model_id' effect
        # The table structure usually has 'model_id' as a row index
        p_value = anova_table.tables[0].loc['model_id', 'Pr > F']
        return float(p_value)
    except Exception as e:
        # Log warning but return None if ANOVA fails
        print(f"Warning: ANOVA failed on dataset: {e}")
        return None

def run_sensitivity_analysis(original_p_value, perturbed_p_value):
    """
    Calculate delta and determine robustness flag.
    Robustness logic: If the p-value change is small (e.g., < 0.05 absolute delta) 
    and the significance conclusion (p < 0.05) remains the same, it is robust.
    """
    if original_p_value is None or perturbed_p_value is None:
        return None, False, "Missing data"

    delta = perturbed_p_value - original_p_value
    
    # Determine significance status
    sig_orig = original_p_value < 0.05
    sig_pert = perturbed_p_value < 0.05
    
    # Robust if significance status didn't change AND delta is within reasonable bounds
    is_robust = (sig_orig == sig_pert) and (abs(delta) < 0.05)
    
    return delta, is_robust, "Robust" if is_robust else "Sensitive"

def main():
    """
    Main entry point for T024b: Sensitivity Analysis Output Generation.
    1. Loads aggregated data.
    2. Runs ANOVA on original data (re-using logic from T024a conceptually, 
       but explicitly running here to ensure fresh calculation).
    3. Perturbs data.
    4. Runs ANOVA on perturbed data.
    5. Computes delta and robustness.
    6. Writes results to data/processed/sensitivity_delta.csv.
    """
    print("Starting Sensitivity Analysis (T024b)...")
    
    # 1. Load original data
    df_original = load_data()
    print(f"Loaded {len(df_original)} rows from energy_results_aggregated.csv")
    
    # 2. Run ANOVA on original
    p_original = run_anova_on_data(df_original)
    print(f"Original ANOVA p-value: {p_original}")
    
    # 3. Perturb data
    df_perturbed = perturb_energy_values(df_original, perturbation_pct=0.10)
    
    # 4. Run ANOVA on perturbed
    p_perturbed = run_anova_on_data(df_perturbed)
    print(f"Perturbed ANOVA p-value: {p_perturbed}")
    
    # 5. Calculate metrics
    delta, is_robust, status = run_sensitivity_analysis(p_original, p_perturbed)
    print(f"Delta p-value: {delta}, Status: {status}")
    
    # 6. Write output
    output_path = os.path.join(DATA_PROCESSED_DIR, "sensitivity_delta.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    results = [{
        'original_p_value': p_original,
        'perturbed_p_value': p_perturbed,
        'delta_p_value': delta,
        'is_robust': is_robust,
        'status': status
    }]
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_path, index=False)
    
    print(f"Sensitivity results written to {output_path}")
    return output_path

if __name__ == "__main__":
    main()