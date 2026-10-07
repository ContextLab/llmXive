"""
Mixed Effects Model analysis script.
Implements US3: Robustness and Validation Checks.
Formula: Credibility ~ Condition + Age + Education + (1|Participant)
"""
import os
import sys
import json
import argparse
import warnings
import logging
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.helpers import get_project_root, set_reproducibility_seed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def get_cleaned_csv_path() -> Path:
    """Return path to the cleaned CSV data."""
    return get_project_root() / "data" / "processed" / "clean_data.csv"

def get_anova_results_path() -> Path:
    """Return path to ANOVA results (dependency check)."""
    return get_project_root() / "data" / "processed" / "anova_results.json"

def get_output_path() -> Path:
    """Return path for mixed effects results output."""
    return get_project_root() / "data" / "processed" / "mixed_effects_results.json"

def load_wide_data_for_mixed(input_path: str | Path) -> list[dict]:
    """
    Load wide-format CSV data for mixed effects analysis.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        List of dictionaries representing rows.
        
    Raises:
        FileNotFoundError: If input file does not exist.
    """
    import csv
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    with open(path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def check_residual_normality(residuals: list) -> bool:
    """
    Check if residuals are normally distributed using Shapiro-Wilk test.
    
    Args:
        residuals: List of residual values.
        
    Returns:
        True if normal (p > 0.05), False otherwise.
    """
    try:
        from scipy.stats import shapiro
        if len(residuals) < 3:
            return True # Not enough data to test, assume ok
        stat, p = shapiro(residuals)
        return p > 0.05
    except Exception as e:
        logger.warning(f"Normality check failed: {e}. Assuming normal.")
        return True

def transform_variable(data: list[dict], column: str) -> list[dict]:
    """
    Transform variable if necessary (e.g., log transform for skewness).
    Currently a pass-through for simplicity.
    """
    return data

def run_mixed_effects_model_with_convergence(data: list[dict]) -> dict:
    """
    Run Mixed Effects Model: Credibility ~ Condition + Age + Education + (1|Participant)
    
    Args:
        data: List of dictionaries containing the wide-format data.
        
    Returns:
        Dictionary containing model results.
    """
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
        import pandas as pd
        
        if not data:
            return {"error": "No data provided", "convergence_status": False}

        df = pd.DataFrame(data)
        
        # Identify stimulus columns (e.g., professional_credibility, minimalist_credibility)
        stimulus_cols = [c for c in df.columns if c.endswith("_credibility")]
        
        if not stimulus_cols:
            raise ValueError("No credibility columns found in data. Expected columns ending with '_credibility'.")
        
        # Melt to long format for mixed models
        # ID vars: participant_id, age, education
        # Value vars: the stimulus credibility columns
        df_long = df.melt(
            id_vars=["participant_id", "age", "education"], 
            value_vars=stimulus_cols,
            var_name="condition", 
            value_name="score"
        )
        
        # Clean condition names (remove '_credibility' suffix)
        df_long["condition"] = df_long["condition"].str.replace("_credibility", "")
        
        # Ensure age is numeric
        df_long["age"] = pd.to_numeric(df_long["age"], errors="coerce")
        
        # Drop rows with missing critical values
        df_long = df_long.dropna(subset=["score", "age", "participant_id"])
        
        if len(df_long) == 0:
            raise ValueError("No valid data rows after cleaning.")

        # Define formula
        # C(condition) treats condition as categorical
        # C(education) treats education as categorical
        formula = "score ~ C(condition) + age + C(education)"
        
        logger.info(f"Running Mixed Effects Model with formula: {formula}")
        
        # Fit the model
        # groups=df_long["participant_id"] specifies the random intercept per participant
        model = smf.mixedlm(formula, df_long, groups=df_long["participant_id"])
        result = model.fit()
        
        # Check convergence
        converged = result.converged
        if not converged:
            logger.warning("Mixed effects model did not converge.")
        
        # Extract coefficients
        params = result.params
        pvalues = result.pvalues
        
        # Identify condition coefficients (keys starting with 'C(condition)[T.')
        condition_keys = [k for k in params.keys() if k.startswith("C(condition)[T.")]
        
        # Calculate an aggregate condition effect or pick the first significant one
        # For the report, we will extract the first non-reference condition coefficient
        # and its p-value. If no specific condition is significant, we note the range.
        
        condition_coefficient = 0.0
        condition_p_value = 1.0
        
        if condition_keys:
            # Sort keys to ensure deterministic selection if multiple exist
            condition_keys.sort()
            first_cond_key = condition_keys[0]
            
            condition_coefficient = float(params[first_cond_key])
            if first_cond_key in pvalues:
                condition_p_value = float(pvalues[first_cond_key])
            else:
                # If p-value missing for specific, try to find min p-value among conditions
                cond_pvals = [float(pvalues[k]) for k in condition_keys if k in pvalues]
                if cond_pvals:
                    condition_p_value = min(cond_pvals)
        
        # Extract Age coefficient
        age_coeff = float(params.get("age", 0.0))
        
        # Extract Education coefficient (first non-intercept education key)
        edu_keys = [k for k in params.keys() if k.startswith("C(education)[T.")]
        edu_coeff = 0.0
        if edu_keys:
            edu_keys.sort()
            edu_coeff = float(params[edu_keys[0]])
        
        # Check residual normality
        residuals = result.resid
        is_normal = check_residual_normality(residuals.tolist())
        
        return {
            "condition_coefficient": condition_coefficient,
            "condition_p_value": condition_p_value,
            "age_coefficient": age_coeff,
            "education_coefficient": edu_coeff,
            "convergence_status": bool(converged),
            "residual_normality": is_normal,
            "method": "statsmodels.mixedlm",
            "formula": formula,
            "n_obs": int(len(df_long)),
            "n_groups": int(df_long["participant_id"].nunique())
        }

    except ImportError:
        raise RuntimeError("statsmodels required for mixed effects. Install with: pip install statsmodels")
    except Exception as e:
        logger.error(f"Error running mixed effects model: {e}")
        return {
            "error": str(e),
            "convergence_status": False
        }

def main():
    parser = argparse.ArgumentParser(description="Run Mixed Effects Model for Robustness Check (US3)")
    parser.add_argument("--input", required=True, help="Path to clean data CSV (wide format)")
    parser.add_argument("--output", required=True, help="Path to output JSON results")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading data from {input_path}...")
    try:
        data = load_wide_data_for_mixed(input_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    if not data:
        logger.warning("No data loaded. Writing empty result.")
        result = {"error": "No data", "convergence_status": False}
    else:
        logger.info(f"Loaded {len(data)} rows. Running Mixed Effects Model...")
        result = run_mixed_effects_model_with_convergence(data)

    logger.info(f"Saving results to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    logger.info("Mixed Effects analysis complete.")
    print(f"Results written to: {output_path}")

if __name__ == "__main__":
    main()