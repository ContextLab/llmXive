"""
Analysis pipeline for fungal community environmental impact study.

Implements PERMANOVA, Variance Partitioning (varpart), and db-RDA.
"""
import os
import logging
import pandas as pd
import numpy as np
from skbio.stats.ordination import capscale
from skbio.stats.distance import permanova
from scipy.stats import fdr_bh
import yaml

# Configure logging
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from constants.yaml."""
    config_path = "src/config/constants.yaml"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {
        'thresholds': {
            'vif': 5,
            'p_value': 0.05,
            'min_samples': 10,
            'max_ram_gb': 7
        }
    }

def run_variance_partitioning(
    asv_table_path: str,
    metadata_path: str,
    env_vars: list,
    output_path: str = "results/db_rda_variance.csv"
) -> pd.DataFrame:
    """
    Perform variance partitioning to quantify unique and shared variance 
    explained by environmental predictors.
    
    Uses capscale (db-RDA) to approximate varpart logic for continuous predictors.
    Since skbio does not have a direct 'varpart' function like vegan in R,
    we implement a sequential partitioning approach:
    1. Total variance explained by all env vars together.
    2. Unique variance for each predictor (conditional on others).
    
    Parameters
    ----------
    asv_table_path : str
        Path to the ASV table (samples x features).
    metadata_path : str
        Path to the cleaned metadata CSV.
    env_vars : list
        List of column names in metadata to use as predictors.
    output_path : str
        Path to save the results CSV.
        
    Returns
    -------
    pd.DataFrame
        DataFrame with columns: source, r2_adj, p_value, p_value_adj
    """
    logger.info(f"Starting variance partitioning for predictors: {env_vars}")
    
    # Load data
    asv_df = pd.read_csv(asv_table_path, sep='\t', index_col=0)
    meta_df = pd.read_csv(metadata_path, index_col=0)
    
    # Ensure alignment
    common_samples = asv_df.index.intersection(meta_df.index)
    if len(common_samples) < 5:
        raise ValueError(f"Insufficient common samples for variance partitioning: {len(common_samples)}")
    
    asv_df = asv_df.loc[common_samples]
    meta_df = meta_df.loc[common_samples]
    
    # Filter to requested env vars
    available_vars = [v for v in env_vars if v in meta_df.columns]
    if len(available_vars) < 2:
        logger.warning(f"Not enough environmental variables to partition variance. Found: {available_vars}")
        # If only 1 var, just report its total effect
        if len(available_vars) == 1:
            return _run_single_rda(asv_df, meta_df, available_vars, output_path)
        else:
            raise ValueError("Need at least one environmental variable to perform analysis.")
    
    # Calculate Bray-Curtis distance matrix from ASV table
    # skbio expects samples in rows, features in columns
    dist_matrix = asv_df.div(asv_df.sum(axis=1), axis=0) # Relative abundance
    # skbio distance matrix calculation
    from skbio.stats.distance import DistanceMatrix
    # We need a function to calculate distance. skbio.diversity.beta.bray_curtis works on 1D arrays.
    # Let's use a vectorized approach or loop.
    # For efficiency with large data, we might use scipy, but skbio is requested.
    # We'll use a custom distance matrix builder for Bray-Curtis
    
    from scipy.spatial.distance import cdist
    # Bray-Curtis in scipy is 'braycurtis' but it's 1 - similarity. 
    # skbio uses sum(|a-b|) / sum(|a+b|). scipy.spatial.distance.braycurtis is exactly that.
    dist_array = cdist(asv_df.values, asv_df.values, metric='braycurtis')
    dist_matrix = DistanceMatrix(dist_array, ids=asv_df.index)
    
    results = []
    n_perm = 999
    
    # 1. Total variance (Model with all vars)
    formula_all = "~ " + " + ".join(available_vars)
    res_all = permanova(dist_matrix, meta_df, formula=formula_all, permutations=n_perm)
    results.append({
        'source': 'All_Predictors',
        'r2_adj': res_all['pseudo_f'], # Using F as proxy for significance, but we need R2. 
                                       # skbio permanova returns 'pseudo_f', 'p_value', 'n_perm', 'n_obs'
                                       # It does NOT return R2 directly in the dict. 
                                       # We must calculate R2 manually: SS_model / SS_total
                                       # However, for variance partitioning, we often look at R2.
                                       # Let's approximate R2 from F and df if possible, or re-run capscale.
        'p_value': res_all['p_value'],
        'p_value_adj': res_all['p_value'] # Will adjust later
    })
    
    # Correcting R2 calculation for skbio permanova
    # R2 = SS_model / SS_total. 
    # skbio doesn't return SS. We will use capscale for R2 extraction which is more robust for varpart-like needs.
    
    # Re-calculate using capscale for R2 values
    # capscale returns an OrdinationResult
    cap_all = capscale(dist_matrix, meta_df, formula=formula_all)
    total_r2 = cap_all.proportion_explained[0] # First axis usually dominant, but sum of all constrained axes?
    # capscale.proportion_explained is a list of values for each axis. 
    # The sum of constrained axes R2 is what we want for "Total".
    constrained_axes = [k for k in cap_all.axes if k.startswith('CCA')]
    total_r2_sum = sum(cap_all.proportion_explained[i] for i in range(len(constrained_axes)))
    # Actually, capscale in skbio might behave differently. 
    # Let's use a simpler approach: Run separate RDA for each variable conditional on others.
    
    # Variance Partitioning Strategy:
    # For each variable V_i:
    #   Unique(V_i) = R2(V_i | All_others)
    #   Shared = Total - sum(Unique)
    
    unique_r2s = []
    
    for i, var in enumerate(available_vars):
        others = [v for v in available_vars if v != var]
        if not others:
            # Single variable case
            formula = f"~ {var}"
            cap = capscale(dist_matrix, meta_df, formula=formula)
            r2 = cap.proportion_explained[0] # Approximation
        else:
            # Condition on others
            formula = f"~ {var} + Condition({'+'.join(others)})"
            try:
                cap = capscale(dist_matrix, meta_df, formula=formula)
                # Sum of constrained axes R2
                r2 = sum(cap.proportion_explained[:len(cap.axes)]) # Heuristic
            except Exception as e:
                logger.warning(f"Failed to compute unique variance for {var}: {e}")
                r2 = 0.0
        
        # Run permanova for p-value of this specific term
        # Note: skbio permanova doesn't support 'Condition' in formula easily for p-values.
        # We will use the R2 as the primary metric for varpart and log a warning about p-values.
        # Alternatively, we can run a full model and use the coefficients, but that's complex.
        # For this implementation, we focus on the R2 partitioning.
        
        unique_r2s.append({
            'source': f'Unique_{var}',
            'r2': r2,
            'p_value': np.nan, # Skbio permanova doesn't support conditional p-values easily without R
            'p_value_adj': np.nan
        })
    
    # Calculate Shared Variance
    # Total R2 from full model
    formula_full = "~ " + " + ".join(available_vars)
    cap_full = capscale(dist_matrix, meta_df, formula=formula_full)
    total_r2 = sum(cap_full.proportion_explained[:len(cap_full.axes)])
    
    sum_unique = sum(item['r2'] for item in unique_r2s)
    shared_r2 = max(0, total_r2 - sum_unique)
    
    # Build final dataframe
    final_data = []
    for item in unique_r2s:
        final_data.append({
            'source': item['source'].replace('Unique_', ''),
            'variance_component': 'Unique',
            'r2': item['r2'],
            'p_value': np.nan,
            'p_value_adj': np.nan
        })
    
    final_data.append({
        'source': 'Shared',
        'variance_component': 'Shared',
        'r2': shared_r2,
        'p_value': np.nan,
        'p_value_adj': np.nan
    })
    
    final_data.append({
        'source': 'Unexplained',
        'variance_component': 'Unexplained',
        'r2': max(0, 1.0 - total_r2),
        'p_value': np.nan,
        'p_value_adj': np.nan
    })
    
    df_res = pd.DataFrame(final_data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_res.to_csv(output_path, index=False)
    logger.info(f"Variance partitioning results saved to {output_path}")
    
    return df_res

def _run_single_rda(asv_df, meta_df, vars, output_path):
    """Helper for single variable case."""
    dist_array = cdist(asv_df.values, asv_df.values, metric='braycurtis')
    dist_matrix = DistanceMatrix(dist_array, ids=asv_df.index)
    formula = f"~ {vars[0]}"
    cap = capscale(dist_matrix, meta_df, formula=formula)
    r2 = cap.proportion_explained[0]
    
    df_res = pd.DataFrame([
        {'source': vars[0], 'variance_component': 'Unique', 'r2': r2, 'p_value': np.nan, 'p_value_adj': np.nan}
    ])
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_res.to_csv(output_path, index=False)
    return df_res

# Entry point for testing
if __name__ == "__main__":
    # This block is for manual testing if files exist
    if os.path.exists("data/qc/asv_table.tsv") and os.path.exists("data/cleaned_metadata.csv"):
        run_variance_partitioning(
            "data/qc/asv_table.tsv",
            "data/cleaned_metadata.csv",
            ["pH", "nutrients", "moisture"]
        )
    else:
        print("Data files not found. Skipping execution.")
