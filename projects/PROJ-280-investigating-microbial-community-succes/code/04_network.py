import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import networkx as nx
from scipy import stats

# Import shared utilities
from utils import log_under_determined_flag, generate_checksum
from state_tracker import update_multiple_artifacts, ensure_state_file

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/network_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

def load_processed_taxon_data(data_dir: str = "data/processed") -> pd.DataFrame:
    """
    Load the filtered feature table from the processed data directory.
    Expects a file named 'filtered_feature_table.csv' or similar.
    """
    # Look for common processed feature table names
    possible_files = [
        "filtered_feature_table.csv",
        "feature_table.csv",
        "taxon_abundance.csv"
    ]
    
    target_file = None
    for fname in possible_files:
        fpath = Path(data_dir) / fname
        if fpath.exists():
            target_file = fpath
            break
    
    if not target_file:
        # Fallback: try to find any csv in data_dir
        csv_files = list(Path(data_dir).glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No feature table found in {data_dir}")
        target_file = csv_files[0]
    
    logger.info(f"Loading taxon data from {target_file}")
    df = pd.read_csv(target_file)
    
    # Ensure first column is index if it looks like sample IDs
    if df.columns[0] == 'sample_id' or df.columns[0] == 'SampleID':
        df.set_index(df.columns[0], inplace=True)
    
    return df

def calculate_spearman_correlation_matrix(taxon_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate Spearman correlation matrix and p-value matrix for taxon abundances.
    Rows are samples, columns are taxa.
    """
    logger.info("Calculating Spearman correlation matrix...")
    
    # Transpose so rows are taxa, columns are samples for correlation calculation
    # We want correlation between taxa (columns in original df)
    corr_matrix, p_matrix = stats.spearmanr(taxon_df, axis=0)
    
    # Convert to DataFrames for easier handling
    taxa_names = taxon_df.columns
    corr_df = pd.DataFrame(corr_matrix, index=taxa_names, columns=taxa_names)
    p_df = pd.DataFrame(p_matrix, index=taxa_names, columns=taxa_names)
    
    return corr_df, p_df

def check_under_determined(taxon_df: pd.DataFrame) -> bool:
    """
    Check if the dataset is under-determined (n_samples < n_taxa).
    Returns True if under-determined.
    """
    n_samples = taxon_df.shape[0]
    n_taxa = taxon_df.shape[1]
    
    logger.info(f"Dataset dimensions: {n_samples} samples, {n_taxa} taxa")
    
    if n_samples < n_taxa:
        log_under_determined_flag(f"Under-determined: {n_samples} samples < {n_taxa} taxa")
        return True
    return False

def construct_network_graph(corr_df: pd.DataFrame, p_df: pd.DataFrame, 
                            threshold: float = 0.6, p_threshold: float = 0.01) -> nx.Graph:
    """
    Construct a network graph based on correlation threshold and p-value threshold.
    """
    G = nx.Graph()
    
    taxa = corr_df.columns.tolist()
    G.add_nodes_from(taxa)
    
    count = 0
    for i, taxon1 in enumerate(taxa):
        for j, taxon2 in enumerate(taxa):
            if i >= j:
                continue
            
            corr_val = corr_df.loc[taxon1, taxon2]
            p_val = p_df.loc[taxon1, taxon2]
            
            # Apply thresholds
            if abs(corr_val) >= threshold and p_val <= p_threshold:
                G.add_edge(taxon1, taxon2, weight=corr_val, p_value=p_val)
                count += 1
    
    logger.info(f"Constructed network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G

def calculate_modularity(G: nx.Graph) -> float:
    """
    Calculate the modularity of the network graph using the Louvain method.
    """
    if G.number_of_edges() == 0:
        return 0.0
    
    try:
        # Use the louvain_communities method if available (networkx >= 2.5)
        # Otherwise fall back to standard community detection
        if hasattr(nx.community, 'louvain_communities'):
            communities = nx.community.louvain_communities(G, seed=42)
        else:
            # Fallback for older networkx versions
            from community import community_louvain
            partition = community_louvain.best_partition(G, random_state=42)
            communities = [ [node for node, p in partition.items() if p == val] 
                            for val in set(partition.values()) ]
        
        modularity = nx.community.modularity(G, communities)
        return modularity
    except Exception as e:
        logger.warning(f"Modularity calculation failed: {e}. Returning 0.0.")
        return 0.0

def calculate_delta_modularity(early_df: pd.DataFrame, mature_df: pd.DataFrame,
                               threshold: float = 0.6, p_threshold: float = 0.01) -> Tuple[float, float, float]:
    """
    Calculate modularity for early and mature stages and return the signed delta.
    Returns (modularity_early, modularity_mature, delta_modularity).
    """
    logger.info("Calculating modularity for early and mature stages...")
    
    # Calculate correlations and graphs for each stage
    corr_early, p_early = calculate_spearman_correlation_matrix(early_df)
    G_early = construct_network_graph(corr_early, p_early, threshold, p_threshold)
    mod_early = calculate_modularity(G_early)
    
    corr_mature, p_mature = calculate_spearman_correlation_matrix(mature_df)
    G_mature = construct_network_graph(corr_mature, p_mature, threshold, p_threshold)
    mod_mature = calculate_modularity(G_mature)
    
    delta = mod_early - mod_mature
    
    logger.info(f"Modularity Early: {mod_early:.4f}")
    logger.info(f"Modularity Mature: {mod_mature:.4f}")
    logger.info(f"Delta Modularity (Early - Mature): {delta:.4f}")
    
    return mod_early, mod_mature, delta

def run_sensitivity_analysis(taxon_df: pd.DataFrame, stage_col: str = "stage") -> Dict[str, Any]:
    """
    Run sensitivity analysis on modularity by sweeping correlation thresholds.
    This is a helper for T030, but we can use it here to ensure robustness.
    """
    thresholds = [0.5, 0.6, 0.7]
    results = {}
    
    # Split by stage
    if stage_col not in taxon_df.columns:
        # Try to find stage column
        possible_cols = ["stage", "Stage", "establishment_stage"]
        for col in possible_cols:
            if col in taxon_df.columns:
                stage_col = col
                break
        else:
            logger.warning("Stage column not found. Cannot split by stage.")
            return {}
    
    # Assuming the first column is sample metadata or we need to load separate metadata
    # For this implementation, we assume the input df has a 'stage' column or we filter externally
    # Since T012 already filtered, we assume the data is already split or we need to split here
    
    # NOTE: The input taxon_df here is likely just the abundance matrix (samples x taxa).
    # We need the metadata to split. Let's assume we load metadata from a known file.
    meta_path = Path("data/processed/metadata.csv")
    if not meta_path.exists():
        meta_path = Path("data/processed/sample_metadata.csv")
    
    if meta_path.exists():
        metadata = pd.read_csv(meta_path)
        # Ensure index matches
        if 'sample_id' in metadata.columns:
            metadata.set_index('sample_id', inplace=True)
        
        # Filter taxon_df to only include samples in metadata
        common_samples = taxon_df.index.intersection(metadata.index)
        taxon_df = taxon_df.loc[common_samples]
        metadata = metadata.loc[common_samples]
        
        early_mask = metadata[stage_col].str.lower().isin(['early', 'initial', 'start'])
        mature_mask = metadata[stage_col].str.lower().isin(['mature', 'late', 'end'])
        
        early_df = taxon_df[early_mask]
        mature_df = taxon_df[mature_mask]
    else:
        logger.warning("Metadata file not found. Cannot perform stage-specific modularity calculation.")
        return {}
    
    if early_df.empty or mature_df.empty:
        logger.warning("Could not split data into early and mature stages.")
        return {}
    
    deltas = []
    for thresh in thresholds:
        _, _, delta = calculate_delta_modularity(early_df, mature_df, threshold=thresh)
        deltas.append(delta)
        results[f"threshold_{thresh}"] = delta
    
    results["delta_variance"] = float(np.var(deltas))
    return results

def save_modularity_results(mod_early: float, mod_mature: float, delta: float, 
                            output_path: str = "data/processed/modularity_results.json"):
    """
    Save the modularity results to a JSON file.
    """
    results = {
        "modularity_early": mod_early,
        "modularity_mature": mod_mature,
        "delta_modularity": delta,
        "interpretation": "Positive delta indicates higher modularity in early stages."
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved modularity results to {output_path}")
    return output_path

def main():
    """
    Main entry point for network modularity analysis.
    """
    logger.info("Starting Network Modularity Analysis (T031)")
    
    # Load data
    try:
        taxon_df = load_processed_taxon_data()
    except Exception as e:
        logger.error(f"Failed to load taxon data: {e}")
        sys.exit(1)
    
    # Check under-determined
    if check_under_determined(taxon_df):
        logger.warning("Dataset is under-determined. Modularity calculation may be unreliable.")
        # Still attempt calculation but flag it
    
    # We need to split data by stage. 
    # Assumption: T012 produced a file with stage information or we have a separate metadata file.
    # If the taxon_df includes the stage column, we split. If not, we load metadata.
    
    # Try to split if stage column exists in the loaded df
    stage_col = None
    for col in ['stage', 'Stage', 'establishment_stage']:
        if col in taxon_df.columns:
            stage_col = col
            break
    
    if stage_col:
        # Split by stage
        early_df = taxon_df[taxon_df[stage_col].str.lower().isin(['early', 'initial', 'start'])]
        mature_df = taxon_df[taxon_df[stage_col].str.lower().isin(['mature', 'late', 'end'])]
        
        # Drop the stage column for calculation
        early_df = early_df.drop(columns=[stage_col])
        mature_df = mature_df.drop(columns=[stage_col])
    else:
        # Load external metadata
        meta_path = Path("data/processed/metadata.csv")
        if not meta_path.exists():
            meta_path = Path("data/processed/sample_metadata.csv")
        
        if meta_path.exists():
            metadata = pd.read_csv(meta_path)
            if 'sample_id' in metadata.columns:
                metadata.set_index('sample_id', inplace=True)
            
            # Align with taxon_df
            common = taxon_df.index.intersection(metadata.index)
            taxon_df = taxon_df.loc[common]
            metadata = metadata.loc[common]
            
            # Find stage column
            for col in ['stage', 'Stage', 'establishment_stage']:
                if col in metadata.columns:
                    stage_col = col
                    break
            
            if stage_col:
                early_mask = metadata[stage_col].str.lower().isin(['early', 'initial', 'start'])
                mature_mask = metadata[stage_col].str.lower().isin(['mature', 'late', 'end'])
                
                early_df = taxon_df[early_mask]
                mature_df = taxon_df[mature_mask]
            else:
                logger.error("No stage column found in metadata or taxon data.")
                sys.exit(1)
        else:
            logger.error("No metadata file found to split by stage.")
            sys.exit(1)
    
    if early_df.empty or mature_df.empty:
        logger.error("Could not form early or mature stage groups.")
        sys.exit(1)
    
    # Calculate modularity
    mod_early, mod_mature, delta = calculate_delta_modularity(early_df, mature_df)
    
    # Save results
    output_file = save_modularity_results(mod_early, mod_mature, delta)
    
    # Update state tracker
    ensure_state_file()
    update_multiple_artifacts([output_file])
    
    logger.info("T031 Modularity Analysis Complete")
    print(f"Delta Modularity: {delta:.4f}")

if __name__ == "__main__":
    main()