import os
import sys
import json
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from utils import get_logger, set_random_seed, get_global_seed

logger = get_logger(__name__)

def load_analysis_data():
    """Load the final analysis data from the processed directory."""
    path = "data/processed/final_analysis_data_all.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Analysis data file not found: {path}")
    return pd.read_csv(path)

def sm_add_constant(df, columns):
    """Add a constant column to the dataframe for regression intercept."""
    return sm.add_constant(df[columns])

def calculate_correlations(df):
    """Calculate Pearson correlations between predictors and outcomes."""
    predictors = ['edge_density', 'color_entropy', 'object_count']
    outcomes = ['reaction_time', 'accuracy']
    correlations = {}

    for pred in predictors:
        for out in outcomes:
            if pred in df.columns and out in df.columns:
                # Drop NaNs for correlation calculation
                valid_data = df[[pred, out]].dropna()
                if len(valid_data) > 2:
                    r, p = valid_data[pred].corr(valid_data[out], method='pearson')
                    correlations[f"{pred}_vs_{out}"] = {'r': r, 'p': p}
                else:
                    logger.warning(f"Not enough data for correlation: {pred} vs {out}")
            else:
                logger.warning(f"Missing columns for correlation: {pred} or {out}")
    return correlations

def run_regression_standard(df, predictor, outcome):
    """Run a standard linear regression."""
    if predictor not in df.columns or outcome not in df.columns:
        raise ValueError(f"Missing columns for regression: {predictor} or {outcome}")
    
    valid_data = df[[predictor, outcome]].dropna()
    if len(valid_data) < 3:
        raise ValueError("Not enough data for regression")

    X = sm.add_constant(valid_data[predictor])
    y = valid_data[outcome]
    model = sm.OLS(y, X).fit()
    return {
        'r_squared': model.rsquared,
        'adj_r_squared': model.rsquared_adj,
        'beta': model.params[predictor],
        'p_value': model.pvalues[predictor],
        'std_err': model.bse[predictor]
    }

def calculate_vif(df):
    """Calculate Variance Inflation Factor for predictors."""
    predictors = ['edge_density', 'color_entropy', 'object_count']
    vif_results = {}
    
    # Handle NaNs in object_count by excluding it from VIF matrix if necessary
    # Or impute 0 for calculation purposes as per task instructions
    # We will drop rows with NaN in object_count for VIF calculation to be strict
    # but if object_count is all NaN, we skip it.
    
    # Check for NaN in object_count
    if df['object_count'].isna().all():
        logger.warning("object_count is entirely NaN. Excluding from VIF.")
        predictors = ['edge_density', 'color_entropy']
    elif df['object_count'].isna().any():
        logger.warning("object_count has NaN values. Dropping rows with NaN for VIF calculation.")
        df_vif = df.dropna(subset=predictors)
    else:
        df_vif = df

    if len(df_vif) < len(predictors) + 1:
        logger.error("Not enough valid rows to calculate VIF.")
        return vif_results

    X = df_vif[predictors]
    
    # Check for zero variance
    for col in X.columns:
        if X[col].var() == 0:
            logger.warning(f"Zero variance detected in {col}. Excluding from VIF.")
            X = X.drop(columns=[col])
            predictors = X.columns.tolist()

    if len(predictors) == 0:
        return vif_results

    try:
        X_with_const = sm.add_constant(X)
        for col in X.columns:
            vif = variance_inflation_factor(X_with_const.values, X_with_const.columns.get_loc(col))
            vif_results[col] = vif
    except Exception as e:
        logger.error(f"VIF calculation failed: {e}")
    
    return vif_results

def save_vif_report(vif_results, output_path="results/statistics/vif_report.json"):
    """Save VIF report to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(vif_results, f, indent=2)
    logger.info(f"VIF report saved to {output_path}")

def run_pca(df, predictors=['edge_density', 'color_entropy', 'object_count']):
    """Perform PCA on predictors and return component scores."""
    # Drop NaNs for PCA
    df_pca = df.dropna(subset=predictors)
    
    if len(df_pca) < 2:
        logger.error("Not enough data for PCA.")
        return None, None

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_pca[predictors])
    
    pca = PCA(n_components=1)
    component = pca.fit_transform(X_scaled)
    
    # Map back to original index
    pca_df = pd.DataFrame({'pca_component_1': component.flatten()}, index=df_pca.index)
    
    logger.info(f"PCA explained variance ratio: {pca.explained_variance_ratio_}")
    return pca_df, scaler

def compute_vif_and_pca():
    """
    Main logic for T031a: Compute VIF, decide on PCA, run regression if needed.
    """
    logger.info("Starting VIF and PCA computation (Task T031a)...")
    
    # Load data
    try:
        df = load_analysis_data()
    except FileNotFoundError as e:
        logger.error(f"Failed to load analysis data: {e}")
        raise

    # 1. Calculate VIF
    vif_results = calculate_vif(df)
    save_vif_report(vif_results)
    
    if not vif_results:
        logger.warning("VIF calculation yielded no results. Skipping PCA logic.")
        return None, None, df

    max_vif = max(vif_results.values()) if vif_results else 0
    logger.info(f"Max VIF: {max_vif}")

    pca_component = None
    regression_pca_results = None

    # 2. PCA Decision
    if max_vif >= 5:
        logger.info("Max VIF >= 5. Performing PCA.")
        pca_df, scaler = run_pca(df)
        
        if pca_df is not None:
            # Merge PCA component back to main df
            df = df.merge(pca_df, left_index=True, right_index=True, how='left')
            pca_component = 'pca_component_1'
            
            # 3. Linear Regression using PCA component
            logger.info("Running Linear Regression with PCA component.")
            try:
                # Regression against reaction_time
                reg_rt = run_regression_standard(df, 'pca_component_1', 'reaction_time')
                # Regression against accuracy
                reg_acc = run_regression_standard(df, 'pca_component_1', 'accuracy')
                
                regression_pca_results = {
                    'reaction_time': reg_rt,
                    'accuracy': reg_acc
                }
                
                # Save regression results
                output_path = "results/statistics/regression_pca.json"
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w') as f:
                    json.dump(regression_pca_results, f, indent=2)
                logger.info(f"PCA Regression results saved to {output_path}")
                
            except Exception as e:
                logger.error(f"Regression with PCA component failed: {e}")
        else:
            logger.error("PCA failed to produce components.")
    else:
        logger.info(f"Max VIF ({max_vif}) < 5. No PCA required. Using raw metrics.")

    return vif_results, regression_pca_results, df

def apply_holm_bonferroni(p_values_dict):
    """Apply Holm-Bonferroni correction to a dictionary of p-values."""
    from statsmodels.stats.multitest import multipletests
    
    names = list(p_values_dict.keys())
    p_vals = list(p_values_dict.values())
    
    if len(p_vals) == 0:
        return {}

    # multipletests returns (reject, p_corrected, p_sidak, p_bonferroni)
    _, p_corrected, _, _ = multipletests(p_vals, method='holm')
    
    return dict(zip(names, p_corrected.tolist()))

def main():
    """Main entry point for T031a."""
    set_random_seed(get_global_seed())
    compute_vif_and_pca()

if __name__ == "__main__":
    main()