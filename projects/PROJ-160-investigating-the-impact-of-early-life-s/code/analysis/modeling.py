import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import warnings

logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, formula: str) -> Dict[str, float]:
    """
    Calculates Variance Inflation Factor (VIF) for covariates in the formula.
    Returns a dictionary mapping column names to VIF values.
    """
    # Extract variables from formula string (simplified parsing)
    # Formula format: Y ~ X1 + X2 + ...
    parts = formula.split('~')
    if len(parts) != 2:
        raise ValueError("Invalid formula format. Expected 'Y ~ X1 + X2'")
    
    _, rhs = parts
    # Remove random effects part (1|...) for VIF calculation
    rhs_clean = rhs.split('+ (1')[0]
    
    vars = [v.strip() for v in rhs_clean.split('+') if v.strip()]
    
    # Create design matrix
    try:
        design = smf.ols(formula, data=df).fit().model.exog
    except Exception as e:
        logger.warning(f"Could not build design matrix for VIF: {e}")
        return {}

    vifs = {}
    for i, col_name in enumerate(df.columns):
        if col_name in vars:
            try:
                # VIF = 1 / (1 - R^2)
                # Regress col against all other vars
                other_vars = [v for v in vars if v != col_name]
                if not other_vars:
                    continue
                
                sub_formula = f"{col_name} ~ {' + '.join(other_vars)}"
                r2 = smf.ols(sub_formula, data=df).fit().rsquared
                vif = 1.0 / (1.0 - r2)
                vifs[col_name] = vif
            except Exception:
                vifs[col_name] = float('inf')
    
    return vifs

def residualize_column(df: pd.DataFrame, target_col: str, control_cols: List[str]) -> pd.Series:
    """
    Regresses target_col against control_cols and returns the residuals.
    """
    formula = f"{target_col} ~ {' + '.join(control_cols)}"
    model = smf.ols(formula, data=df).fit()
    return model.resid

def apply_residualization_strategy(df: pd.DataFrame, target_col: str, vif_dict: Dict[str, float], threshold: float = 5.0) -> pd.DataFrame:
    """
    If any covariate has VIF > threshold, residualize the target against it.
    Returns the modified dataframe.
    """
    high_vif_vars = [k for k, v in vif_dict.items() if v > threshold]
    if not high_vif_vars:
        return df

    logger.info(f"Applying residualization for {target_col} against high VIF variables: {high_vif_vars}")
    df[target_col] = residualize_column(df, target_col, high_vif_vars)
    return df

def fit_lmm_for_subfield(df: pd.DataFrame, subfield_col: str, covariates: List[str], family_id_col: str) -> Tuple[Any, float]:
    """
    Fits a Linear Mixed Effects Model for a specific subfield.
    Formula: subfield_vol ~ ACE_score + age + sex + scanner_site + (1|family_id)
    Returns the fitted model and the p-value for ACE_score.
    """
    # Construct formula
    # Ensure ACE_score is in covariates
    if 'ACE_score' not in covariates:
        raise ValueError("ACE_score must be in covariates")
    
    fixed_effects = ' + '.join(covariates)
    formula = f"{subfield_col} ~ {fixed_effects} + (1|{family_id_col})"
    
    # Fit model
    # Using statsmodels MixedLM
    # Note: statsmodels MixedLM requires specific handling for random effects syntax
    # We use the 'groups' argument for random intercepts
    
    groups = df[family_id_col]
    endog = df[subfield_col]
    exog = df[covariates]
    
    try:
        model = smf.mixedlm(f"{subfield_col} ~ {fixed_effects}", df, groups=groups)
        result = model.fit()
        
        # Extract p-value for ACE_score
        # params index might be 'ACE_score' or 'Intercept' etc.
        p_val = result.pvalues.get('ACE_score', 1.0)
        
        return result, p_val
    except Exception as e:
        logger.error(f"Failed to fit LMM for {subfield_col}: {e}")
        return None, 1.0

def run_primary_analysis(data_path: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Runs the primary analysis for CA3, DG, and Subiculum.
    Returns a dictionary of results.
    """
    # Load data
    df = pd.read_csv(data_path)
    
    # Ensure numeric columns
    numeric_cols = ['CA3', 'DG', 'Subiculum', 'ACE_score', 'Age', 'ICV']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows with missing critical values
    df = df.dropna(subset=['CA3', 'DG', 'Subiculum', 'ACE_score', 'Age', 'FamilyID'])
    
    # Covariates
    covariates = ['ACE_score', 'Age', 'Sex', 'Site']
    family_id = 'FamilyID'
    
    subfields = ['CA3', 'DG', 'Subiculum']
    results = {}
    
    for sub in subfields:
        logger.info(f"Fitting model for {sub}")
        model, p_val = fit_lmm_for_subfield(df, sub, covariates, family_id)
        if model:
            # Check VIF
            vifs = calculate_vif(df, f"{sub} ~ {' + '.join(covariates)}")
            if any(v > 5 for v in vifs.values()):
                # Apply residualization if needed (simplified for this task)
                # In full implementation, we would re-fit with residualized ACE
                logger.warning(f"High VIF detected for {sub}. Residualization strategy pending full implementation.")
            
            results[sub] = {
                'model': model,
                'p_value': p_val,
                'vifs': vifs
            }
        else:
            results[sub] = {'model': None, 'p_value': 1.0, 'vifs': {}}
    
    return results

def main():
    """
    Entry point for modeling script.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Running primary analysis pipeline.")
    
    # Placeholder paths - in real execution, these come from config
    data_path = Path("data/processed/cleaned_dataset.csv")
    output_dir = Path("data/processed")
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return
    
    results = run_primary_analysis(data_path, output_dir)
    logger.info(f"Analysis complete. Results keys: {list(results.keys())}")

if __name__ == "__main__":
    main()
