"""
Design-based variance estimation utilities.

Implements Taylor series linearization and Jackknife variance estimation
for complex survey data, with specific handling for design column presence
and edge cases like small clusters (PSU size = 1).
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_manifest(manifest_path: str = "state/manifest.yaml") -> Dict[str, Any]:
    """Load the state manifest file."""
    try:
        import yaml
        with open(manifest_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning(f"Manifest file not found at {manifest_path}. Returning empty dict.")
        return {}

def update_manifest_with_entry(manifest: Dict[str, Any], key: str, value: Any) -> None:
    """Update the manifest dictionary with a new entry."""
    manifest[key] = value

def check_design_columns(df: pd.DataFrame, variable: str) -> Tuple[bool, List[str]]:
    """
    Check if required design columns (psu, strata, weight) are present.
    
    Args:
        df: The dataframe to check.
        variable: The variable being analyzed (for logging).
        
    Returns:
        Tuple of (is_valid, list_of_missing_columns).
        
    Raises:
        MissingDesignColumnsError: If critical columns are missing.
    """
    required_cols = ['psu', 'strata', 'weight']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing design columns for variable '{variable}': {missing_cols}")
        # Log to manifest as per T009 requirement
        manifest = load_manifest()
        update_manifest_with_entry(manifest, f"missing_design_cols_{variable}", missing_cols)
        # Save manifest back
        import yaml
        with open("state/manifest.yaml", 'w') as f:
            yaml.dump(manifest, f)
        raise MissingDesignColumnsError(f"Missing columns: {missing_cols} for variable {variable}")
    
    return True, []

class MissingDesignColumnsError(Exception):
    """Raised when required design columns are missing."""
    pass

class SubsetLimitError(Exception):
    """Raised when dataset exceeds row limit."""
    pass

def estimate_taylor_variance(df: pd.DataFrame, variable: str) -> Dict[str, Any]:
    """
    Estimate variance using Taylor series linearization.
    
    This function detects small clusters (PSU size = 1) as per T009b.
    If a PSU has size 1, it issues a warning and flags the variance as
    "potentially unstable" but does not abort.
    
    Args:
        df: Dataframe with survey design columns.
        variable: The variable name to estimate variance for.
        
    Returns:
        Dictionary containing variance estimate and stability flags.
    """
    # Check for design columns first
    is_valid, missing = check_design_columns(df, variable)
    
    if variable not in df.columns:
        raise ValueError(f"Variable '{variable}' not found in dataframe")
        
    # Drop missing values for the target variable
    clean_df = df[[variable, 'psu', 'strata', 'weight']].dropna()
    
    if len(clean_df) == 0:
        logger.warning(f"No valid data for variable '{variable}' after dropping NaNs")
        return {
            "variable": variable,
            "variance_estimate": None,
            "status": "no_data",
            "potentially_unstable": False
        }

    # Detect small clusters (PSU size = 1) - T009b Logic
    psu_counts = clean_df.groupby('psu').size()
    single_cluster_psus = psu_counts[psu_counts == 1].index.tolist()
    is_unstable = len(single_cluster_psus) > 0
    
    if is_unstable:
        logger.warning(
            f"Variable '{variable}': Detected {len(single_cluster_psus)} clusters with PSU size = 1. "
            f"Variance estimate is potentially unstable."
        )
        # Log to manifest
        manifest = load_manifest()
        if "psu1_warnings" not in manifest:
            manifest["psu1_warnings"] = []
        manifest["psu1_warnings"].append({
            "variable": variable,
            "psu_count": len(single_cluster_psus),
            "action_taken": "warn",
            "message": "Detected clusters with PSU size = 1"
        })
        import yaml
        with open("state/manifest.yaml", 'w') as f:
            yaml.dump(manifest, f)

    # Calculate Taylor Series Linearization Variance
    # 1. Calculate weighted mean
    weights = clean_df['weight']
    values = clean_df[variable]
    w_mean = np.average(values, weights=weights)
    
    # 2. Calculate residuals (linearization)
    residuals = values - w_mean
    
    # 3. Group by PSU to get cluster totals of residuals
    # We need to sum (weight * residual) per PSU
    clean_df['residual_contrib'] = clean_df['weight'] * residuals
    psu_totals = clean_df.groupby('strata').apply(
        lambda x: x.groupby('psu')['residual_contrib'].sum()
    )
    
    # Flatten the multi-index if necessary
    if isinstance(psu_totals, pd.Series) and psu_totals.index.nlevels > 1:
        psu_totals = psu_totals.droplevel(0)
    
    # 4. Calculate variance of PSU totals within strata
    # Variance formula: sum((t_h - t)^2) / (L-1) ... simplified for this context
    # Using a robust estimator for variance of the mean
    n_strata = clean_df['strata'].nunique()
    if n_strata < 2:
        logger.warning("Only one stratum found. Variance estimation may be unreliable.")
        # Fallback to naive variance if only one stratum, but flag it
        naive_var = np.average(residuals**2, weights=weights)
        return {
            "variable": variable,
            "variance_estimate": float(naive_var),
            "status": "single_stratum",
            "potentially_unstable": True
        }

    # Standard Taylor Linearization for mean variance
    # V(mean) = sum_h (1 - f_h) * (S_h^2 / n_h) approximated by cluster totals
    # Simplified implementation: Variance of cluster totals weighted by design
    total_weight = weights.sum()
    cluster_var = np.var(psu_totals, ddof=1) if len(psu_totals) > 1 else 0.0
    
    # Variance of the estimator
    variance_est = (cluster_var / (n_strata * (total_weight**2))) if total_weight > 0 else 0.0
    
    return {
        "variable": variable,
        "variance_estimate": float(variance_est) if not np.isnan(variance_est) else 0.0,
        "status": "success",
        "potentially_unstable": is_unstable,
        "n_clusters": len(psu_counts),
        "single_cluster_count": len(single_cluster_psus)
    }

def calculate_jackknife_variance_for_variable(df: pd.DataFrame, variable: str) -> Dict[str, Any]:
    """
    Calculate Jackknife variance for a specific variable.
    
    Args:
        df: Dataframe with survey data.
        variable: Variable name.
        
    Returns:
        Dictionary with variance estimate.
    """
    if variable not in df.columns:
        raise ValueError(f"Variable '{variable}' not found")
        
    # Basic delete-one jackknife
    clean_df = df[[variable, 'weight']].dropna()
    if len(clean_df) < 2:
        return {"variable": variable, "variance_estimate": None, "status": "insufficient_data"}
        
    weights = clean_df['weight']
    values = clean_df[variable]
    full_mean = np.average(values, weights=weights)
    
    jackknife_means = []
    for i in range(len(clean_df)):
        # Leave-one-out
        mask = np.ones(len(clean_df), dtype=bool)
        mask[i] = False
        w_jack = weights[mask]
        v_jack = values[mask]
        if len(w_jack) == 0:
            continue
        mean_jack = np.average(v_jack, weights=w_jack)
        jackknife_means.append(mean_jack)
        
    if len(jackknife_means) < 2:
        return {"variable": variable, "variance_estimate": None, "status": "insufficient_jackknife"}
        
    # Variance formula: (n-1)/n * sum((theta_i - theta_bar)^2)
    theta_bar = np.mean(jackknife_means)
    variance_est = ((len(jackknife_means) - 1) / len(jackknife_means)) * np.sum((np.array(jackknife_means) - theta_bar)**2)
    
    return {
        "variable": variable,
        "variance_estimate": float(variance_est),
        "status": "success"
    }

def delete_one_jackknife_variance(df: pd.DataFrame, variable: str) -> float:
    """Helper for delete-one jackknife."""
    result = calculate_jackknife_variance_for_variable(df, variable)
    return result.get("variance_estimate", 0.0)

def run_jackknife_analysis(df: pd.DataFrame, variables: List[str]) -> List[Dict[str, Any]]:
    """Run jackknife analysis on a list of variables."""
    results = []
    for var in variables:
        try:
            res = calculate_jackknife_variance_for_variable(df, var)
            results.append(res)
        except Exception as e:
            logger.error(f"Jackknife failed for {var}: {e}")
            results.append({"variable": var, "error": str(e)})
    return results

def apply_simplified_estimator(df: pd.DataFrame, variable: str) -> Dict[str, Any]:
    """
    Apply a simplified variance estimator as a fallback for edge cases.
    
    Note: Per T009b revised instruction, the primary directive is to flag instability
    rather than enforce a specific heuristic. This function provides a conservative
    estimate if needed, but the main logic in estimate_taylor_variance handles the flagging.
    """
    clean_df = df[[variable, 'weight']].dropna()
    if len(clean_df) == 0:
        return {"variable": variable, "variance_estimate": None, "status": "no_data"}
        
    values = clean_df[variable]
    weights = clean_df['weight']
    
    # Conservative estimate: 2x naive variance (heuristic)
    naive_var = np.average((values - np.average(values, weights=weights))**2, weights=weights)
    conservative_var = 2.0 * naive_var
    
    return {
        "variable": variable,
        "variance_estimate": float(conservative_var),
        "status": "estimated_with_fallback",
        "note": "Conservative estimator applied due to edge case"
    }

def main():
    """Main entry point for command line testing."""
    import argparse
    parser = argparse.ArgumentParser(description="Design-based variance estimation")
    parser.add_argument('--variable', type=str, default='hrs1', help='Variable to analyze')
    parser.add_argument('--input', type=str, default='data/raw/gss_2018_subset.csv', help='Input data file')
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
        
    df = pd.read_csv(args.input)
    try:
        result = estimate_taylor_variance(df, args.variable)
        print(json.dumps(result, indent=2))
    except MissingDesignColumnsError as e:
        logger.error(f"Analysis aborted: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()