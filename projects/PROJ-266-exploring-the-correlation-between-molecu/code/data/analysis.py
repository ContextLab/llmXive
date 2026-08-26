import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit
import statsmodels.api as sm
import json

from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

# Configure logging
logger = get_logger(__name__)
configure_root_logger()

def get_project_root() -> Path:
    """Return the project root directory."""
    return get_project_root()

def load_analysis_data() -> pd.DataFrame:
    """
    Load the processed data required for analysis.
    Merges filtered permeability data with computed descriptors.
    """
    root = get_project_root()
    filtered_path = root / "data" / "processed" / "filtered_data.csv"
    descriptors_path = root / "data" / "processed" / "descriptors_raw.csv"

    if not filtered_path.exists():
        raise FileNotFoundError(f"Required file not found: {filtered_path}")
    if not descriptors_path.exists():
        raise FileNotFoundError(f"Required file not found: {descriptors_path}")

    df_perm = pd.read_csv(filtered_path)
    df_desc = pd.read_csv(descriptors_path)

    # Merge on SMILES
    # Ensure SMILES is string to avoid type mismatches
    df_perm['smiles'] = df_perm['smiles'].astype(str)
    df_desc['smiles'] = df_desc['smiles'].astype(str)

    merged = pd.merge(df_perm, df_desc, on='smiles', how='inner')

    # Drop rows with NaN in critical columns
    critical_cols = ['logPapp', 'dihedral_variance']
    merged = merged.dropna(subset=critical_cols)

    logger.info(f"Loaded {len(merged)} records for analysis after merge.")
    return merged

def calculate_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Pearson and Spearman correlations between dihedral_variance and logPapp.
    Controls for confounders (logP, MW, PSA) via partial correlation logic if available,
    otherwise reports simple correlations and VIF separately.
    """
    logger.info("Calculating correlations...")
    
    results = []
    
    # Primary metric: dihedral_variance
    x = df['dihedral_variance']
    y = df['logPapp']

    # Pearson
    r_pearson, p_pearson = stats.pearsonr(x, y)
    # Spearman
    r_spearman, p_spearman = stats.spearmanr(x, y)

    results.append({
        'variable_x': 'dihedral_variance',
        'variable_y': 'logPapp',
        'correlation_type': 'pearson',
        'r_value': r_pearson,
        'p_value': p_pearson,
        'r_squared': r_pearson**2
    })
    results.append({
        'variable_x': 'dihedral_variance',
        'variable_y': 'logPapp',
        'correlation_type': 'spearman',
        'r_value': r_spearman,
        'p_value': p_spearman,
        'r_squared': r_spearman**2
    })

    return pd.DataFrame(results)

def calculate_vif(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Variance Inflation Factor for confounders."""
    logger.info("Calculating VIF...")
    # Simple VIF calculation
    # Using logP, MW, PSA as potential confounders if present
    confounders = ['logP', 'mw', 'psa']
    available_conf = [c for c in confounders if c in df.columns]
    
    if not available_conf:
        logger.warning("No confounders found for VIF calculation.")
        return pd.DataFrame()

    X = df[available_conf]
    X = sm.add_constant(X)
    
    vif_data = []
    for col in X.columns:
        if col == 'const':
            continue
        try:
            model = sm.OLS(X[col], X.drop(columns=[col])).fit()
            vif = model.rsquared_adj  # Approximation or use 1/(1-R2)
            # Correct VIF formula: 1 / (1 - R^2) where R^2 is from regressing col on others
            r2 = model.rsquared
            vif = 1.0 / (1.0 - r2)
            vif_data.append({'variable': col, 'vif': vif})
        except Exception as e:
            logger.error(f"VIF calculation failed for {col}: {e}")
            
    return pd.DataFrame(vif_data)

def fit_multivariate_model(df: pd.DataFrame) -> Dict[str, Any]:
    """Fit a multivariate linear regression model."""
    logger.info("Fitting multivariate model...")
    # Target: logPapp
    # Predictors: dihedral_variance + confounders
    target = 'logPapp'
    predictors = ['dihedral_variance']
    confounders = ['logP', 'mw', 'psa']
    
    available_conf = [c for c in confounders if c in df.columns]
    X_cols = predictors + available_conf
    
    if not all(c in df.columns for c in X_cols):
        missing = [c for c in X_cols if c not in df.columns]
        logger.error(f"Missing columns for model: {missing}")
        return {}

    X = df[X_cols]
    y = df[target]
    
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    
    return {
        'rsquared': model.rsquared,
        'rsquared_adj': model.rsquared_adj,
        'aic': model.aic,
        'bic': model.bic,
        'params': model.params.to_dict(),
        'pvalues': model.pvalues.to_dict()
    }

def apply_benjamini_hochberg(df: pd.DataFrame, p_col: str = 'p_value', alpha: float = 0.05) -> pd.DataFrame:
    """Apply Benjamini-Hochberg FDR correction."""
    logger.info("Applying Benjamini-Hochberg FDR correction...")
    if df.empty:
        return df

    # Sort by p-value
    df_sorted = df.sort_values(by=p_col)
    n = len(df_sorted)
    ranks = np.arange(1, n + 1)
    
    # Calculate q-values
    # q_i = (p_i * n) / rank_i
    # Ensure q <= 1
    q_values = (df_sorted[p_col] * n) / ranks
    q_values = np.minimum(q_values, 1.0)
    
    # Monotonicity check: q_i should be >= q_{i-1}
    # We enforce monotonicity from bottom up
    for i in range(n - 2, -1, -1):
        if q_values[i] > q_values[i+1]:
            q_values[i] = q_values[i+1]
    
    df_sorted = df_sorted.copy()
    df_sorted['q_value'] = q_values
    df_sorted['is_significant'] = df_sorted['q_value'] < alpha
    
    # Restore original order
    df_result = df_sorted.sort_index()
    return df_result

def write_correlation_results(df: pd.DataFrame, output_path: Path):
    """Write correlation results to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Correlation results written to {output_path}")

def write_fdr_results(df: pd.DataFrame, output_path: Path):
    """Write FDR corrected results to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"FDR results written to {output_path}")

def compute_complexity_index(df: pd.DataFrame) -> pd.Series:
    """
    Compute a complexity_index based on molecular size and flexibility.
    Formula: complexity_index = (MW * dihedral_variance) / 1000
    This is a heuristic combining size (MW) and flexibility (dihedral_variance).
    """
    if 'mw' not in df.columns:
        logger.warning("MW column not found, using placeholder for complexity.")
        # Fallback if MW is missing, just use variance scaled
        return df['dihedral_variance'] * 100
    
    # Normalize or scale appropriately
    # Using raw product as a simple complexity metric for scaling law
    return (df['mw'] * df['dihedral_variance']) / 1000.0

def check_linear_correlation_strength(df: pd.DataFrame) -> Tuple[float, bool]:
    """
    Check if linear correlation (R²) is below 0.3.
    Returns (r_squared, should_initiate_scaling).
    """
    if df.empty or 'dihedral_variance' not in df.columns or 'logPapp' not in df.columns:
        logger.warning("Insufficient data to check linear correlation strength.")
        return 0.0, False
    
    x = df['dihedral_variance'].values
    y = df['logPapp'].values
    
    # Remove NaNs
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 3:
        logger.warning("Not enough data points to calculate R².")
        return 0.0, False
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_clean, y_clean)
    r_squared = r_value ** 2
    
    logger.info(f"Linear R² between dihedral_variance and logPapp: {r_squared:.4f}")
    return r_squared, r_squared < 0.3

def main():
    """Main execution flow for T026: Scaling Law Analysis Logic."""
    logger.info("Starting T026: Scaling Law Analysis Logic")
    
    root = get_project_root()
    correlation_results_path = root / "data" / "processed" / "correlation_results.csv"
    scaling_analysis_path = root / "data" / "processed" / "scaling_analysis_results.json"
    
    # 1. Load data
    try:
        df = load_analysis_data()
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)
    
    # 2. Check linear correlation strength
    r_squared, should_scale = check_linear_correlation_strength(df)
    
    result_summary = {
        'linear_r_squared': r_squared,
        'scaling_analysis_triggered': should_scale,
        'sample_size': len(df),
        'complexity_index_computed': False,
        'message': 'Linear correlation R² >= 0.3. Scaling law analysis not required.'
    }
    
    if not should_scale:
        logger.info("Linear correlation is strong enough (R² >= 0.3). Skipping scaling law analysis.")
        # Still save the summary
        with open(scaling_analysis_path, 'w') as f:
            json.dump(result_summary, f, indent=2)
        return

    logger.info("Linear correlation R² < 0.3. Initiating scaling law analysis.")
    
    # 3. Compute complexity_index
    try:
        df['complexity_index'] = compute_complexity_index(df)
        result_summary['complexity_index_computed'] = True
        result_summary['complexity_index_stats'] = {
            'mean': float(df['complexity_index'].mean()),
            'std': float(df['complexity_index'].std()),
            'min': float(df['complexity_index'].min()),
            'max': float(df['complexity_index'].max())
        }
        logger.info("Complexity index computed successfully.")
    except Exception as e:
        logger.error(f"Failed to compute complexity index: {e}")
        result_summary['error_computing_complexity'] = str(e)
    
    # 4. Save intermediate state for next tasks (T027)
    # Save the enriched dataframe to allow power-law regression to run
    enriched_df_path = root / "data" / "processed" / "enriched_analysis_data.csv"
    df.to_csv(enriched_df_path, index=False)
    result_summary['enriched_data_path'] = str(enriched_df_path)
    
    # 5. Write summary
    with open(scaling_analysis_path, 'w') as f:
        json.dump(result_summary, f, indent=2)
    
    logger.info(f"Scaling law analysis logic completed. Results saved to {scaling_analysis_path}")
    
    # Invoke checksum utility
    checksum_path = root / "state" / "pending" / "checksums.yaml"
    try:
        from utils.checksum import scan_and_register_data_files
        scan_and_register_data_files(root, checksum_path)
        logger.info("Checksums updated.")
    except Exception as e:
        logger.warning(f"Failed to update checksums: {e}")

if __name__ == "__main__":
    main()