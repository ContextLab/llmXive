import os
import sys
import json
import warnings
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.formula.api import ols
from logger import setup_logger

logger = setup_logger("analysis", "logs/analysis.log")

def validate_design_structure(data_path: str) -> str:
    """
    Reads cleaned_data.csv to determine if the design is within-subjects
    or between-subjects based on participant_id variance.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    unique_participants = df['participant_id'].nunique()
    total_rows = len(df)
    
    if unique_participants == total_rows:
        design_type = "between-subjects"
    elif unique_participants < total_rows:
        design_type = "within-subjects"
    else:
        raise ValueError("Data integrity error: Unique participants cannot exceed total rows.")
    
    logger.info(f"Detected design structure: {design_type}")
    return design_type

def calculate_vif(df: pd.DataFrame, formula: str) -> dict:
    """
    Calculates Variance Inflation Factors (VIF) for all predictors in the model.
    Flags any VIF > 5.0.
    
    Args:
        df: DataFrame containing the data.
        formula: Statsmodels formula string (e.g., 'y ~ x1 + x2').
    
    Returns:
        dict: VIF values for each predictor and a boolean flag for high collinearity.
    """
    # Ensure categorical variables are handled correctly by statsmodels
    # The formula API usually handles this, but we need to ensure the model matrix is numeric
    try:
        model = ols(formula, data=df).fit()
        # Get the design matrix (excluding the intercept for VIF calculation)
        # model.model.exog includes the intercept column (usually first column of 1s)
        exog = model.model.exog
        
        # Calculate VIF for each column
        # VIF is undefined for the intercept, so we skip index 0 if it's all 1s
        # However, the standard loop below handles it if we name columns.
        
        vif_data = {}
        high_vif_detected = False
        
        # statsmodels VIF function expects a 2D array and column names
        # We need to map columns back to predictor names
        # The formula parser creates column names like 'C(status_level)[T.High]'
        
        # To be robust, we iterate through the columns of exog
        # We need to know which column corresponds to which term
        # A safer way for VIF in statsmodels is to use the vif function on the design matrix
        
        # Re-construct design matrix with explicit column names for VIF
        # We can use the formula to get the terms, but simpler is to just use the exog
        # and map indices to terms.
        
        # Let's use the standard approach:
        # 1. Build the model matrix explicitly to get column names
        import patsy
        y, X = patsy.dmatrices(formula, df, return_type='dataframe')
        
        # VIF calculation
        # X includes the intercept column (usually named 'Intercept')
        # We calculate VIF for all columns, but Intercept is often excluded or ignored
        
        vif_values = []
        column_names = X.columns.tolist()
        
        # Remove Intercept for VIF calculation if present
        if 'Intercept' in column_names:
            X_vif = X.drop('Intercept', axis=1)
            column_names_vif = X_vif.columns.tolist()
        else:
            X_vif = X
            column_names_vif = column_names
        
        for i in range(X_vif.shape[1]):
            try:
                vif = variance_inflation_factor(X_vif.values, i)
                vif_values.append(vif)
            except Exception as e:
                # Handle singular matrix cases
                vif_values.append(np.inf)
        
        # Map back to dictionary
        vif_dict = {col: round(vif, 4) for col, vif in zip(column_names_vif, vif_values)}
        
        # Check for high VIF
        if any(v > 5.0 for v in vif_dict.values()):
            high_vif_detected = True
            logger.warning("High VIF detected (> 5.0). Multicollinearity may be an issue.")
            for col, v in vif_dict.items():
                if v > 5.0:
                    logger.warning(f"  - {col}: VIF = {v}")
        else:
            logger.info("No high VIF detected (all < 5.0).")
        
        return {
            "vif_values": vif_dict,
            "high_vif_detected": high_vif_detected,
            "threshold": 5.0
        }
        
    except Exception as e:
        logger.error(f"Error calculating VIF: {str(e)}")
        # Fallback for near-singular matrices using SVD/QR logic if needed
        # For now, return a safe default structure if calculation fails
        return {
            "vif_values": {},
            "high_vif_detected": False,
            "error": str(e)
        }

def fit_fixed_effects(df: pd.DataFrame, formula: str) -> object:
    """Fits a fixed effects OLS model."""
    try:
        model = ols(formula, data=df).fit()
        return model
    except Exception as e:
        logger.error(f"Fixed effects model fitting failed: {e}")
        raise

def fit_mixed_effects(df: pd.DataFrame, formula: str) -> object:
    """Fits a mixed effects (Linear Mixed Model) model."""
    try:
        import statsmodels.api as sm
        # Use MixedLM for mixed effects
        # Formula: 'y ~ x1 + x2' with groups='participant_id'
        # Note: statsmodels MixedLM does not support formula strings directly in the same way as OLS
        # We need to construct the arrays or use a helper if available.
        # Alternatively, use linearmodels if available, but sticking to statsmodels as per deps.
        
        # Manual construction for robustness if formula parsing is tricky with groups
        # But let's try the standard approach first if we can parse it.
        # Actually, statsmodels MixedLM doesn't take a formula string in the constructor easily.
        # We will use the patsy to get y and X, then fit.
        
        import patsy
        y, X = patsy.dmatrices(formula, df, return_type='dataframe')
        
        # Identify the grouping variable from the formula if it was embedded, 
        # but typically for MixedLM we pass groups explicitly.
        # The task description says: (1|participant_id) in formula.
        # We need to extract 'participant_id' from the formula string or assume it's known.
        # Since T021a logic is "If within-subjects, fit ... (1|participant_id)",
        # we assume the formula passed here is the fixed part, and we extract groups.
        
        # Extract groups column name from the original dataframe or formula context?
        # The formula passed to this function is likely just the fixed effects part.
        # Let's assume the caller passes the correct formula for fixed effects.
        # We need the group column.
        
        if 'participant_id' not in df.columns:
            raise ValueError("participant_id column missing for mixed effects model.")
        
        groups = df['participant_id']
        
        model = sm.MixedLM(y, X, groups=groups).fit()
        return model
    except Exception as e:
        logger.error(f"Mixed effects model fitting failed: {e}")
        raise

def fit_adaptive_model(df: pd.DataFrame, design_type: str, family_type: str) -> tuple:
    """
    Fits the appropriate model based on design structure and outcome family.
    Returns (model, formula_used, vif_results).
    """
    # Construct formula based on design type
    # Fixed effects: risk_taking ~ status_level * observed_behavior
    # Mixed effects: risk_taking ~ status_level * observed_behavior + (1|participant_id)
    # Note: For statsmodels MixedLM, we pass fixed formula and groups separately.
    
    fixed_formula = "risk_taking_score ~ status_level * observed_behavior"
    
    if design_type == "within-subjects":
        logger.info("Fitting Mixed-Effects model (Within-Subjects)")
        model = fit_mixed_effects(df, fixed_formula)
        # For VIF in mixed models, we typically look at the fixed effects design matrix
        vif_results = calculate_vif(df, fixed_formula)
    else:
        logger.info("Fitting Fixed-Effects model (Between-Subjects)")
        model = fit_fixed_effects(df, fixed_formula)
        vif_results = calculate_vif(df, fixed_formula)
    
    return model, fixed_formula, vif_results

def main():
    """Main entry point for analysis."""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Load data
    data_path = "data/processed/cleaned_data.csv"
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    df = pd.read_csv(data_path)
    
    # Validate design
    design_type = validate_design_structure(data_path)
    
    # Load config to determine family (though VIF is generally for linear models)
    config_path = "data/processed/model_config.json"
    family_type = "gaussian" # Default
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            family_type = config.get('family_type', 'gaussian')
    
    # Fit model
    try:
        model, formula, vif_results = fit_adaptive_model(df, design_type, family_type)
        
        # Save VIF results
        output_path = "data/processed/vif_results.json"
        with open(output_path, 'w') as f:
            json.dump(vif_results, f, indent=2)
        logger.info(f"VIF results saved to {output_path}")
        
        # Flag if VIF > 5.0
        if vif_results.get('high_vif_detected', False):
            logger.warning("High multicollinearity detected. Review model predictors.")
        
        # Continue with other analysis steps (coefficients, etc.) if needed
        # This task specifically focuses on VIF calculation and flagging.
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()