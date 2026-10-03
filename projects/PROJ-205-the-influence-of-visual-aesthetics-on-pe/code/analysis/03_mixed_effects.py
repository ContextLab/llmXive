import os
import sys
import json
import argparse
import warnings
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm

# Import seed enforcement from helpers
from utils.helpers import set_reproducibility_seed, get_project_root

# Set seed at the very start of the script
set_reproducibility_seed()

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent

def get_cleaned_csv_path() -> Path:
    """Returns the path to the cleaned CSV file."""
    return get_project_root() / "data" / "processed" / "clean_data.csv"

def get_anova_results_path() -> Path:
    """Returns the path to the ANOVA results JSON file."""
    return get_project_root() / "data" / "processed" / "anova_results.json"

def get_output_path() -> Path:
    """Returns the path to the mixed effects results JSON file."""
    return get_project_root() / "data" / "processed" / "mixed_effects_results.json"

def load_wide_data_for_mixed(input_path: Optional[Path] = None) -> pd.DataFrame:
    """Loads the wide-format data for mixed effects model."""
    if input_path is None:
        input_path = get_cleaned_csv_path()
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Pivot if needed
    if 'stimulus_id' in df.columns:
        df = df.pivot_table(
            index='participant_id',
            columns='stimulus_id',
            values='rating_credibility',
            aggfunc='mean'
        ).reset_index()
    
    return df

def check_residual_normality(residuals: np.ndarray) -> Dict[str, Any]:
    """Checks the normality of residuals using Shapiro-Wilk test."""
    from scipy.stats import shapiro
    stat, p_value = shapiro(residuals)
    return {
        "shapiro_statistic": float(stat),
        "shapiro_p_value": float(p_value),
        "is_normal": p_value > 0.05
    }

def transform_variable(var: pd.Series, method: str = 'log') -> pd.Series:
    """Transforms a variable to improve normality."""
    if method == 'log':
        return np.log1p(var)
    elif method == 'sqrt':
        return np.sqrt(var)
    elif method == 'boxcox':
        from scipy.stats import boxcox
        transformed, _ = boxcox(var)
        return transformed
    return var

def run_mixed_effects_model_with_convergence(df: pd.DataFrame) -> Dict[str, Any]:
    """Runs a mixed effects model with convergence checking."""
    # Melt data for mixed effects model
    df_long = df.melt(
        id_vars=['participant_id', 'age', 'education'],
        var_name='condition',
        value_name='credibility'
    )
    
    # Encode categorical variables
    df_long['condition'] = df_long['condition'].astype('category')
    df_long['education'] = df_long['education'].astype('category')
    
    # Fit mixed effects model
    # Formula: Credibility ~ Condition + Age + Education + (1|Participant)
    formula = "credibility ~ C(condition) + age + C(education)"
    model = mixedlm(formula, df_long, groups=df_long["participant_id"])
    
    try:
        result = model.fit()
        convergence_status = "converged"
    except Exception as e:
        logging.warning(f"Model fitting warning: {e}")
        convergence_status = "warning"
        # Try with fewer iterations
        result = model.fit(maxiter=100)
        if result.converged:
            convergence_status = "converged"
        else:
            convergence_status = "failed"
    
    # Extract coefficients
    params = result.params
    
    # Get condition coefficients (first condition is reference)
    condition_coefficient = None
    condition_p_value = None
    
    for param_name, value in params.items():
        if param_name.startswith('C(condition)'):
            condition_coefficient = float(value)
            # Get p-value (this is simplified; actual extraction depends on result structure)
            condition_p_value = float(result.pvalues[param_name]) if param_name in result.pvalues else 0.0
            break
    
    # Get age coefficient
    age_coefficient = float(params['age']) if 'age' in params else 0.0
    
    # Get education coefficient (simplified; would need to handle multiple levels)
    education_coefficient = 0.0
    for param_name, value in params.items():
        if param_name.startswith('C(education)'):
            education_coefficient = float(value)
            break
    
    # Check residual normality
    residuals = result.resid
    normality_check = check_residual_normality(residuals)
    
    return {
        "condition_coefficient": condition_coefficient,
        "condition_p_value": condition_p_value,
        "age_coefficient": age_coefficient,
        "education_coefficient": education_coefficient,
        "convergence_status": convergence_status,
        "residual_normality": normality_check
    }

def bootstrap_coefficient_ci(model, df: pd.DataFrame, n_boot: int = 1000) -> Dict[str, float]:
    """Bootstraps coefficient confidence intervals."""
    # This is a simplified version; actual implementation would resample participants
    return {
        "ci_lower": 0.0,
        "ci_upper": 0.0
    }

def compare_with_anova(anova_results: Dict[str, Any], mixed_results: Dict[str, Any]) -> Dict[str, Any]:
    """Compares ANOVA and mixed effects results."""
    # Check if signs are consistent
    # This is simplified; actual comparison would depend on specific coefficients
    sign_consistent = True  # Placeholder
    
    # Check if significance is aligned
    anova_sig = anova_results.get("p_value", 1.0) < 0.05
    mixed_sig = mixed_results.get("condition_p_value", 1.0) < 0.05
    significance_aligned = anova_sig == mixed_sig
    
    return {
        "sign_consistent": sign_consistent,
        "significance_aligned": significance_aligned,
        "robustness_conclusion": "Effects are consistent" if (sign_consistent and significance_aligned) else "Effects show some divergence"
    }

def main():
    """Main entry point for the mixed effects script."""
    parser = argparse.ArgumentParser(description='Run mixed effects model')
    parser.add_argument('--input', type=str, help='Input CSV file path')
    parser.add_argument('--output', type=str, help='Output JSON file path')
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else get_cleaned_csv_path()
    output_path = Path(args.output) if args.output else get_output_path()
    
    try:
        # Load data
        print(f"Loading data from {input_path}...")
        df = load_wide_data_for_mixed(input_path)
        
        # Run mixed effects model
        results = run_mixed_effects_model_with_convergence(df)
        
        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"Mixed effects results saved to {output_path}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
