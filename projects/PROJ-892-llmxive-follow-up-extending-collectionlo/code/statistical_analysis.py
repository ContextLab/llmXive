import os
import json
import logging
import pandas as pd
import numpy as np
import pymc as pm
import arviz as az
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_results_data(results_path: str = "data/results.csv") -> pd.DataFrame:
    """
    Load the results CSV containing generation metrics and quantization levels.
    
    Args:
        results_path: Path to the results CSV file.
        
    Returns:
        DataFrame with columns: prompt, effect, quantization_level, cosine_similarity, lpips_distance, cesr_score
    """
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Results file not found at {results_path}. "
                              "Ensure Phase 3 and Phase 4 have completed generation.")
    
    df = pd.read_csv(results_path)
    logger.info(f"Loaded {len(df)} rows from {results_path}")
    return df

def load_subspace_ranks(ranks_path: str = "data/subspace_ranks.json") -> Dict[str, float]:
    """
    Load per-effect LoRA subspace ranks.
    
    Args:
        ranks_path: Path to the subspace ranks JSON file.
        
    Returns:
        Dictionary mapping effect names to their subspace ranks.
    """
    if not os.path.exists(ranks_path):
        raise FileNotFoundError(f"Subspace ranks file not found at {ranks_path}. "
                              "Ensure T009 has completed SVD analysis.")
    
    with open(ranks_path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded subspace ranks for {len(data)} effects")
    return data

def prepare_correlation_data(results_df: pd.DataFrame, subspace_ranks: Dict[str, float]) -> pd.DataFrame:
    """
    Prepare data for correlation analysis between subspace rank and concept bleeding.
    
    Concept bleeding is measured by the mean CESR score per effect.
    
    Args:
        results_df: DataFrame with generation results.
        subspace_ranks: Dictionary of effect -> subspace rank.
        
    Returns:
        DataFrame with columns: effect, subspace_rank, mean_cesr, n_observations
    """
    # Calculate mean CESR per effect (aggregating across quantization levels and prompts)
    cesr_by_effect = results_df.groupby('effect')['cesr_score'].mean().reset_index()
    cesr_by_effect.columns = ['effect', 'mean_cesr']
    
    # Merge with subspace ranks
    merged = cesr_by_effect.merge(
        pd.DataFrame(list(subspace_ranks.items()), columns=['effect', 'subspace_rank']),
        on='effect',
        how='inner'
    )
    
    # Count observations per effect
    obs_counts = results_df.groupby('effect').size().reset_index(name='n_observations')
    merged = merged.merge(obs_counts, on='effect', how='left')
    
    logger.info(f"Prepared correlation data for {len(merged)} effects")
    return merged

def run_bayesian_hierarchical_model(
    results_df: pd.DataFrame,
    posterior_width_threshold: float = 0.2
) -> Dict[str, Any]:
    """
    Run the Bayesian Hierarchical Model and perform posterior width analysis.
    
    This model estimates quantization effects on concept adherence and bleeding,
    with hierarchical structure to handle limited sample sizes (N=10 effects).
    
    Args:
        results_df: DataFrame with generation results.
        posterior_width_threshold: Threshold for flagging underpowered results.
            If credible interval width > threshold, result is flagged as "Underpowered".
            
    Returns:
        Dictionary containing:
            - model_summary: Summary statistics from ArviZ
            - posterior_widths: Dict of parameter -> credible interval width
            - underpowered_params: List of parameters flagged as underpowered
            - correlation_analysis: Results from subspace rank correlation
            - power_assessment: Overall power assessment string
    """
    logger.info("Starting Bayesian Hierarchical Model analysis...")
    
    # Prepare data for BHM
    # We model cosine_similarity as outcome, with quantization_level as fixed effect
    # and effect as random effect to account for effect-specific baselines
    
    # Convert quantization level to numeric (FP16=0, INT8=1, INT4=2)
    quantization_map = {'FP16': 0, 'INT8': 1, 'INT4': 2}
    results_df['quant_level_numeric'] = results_df['quantization_level'].map(quantization_map)
    
    # Remove rows with missing quantization level mapping
    results_df = results_df.dropna(subset=['quant_level_numeric'])
    
    if len(results_df) < 10:
        logger.warning(f"Only {len(results_df)} observations available. "
                     "Model may be severely underpowered.")
    
    # Prepare data for PyMC
    data_dict = {
        'cosine_similarity': results_df['cosine_similarity'].values,
        'quant_level': results_df['quant_level_numeric'].values.astype(int),
        'effect_idx': pd.Categorical(results_df['effect']).codes,
        'n_effects': len(pd.Categorical(results_df['effect']).categories)
    }
    
    logger.info(f"Running BHM with {len(data_dict['cosine_similarity'])} observations "
               f"across {data_dict['n_effects']} effects")
    
    # Define and run the hierarchical model
    with pm.Model() as model:
        # Priors for fixed effects (quantization impact)
        quantization_effect = pm.Normal('quantization_effect', mu=0, sigma=1, shape=3)
        
        # Priors for random effects (effect-specific baselines)
        effect_mu = pm.Normal('effect_mu', mu=0, sigma=1)
        effect_sigma = pm.HalfNormal('effect_sigma', sigma=1)
        effect_offsets = pm.Normal('effect_offsets', mu=0, sigma=1, shape=data_dict['n_effects'])
        effect_rv = pm.Deterministic('effect_rv', effect_mu + effect_sigma * effect_offsets)
        
        # Expected value
        mu = (
            pm.math.take(quantization_effect, data_dict['quant_level']) +
            pm.math.take(effect_rv, data_dict['effect_idx'])
        )
        
        # Likelihood
        sigma = pm.HalfNormal('sigma', sigma=1)
        y_obs = pm.Normal('y_obs', mu=mu, sigma=sigma, observed=data_dict['cosine_similarity'])
        
        # Sample
        logger.info("Sampling from posterior...")
        trace = pm.sample(
            draws=2000,
            tune=1000,
            chains=4,
            target_accept=0.95,
            return_inferencedata=True,
            progressbar=True
        )
    
    logger.info("Model sampling complete. Computing posterior width analysis...")
    
    # Compute summary statistics
    summary = az.summary(trace)
    
    # Calculate credible interval widths for key parameters
    posterior_widths = {}
    underpowered_params = []
    
    # Check quantization effect parameters
    for i, level_name in enumerate(['FP16', 'INT8', 'INT4']):
        param_name = f'quantization_effect[{i}]'
        if param_name in summary.index:
            ci_low = summary.loc[param_name, 'hdi_3%']
            ci_high = summary.loc[param_name, 'hdi_97%']
            width = ci_high - ci_low
            posterior_widths[param_name] = width
            
            if width > posterior_width_threshold:
                underpowered_params.append(param_name)
                logger.warning(f"Parameter '{param_name}' has CI width {width:.3f} > {posterior_width_threshold} "
                             "(Underpowered)")
    
    # Check effect_sigma (variability across effects)
    if 'effect_sigma' in summary.index:
        param_name = 'effect_sigma'
        ci_low = summary.loc[param_name, 'hdi_3%']
        ci_high = summary.loc[param_name, 'hdi_97%']
        width = ci_high - ci_low
        posterior_widths[param_name] = width
        
        if width > posterior_width_threshold:
            underpowered_params.append(param_name)
            logger.warning(f"Parameter '{param_name}' has CI width {width:.3f} > {posterior_width_threshold} "
                         "(Underpowered)")
    
    # Determine overall power assessment
    if len(underpowered_params) > 0:
        power_assessment = "Underpowered"
        logger.warning(f"Analysis flagged as UNDERPOWERED: {len(underpowered_params)} parameters "
                     f"have CI width > {posterior_width_threshold}")
    else:
        power_assessment = "Adequately Powered"
        logger.info("Analysis passes power threshold: all key parameters have CI width <= "
                   f"{posterior_width_threshold}")
    
    # Perform correlation analysis between subspace rank and concept bleeding
    # Load subspace ranks and compute correlation
    try:
        subspace_ranks = load_subspace_ranks()
        correlation_data = prepare_correlation_data(results_df, subspace_ranks)
        
        if len(correlation_data) > 2:
            # Compute Pearson correlation and its uncertainty via bootstrap
            n_bootstrap = 1000
            bootstrap_corrs = []
            
            for _ in range(n_bootstrap):
                sample = correlation_data.sample(n=len(correlation_data), replace=True)
                corr, _ = np.corrcoef(sample['subspace_rank'], sample['mean_cesr'])
                bootstrap_corrs.append(corr)
            
            corr_mean = np.mean(bootstrap_corrs)
            corr_ci_low = np.percentile(bootstrap_corrs, 3)
            corr_ci_high = np.percentile(bootstrap_corrs, 97)
            corr_ci_width = corr_ci_high - corr_ci_low
            
            correlation_results = {
                'correlation_coefficient': corr_mean,
                'credible_interval': [corr_ci_low, corr_ci_high],
                'ci_width': corr_ci_width,
                'n_effects': len(correlation_data),
                'is_significant': 0 not in [corr_ci_low, corr_ci_high],
                'underpowered': corr_ci_width > posterior_width_threshold
            }
            
            if corr_ci_width > posterior_width_threshold:
                logger.warning(f"Correlation analysis is underpowered (CI width: {corr_ci_width:.3f})")
        else:
            correlation_results = {
                'error': 'Insufficient data for correlation analysis',
                'n_effects': len(correlation_data)
            }
            
    except FileNotFoundError as e:
        logger.warning(f"Could not perform correlation analysis: {e}")
        correlation_results = {'error': str(e)}
    
    # Prepare final results
    results = {
        'model_summary': summary.to_dict(),
        'posterior_widths': posterior_widths,
        'underpowered_params': underpowered_params,
        'power_assessment': power_assessment,
        'posterior_width_threshold': posterior_width_threshold,
        'correlation_analysis': correlation_results,
        'n_observations': len(results_df),
        'n_effects': data_dict['n_effects']
    }
    
    logger.info(f"BHM analysis complete. Power assessment: {power_assessment}")
    return results

def main():
    """
    Main entry point for statistical analysis.
    
    This function:
    1. Loads results from data/results.csv
    2. Runs the Bayesian Hierarchical Model
    3. Performs posterior width analysis
    4. Flags underpowered results (CI width > 0.2)
    5. Saves results to data/analysis_results.json
    """
    logger.info("Starting statistical analysis pipeline...")
    
    # Load data
    try:
        results_df = load_results_data()
    except FileNotFoundError as e:
        logger.error(f"Failed to load results: {e}")
        return 1
    
    # Run BHM with posterior width analysis
    try:
        analysis_results = run_bayesian_hierarchical_model(
            results_df,
            posterior_width_threshold=0.2
        )
    except Exception as e:
        logger.error(f"Failed to run BHM: {e}")
        return 1
    
    # Save results
    output_path = "data/analysis_results.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert numpy types for JSON serialization
    def convert_numpy(obj):
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(i) for i in obj]
        return obj
    
    serializable_results = convert_numpy(analysis_results)
    
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"Analysis results saved to {output_path}")
    
    # Print power assessment summary
    power_status = analysis_results['power_assessment']
    threshold = analysis_results['posterior_width_threshold']
    underpowered = analysis_results['underpowered_params']
    
    print("\n" + "="*60)
    print("POSTERIOR WIDTH ANALYSIS SUMMARY")
    print("="*60)
    print(f"Power Assessment: {power_status}")
    print(f"CI Width Threshold: {threshold}")
    
    if underpowered:
        print(f"\n⚠️  UNDERPOWERED PARAMETERS ({len(underpowered)}):")
        for param in underpowered:
            width = analysis_results['posterior_widths'].get(param, 'N/A')
            print(f"  - {param}: CI width = {width:.4f} > {threshold}")
    else:
        print("\n✓ All key parameters have credible interval widths within threshold.")
    
    if 'correlation_analysis' in analysis_results and 'correlation_coefficient' in analysis_results['correlation_analysis']:
        corr = analysis_results['correlation_analysis']
        print(f"\nSubspace Rank vs. Concept Bleeding Correlation:")
        print(f"  Coefficient: {corr['correlation_coefficient']:.3f}")
        print(f"  95% CI: [{corr['credible_interval'][0]:.3f}, {corr['credible_interval'][1]:.3f}]")
        print(f"  Significant: {'Yes' if corr['is_significant'] else 'No'}")
        if corr.get('underpowered'):
            print(f"  ⚠️  Correlation analysis is underpowered (CI width > {threshold})")
    
    print("="*60 + "\n")
    
    return 0

if __name__ == '__main__':
    exit(main())