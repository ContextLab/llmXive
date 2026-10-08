import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from statsmodels.stats.stattools import owen_vif
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant

# Import from utils if needed, but we will define helpers locally if not exported
# Assuming utils has read_memory_measurements_csv based on task T017 description
try:
    from utils import read_memory_measurements_csv
except ImportError:
    read_memory_measurements_csv = None

def load_memory_data(filepath: str = "data/processed/memory_measurements.csv") -> pd.DataFrame:
    """
    Load memory measurements from the processed CSV file.
    Handles the case where utils.read_memory_measurements_csv is not available by using pandas directly.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    if read_memory_measurements_csv:
        return read_memory_measurements_csv(filepath)
    
    # Fallback to direct pandas read if helper not available
    df = pd.read_csv(filepath)
    # Ensure numeric columns are numeric
    numeric_cols = ['peak_memory', 'steady_state', 'total_resource_cost']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def extract_paired_data(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """
    Extract paired memory measurements (LLM vs Human) for the same problem_id.
    Returns two series: llm_mem, human_mem.
    """
    # Pivot or filter to get pairs
    # Assuming columns: problem_id, source_type (LLM/Human), peak_memory
    if 'source_type' not in df.columns or 'problem_id' not in df.columns:
        raise ValueError("DataFrame must contain 'problem_id' and 'source_type' columns")
    
    llm_data = df[df['source_type'] == 'LLM'][['problem_id', 'peak_memory']].copy()
    human_data = df[df['source_type'] == 'Human'][['problem_id', 'peak_memory']].copy()
    
    # Merge on problem_id
    paired = llm_data.merge(human_data, on='problem_id', suffixes=('_llm', '_human'))
    
    if paired.empty:
        raise ValueError("No paired data found between LLM and Human sources.")
    
    return paired['peak_memory_llm'], paired['peak_memory_human']

def wilcoxon_signed_rank_test(llm_vals: pd.Series, human_vals: pd.Series) -> Dict[str, float]:
    """
    Perform Wilcoxon signed-rank test on paired data.
    Returns dict with statistic and p-value.
    """
    from scipy.stats import wilcoxon
    stat, pval = wilcoxon(llm_vals, human_vals)
    return {"statistic": float(stat), "p_value": float(pval)}

def calculate_effect_size(llm_vals: pd.Series, human_vals: pd.Series) -> Dict[str, float]:
    """
    Calculate effect size (Cohen's d for paired samples or rank-biserial).
    Here we use Cohen's d for paired samples.
    """
    diff = llm_vals - human_vals
    mean_diff = diff.mean()
    std_diff = diff.std()
    
    if std_diff == 0:
        return {"cohens_d": 0.0}
        
    cohens_d = mean_diff / std_diff
    return {"cohens_d": float(cohens_d)}

def holm_bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Holm-Bonferroni correction to a list of p-values.
    Returns adjusted p-values.
    """
    from statsmodels.stats.multitest import multipletests
    # multipletests returns (reject, p_corrected, p_corrected_sidak, p_corrected_holm)
    # We want Holm specifically
    _, p_corrected, _, _ = multipletests(p_values, method='holm')
    return [float(p) for p in p_corrected]

def interpret_effect_size(cohens_d: float) -> str:
    """
    Interpret Cohen's d magnitude.
    """
    abs_d = abs(cohens_d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"

def calculate_vif(features: pd.DataFrame, target: pd.Series = None) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for predictors.
    
    Args:
        features: DataFrame of predictor variables (must be numeric, no constant column).
        target: Optional target variable (not strictly needed for VIF calculation 
                as VIF is based on predictors' relationships, but included for signature compatibility).
    
    Returns:
        DataFrame with columns: 'feature', 'VIF'.
        Flags predictors with VIF > 5.
    """
    if features.empty:
        raise ValueError("Features DataFrame is empty.")
    
    # Add constant for OLS (intercept) - VIF calculation typically uses the constant
    # statsmodels owen_vif handles the constant internally or expects it?
    # Standard VIF formula: VIF_j = 1 / (1 - R_j^2) where R_j^2 is from regressing X_j on all other X's.
    # We use statsmodels' variance_inflation_factor or manual calculation.
    
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Ensure features are float
    X = features.astype(float)
    
    # If a constant column exists, VIF will be NaN or undefined for it.
    # We assume input features do not include a constant column (add_constant adds it).
    # However, VIF calculation requires the design matrix including intercept to be valid for the regression context,
    # but for the VIF of a specific predictor, we regress that predictor against others.
    
    vif_data = []
    
    # Check for constant column
    if 'const' in X.columns:
        # Remove constant for VIF calculation of predictors, or handle gracefully
        X_no_const = X.drop(columns=['const'])
        cols = X_no_const.columns
    else:
        X_no_const = X
        cols = X.columns
        
    if len(cols) == 0:
        return pd.DataFrame(columns=['feature', 'VIF', 'flag_high'])

    for col in cols:
        try:
            # Calculate VIF for this column
            # variance_inflation_factor expects the full design matrix (including intercept)
            # but we pass the matrix of predictors.
            # If we passed X_no_const, we are regressing col on other cols in X_no_const.
            # This is the standard definition.
            vif = variance_inflation_factor(X_no_const.values, X_no_const.columns.get_loc(col))
            vif_data.append({
                'feature': col,
                'VIF': float(vif),
                'flag_high': 'Yes' if vif > 5 else 'No'
            })
        except Exception as e:
            # Handle singular matrix or other errors
            vif_data.append({
                'feature': col,
                'VIF': float('nan'),
                'flag_high': 'Error'
            })
    
    return pd.DataFrame(vif_data)

def generate_analysis_report(results: Dict[str, Any], output_path: str = "data/processed/analysis_report.json") -> None:
    """
    Generate a JSON report with statistical results.
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

def main():
    """
    Main entry point for statistical analysis including VIF calculation.
    """
    print("Loading memory data...")
    try:
        df = load_memory_data()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # 1. Extract paired data for Wilcoxon (if applicable)
    # Note: T032 focuses on VIF for regression features, but we include the pipeline context.
    # Assuming features are already extracted and stored or available.
    # For T032, we specifically need to calculate VIF on predictors used in regression.
    
    # Check if feature columns exist (from T027-T029: LOC, Complexity, Imports)
    feature_cols = ['loc', 'complexity', 'num_imports']
    missing_cols = [c for c in feature_cols if c not in df.columns]
    
    if not missing_cols:
        print("Calculating VIF for predictors...")
        predictors = df[feature_cols].dropna()
        vif_results = calculate_vif(predictors)
        
        print("VIF Results:")
        print(vif_results.to_string(index=False))
        
        # Save VIF results to a CSV file as an artifact
        vif_output_path = "data/processed/vif_analysis.csv"
        vif_results.to_csv(vif_output_path, index=False)
        print(f"VIF results saved to {vif_output_path}")
        
        # Flag high VIFs
        high_vif = vif_results[vif_results['VIF'] > 5]
        if not high_vif.empty:
            print(f"WARNING: {len(high_vif)} predictor(s) have VIF > 5:")
            print(high_vif.to_string(index=False))
    else:
        print(f"Feature columns missing for VIF calculation: {missing_cols}")
        print("Skipping VIF calculation. Ensure T027-T029 have populated these columns.")

    # Run other analysis if data permits
    if 'source_type' in df.columns:
        try:
            llm, human = extract_paired_data(df)
            wilcoxon_res = wilcoxon_signed_rank_test(llm, human)
            effect_res = calculate_effect_size(llm, human)
            print(f"Wilcoxon: {wilcoxon_res}")
            print(f"Effect Size: {effect_res}")
        except Exception as e:
            print(f"Skipping paired analysis: {e}")

if __name__ == "__main__":
    main()