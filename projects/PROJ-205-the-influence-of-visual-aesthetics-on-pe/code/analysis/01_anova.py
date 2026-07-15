"""
Repeated-Measures ANOVA for Credibility Ratings.

Implements a one-way repeated-measures ANOVA to test the effect of
visual design condition on perceived credibility.

Input: data/processed/analysis_data_wide.csv (produced by 01_preprocess.py)
Output: data/processed/anova_results.json
"""
import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.stats.anova import AnovaRM
from statsmodels.stats.multitest import multipletests

# Ensure paths are resolvable from project root or script location
def get_project_root():
    current = Path(__file__).resolve()
    while not (current / "requirements.txt").exists():
        current = current.parent
        if current == current.parent:
            raise FileNotFoundError("Project root not found")
    return current

PROJECT_ROOT = get_project_root()
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
INPUT_FILE = DATA_PROCESSED_DIR / "analysis_data_wide.csv"
OUTPUT_FILE = DATA_PROCESSED_DIR / "anova_results.json"

def load_wide_data(filepath: Path) -> pd.DataFrame:
    """Load the wide-format dataframe prepared by 01_preprocess.py."""
    if not filepath.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}. Run 01_preprocess.py first.")
    df = pd.read_csv(filepath)
    
    # Validate expected columns exist
    expected_cols = ['participant_id', 'Credibility_Professional', 'Credibility_Minimalist', 
                     'Credibility_Low-Quality', 'Credibility_Neutral']
    missing = set(expected_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in wide data: {missing}")
    
    return df

def run_repeated_measures_anova(df: pd.DataFrame, dv_prefix: str = "Credibility") -> dict:
    """
    Run one-way repeated-measures ANOVA.
    
    Args:
        df: Wide-format dataframe with participant_id and condition columns.
        dv_prefix: Prefix for the dependent variable columns (e.g., "Credibility").
        
    Returns:
        Dictionary with F-statistic, degrees of freedom, p-value, and effect size.
    """
    # Reshape to long format for statsmodels AnovaRM
    # Columns: participant_id, condition, value
    long_df = pd.melt(
        df,
        id_vars=['participant_id'],
        value_vars=[f"{dv_prefix}_Professional", f"{dv_prefix}_Minimalist", 
                    f"{dv_prefix}_Low-Quality", f"{dv_prefix}_Neural"],
        var_name='condition',
        value_name='score'
    )
    
    # Extract condition name from column name (e.g., "Credibility_Professional" -> "Professional")
    long_df['condition'] = long_df['condition'].str.replace(f"{dv_prefix}_", "", regex=False)
    
    # Run ANOVA
    try:
        aov_rm = AnovaRM(long_df, depvar='score', subject='participant_id', within=['condition'])
        res = aov_rm.fit()
    except Exception as e:
        raise RuntimeError(f"ANOVA failed: {e}")

    # Extract results
    # statsmodels output is a DataFrame; we need to parse it
    # The main row is usually labeled 'condition'
    main_row = res.tables[0].loc['condition']
    f_stat = main_row['F']
    df_num = main_row['df_num']
    df_den = main_row['df_den']
    p_val = main_row['Pr > F']
    
    # Calculate partial eta-squared (η²)
    # η² = SS_effect / (SS_effect + SS_error)
    # We need to extract Sum of Squares from the ANOVA table
    ss_effect = main_row['Sum Sq']
    # Find the error row for the within-subjects effect
    # In statsmodels, the error term is usually labeled 'condition:Error' or similar
    error_row = None
    for idx in res.tables[0].index:
        if 'Error' in str(idx) and 'condition' in str(idx):
            error_row = res.tables[0].loc[idx]
            break
    
    if error_row is not None:
        ss_error = error_row['Sum Sq']
        eta_squared = ss_effect / (ss_effect + ss_error)
    else:
        # Fallback: estimate from F and df if error row not found
        # F = MS_effect / MS_error = (SS_effect/df_num) / (SS_error/df_den)
        # MS_error = MS_effect / F
        # SS_error = MS_error * df_den
        ms_effect = ss_effect / df_num
        ms_error = ms_effect / f_stat
        ss_error = ms_error * df_den
        eta_squared = ss_effect / (ss_effect + ss_error)

    return {
        "f_statistic": float(f_stat),
        "df_numerator": int(df_num),
        "df_denominator": int(df_den),
        "p_value": float(p_val),
        "partial_eta_squared": float(eta_squared),
        "significant": bool(p_val < 0.05)
    }

def main():
    """Main entry point for the ANOVA script."""
    parser = argparse.ArgumentParser(description="Run Repeated-Measures ANOVA on credibility data.")
    parser.add_argument("--input", type=str, default=str(INPUT_FILE), help="Path to wide-format input CSV")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE), help="Path to output JSON results")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    print(f"Loading data from {input_path}...")
    df = load_wide_data(input_path)
    print(f"Loaded {len(df)} participants.")

    print("Running Repeated-Measures ANOVA...")
    results = run_repeated_measures_anova(df, dv_prefix="Credibility")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"ANOVA results saved to {output_path}")
    print(f"F({results['df_numerator']}, {results['df_denominator']}) = {results['f_statistic']:.4f}, "
          f"p = {results['p_value']:.4f}, η² = {results['partial_eta_squared']:.4f}")
    
    return results

if __name__ == "__main__":
    main()
