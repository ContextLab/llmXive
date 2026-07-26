"""
Statistical modeling module.
Fits mixed-effects logistic regression models.
"""
import os
import sys
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("modeling")

def calculate_vif(df: pd.DataFrame):
    """Calculate VIF for collinearity check."""
    # Select numeric predictors
    predictors = ['Conscientiousness', 'Need_for_Achievement']
    valid_predictors = [p for p in predictors if p in df.columns]
    
    if len(valid_predictors) < 2:
        logger.info("Not enough predictors for VIF calculation.")
        return {}
    
    X = df[valid_predictors].dropna()
    if X.shape[0] < 2:
        return {}
    
    X_with_const = sm.add_constant(X)
    vif_data = {}
    
    for i, col in enumerate(X_with_const.columns):
        if col != 'const':
            try:
                vif = variance_inflation_factor(X_with_const.values, i)
                vif_data[col] = vif
            except Exception as e:
                logger.warning(f"VIF calculation failed for {col}: {e}")
    
    return vif_data

def fit_mixed_effects_model(df: pd.DataFrame):
    """Fit mixed-effects logistic regression."""
    # Prepare data
    df_clean = df.dropna(subset=['Adherence', 'Conscientiousness', 'Gamified'])
    
    # VIF check
    vif_data = calculate_vif(df_clean)
    for col, vif in vif_data.items():
        logger.info(f"VIF for {col}: {vif:.2f}")
        if vif > 5:
            logger.warning(f"High collinearity for {col} (VIF={vif}). Consider removing.")
    
    # Formula
    formula = "Adherence ~ Gamified * Conscientiousness + (1|User_ID)"
    
    try:
        model = mixedlm.from_formula(formula, df_clean, groups=df_clean['User_ID'])
        result = model.fit()
        logger.info("Model fitting successful.")
        logger.info(result.summary())
        return result
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        return None

def main():
    """CLI entry point."""
    log_pipeline_stage(logger, "START", "Statistical Modeling")
    
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(root, "data", "processed", "merged_data.csv")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    df = pd.read_csv(input_path)
    result = fit_mixed_effects_model(df)
    
    if result:
        # Save summary
        summary_path = os.path.join(root, "data", "processed", "model_summary.txt")
        with open(summary_path, 'w') as f:
            f.write(str(result.summary()))
        logger.info(f"Model summary saved to {summary_path}")
    
    log_pipeline_stage(logger, "END", "Statistical Modeling")

if __name__ == "__main__":
    main()
