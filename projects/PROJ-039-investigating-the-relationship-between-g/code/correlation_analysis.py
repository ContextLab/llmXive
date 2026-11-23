"""
Spearman correlation analysis for stratum-level data.

Implements T022:
- Selects top 20 taxa by mean relative abundance from raw microbiome features.
- Computes Spearman correlation between CLR-transformed taxa abundances and mean alpha power.
- Applies Benjamini-Hochberg FDR correction.
- Outputs results to artifacts/correlation_results.json and artifacts/top_taxa.txt.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from statsmodels.stats.multitest import multipletests

# Project root handling
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Ensure output directory exists
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "artifacts" / "correlation_analysis.log")
    ]
)
logger = logging.getLogger(__name__)


def load_stratum_features() -> pd.DataFrame:
    """Load stratum features computed in T015."""
    path = PROCESSED_DIR / "stratum_features.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    
    df = pd.read_csv(path)
    # Handle JSON-like column for CLR abundances if stored as string
    if 'clr_taxa_abundances' in df.columns:
        # Attempt to parse JSON strings in the column
        def parse_json(x):
            if isinstance(x, str):
                try:
                    return json.loads(x)
                except (json.JSONDecodeError, TypeError):
                    return None
            return x
        
        df['clr_taxa_abundances'] = df['clr_taxa_abundances'].apply(parse_json)
    
    logger.info(f"Loaded stratum features: {len(df)} strata")
    return df


def load_microbiome_features() -> pd.DataFrame:
    """Load raw microbiome features to select top taxa (T012 output)."""
    path = PROCESSED_DIR / "microbiome_features.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded microbiome features: {len(df)} subjects, {len(df.columns)} columns")
    return df


def select_top_taxa(microbiome_df: pd.DataFrame, n_taxa: int = 20) -> List[str]:
    """
    Select top N taxa by mean relative abundance across all subjects.
    
    Sorting Rule:
    1. Mean relative abundance (descending)
    2. Alphabetical by genus name (ascending) for ties
    
    Returns list of taxon names.
    """
    # Identify taxon columns (exclude metadata like 'subject_id', 'age', 'sex', etc.)
    # Assuming taxon columns are those not in a known metadata list
    metadata_cols = {'subject_id', 'age', 'sex', 'bmi', 'diet', 'imputed_flag'}
    taxon_cols = [col for col in microbiome_df.columns if col not in metadata_cols]
    
    if len(taxon_cols) == 0:
        logger.warning("No taxon columns found in microbiome features.")
        return []
    
    # Compute mean abundance for each taxon
    mean_abundances = microbiome_df[taxon_cols].mean(axis=0)
    
    # Sort: descending by mean, then ascending by name for ties
    sorted_taxa = mean_abundances.sort_values(ascending=False).to_frame().reset_index()
    sorted_taxa.columns = ['taxon', 'mean_abundance']
    
    # Secondary sort by name (ascending) for ties
    sorted_taxa = sorted_taxa.sort_values(by=['mean_abundance', 'taxon'], 
                                          ascending=[False, True])
    
    selected = sorted_taxa['taxon'].head(n_taxa).tolist()
    
    logger.info(f"Selected top {len(selected)} taxa: {selected}")
    
    if len(selected) < n_taxa:
        logger.warning(f"Only {len(selected)} taxa found, fewer than requested {n_taxa}.")
    
    return selected


def compute_spearman_correlations(stratum_df: pd.DataFrame, selected_taxa: List[str]) -> List[Dict[str, Any]]:
    """
    Compute Spearman correlation between CLR-transformed taxon abundances and mean alpha power.
    
    Args:
        stratum_df: DataFrame with stratum features (must have 'mean_alpha_power' and 'clr_taxa_abundances')
        selected_taxa: List of taxon names to correlate
    
    Returns:
        List of dicts with correlation results.
    """
    if 'mean_alpha_power' not in stratum_df.columns:
        raise ValueError("stratum_df must contain 'mean_alpha_power' column.")
    
    results = []
    alpha_power = stratum_df['mean_alpha_power'].values
    
    # Extract CLR abundances for selected taxa
    # Handle case where clr_taxa_abundances is a dict per row
    clr_data = {}
    for taxon in selected_taxa:
        values = []
        for idx, row in stratum_df.iterrows():
            abundances = row.get('clr_taxa_abundances')
            if isinstance(abundances, dict) and taxon in abundances:
                values.append(abundances[taxon])
            else:
                # If missing, treat as NaN or skip? Spec implies valid data.
                values.append(np.nan)
        clr_data[taxon] = np.array(values)
    
    # Compute correlations
    for taxon in selected_taxa:
        x = clr_data[taxon]
        
        # Handle NaNs
        valid_mask = ~(np.isnan(x) | np.isnan(alpha_power))
        if np.sum(valid_mask) < 3:
            logger.warning(f"Not enough valid data points for {taxon}. Skipping.")
            results.append({
                'taxon': taxon,
                'rho': np.nan,
                'p_value': np.nan,
                'q_value': np.nan,
                'significant': False,
                'n_valid': int(np.sum(valid_mask))
            })
            continue
        
        x_valid = x[valid_mask]
        y_valid = alpha_power[valid_mask]
        
        rho, p_val = spearmanr(x_valid, y_valid)
        
        results.append({
            'taxon': taxon,
            'rho': float(rho),
            'p_value': float(p_val),
            'q_value': np.nan,  # To be filled later
            'significant': False,  # To be filled later
            'n_valid': int(np.sum(valid_mask))
        })
    
    logger.info(f"Computed {len(results)} Spearman correlations.")
    return results


def apply_fdr_correction(results: List[Dict[str, Any]], alpha: float = 0.1) -> List[Dict[str, Any]]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        results: List of correlation result dicts
        alpha: Significance threshold for q-value (default 0.1)
    
    Returns:
        Updated results list with q-values and significance flags.
    """
    p_values = np.array([r['p_value'] for r in results])
    
    # Filter out NaNs for correction
    valid_mask = ~np.isnan(p_values)
    if not np.any(valid_mask):
        logger.warning("No valid p-values for FDR correction.")
        return results
    
    # Benjamini-Hochberg correction using statsmodels
    # method='fdr_bh' implements Benjamini-Hochberg
    reject, pvals_corrected, _, _ = multipletests(
        p_values[valid_mask], 
        alpha=alpha, 
        method='fdr_bh'
    )
    
    # Map back to results
    valid_indices = np.where(valid_mask)[0]
    for i, idx in enumerate(valid_indices):
        results[idx]['q_value'] = float(pvals_corrected[i])
        results[idx]['significant'] = bool(reject[i])
    
    logger.info(f"FDR correction applied. Significant taxa (q < {alpha}): {sum(r['significant'] for r in results)}")
    return results


def save_results(results: List[Dict[str, Any]], top_taxa: List[str]):
    """
    Save results to JSON and top taxa to text file.
    """
    # Save correlation results
    output_path = ARTIFACTS_DIR / "correlation_results.json"
    with open(output_path, 'w') as f:
        json.dump({
            'analysis_type': 'spearman_correlation',
            'method': 'Benjamini-Hochberg FDR',
            'fdr_threshold': 0.1,
            'top_taxa_selected': top_taxa,
            'results': results,
            'note': 'This analysis is associational only; no causal inference is made.'
        }, f, indent=2)
    logger.info(f"Saved correlation results to {output_path}")
    
    # Save top taxa list
    taxa_path = ARTIFACTS_DIR / "top_taxa.txt"
    with open(taxa_path, 'w') as f:
        for taxon in top_taxa:
            f.write(f"{taxon}\n")
    logger.info(f"Saved top taxa list to {taxa_path}")


def main():
    """Main entry point for T022."""
    logger.info("Starting Spearman correlation analysis (T022)...")
    
    try:
        # 1. Load data
        logger.info("Loading stratum features...")
        stratum_df = load_stratum_features()
        
        logger.info("Loading microbiome features...")
        microbiome_df = load_microbiome_features()
        
        # 2. Select top 20 taxa
        logger.info("Selecting top 20 taxa...")
        top_taxa = select_top_taxa(microbiome_df, n_taxa=20)
        
        if len(top_taxa) == 0:
            logger.error("No taxa selected. Exiting.")
            sys.exit(1)
        
        # 3. Compute correlations
        logger.info("Computing Spearman correlations...")
        results = compute_spearman_correlations(stratum_df, top_taxa)
        
        # 4. Apply FDR
        logger.info("Applying FDR correction...")
        results = apply_fdr_correction(results, alpha=0.1)
        
        # 5. Save results
        logger.info("Saving results...")
        save_results(results, top_taxa)
        
        logger.info("T022 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()