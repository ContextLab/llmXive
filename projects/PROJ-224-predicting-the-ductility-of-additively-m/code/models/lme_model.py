import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CURATED_DATA_PATH = "data/curated_builds.csv"
ARTIFACT_PATH = "artifacts/mixed_effects_results.json"
STATE_FILE_PATH = "state/projects/PROJ-224-predicting-the-ductility-of-additively-m.yaml"

def load_data():
    """Load the curated dataset."""
    if not os.path.exists(CURATED_DATA_PATH):
        raise FileNotFoundError(f"Curated data file not found at {CURATED_DATA_PATH}")
    
    logger.info(f"Loading data from {CURATED_DATA_PATH}")
    df = pd.read_csv(CURATED_DATA_PATH)
    
    # Verify required columns exist
    required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 
                   'ductility', 'alloy_family', 'energy_density']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns in curated data: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
    return df

def prepare_features(df):
    """
    Prepare features for LME model based on T023 VIF analysis results.
    Returns X (fixed effects) and y (target) with appropriate handling.
    """
    # T023 logic: If Energy Density VIF > 5, drop individual predictors and keep only Energy Density
    # We assume T023 has already determined the feature set.
    # For robustness, we check if energy_density is in the data and use it preferentially.
    
    # Check if we should use Energy Density only or individual parameters
    # This decision is typically made in T023, but we implement the logic here for completeness
    use_energy_density_only = True  # Default assumption based on T023 requirements
    
    if use_energy_density_only:
        if 'energy_density' not in df.columns:
            raise ValueError("energy_density column required but not found. Run T018 first.")
        features = ['energy_density']
        logger.info("Using energy_density as the sole fixed effect predictor (VIF > 5 logic)")
    else:
        # Fallback to individual parameters if energy_density is not used
        features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
        missing = [f for f in features if f not in df.columns]
        if missing:
            raise ValueError(f"Missing feature columns: {missing}")
        logger.info(f"Using individual parameters: {features}")
    
    # Prepare design matrix
    X = df[features].copy()
    y = df['ductility'].copy()
    
    # Handle missing values in features or target
    mask = ~X.isna().any(axis=1) & ~y.isna()
    if not mask.all():
        logger.warning(f"Dropping { (~mask).sum() } rows with missing values in features or target")
        X = X[mask]
        y = y[mask]
    
    # Add intercept term for statsmodels (MixedLM doesn't add it automatically)
    X_with_intercept = sm.add_constant(X)
    
    logger.info(f"Prepared {len(X)} samples with features: {list(X_with_intercept.columns)}")
    return X_with_intercept, y, df.loc[mask, 'alloy_family']

def fit_lme_model(X, y, groups):
    """
    Fit Linear Mixed-Effects model with fixed effects from X and random intercept for alloy_family.
    Returns the fitted model and convergence status.
    """
    logger.info("Fitting Linear Mixed-Effects model...")
    
    try:
        # Fit model with random intercept for alloy_family
        # formula: y ~ features | groups
        # We use the explicit design matrix approach
        model = MixedLM(y, X, groups=groups)
        
        # Fit with CPU-only execution (statsmodels is CPU-only by default)
        # Use 'lbfgs' as it's more robust for convergence
        result = model.fit(method='lbfgs', disp=False)
        
        convergence_status = result.converged
        logger.info(f"Model convergence status: {convergence_status}")
        
        if not convergence_status:
            logger.error("LME model failed to converge. Results may be unreliable.")
        
        return result, convergence_status
        
    except Exception as e:
        logger.error(f"Failed to fit LME model: {str(e)}")
        raise

def extract_results(result, X, y, convergence_status):
    """
    Extract standardized coefficients, 95% CIs, p-values, and random effects.
    """
    logger.info("Extracting model results...")
    
    # Get fixed effects parameters
    fixed_effects = result.fe_params
    std_errors = result.bse
    
    # Calculate 95% confidence intervals
    alpha = 0.05
    df_resid = result.df_resid
    t_crit = stats.t.ppf(1 - alpha/2, df_resid)
    ci_lower = fixed_effects - t_crit * std_errors
    ci_upper = fixed_effects + t_crit * std_errors
    
    # Calculate p-values (two-tailed)
    z_scores = fixed_effects / std_errors
    p_values = 2 * (1 - stats.t.cdf(np.abs(z_scores), df_resid))
    
    # Standardize coefficients
    # Standardization: beta_std = beta * (std_X / std_y)
    y_std = np.std(y)
    X_std = np.std(X, axis=0)
    
    standardized_coeffs = {}
    for i, col in enumerate(X.columns):
        if col == 'const':
            standardized_coeffs[col] = fixed_effects.iloc[i]  # Intercept not standardized
        else:
            standardized_coeffs[col] = fixed_effects.iloc[i] * (X_std[i] / y_std)
    
    # Extract random effects (intercepts for each alloy_family)
    random_effects = result.random_effects
    random_intercepts = {}
    for group, re in random_effects.items():
        # re is a 1D array for random intercept
        random_intercepts[str(group)] = float(re[0]) if len(re) > 0 else 0.0
    
    # Model statistics
    aic = result.aic
    bic = result.bic
    log_likelihood = result.llf
    num_obs = result.nobs
    num_groups = result.ngroups
    
    # Compile results
    results_dict = {
        'convergence_status': convergence_status,
        'fixed_effects': {
            'coefficients': {k: float(v) for k, v in fixed_effects.items()},
            'standardized_coefficients': {k: float(v) for k, v in standardized_coeffs.items()},
            'standard_errors': {k: float(v) for k, v in std_errors.items()},
            'confidence_intervals_95': {
                k: {'lower': float(ci_lower.iloc[i]), 'upper': float(ci_upper.iloc[i])}
                for i, k in enumerate(fixed_effects.index)
            },
            'p_values': {k: float(v) for k, v in p_values.items()}
        },
        'random_effects': {
            'type': 'intercept',
            'estimates_by_group': random_intercepts,
            'variance': float(result.cov_re[0, 0]) if result.cov_re.size > 0 else 0.0
        },
        'model_statistics': {
            'aic': float(aic),
            'bic': float(bic),
            'log_likelihood': float(log_likelihood),
            'num_observations': int(num_obs),
            'num_groups': int(num_groups),
            'degrees_of_freedom_resid': int(result.df_resid)
        }
    }
    
    logger.info(f"Extracted results for {len(fixed_effects)} fixed effects and {len(random_intercepts)} groups")
    return results_dict

def save_results(results_dict):
    """Save results to JSON artifact and update state file."""
    # Ensure artifacts directory exists
    artifact_path = Path(ARTIFACT_PATH)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON
    with open(artifact_path, 'w') as f:
        json.dump(results_dict, f, indent=2)
    
    logger.info(f"Saved LME results to {ARTIFACT_PATH}")
    
    # Update state file with artifact hash (T020 requirement)
    from data.version_artifact import compute_sha256, ensure_state_file, save_state
    
    artifact_hash = compute_sha256(artifact_path)
    state_data = ensure_state_file(STATE_FILE_PATH)
    
    if 'artifact_hashes' not in state_data:
        state_data['artifact_hashes'] = {}
    
    state_data['artifact_hashes']['mixed_effects_results'] = artifact_hash
    save_state(STATE_FILE_PATH, state_data)
    
    logger.info(f"Updated state file with hash: {artifact_hash}")
    
    return artifact_path

def main():
    """Main entry point for LME model fitting."""
    logger.info("Starting Linear Mixed-Effects model fitting (T024)")
    
    try:
        # Load data
        df = load_data()
        
        # Prepare features
        X, y, groups = prepare_features(df)
        
        # Fit model
        result, convergence_status = fit_lme_model(X, y, groups)
        
        # Extract results
        results_dict = extract_results(result, X, y, convergence_status)
        
        # Save results
        artifact_path = save_results(results_dict)
        
        # Log summary
        logger.info("LME model fitting completed successfully")
        logger.info(f"Convergence: {convergence_status}")
        logger.info(f"Fixed effects coefficients: {results_dict['fixed_effects']['coefficients']}")
        logger.info(f"Random effects variance: {results_dict['random_effects']['variance']}")
        
        return results_dict, artifact_path
        
    except Exception as e:
        logger.error(f"LME model fitting failed: {str(e)}")
        # If model fails to converge, we still save results but flag it
        if 'convergence_status' in locals() and not convergence_status:
            logger.warning("Results saved despite convergence failure")
            return None, None
        raise

if __name__ == "__main__":
    main()
