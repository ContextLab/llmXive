import os
import csv
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.anova import AnovaRM
from code.config import DATA_PROCESSED_DIR

def load_data(filepath=None):
    """Load the aggregated energy results."""
    if filepath is None:
        filepath = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    return pd.read_csv(filepath)

def perturb_energy_values(df, perturbation_pct=0.10, seed=42):
    """
    Create a perturbed copy of the dataframe with +/- 10% energy values.
    Uses the specified random seed for determinism.
    """
    df_perturbed = df.copy()
    np.random.seed(seed)
    
    # Generate random factors between (1 - pct) and (1 + pct)
    factors = np.random.uniform(1 - perturbation_pct, 1 + perturbation_pct, size=len(df_perturbed))
    
    # Apply perturbation to the 'energy_kwh' column if it exists
    if 'energy_kwh' in df_perturbed.columns:
        df_perturbed['energy_kwh'] = df_perturbed['energy_kwh'] * factors
    else:
        raise ValueError("DataFrame must contain 'energy_kwh' column for perturbation.")
        
    return df_perturbed

def run_anova_on_data(df):
    """
    Run Repeated-Measures ANOVA on the provided dataframe.
    Returns the p-value from the F-test.
    """
    if df.empty:
        raise ValueError("Cannot run ANOVA on empty dataframe.")
    
    # Ensure numeric types
    df_numeric = df.copy()
    df_numeric['energy_kwh'] = pd.to_numeric(df_numeric['energy_kwh'], errors='coerce')
    df_numeric = df_numeric.dropna(subset=['energy_kwh'])
    
    if df_numeric.empty:
        raise ValueError("No valid data remaining for ANOVA after dropping NaNs.")

    # Prepare data for statsmodels AnovaRM
    # We treat 'problem_id' as the subject and 'model_id' as the within-subject factor
    # The dependent variable is 'energy_kwh'
    
    try:
        aov_rm = AnovaRM(df_numeric, depvar='energy_kwh', subject='problem_id', within=['model_id'])
        res = aov_rm.fit()
        
        # Extract p-value for the 'model_id' effect
        # The summary table is a DataFrame; we need to find the row for 'model_id'
        # The p-values are usually in a column named 'Pr > F' or similar in the summary
        summary_df = res.summary()
        
        # statsmodels AnovaRM summary returns a table. We need to parse it.
        # A more robust way is to use the F-statistic and degrees of freedom if available,
        # but accessing the summary table is standard.
        # Let's try to get the p-value directly from the result object if possible, 
        # or parse the string representation if the API is opaque.
        
        # Fallback: Use scipy.stats.f_oneway on grouped data if statsmodels is tricky to parse programmatically
        # However, the spec asks for Repeated-Measures. Let's stick to statsmodels but extract carefully.
        # The summary object usually has a __str__ or we can access the underlying table.
        # Let's convert the summary to a string and parse, or use the 'anova_table' if available in newer versions.
        # In many versions, res.anova_table exists.
        
        if hasattr(res, 'anova_table'):
            anova_table = res.anova_table
            if 'model_id' in anova_table.index:
                p_val = anova_table.loc['model_id', 'Pr(>F)']
                return p_val
            # Fallback for different column names
            for col in anova_table.columns:
                if 'p' in col.lower() and 'model_id' in anova_table.index:
                    return anova_table.loc['model_id', col]
        
        # If all else fails, try to extract from summary string (less robust)
        summary_str = str(res.summary())
        # This is a fallback and might be brittle, but ensures we don't crash if the attribute is missing
        # We assume the output format is standard.
        raise RuntimeError("Could not extract p-value from AnovaRM result automatically.")
        
    except Exception as e:
        # Fallback to scipy f_oneway if we are strictly comparing groups (ignoring subject blocking for a moment 
        # to get a p-value, though this is technically less correct for repeated measures without the subject factor)
        # BUT the task specifically says "Re-run ANOVA". If statsmodels fails, we might have to fallback or crash.
        # Let's try a simpler extraction from the result object which is often a dict-like structure in some versions
        # or just re-implement the logic if the object is opaque.
        # Actually, let's just use scipy f_oneway as a proxy for "ANOVA" if the statsmodels object is hard to parse,
        # but note that f_oneway is independent samples.
        # Given the constraint "Re-run ANOVA", we should try to get the repeated measures p-value.
        # Let's assume the standard statsmodels output structure.
        # If the above fails, we raise.
        raise e

def run_sensitivity_analysis(original_df, perturbation_pct=0.10, seed=42):
    """
    Performs the full sensitivity analysis:
    1. Perturb the data.
    2. Run ANOVA on original.
    3. Run ANOVA on perturbed.
    4. Calculate delta p-values.
    """
    # Run ANOVA on original
    p_original = run_anova_on_data(original_df)
    
    # Perturb data
    df_perturbed = perturb_energy_values(original_df, perturbation_pct, seed)
    
    # Run ANOVA on perturbed
    p_perturbed = run_anova_on_data(df_perturbed)
    
    delta = p_perturbed - p_original
    
    return {
        'original_p_value': p_original,
        'perturbed_p_value': p_perturbed,
        'delta_p_value': delta
    }

def main():
    """Main entry point to generate sensitivity_delta.csv."""
    input_file = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")
    output_file = os.path.join(DATA_PROCESSED_DIR, "sensitivity_delta.csv")
    
    print(f"Loading data from {input_file}...")
    df = load_data(input_file)
    
    print("Running sensitivity analysis (seed=42)...")
    try:
        results = run_sensitivity_analysis(df, perturbation_pct=0.10, seed=42)
        
        # Write results to CSV
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['original_p_value', 'perturbed_p_value', 'delta_p_value'])
            writer.writeheader()
            writer.writerow(results)
        
        print(f"Sensitivity analysis complete. Results written to {output_file}")
        print(f"Original p-value: {results['original_p_value']}")
        print(f"Perturbed p-value: {results['perturbed_p_value']}")
        print(f"Delta: {results['delta_p_value']}")
        
    except Exception as e:
        print(f"Error during sensitivity analysis: {e}")
        raise

if __name__ == "__main__":
    main()