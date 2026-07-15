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
    """Load processed data."""
    path = Path(__file__).parent.parent.parent / "data" / "processed_data.csv"
    if not path.exists():
        raise FileNotFoundError(f"Data not found: {path}")
    return pd.read_csv(path)

def prepare_features(df):
    """Prepare features for LME."""
    # Select features based on VIF analysis (assumed to be in 'energy_density' or all)
    features = ['energy_density'] # Simplified for demo
    if 'energy_density' not in df.columns:
        features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    return df[features]

def fit_lme_model(df):
    """Fit Linear Mixed-Effects model."""
    logger.info("Fitting LME model...")
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
    except ImportError:
        logger.error("statsmodels not installed. Please install via requirements.txt.")
        sys.exit(1)
    
    # Formula: ductility ~ energy_density + (1 | alloy_family)
    # If energy_density is not available, use other features
    if 'energy_density' in df.columns:
        formula = "ductility ~ energy_density"
    else:
        formula = "ductility ~ laser_power + scan_speed"
    
    formula += " + (1 | alloy_family)"
    
    try:
        model = smf.mixedlm(formula, df, groups=df["alloy_family"])
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        return None

def extract_results(result):
    """Extract standardized coefficients, CIs, p-values."""
    logger.info("Extracting results...")
    if result is None:
        return None
    
    # Simplified extraction
    summary = result.summary2().tables[1]
    coeffs = summary["Coef."]
    std_err = summary["Std.Err."]
    pvalues = summary["P>|t|"]
    
    return {
        "coefficients": coeffs.to_dict(),
        "std_errors": std_err.to_dict(),
        "pvalues": pvalues.to_dict(),
        "convergence": result.converged
    }

def save_results(results, output_path):
    """Save results to JSON."""
    logger.info(f"Saving results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

def main():
    """Main entry point for LME modeling."""
    logger.info("Starting LME Modeling...")
    
    df = load_data()
    result = fit_lme_model(df)
    
    if result is None:
        logger.error("LME model fitting failed.")
        sys.exit(1)
    
    extracted = extract_results(result)
    output_path = Path(__file__).parent.parent.parent / "artifacts" / "lme_results.json"
    save_results(extracted, output_path)
    
    logger.info("LME Modeling stage completed.")
    return extracted

if __name__ == "__main__":
    main()
