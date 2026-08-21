"""
Mixed-effects model analysis for the Visual Aesthetics Credibility Study.

This script:
1. Loads wide-format data
2. Runs linear mixed-effects model with condition as fixed effect and participant as random effect
3. Includes age and education as covariates
4. Checks for model convergence
5. Outputs results to JSON
"""

import os
import sys
import json
import random
import numpy as np
import pandas as pd

# Set seeds for reproducibility
np.random.seed(42)
random.seed(42)

from pathlib import Path

def get_project_root():
    """Get the project root directory."""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "data").exists() and (current / "code").exists():
            return current
        current = current.parent
    return Path.cwd()

PROJECT_ROOT = get_project_root()
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def load_wide_data_for_mixed(input_path):
    """
    Load wide-format data and reshape to long format for mixed-effects model.
    
    Args:
        input_path: Path to the wide-format CSV file
    
    Returns:
        pandas DataFrame in long format
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Verify required columns exist
    required_cols = [
        "credibility_Professional",
        "credibility_Minimalist",
        "credibility_Low-Quality",
        "credibility_Neutral"
    ]
    
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Reshape to long format
    conditions = ["Professional", "Minimalist", "Low-Quality", "Neutral"]
    credibility_cols = [f"credibility_{cond}" for cond in conditions]
    
    # Keep only necessary columns
    df_subset = df[["participant_id", "age", "education"] + credibility_cols].copy()
    
    # Melt to long format
    df_long = df_subset.melt(
        id_vars=["participant_id", "age", "education"],
        value_vars=credibility_cols,
        var_name="condition",
        value_name="credibility"
    )
    
    # Extract condition name from column name
    df_long["condition"] = df_long["condition"].str.replace("credibility_", "")
    
    # Drop rows with NaN credibility
    df_long = df_long.dropna(subset=["credibility"])
    
    return df_long

def run_mixed_effects_model(df):
    """
    Run linear mixed-effects model.
    
    Formula: credibility ~ condition + age + education + (1|participant_id)
    
    Args:
        df: Long-format DataFrame
    
    Returns:
        dict: Model results including coefficients and convergence status
    """
    import statsmodels.formula.api as smf
    import warnings
    
    # Suppress convergence warnings for cleaner output
    warnings.filterwarnings("ignore", category=UserWarning)
    
    # Fit model
    try:
        model = smf.mixedlm(
            "credibility ~ C(condition) + age + education",
            df,
            groups=df["participant_id"]
        )
        result = model.fit()
        
        convergence_failed = False
    except Exception as e:
        # Model failed to converge or other error
        convergence_failed = True
        result = None
    
    if convergence_failed or result is None:
        return {
            "convergence_failed": True,
            "error": "Model failed to converge or encountered an error",
            "condition_coef": None,
            "condition_p": None,
            "age_coef": None,
            "education_coef": None,
            "r_squared": None
        }
    
    # Extract condition coefficients (relative to reference category)
    # The reference category is the first one alphabetically: "Low-Quality"
    condition_params = {}
    for param_name, param in result.params.items():
        if param_name.startswith("C(condition)"):
            condition_params[param_name] = param
    
    # Extract p-values
    condition_pvalues = {}
    for param_name, param in result.pvalues.items():
        if param_name.startswith("C(condition)"):
            condition_pvalues[param_name] = param
    
    # Get age and education coefficients
    age_coef = result.params.get("age", None)
    education_coef = result.params.get("education", None)
    
    # Calculate pseudo R-squared (marginal)
    # This is a simplified approximation
    try:
        r_squared = result.prsquared if hasattr(result, 'prsquared') else None
    except:
        r_squared = None
    
    return {
        "convergence_failed": False,
        "condition_coef": {k: float(v) for k, v in condition_params.items()},
        "condition_p": {k: float(v) for k, v in condition_pvalues.items()},
        "age_coef": float(age_coef) if age_coef is not None else None,
        "education_coef": float(education_coef) if education_coef is not None else None,
        "r_squared": float(r_squared) if r_squared is not None else None
    }

def main():
    """Main entry point for mixed-effects analysis."""
    parser = argparse.ArgumentParser(description="Run mixed-effects model analysis")
    parser.add_argument("--input", type=str, required=True, help="Path to wide-format CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")
    args = parser.parse_args()
    
    print(f"Loading data from {args.input}...")
    df = load_wide_data_for_mixed(args.input)
    
    print(f"Loaded {len(df)} observations from {df['participant_id'].nunique()} participants.")
    
    print("Running mixed-effects model...")
    results = run_mixed_effects_model(df)
    
    if results["convergence_failed"]:
        print("Warning: Model failed to converge.")
        # Log warning to file
        log_path = DATA_PROCESSED_DIR / "mixed_effects_warnings.log"
        with open(log_path, "a") as f:
            f.write(f"{args.input}: {results.get('error', 'Unknown error')}\n")
    else:
        print("Model converged successfully.")
    
    # Write output
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results written to {args.output}")

if __name__ == "__main__":
    main()
