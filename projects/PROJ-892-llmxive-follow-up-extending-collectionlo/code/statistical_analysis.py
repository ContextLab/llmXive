import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import pymc as pm
import arviz as az
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
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

def load_results_data() -> pd.DataFrame:
    """Load the results CSV file."""
    project_root = get_project_root()
    results_path = project_root / "data" / "results.csv"
    
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found at {results_path}")
    
    df = pd.read_csv(results_path)
    logger.info(f"Loaded {len(df)} rows from results.csv")
    return df

def load_subspace_ranks() -> Dict[str, int]:
    """Load subspace ranks from JSON file."""
    project_root = get_project_root()
    ranks_path = project_root / "data" / "subspace_ranks.json"
    
    if not ranks_path.exists():
        raise FileNotFoundError(f"Subspace ranks file not found at {ranks_path}")
    
    with open(ranks_path, 'r') as f:
        ranks = json.load(f)
    
    logger.info(f"Loaded subspace ranks for {len(ranks)} effects")
    return ranks

def prepare_correlation_data(df: pd.DataFrame, ranks: Dict[str, int]) -> pd.DataFrame:
    """Prepare data for correlation analysis by aggregating by effect."""
    # Validate required columns
    required_cols = ['effect', 'similarity_score', 'quantization_level']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Validate subspace_rank column exists and is valid
    if 'subspace_rank' not in df.columns:
        # Try to add it from ranks dict
        df = df.copy()
        df['subspace_rank'] = df['effect'].map(ranks)
        if df['subspace_rank'].isnull().any():
            raise ValueError("Data Integrity Error: Subspace Ranks Missing")
    
    # Check for valid positive integers
    if not all(df['subspace_rank'].dropna() > 0):
        raise ValueError("Data Integrity Error: Invalid Subspace Rank values")
    
    # Aggregate by effect and quantization level
    aggregated = df.groupby(['effect', 'quantization_level']).agg({
        'similarity_score': 'mean',
        'cesr_score': 'mean',
        'subspace_rank': 'first'
    }).reset_index()
    
    aggregated.rename(columns={'effect': 'effect_id'}, inplace=True)
    logger.info(f"Prepared {len(aggregated)} aggregated rows for analysis")
    return aggregated

def aggregate_cesr_to_effect_level(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate CESR scores to effect level."""
    if 'cesr_score' not in df.columns:
        raise ValueError("Missing cesr_score column")
    
    aggregated = df.groupby('effect').agg({
        'cesr_score': 'mean',
        'subspace_rank': 'first'
    }).reset_index()
    
    aggregated.rename(columns={'effect': 'effect_id'}, inplace=True)
    return aggregated

def run_bayesian_hierarchical_model(df: pd.DataFrame) -> Dict[str, Any]:
    """Run the Bayesian Hierarchical Model."""
    logger.info("Running Bayesian Hierarchical Model...")
    
    # Prepare data
    df = df.copy()
    df['quantization_level'] = df['quantization_level'].astype('category')
    df['effect_id'] = df['effect_id'].astype('category')
    
    # Convert to numeric for model
    quant_levels = df['quantization_level'].cat.codes.values
    effect_ids = df['effect_id'].cat.codes.values
    scores = df['similarity_score'].values
    
    n_effects = df['effect_id'].nunique()
    n_levels = df['quantization_level'].nunique()
    
    logger.info(f"Model: {len(df)} observations, {n_effects} effects, {n_levels} quantization levels")
    
    with pm.Model() as model:
        # Priors
        mu = pm.Normal('mu', mu=0, sigma=10)
        quant_effects = pm.Normal('quantization_effects', mu=0, sigma=5, shape=n_levels)
        effect_random = pm.Normal('effect_random', mu=0, sigma=5, shape=n_effects)
        sigma = pm.HalfNormal('sigma', sigma=1)
        
        # Expected value
        mu_expected = mu + quant_effects[quant_levels] + effect_random[effect_ids]
        
        # Likelihood
        likelihood = pm.Normal('y', mu=mu_expected, sigma=sigma, observed=scores)
        
        # Sample
        logger.info("Sampling...")
        trace = pm.sample(
            draws=2000,
            tune=1000,
            chains=4,
            target_accept=0.9,
            return_inferencedata=True,
            random_seed=42
        )
    
    logger.info("Model sampling complete")
    return {
        'trace': trace,
        'model': model
    }

def compute_correlation_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute correlation between subspace rank and concept bleeding."""
    if 'subspace_rank' not in df.columns or 'cesr_score' not in df.columns:
        raise ValueError("Missing required columns for correlation")
    
    # Remove NaN values
    valid_data = df.dropna(subset=['subspace_rank', 'cesr_score'])
    
    if len(valid_data) < 2:
        logger.warning("Insufficient data for correlation analysis")
        return {
            'correlation_coefficient': np.nan,
            'correlation_ci': [np.nan, np.nan],
            'p_value': np.nan
        }
    
    # Compute Pearson correlation
    corr, p_value = np.corrcoef(
        valid_data['subspace_rank'].values,
        valid_data['cesr_score'].values
    )
    
    # Bootstrap for confidence interval
    n_bootstrap = 1000
    boot_corrs = []
    rng = np.random.default_rng(42)
    
    for _ in range(n_bootstrap):
        sample_idx = rng.choice(len(valid_data), size=len(valid_data), replace=True)
        sample = valid_data.iloc[sample_idx]
        corr_sample, _ = np.corrcoef(
            sample['subspace_rank'].values,
            sample['cesr_score'].values
        )
        boot_corrs.append(corr_sample)
    
    ci_lower = np.percentile(boot_corrs, 2.5)
    ci_upper = np.percentile(boot_corrs, 97.5)
    
    return {
        'correlation_coefficient': float(corr),
        'correlation_ci': [float(ci_lower), float(ci_upper)],
        'p_value': float(p_value),
        'n_samples': len(valid_data)
    }

def compute_hdi_width(trace: az.InferenceData, var_name: str = 'quantization_effects') -> Tuple[float, float]:
    """Compute HDI width for a variable."""
    try:
        hdi = az.hdi(trace, hdi_prob=0.94)
        if var_name in hdi:
            var_hdi = hdi[var_name]
            # For array variables, take the mean width across dimensions
            if isinstance(var_hdi, pd.DataFrame):
                widths = var_hdi['hdi_94%'].max(axis=1) - var_hdi['hdi_94%'].min(axis=1)
                avg_width = widths.mean()
                max_width = widths.max()
            else:
                avg_width = var_hdi.max() - var_hdi.min()
                max_width = avg_width
            return float(avg_width), float(max_width)
        else:
            logger.warning(f"Variable {var_name} not found in trace")
            return np.nan, np.nan
    except Exception as e:
        logger.error(f"Error computing HDI: {e}")
        return np.nan, np.nan

def compute_ess(trace: az.InferenceData, var_name: str) -> float:
    """Compute Effective Sample Size for a variable."""
    try:
        ess = az.ess(trace, var_names=[var_name])
        if var_name in ess:
            # For array variables, return minimum ESS across dimensions
            if isinstance(ess[var_name], pd.DataFrame):
                return float(ess[var_name].min().min())
            return float(ess[var_name])
        else:
            logger.warning(f"Variable {var_name} not found in ESS calculation")
            return np.nan
    except Exception as e:
        logger.error(f"Error computing ESS: {e}")
        return np.nan

def analyze_posterior_stability(trace: az.InferenceData, quantization_level_map: Dict[str, int]) -> Dict[str, Any]:
    """
    Analyze posterior stability and power for quantization effect.
    
    Decision Rule:
    1. Extract posterior samples for quantization effect coefficient
    2. Calculate HDI width
    3. If width > 0.2, flag as "Underpowered"
    4. Calculate ESS for correlation coefficient
    5. If ESS < 200, flag as "Unstable Posterior"
    6. If either flag is set, result is NOT "Significant"
    """
    logger.info("Analyzing posterior stability...")
    
    # Get the quantization effect variable name (typically 'quantization_effects[0]' for binary)
    # For multi-level, we analyze the variance or specific contrasts
    var_names = list(trace.posterior.data_vars)
    quant_var = None
    for name in var_names:
        if 'quantization' in name.lower():
            quant_var = name
            break
    
    if not quant_var:
        logger.warning("Could not find quantization effect variable in trace")
        return {
            'underpowered': True,
            'unstable_posterior': True,
            'posterior_width': np.nan,
            'ess': np.nan,
            'significant': False,
            'reason': 'Quantization effect variable not found'
        }
    
    # Compute HDI width
    avg_width, max_width = compute_hdi_width(trace, quant_var)
    
    # For multi-level quantization, we check the maximum width across levels
    # or compute a contrast. Here we use the maximum width as the conservative estimate.
    hdi_width = max_width if not np.isnan(max_width) else avg_width
    
    # Compute ESS
    ess = compute_ess(trace, quant_var)
    
    # Determine flags
    underpowered = hdi_width > 0.2 if not np.isnan(hdi_width) else True
    unstable_posterior = ess < 200 if not np.isnan(ess) else True
    
    # Determine significance (only if not underpowered and not unstable)
    significant = False
    if not underpowered and not unstable_posterior:
        # Check if HDI excludes zero
        try:
            hdi = az.hdi(trace, hdi_prob=0.94)
            if quant_var in hdi:
                var_hdi = hdi[quant_var]
                if isinstance(var_hdi, pd.DataFrame):
                    # Check if any level's HDI excludes zero
                    for col in var_hdi.columns:
                        if col.startswith('hdi_94%'):
                            lower = var_hdi[col].min()
                            upper = var_hdi[col].max()
                            if lower > 0 or upper < 0:
                                significant = True
                                break
                else:
                    lower = var_hdi.min()
                    upper = var_hdi.max()
                    if lower > 0 or upper < 0:
                        significant = True
        except Exception as e:
            logger.error(f"Error checking HDI for significance: {e}")
            significant = False
    
    result = {
        'posterior_width': float(hdi_width) if not np.isnan(hdi_width) else None,
        'ess': float(ess) if not np.isnan(ess) else None,
        'underpowered': underpowered,
        'unstable_posterior': unstable_posterior,
        'significant': significant
    }
    
    if underpowered:
        result['reason'] = 'HDI width > 0.2 indicates underpowered analysis'
    elif unstable_posterior:
        result['reason'] = f'ESS ({ess}) < 200 indicates unstable posterior'
    else:
        result['reason'] = 'Posterior is stable and sufficiently powered'
    
    logger.info(f"Posterior analysis: width={hdi_width:.4f}, ess={ess:.1f}, "
               f"underpowered={underpowered}, unstable={unstable_posterior}, "
               f"significant={significant}")
    
    return result

def main():
    """Main entry point for statistical analysis."""
    logger.info("Starting statistical analysis...")
    
    try:
        # Load data
        df = load_results_data()
        ranks = load_subspace_ranks()
        
        # Validate and prepare data
        df = prepare_correlation_data(df, ranks)
        
        # Run Bayesian model
        model_result = run_bayesian_hierarchical_model(df)
        trace = model_result['trace']
        
        # Compute correlation stats
        corr_stats = compute_correlation_stats(df)
        
        # Analyze posterior stability
        # Map quantization levels to indices if needed
        quant_levels = df['quantization_level'].unique()
        quant_level_map = {level: i for i, level in enumerate(quant_levels)}
        
        stability_analysis = analyze_posterior_stability(trace, quant_level_map)
        
        # Compile final results
        # Extract posterior mean for quantization effect (first level for simplicity)
        try:
            posterior_mean = float(trace.posterior['quantization_effects'].mean().values)
            credible_interval = az.hdi(trace, hdi_prob=0.94)['quantization_effects'].values.flatten().tolist()
        except Exception as e:
            logger.error(f"Error extracting posterior stats: {e}")
            posterior_mean = None
            credible_interval = [None, None]
        
        results = {
            'posterior_mean': posterior_mean,
            'credible_interval': credible_interval,
            'correlation_coefficient': corr_stats.get('correlation_coefficient'),
            'correlation_ci': corr_stats.get('correlation_ci'),
            'underpowered': stability_analysis['underpowered'],
            'unstable_posterior': stability_analysis['unstable_posterior'],
            'posterior_width': stability_analysis['posterior_width'],
            'ess': stability_analysis['ess'],
            'significant': stability_analysis['significant'],
            'reason': stability_analysis.get('reason'),
            'n_observations': len(df),
            'n_effects': df['effect_id'].nunique()
        }
        
        # Save results
        project_root = get_project_root()
        output_path = project_root / "data" / "analysis_results.json"
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Analysis results saved to {output_path}")
        logger.info(f"Summary: width={results['posterior_width']}, "
                   f"underpowered={results['underpowered']}, "
                   f"significant={results['significant']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()