"""
Linear Mixed-Effects Model Implementation for Ductility Prediction.
Tasks: T023 (VIF handled in preprocessing), T024 (Model Fit), T027 (Artifact Save logic moved to save_lme_artifact.py but this provides extract_results).
"""
import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure code directory is in path
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    from statsmodels.regression.mixed_linear_model import MixedLM
except ImportError:
    logging.critical("Missing dependency: statsmodels. Please install via requirements.txt.")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_PATH = Path("data/curated_builds.csv")
# The feature set is determined by T023 (VIF logic).
# We assume the CSV already has the correct columns (either E_v alone or the components).
FIXED_EFFECTS = ['energy_density', 'alloy_family'] # Default fallback, will be dynamic
RANDOM_GROUP = 'alloy_family'

def load_data():
    """Load the curated dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}. Run T017 first.")
    df = pd.read_csv(DATA_PATH)
    logger.info(f"Loaded {len(df)} records from {DATA_PATH}")
    return df

def prepare_features(df):
    """
    Prepare features based on VIF analysis results (T023).
    If VIF analysis dropped individual parameters in favor of Energy Density,
    we use 'energy_density'. Otherwise, we might use individual parameters.
    For this implementation, we check column existence.
    """
    # Target
    y = df['ductility'].values

    # Grouping
    groups = df[RANDOM_GROUP].values

    # Features: Check if Energy Density is present (preferred if VIF > 5)
    # If not, check for components.
    potential_features = ['energy_density', 'laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    selected_features = []

    for col in potential_features:
        if col in df.columns:
            selected_features.append(col)

    if not selected_features:
        raise ValueError("No valid predictor columns found in dataset for fixed effects.")

    X = df[selected_features].values
    feature_names = selected_features

    # Handle missing values in X or y
    mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    if not np.all(mask):
        logger.warning(f"Removing {np.sum(~mask)} rows with NaN values.")
        X = X[mask]
        y = y[mask]
        groups = groups[mask]

    return X, y, groups, feature_names

def fit_lme_model(X, y, groups, feature_names):
    """
    Fit the Linear Mixed-Effects model.
    Returns the fitted model and a dictionary of raw results.
    """
    # Construct formula
    # Fixed effects: sum of selected features
    # Random effects: random intercept by alloy_family
    fixed_formula = " + ".join(feature_names)
    random_formula = "1"
    full_formula = f"{y.name} ~ {fixed_formula}" if hasattr(y, 'name') else f"ductility ~ {fixed_formula}"
    # Actually, we need a DataFrame for formula API
    temp_df = pd.DataFrame(X, columns=feature_names)
    temp_df['ductility'] = y
    temp_df[RANDOM_GROUP] = groups

    logger.info(f"Fitting LME with formula: {full_formula} | Random: 1 | {RANDOM_GROUP}")

def fit_lme_model(X, y, groups):
    """
    Fit Linear Mixed-Effects model with fixed effects from X and random intercept for alloy_family.
    Returns the fitted model and convergence status.
    """
    logger.info("Fitting Linear Mixed-Effects model...")
    
    try:
        model = smf.mixedlm(full_formula, temp_df, groups=temp_df[RANDOM_GROUP])
        result = model.fit()
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        raise

    return model, result

def extract_results(model, result, feature_names):
    """
    Extract standardized coefficients, CIs, p-values, and random effects.
    Returns a dictionary suitable for JSON serialization.
    """
    # Fixed Effects
    params = result.params
    bse = result.bse
    tvalues = result.tvalues
    pvalues = result.pvalues
    conf_int = result.conf_int()

    fixed_effects = []
    for i, feat in enumerate(feature_names):
        if feat in params.index:
            coef = params[feat]
            se = bse[feat] if feat in bse.index else 0.0
            t_val = tvalues[feat] if feat in tvalues.index else 0.0
            p_val = pvalues[feat] if feat in pvalues.index else 1.0
            ci_low = conf_int[feat][0] if feat in conf_int.index else 0.0
            ci_high = conf_int[feat][1] if feat in conf_int.index else 0.0
            
            fixed_effects.append({
                "term": feat,
                "coefficient": float(coef),
                "std_error": float(se),
                "t_value": float(t_val),
                "p_value": float(p_val),
                "ci_95_low": float(ci_low),
                "ci_95_high": float(ci_high)
            })

    # Random Effects (Intercepts per group)
    random_effects = {}
    if hasattr(result, 'random_effects'):
        re = result.random_effects
        for group, re_vals in re.items():
            # re_vals is usually a dict or array depending on the model structure
            # For random intercepts, it's typically a scalar or dict with intercept key
            if isinstance(re_vals, dict):
                val = re_vals.get('Intercept', 0.0)
            else:
                val = float(re_vals[0]) if len(re_vals) > 0 else 0.0
            random_effects[str(group)] = float(val)

    # Convergence Check
    # statsmodels fit result has a 'converged' attribute or we check the warning
    converged = result.converged if hasattr(result, 'converged') else True
    # If the result object doesn't explicitly flag convergence, we might infer from warnings
    # But standard fit() usually sets this.
    
    artifact = {
        "convergence_status": "success" if converged else "failed",
        "fixed_effects": fixed_effects,
        "random_effects": random_effects,
        "model_info": {
            "num_observations": len(result.model.endog),
            "num_groups": result.model.exog_grpcol.unique().shape[0] if hasattr(result.model, 'exog_grpcol') else len(set(result.model.groups)),
            "log_likelihood": float(result.llf) if hasattr(result, 'llf') else None
        }
    }
    
    logger.info(f"Extracted results for {len(fixed_effects)} fixed effects and {len(random_intercepts)} groups")
    return results_dict

    return artifact

def save_results(artifact_data, path):
    """Helper to save results to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(artifact_data, f, indent=2, default=str)

def main():
    """Main execution flow."""
    try:
        # Load data
        df = load_data()
        X, y, groups, feature_names = prepare_features(df)
        model, result = fit_lme_model(X, y, groups, feature_names)
        artifact = extract_results(model, result, feature_names)
        
        # Save to the specific artifact path for T027
        artifact_path = Path("artifacts/mixed_effects_result.json")
        save_results(artifact, artifact_path)
        
        logger.info(f"LME Model Artifact saved to {artifact_path}")
        print(f"Artifact saved. Convergence: {artifact['convergence_status']}")
        
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
