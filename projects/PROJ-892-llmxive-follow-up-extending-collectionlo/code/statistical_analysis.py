import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_results_data() -> pd.DataFrame:
    """
    Load the results CSV file.
    Validates that the file exists and is not empty.
    """
    results_path = get_project_root() / "data" / "results.csv"
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    df = pd.read_csv(results_path)
    if df.empty:
        raise ValueError(f"Results file is empty: {results_path}")
    
    logger.info(f"Loaded {len(df)} rows from {results_path}")
    return df

def load_subspace_ranks() -> Dict[str, Any]:
    """
    Load the subspace ranks JSON file.
    Validates that the file exists and contains valid data.
    """
    ranks_path = get_project_root() / "data" / "subspace_ranks.json"
    if not ranks_path.exists():
        raise FileNotFoundError(f"Subspace ranks file not found: {ranks_path}")
    
    with open(ranks_path, 'r') as f:
        ranks = json.load(f)
    
    if not ranks:
        raise ValueError(f"Subspace ranks file is empty: {ranks_path}")
    
    logger.info(f"Loaded subspace ranks for {len(ranks)} effects")
    return ranks

def prepare_bayesian_dataset() -> pd.DataFrame:
    """
    Prepare the dataset for Bayesian analysis.
    1. Load results.csv
    2. Aggregate by effect to compute mean bleeding per effect
    3. Join with subspace_ranks.json
    4. Validate subspace_rank column
    
    Returns:
        pd.DataFrame: Aggregated dataset with columns: effect_id, mean_bleeding, quantization_level, subspace_rank
    """
    logger.info("Preparing Bayesian dataset...")
    
    # Load results data
    df = load_results_data()
    
    # Validate required columns
    required_cols = ['effect', 'cesr_score', 'quantization_level']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in results.csv: {missing_cols}")
    
    # Check for subspace_rank column - if missing, try to derive it from subspace_ranks.json
    if 'subspace_rank' not in df.columns:
        logger.info("subspace_rank column not found in results.csv, attempting to join from subspace_ranks.json")
        ranks = load_subspace_ranks()
        
        # Create a DataFrame from subspace_ranks
        ranks_df = pd.DataFrame(list(ranks.items()), columns=['effect', 'subspace_rank'])
        
        # Merge with results
        df = df.merge(ranks_df, on='effect', how='left')
        
        # Save the updated results
        results_path = get_project_root() / "data" / "results.csv"
        df.to_csv(results_path, index=False)
        logger.info(f"Updated {results_path} with subspace_rank column")
    
    # Validate subspace_rank column
    if 'subspace_rank' not in df.columns:
        raise ValueError("Data Integrity Error: Subspace Ranks Missing - subspace_rank column not found in results.csv")
    
    # Check for non-null, positive integer values
    if df['subspace_rank'].isnull().any():
        null_count = df['subspace_rank'].isnull().sum()
        raise ValueError(f"Data Integrity Error: Subspace Ranks Missing - {null_count} rows have null subspace_rank values")
    
    if not (df['subspace_rank'] > 0).all():
        invalid_count = (df['subspace_rank'] <= 0).sum()
        raise ValueError(f"Data Integrity Error: Subspace Ranks Missing - {invalid_count} rows have non-positive subspace_rank values")
    
    logger.info("Subspace rank validation passed")
    
    # Aggregate by effect to compute mean bleeding
    aggregated = df.groupby(['effect', 'quantization_level']).agg({
        'cesr_score': 'mean',
        'subspace_rank': 'first'  # Take the first (should be same for all rows of same effect)
    }).reset_index()
    
    aggregated.columns = ['effect', 'quantization_level', 'mean_bleeding', 'subspace_rank']
    
    # Save aggregated dataset
    agg_path = get_project_root() / "data" / "aggregated_bleeding.csv"
    aggregated.to_csv(agg_path, index=False)
    logger.info(f"Saved aggregated dataset to {agg_path}")
    
    return aggregated

def aggregate_cesr_to_effect_level(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate CESR scores to effect level.
    
    Args:
        df: DataFrame with cesr_score and effect columns
        
    Returns:
        pd.DataFrame: Aggregated data with mean cesr_score per effect
    """
    aggregated = df.groupby('effect').agg({
        'cesr_score': 'mean',
        'subspace_rank': 'first'
    }).reset_index()
    aggregated.columns = ['effect', 'mean_cesr', 'subspace_rank']
    return aggregated

def run_bayesian_hierarchical_model(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Run the Bayesian Hierarchical Model using pymc/bambi.
    
    Args:
        data: DataFrame with columns: effect, mean_bleeding, quantization_level, subspace_rank
        
    Returns:
        Dict[str, Any]: Posterior samples and statistics
    """
    logger.info("Running Bayesian Hierarchical Model...")
    
    try:
        import pymc as pm
        import bambi as bmb
    except ImportError:
        logger.warning("pymc or bambi not installed, skipping Bayesian analysis")
        return {
            'status': 'skipped',
            'reason': 'pymc or bambi not installed'
        }
    
    # Prepare the model
    # Model formula: similarity_score ~ quantization_level + (1 | effect_id)
    # We use mean_bleeding as the dependent variable
    
    # Convert quantization_level to categorical for proper handling
    data['quantization_level'] = data['quantization_level'].astype('category')
    
    # Define the model
    model = bmb.Model(
        'mean_bleeding ~ quantization_level + (1 | effect)',
        data,
        family='gaussian'
    )
    
    # Fit the model
    logger.info("Fitting model...")
    try:
        fit = model.fit(draws=1000, tune=1000, chains=2, random_seed=42)
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        return {
            'status': 'failed',
            'reason': str(e)
        }
    
    # Extract posterior samples
    posterior = fit.posterior
    
    # Calculate statistics
    quantization_effect = posterior['beta_quantization_level']
    if isinstance(quantization_effect, xr.DataArray):
        posterior_mean = float(quantization_effect.mean().values)
        hdi = pm.hdi(quantization_effect, hdi_prob=0.94)
        credible_interval = [float(hdi.min().values), float(hdi.max().values)]
        posterior_width = float(hdi.max().values - hdi.min().values)
    else:
        # Fallback if structure is different
        posterior_mean = float(np.mean(quantization_effect))
        credible_interval = [float(np.percentile(quantization_effect, 2.5)), float(np.percentile(quantization_effect, 97.5))]
        posterior_width = credible_interval[1] - credible_interval[0]
    
    # Calculate ESS
    ess = pm.ess(quantization_effect).mean().values
    ess = float(ess) if not np.isnan(ess) else 0.0
    
    return {
        'status': 'success',
        'posterior_mean': posterior_mean,
        'credible_interval': credible_interval,
        'posterior_width': posterior_width,
        'ess': ess,
        'model_fit': fit
    }

def compute_hdi_width(posterior_samples: np.ndarray, hdi_prob: float = 0.94) -> float:
    """
    Compute the HDI width for posterior samples.
    
    Args:
        posterior_samples: Array of posterior samples
        hdi_prob: Probability mass for HDI (default 0.94)
        
    Returns:
        float: Width of the HDI
    """
    try:
        import pymc as pm
        hdi = pm.hdi(posterior_samples, hdi_prob=hdi_prob)
        return float(hdi.max() - hdi.min())
    except ImportError:
        # Fallback to simple percentile-based CI
        lower = np.percentile(posterior_samples, (1 - hdi_prob) / 2 * 100)
        upper = np.percentile(posterior_samples, (1 + hdi_prob) / 2 * 100)
        return float(upper - lower)

def compute_ess(posterior_samples: np.ndarray) -> float:
    """
    Compute the Effective Sample Size (ESS) for posterior samples.
    
    Args:
        posterior_samples: Array of posterior samples
        
    Returns:
        float: ESS value
    """
    try:
        import pymc as pm
        ess = pm.ess(posterior_samples)
        return float(ess) if not np.isnan(ess) else 0.0
    except ImportError:
        # Fallback: approximate ESS using autocorrelation
        n = len(posterior_samples)
        if n < 2:
            return 1.0
        
        # Calculate autocorrelation
        mean = np.mean(posterior_samples)
        var = np.var(posterior_samples)
        if var == 0:
            return float(n)
        
        autocorr = np.correlate(posterior_samples - mean, posterior_samples - mean, mode='full') / var / n
        autocorr = autocorr[n-1:]  # Take positive lags
        
        # Calculate integrated autocorrelation time
        tau = 1 + 2 * np.sum(autocorr[1:])
        if tau <= 0:
            return float(n)
        
        ess = n / tau
        return float(ess)

def analyze_posterior_stability(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze posterior stability and power.
    
    Args:
        results: Dictionary containing posterior statistics
        
    Returns:
        Dict[str, Any]: Stability flags and diagnostics
    """
    underpowered = False
    unstable_posterior = False
    
    if 'posterior_width' in results:
        if results['posterior_width'] > 0.2:
            underpowered = True
    
    if 'ess' in results:
        if results['ess'] < 200:
            unstable_posterior = True
    
    return {
        'underpowered': underpowered,
        'unstable_posterior': unstable_posterior
    }

def compute_correlation_stats(data: pd.DataFrame) -> Dict[str, float]:
    """
    Compute correlation between subspace rank and mean bleeding.
    
    Args:
        data: DataFrame with columns: mean_bleeding, subspace_rank
        
    Returns:
        Dict[str, float]: Correlation coefficient and credible interval
    """
    logger.info("Computing correlation between subspace rank and mean bleeding...")
    
    if len(data) < 2:
        logger.warning("Not enough data points for correlation analysis")
        return {
            'correlation_coefficient': 0.0,
            'correlation_ci': [0.0, 0.0]
        }
    
    # Calculate Pearson correlation
    corr_matrix = data[['mean_bleeding', 'subspace_rank']].corr()
    corr_coef = corr_matrix.loc['mean_bleeding', 'subspace_rank']
    
    # Bootstrap for credible interval
    n_bootstrap = 1000
    boot_corrs = []
    
    for _ in range(n_bootstrap):
        sample = data.sample(n=len(data), replace=True)
        if len(sample) < 2:
            continue
        corr = sample[['mean_bleeding', 'subspace_rank']].corr().loc['mean_bleeding', 'subspace_rank']
        if not np.isnan(corr):
            boot_corrs.append(corr)
    
    if len(boot_corrs) > 1:
        ci_lower = np.percentile(boot_corrs, 2.5)
        ci_upper = np.percentile(boot_corrs, 97.5)
    else:
        ci_lower = ci_upper = corr_coef
    
    return {
        'correlation_coefficient': float(corr_coef),
        'correlation_ci': [float(ci_lower), float(ci_upper)]
    }

def save_analysis_results(results: Dict[str, Any]) -> None:
    """
    Save analysis results to JSON file.
    
    Args:
        results: Dictionary containing all analysis results
    """
    output_path = get_project_root() / "data" / "analysis_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved analysis results to {output_path}")

def main():
    """Main entry point for statistical analysis."""
    try:
        # Prepare dataset with validation
        data = prepare_bayesian_dataset()
        
        # Run Bayesian model
        model_results = run_bayesian_hierarchical_model(data)
        
        if model_results.get('status') != 'success':
            logger.warning(f"Bayesian model failed: {model_results.get('reason')}")
            # Create minimal results structure
            analysis_results = {
                'posterior_mean': 0.0,
                'credible_interval': [0.0, 0.0],
                'correlation_coefficient': 0.0,
                'correlation_ci': [0.0, 0.0],
                'underpowered': True,
                'unstable_posterior': True,
                'posterior_width': 0.0,
                'status': model_results.get('status', 'unknown'),
                'reason': model_results.get('reason', 'Unknown error')
            }
        else:
            # Analyze posterior stability
            stability = analyze_posterior_stability(model_results)
            
            # Compute correlation
            corr_stats = compute_correlation_stats(data)
            
            # Combine results
            analysis_results = {
                'posterior_mean': model_results['posterior_mean'],
                'credible_interval': model_results['credible_interval'],
                'correlation_coefficient': corr_stats['correlation_coefficient'],
                'correlation_ci': corr_stats['correlation_ci'],
                'underpowered': stability['underpowered'],
                'unstable_posterior': stability['unstable_posterior'],
                'posterior_width': model_results['posterior_width']
            }
        
        # Save results
        save_analysis_results(analysis_results)
        
        logger.info("Statistical analysis completed successfully")
        return analysis_results
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()