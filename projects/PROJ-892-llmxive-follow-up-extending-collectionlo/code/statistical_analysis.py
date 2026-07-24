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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_results_data(results_path: str = "data/results.csv") -> pd.DataFrame:
    """
    Load the results CSV and structure data for Bayesian Hierarchical Model.
    The data is expected to have columns:
    - 'prompt': The effect prompt name
    - 'quantization_level': FP16, INT8, INT4
    - 'seed': Random seed
    - 'cosine_similarity': Metric value
    - 'cesr_score': Concept bleeding metric
    """
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Results file not found at {results_path}. Run generation pipeline first.")
    
    df = pd.read_csv(results_path)
    
    # Ensure categorical types for hierarchical grouping
    df['prompt'] = df['prompt'].astype('category')
    df['quantization_level'] = df['quantization_level'].astype('category')
    
    logger.info(f"Loaded {len(df)} records from {results_path}")
    return df

def load_subspace_ranks(ranks_path: str = "data/subspace_ranks.json") -> Dict[str, Any]:
    """Load per-effect LoRA subspace ranks."""
    if not os.path.exists(ranks_path):
        raise FileNotFoundError(f"Subspace ranks file not found at {ranks_path}. Run SVD analysis first.")
    
    with open(ranks_path, 'r') as f:
        return json.load(f)

def prepare_correlation_data(results_df: pd.DataFrame, ranks_dict: Dict[str, Any]) -> pd.DataFrame:
    """
    Prepare data for correlation analysis between subspace rank and concept bleeding.
    Aggregates mean CESR per effect and merges with subspace rank.
    """
    # Calculate mean CESR per prompt
    cesr_by_prompt = results_df.groupby('prompt')['cesr_score'].mean().reset_index()
    cesr_by_prompt.columns = ['prompt', 'mean_cesr']
    
    # Merge with subspace ranks
    # Assuming ranks_dict has structure: { "prompt_name": { "rank": int, ... } }
    merged_data = []
    for prompt in cesr_by_prompt['prompt']:
        if prompt in ranks_dict:
            rank = ranks_dict[prompt].get('rank', 0)
            merged_data.append({
                'prompt': prompt,
                'mean_cesr': cesr_by_prompt[cesr_by_prompt['prompt'] == prompt]['mean_cesr'].values[0],
                'subspace_rank': rank
            })
    
    df_corr = pd.DataFrame(merged_data)
    if df_corr.empty:
        logger.warning("No overlapping prompts found between results and subspace ranks.")
    else:
        logger.info(f"Prepared {len(df_corr)} data points for correlation analysis.")
    return df_corr

def run_bayesian_hierarchical_model(df: pd.DataFrame, 
                                    target_metric: str = 'cosine_similarity', 
                                    chains: int = 4, 
                                    draws: int = 2000) -> Dict[str, Any]:
    """
    Run the Bayesian Hierarchical Model to test quantization effects.
    
    Model:
    Y_ij ~ Normal(mu_ij, sigma)
    mu_ij = intercept + quantization_effect[j] + prompt_random_effect[i]
    
    Returns:
    Dictionary containing posterior summaries and diagnostics.
    """
    logger.info("Starting Bayesian Hierarchical Model...")
    
    # Encode categorical variables
    prompts = df['prompt'].cat.codes.values
    quant_levels = df['quantization_level'].cat.codes.values
    y = df[target_metric].values
    
    # Number of levels
    n_prompts = len(df['prompt'].cat.categories)
    n_quant = len(df['quantization_level'].cat.categories)
    
    with pm.Model() as model:
        # Priors
        sigma = pm.HalfNormal('sigma', 1.0)
        intercept = pm.Normal('intercept', 0, 1)
        
        # Random effects for prompts (partial pooling)
        prompt_sigma = pm.HalfNormal('prompt_sigma', 1.0)
        prompt_effect = pm.Normal('prompt_effect', 0, prompt_sigma, shape=n_prompts)
        
        # Fixed effects for quantization (relative to baseline, usually FP16)
        # We use n_quant - 1 because one level is the reference
        quant_effect = pm.Normal('quant_effect', 0, 1, shape=n_quant - 1)
        
        # Linear predictor
        mu = intercept + prompt_effect[prompts]
        
        # Add quantization effects (skipping the first level as reference)
        # Assuming quant_levels are ordered such that 0 is FP16 (reference)
        # If quant_levels has more than 2 levels, we map accordingly
        quant_indices = quant_levels - 1 
        # Mask out the reference level (0 -> -1, which we handle by not adding)
        mu = mu + pm.math.switch(quant_indices >= 0, quant_effect[quant_indices], 0)
        
        # Likelihood
        obs = pm.Normal('obs', mu, sigma, observed=y)
        
        # Sample
        logger.info("Sampling...")
        trace = pm.sample(draws=draws, chains=chains, tune=1000, return_inferencedata=True, random_seed=42)
    
    # Post-processing
    logger.info("Analyzing posterior...")
    summary = az.summary(trace, var_names=['intercept', 'quant_effect', 'prompt_sigma', 'sigma'])
    
    # Extract specific effect estimates
    # Assuming quant_effect[0] is INT8, quant_effect[1] is INT4 (relative to FP16)
    # This depends on the ordering of categories in pandas
    quant_categories = df['quantization_level'].cat.categories.tolist()
    logger.info(f"Quantization levels: {quant_categories}")
    
    results = {
        "trace_path": None, # Could save trace if needed
        "summary": summary.to_dict(),
        "model_info": {
            "n_prompts": n_prompts,
            "n_observations": len(df),
            "target_metric": target_metric
        },
        "posterior_means": {},
        "credible_intervals": {}
    }
    
    # Extract quantization effects
    if 'quant_effect' in summary.index:
        for i, effect_name in enumerate(quant_categories[1:]): # Skip reference
            mean = summary.loc[f'quant_effect[{i}]', 'mean']
            hdi = summary.loc[f'quant_effect[{i}]', 'hdi_3%'] # Using 3% for 94% HDI or similar
            # ArviZ uses hdi_3% and hdi_97% for 94% HDI by default, or we can use hdi_2.5% for 95%
            # Let's compute 95% HDI explicitly if needed, but summary usually has hdi_3% (94%)
            # For strict 95%, we might need az.hdi(trace.posterior['quant_effect'])
            pass 
    
    # Compute 95% HDI for quant effects manually for clarity
    quant_effects = trace.posterior['quant_effect'].values # (chains, draws, n_quant-1)
    quant_effects_flat = quant_effects.reshape(-1, quant_effects.shape[-1])
    
    for i, effect_name in enumerate(quant_categories[1:]):
        data = quant_effects_flat[:, i]
        mean = np.mean(data)
        # 95% HDI
        hdi_low = np.percentile(data, 2.5)
        hdi_high = np.percentile(data, 97.5)
        
        results["posterior_means"][effect_name] = mean
        results["credible_intervals"][effect_name] = {
            "hdi_95": [hdi_low, hdi_high],
            "width": hdi_high - hdi_low
        }
        
        # Flag if underpowered (width > 0.2)
        if (hdi_high - hdi_low) > 0.2:
            logger.warning(f"Effect {effect_name} is underpowered (HDI width > 0.2)")
            results["underpowered_effects"] = results.get("underpowered_effects", [])
            results["underpowered_effects"].append(effect_name)

    return results

def main():
    """Main entry point for statistical analysis."""
    logger.info("Starting Statistical Analysis Pipeline")
    
    try:
        # 1. Load Data
        df = load_results_data("data/results.csv")
        ranks = load_subspace_ranks("data/subspace_ranks.json")
        
        # 2. Run BHM
        bhm_results = run_bayesian_hierarchical_model(df, target_metric='cosine_similarity')
        
        # 3. Correlation Analysis
        corr_data = prepare_correlation_data(df, ranks)
        if not corr_data.empty:
            # Simple Bayesian correlation for rank vs CESR
            with pm.Model() as corr_model:
                rho = pm.Uniform('rho', -1, 1)
                sigma_corr = pm.HalfNormal('sigma_corr', 1)
                mu_corr = rho * (corr_data['subspace_rank'].values - corr_data['subspace_rank'].values.mean()) / corr_data['subspace_rank'].values.std()
                # Simplified linear model for demonstration
                obs_corr = pm.Normal('obs_corr', mu_corr, sigma_corr, observed=corr_data['mean_cesr'].values)
                trace_corr = pm.sample(draws=1000, chains=2, tune=500, random_seed=42)
            
            rho_summary = az.summary(trace_corr, var_names=['rho'])
            bhm_results['correlation'] = rho_summary.to_dict()
        else:
            bhm_results['correlation'] = None
        
        # 4. Save Results
        output_path = "data/analysis_results.json"
        # Convert non-serializable types (numpy arrays, etc)
        serializable_results = json.loads(json.dumps(bhm_results, default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else str(x)))
        
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"Analysis complete. Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()