"""
Linear Mixed-Effects Model Module.
Fits LME model and extracts results.
"""
import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data():
    """Load processed data from the final VIF-filtered dataset."""
    # Path relative to project root: data/filtered_builds_final.csv
    base_dir = Path(__file__).parent.parent.parent
    path = base_dir / "data" / "filtered_builds_final.csv"
    if not path.exists():
        raise FileNotFoundError(f"Data not found: {path}. Ensure T023b has run.")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def prepare_features(df):
    """Prepare features for LME based on VIF analysis results."""
    # The VIF analysis (T023/T023b) determines which features are retained.
    # We look for the columns that are likely to be present after VIF filtering.
    # Expected columns: energy_density OR (laser_power, scan_speed, hatch_spacing, layer_thickness)
    # Plus target: ductility, grouping: alloy_family
    
    required_cols = ['ductility', 'alloy_family']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' missing from dataset.")
    
    # Determine predictors based on available columns (matching T023 logic)
    # T023 drops constituents if energy_density VIF > 5, else drops energy_density if constituents VIF > 5.
    # We assume the dataset passed through T023b has a valid set of predictors.
    
    predictors = []
    if 'energy_density' in df.columns:
        predictors.append('energy_density')
    
    # Fallback to individual parameters if energy_density is not present
    # (though T023 logic suggests one or the other group should exist)
    if not predictors:
        candidates = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
        for c in candidates:
            if c in df.columns:
                predictors.append(c)
    
    if not predictors:
        raise ValueError("No valid predictor columns found for LME model.")
    
    logger.info(f"Selected predictors: {predictors}")
    return df[predictors + required_cols]

def fit_lme_model(df):
    """Fit Linear Mixed-Effects model using statsmodels."""
    logger.info("Fitting LME model...")
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
    except ImportError:
        logger.error("statsmodels not installed. Please install via requirements.txt.")
        sys.exit(1)
    
    # Construct formula: target ~ predictors + (1 | grouping)
    predictors = [c for c in df.columns if c not in ['ductility', 'alloy_family']]
    if not predictors:
        raise ValueError("No predictors available for model fitting.")
    
    formula = f"ductility ~ {' + '.join(predictors)} + (1 | alloy_family)"
    logger.info(f"Fitting formula: {formula}")
    
    try:
        # Fit the model
        model = smf.mixedlm(formula, df, groups=df["alloy_family"])
        result = model.fit()
        
        if not result.converged:
            logger.error("Model failed to converge.")
        else:
            logger.info("Model converged successfully.")
            
        return result
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        return None

def extract_results(result, df):
    """Extract standardized coefficients, 95% CIs, p-values, and random effects."""
    logger.info("Extracting results...")
    if result is None:
        return None
    
    # Get summary tables
    summary = result.summary2().tables[1] # Fixed effects table
    
    # Extract fixed effects
    fixed_effects = summary["Coef."]
    std_err = summary["Std.Err."]
    pvalues = summary["P>|t|"]
    
    # Calculate 95% Confidence Intervals
    # CI = coef +/- 1.96 * std_err (approximate for large N, or use result.conf_int())
    conf_int = result.conf_int(alpha=0.05)
    
    # Standardize coefficients (Beta)
    # Beta = coef * (std_dev_X / std_dev_Y)
    y_std = df['ductility'].std()
    standardized_coeffs = {}
    
    for var in fixed_effects.index:
        if var in df.columns:
            x_std = df[var].std()
            coef = fixed_effects[var]
            std_beta = coef * (x_std / y_std)
            standardized_coeffs[var] = float(std_beta)
        else:
            # Handle intercept or non-data columns if necessary
            standardized_coeffs[var] = float(fixed_effects[var])
    
    # Extract Random Effects (Intercepts per group)
    random_effects = result.random_effects
    random_intercepts = {}
    for group, re in random_effects.items():
        # re is a dict/array; usually the first element is the intercept for the group
        if isinstance(re, (list, np.ndarray)):
            random_intercepts[str(group)] = float(re[0])
        elif isinstance(re, dict):
            # If it's a dict, look for the intercept key or just take the value if scalar
            random_intercepts[str(group)] = float(list(re.values())[0])
        else:
            random_intercepts[str(group)] = float(re)
    
    # Compile results
    results_dict = {
        "coefficients": {k: float(v) for k, v in fixed_effects.items()},
        "standardized_coefficients": standardized_coeffs,
        "std_errors": {k: float(v) for k, v in std_err.items()},
        "pvalues": {k: float(v) for k, v in pvalues.items()},
        "conf_int_95": {k: [float(v[0]), float(v[1])] for k, v in conf_int.iterrows()},
        "convergence": bool(result.converged),
        "random_intercepts": random_intercepts,
        "formula": result.model.formula,
        "n_obs": len(df),
        "n_groups": df['alloy_family'].nunique()
    }
    
    # Add significance flags
    results_dict["significant_features"] = []
    for var, p in results_dict["pvalues"].items():
        if var != "Intercept" and p < 0.05:
            results_dict["significant_features"].append(var)
    
    return results_dict

def save_results(results, output_path):
    """Save results to JSON."""
    logger.info(f"Saving results to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("Results saved.")

def main():
    """Main entry point for LME modeling."""
    logger.info("Starting LME Modeling...")
    
    try:
        df = load_data()
        prepared_df = prepare_features(df)
        result = fit_lme_model(prepared_df)
        
        if result is None:
            logger.error("LME model fitting failed.")
            sys.exit(1)
        
        extracted = extract_results(result, prepared_df)
        
        base_dir = Path(__file__).parent.parent.parent
        output_path = base_dir / "artifacts" / "lme_model_results.json"
        save_results(extracted, output_path)
        
        logger.info("LME Modeling stage completed.")
        return extracted
    except Exception as e:
        logger.error(f"LME Modeling pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()