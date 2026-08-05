import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from config import get_config
import scipy.stats as stats
import json
from pathlib import Path

logger = logging.getLogger(__name__)

def load_analysis_data(metadata_path: str, retrieval_path: str) -> pd.DataFrame:
    """
    Load and merge metadata and retrieval results for analysis.
    
    Args:
        metadata_path: Path to data/processed/metadata.csv
        retrieval_path: Path to data/processed/retrieval_results.csv
        
    Returns:
        Merged DataFrame with all necessary columns for analysis
    """
    logger.info(f"Loading metadata from {metadata_path}")
    metadata_df = pd.read_csv(metadata_path)
    
    logger.info(f"Loading retrieval results from {retrieval_path}")
    retrieval_df = pd.read_csv(retrieval_path)
    
    # Merge on planet name or ID (assuming a common key exists)
    # Adjust column name based on actual data structure
    merge_key = 'planet_name' if 'planet_name' in metadata_df.columns else 'planet_id'
    if merge_key not in retrieval_df.columns:
        # Try alternative keys
        merge_key = 'planet_id' if 'planet_id' in retrieval_df.columns else None
    
    if merge_key:
        merged_df = pd.merge(metadata_df, retrieval_df, on=merge_key, how='inner')
        logger.info(f"Merged dataset contains {len(merged_df)} records on key '{merge_key}'")
    else:
        raise ValueError("Could not find a common key to merge metadata and retrieval results")
        
    return merged_df

def compute_censored_kendall_tau(df: pd.DataFrame, x_col: str, y_col: str, 
                                 censor_col: str = 'is_upper_limit') -> Tuple[float, float, Dict[str, Any]]:
    """
    Compute Kendall's tau correlation for censored data using scikit-survival.
    
    Args:
        df: DataFrame containing the data
        x_col: Column name for the independent variable (e.g., temperature)
        y_col: Column name for the dependent variable (e.g., water abundance)
        censor_col: Column name indicating if the value is an upper limit (1=True, 0=False)
        
    Returns:
        Tuple of (tau, p_value, stats_dict)
    """
    try:
        from scikit_survival import survival_function
        from scikit_survival.linear_model import CoxPHSurvivalAnalysis
        # Note: scikit-survival doesn't have a direct 'kendall_tau' for censored data in the same way
        # We use the survival analysis framework to compute rank-based correlations
        # For true Kendall's tau with censoring, we implement a manual calculation or use a specialized function
        
        # Since scikit-survival is primarily for survival models, we'll use a manual implementation
        # of Kendall's tau-b with censoring handling
        x = df[x_col].values
        y = df[y_col].values
        is_censored = df[censor_col].astype(bool).values
        
        n = len(x)
        concordant = 0
        discordant = 0
        tied_x = 0
        tied_y = 0
        tied_xy = 0
        
        # Handle censored data: only compare pairs where both are observed or one is censored appropriately
        for i in range(n):
            for j in range(i + 1, n):
                # Skip pairs where both are censored (cannot determine order)
                if is_censored[i] and is_censored[j]:
                    continue
                    
                # For censored data, we treat censored values as lower bounds for upper limits
                # If i is censored (upper limit), we only count if x_i > x_j and y_i > y_j (conservative)
                # This is a simplified approach; a full implementation would use the Akritas-Theil-Sen estimator
                
                xi, xj = x[i], x[j]
                yi, yj = y[i], y[j]
                
                dx = xi - xj
                dy = yi - yj
                
                if dx == 0:
                    tied_x += 1
                if dy == 0:
                    tied_y += 1
                if dx == 0 and dy == 0:
                    tied_xy += 1
                
                if not is_censored[i] and not is_censored[j]:
                    # Both observed: standard Kendall calculation
                    if dx * dy > 0:
                        concordant += 1
                    elif dx * dy < 0:
                        discordant += 1
                elif is_censored[i]:
                    # i is censored (upper limit): only count if xi > xj and yi > yj (conservative)
                    # This assumes the true value is below the limit, so if the limit is higher, 
                    # the true value could still be lower
                    if dx > 0 and dy > 0:
                        concordant += 1
                    elif dx < 0 and dy < 0:
                        discordant += 1
                elif is_censored[j]:
                    # j is censored (upper limit): similar logic
                    if dx > 0 and dy > 0:
                        concordant += 1
                    elif dx < 0 and dy < 0:
                        discordant += 1
        
        n_pairs = n * (n - 1) / 2
        n_effective = concordant + discordant + tied_x + tied_y - tied_xy
        
        if n_effective == 0:
            logger.warning("No effective pairs for Kendall's tau calculation")
            return 0.0, 1.0, {"tau": 0.0, "p_value": 1.0, "n_pairs": 0, "concordant": 0, "discordant": 0}
        
        tau = (concordant - discordant) / np.sqrt((n_effective + tied_x) * (n_effective + tied_y))
        
        # Approximate p-value using normal approximation
        # This is a simplification; exact p-values for censored data require permutation tests
        se_tau = np.sqrt((2 * (2 * n + 5)) / (9 * n * (n - 1)))
        z = tau / se_tau
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
        
        stats_dict = {
            "tau": float(tau),
            "p_value": float(p_value),
            "n_pairs": int(n_pairs),
            "concordant": int(concordant),
            "discordant": int(discordant),
            "n_effective": int(n_effective),
            "method": "censored_kendall_tau_approx"
        }
        
        logger.info(f"Kendall's tau: {tau:.4f}, p-value: {p_value:.4f}")
        return float(tau), float(p_value), stats_dict
        
    except ImportError:
        logger.warning("scikit-survival not available, using scipy.stats.kendalltau on observed data only")
        # Fallback to standard Kendall's tau on observed data
        observed_mask = ~df[censor_col].astype(bool)
        x_obs = df.loc[observed_mask, x_col].values
        y_obs = df.loc[observed_mask, y_col].values
        
        if len(x_obs) < 2:
            logger.warning("Not enough observed data points for correlation")
            return 0.0, 1.0, {"tau": 0.0, "p_value": 1.0, "n_observed": len(x_obs)}
        
        tau, p_value = stats.kendalltau(x_obs, y_obs)
        return float(tau), float(p_value), {"tau": float(tau), "p_value": float(p_value), "n_observed": len(x_obs)}

def run_tobit_regression(df: pd.DataFrame, x_cols: List[str], y_col: str, 
                         censor_col: str = 'is_upper_limit') -> Dict[str, Any]:
    """
    Run Tobit regression for censored data.
    
    Args:
        df: DataFrame containing the data
        x_cols: List of column names for independent variables
        y_col: Column name for dependent variable
        censor_col: Column name indicating if the value is an upper limit
        
    Returns:
        Dictionary containing regression results
    """
    try:
        from lifelines import WeibullAFTFitter
        # Note: lifelines doesn't have a direct Tobit model, but WeibullAFT can approximate it
        # for censored data. Alternatively, we could use statsmodels' Tobit if available.
        
        # Prepare data
        X = df[x_cols].dropna()
        y = df.loc[X.index, y_col]
        censor = df.loc[X.index, censor_col].astype(int)
        
        if len(X) == 0:
            logger.warning("No valid data points for Tobit regression")
            return {"status": "failed", "reason": "no_data", "coefficients": {}, "aic": None}
        
        # Fit Weibull AFT model as a proxy for Tobit
        # This is a simplification; a true Tobit model would be preferred
        aft = WeibullAFTFitter(penalizer=0.1)  # Small regularization
        aft.fit(pd.DataFrame(X, columns=x_cols), duration_col=y, event_col=1-censor)
        
        results = {
            "status": "success",
            "coefficients": aft.params_.to_dict(),
            "aic": aft.aic_,
            "log_likelihood": aft.log_likelihood_,
            "n_samples": len(X),
            "n_censored": int(censor.sum()),
            "n_uncensored": int(len(censor) - censor.sum()),
            "model": "WeibullAFT_proxy"
        }
        
        logger.info(f"Tobit regression completed: AIC = {aft.aic_:.2f}")
        return results
        
    except ImportError:
        logger.warning("lifelines not available, cannot run Tobit regression")
        return {"status": "failed", "reason": "lifelines_not_available", "coefficients": {}, "aic": None}
    except Exception as e:
        logger.error(f"Tobit regression failed: {str(e)}")
        return {"status": "failed", "reason": str(e), "coefficients": {}, "aic": None}

def generate_final_statistics(df: pd.DataFrame, tau: float, p_value: float, 
                              tau_stats: Dict[str, Any], tobit_results: Dict[str, Any],
                              output_path: str) -> Dict[str, Any]:
    """
    Generate and save final statistics to JSON.
    
    Args:
        df: The analysis DataFrame
        tau: Kendall's tau value
        p_value: p-value for the correlation
        tau_stats: Additional statistics from Kendall's tau calculation
        tobit_results: Results from Tobit regression
        output_path: Path to save the results JSON
        
    Returns:
        Dictionary containing all final statistics
    """
    # Calculate CI width for water abundance distribution
    water_col = 'log10_water_abundance' if 'log10_water_abundance' in df.columns else None
    if water_col:
        water_values = df[water_col].dropna()
        if len(water_values) > 1:
            ci_width = water_values.max() - water_values.min()
            ci_width_pct = (ci_width / np.abs(water_values.mean())) * 100 if water_values.mean() != 0 else 0.0
        else:
            ci_width = 0.0
            ci_width_pct = 0.0
    else:
        ci_width = 0.0
        ci_width_pct = 0.0
    
    # Count censored vs uncensored
    censor_col = 'is_upper_limit' if 'is_upper_limit' in df.columns else None
    n_censored = 0
    n_uncensored = 0
    if censor_col:
        n_censored = int(df[censor_col].sum())
        n_uncensored = int(len(df) - n_censored)
    
    final_stats = {
        "kendall_tau": {
            "tau": tau,
            "p_value": p_value,
            "method": tau_stats.get("method", "unknown"),
            "n_pairs": tau_stats.get("n_pairs", 0),
            "concordant": tau_stats.get("concordant", 0),
            "discordant": tau_stats.get("discordant", 0),
            "n_effective": tau_stats.get("n_effective", 0)
        },
        "tobit_regression": tobit_results,
        "data_quality": {
            "total_samples": len(df),
            "n_censored": n_censored,
            "n_uncensored": n_uncensored,
            "ci_width_range": float(ci_width),
            "ci_width_pct": float(ci_width_pct)
        },
        "metadata": {
            "temperature_range": [float(df['equilibrium_temperature'].min()), float(df['equilibrium_temperature'].max())] if 'equilibrium_temperature' in df.columns else None,
            "metallicity_range": [float(df['metallicity'].min()), float(df['metallicity'].max())] if 'metallicity' in df.columns else None,
            "spectral_resolution_range": [float(df['spectral_resolution'].min()), float(df['spectral_resolution'].max())] if 'spectral_resolution' in df.columns else None
        },
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(final_stats, f, indent=2)
    
    logger.info(f"Final statistics saved to {output_path}")
    return final_stats

def main():
    """Main entry point for the analysis pipeline."""
    config = get_config()
    logging.basicConfig(level=config.get('log_level', 'INFO'))
    
    # Define paths
    metadata_path = config.get('metadata_path', 'data/processed/metadata.csv')
    retrieval_path = config.get('retrieval_path', 'data/processed/retrieval_results.csv')
    output_path = config.get('analysis_results_path', 'data/processed/analysis_results.json')
    
    try:
        # Load data
        df = load_analysis_data(metadata_path, retrieval_path)
        
        # Compute Kendall's tau
        tau, p_value, tau_stats = compute_censored_kendall_tau(
            df, 
            x_col='equilibrium_temperature', 
            y_col='log10_water_abundance',
            censor_col='is_upper_limit'
        )
        
        # Run Tobit regression
        tobit_results = run_tobit_regression(
            df,
            x_cols=['equilibrium_temperature', 'metallicity'],
            y_col='log10_water_abundance',
            censor_col='is_upper_limit'
        )
        
        # Generate final statistics
        final_stats = generate_final_statistics(
            df, tau, p_value, tau_stats, tobit_results, output_path
        )
        
        logger.info("Analysis completed successfully")
        return final_stats
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
