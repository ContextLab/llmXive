import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import spearmanr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DATA_DIR / "network_analysis.json"
METADATA_FILE = PROCESSED_DATA_DIR / "processed_metadata.json" # Assuming metadata is stored here or derived

def load_processed_taxon_data(feature_table_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads the processed feature table (taxon abundance) from disk.
    Expects a CSV/TSV where rows are samples and columns are taxa.
    """
    if feature_table_path is None:
        # Default path based on project structure
        feature_table_path = PROCESSED_DATA_DIR / "feature_table_filtered.csv"
    
    if not feature_table_path.exists():
        logger.error(f"Feature table not found at {feature_table_path}")
        raise FileNotFoundError(f"Feature table not found: {feature_table_path}")
    
    logger.info(f"Loading taxon data from {feature_table_path}")
    df = pd.read_csv(feature_table_path, index_col=0)
    return df

def load_sample_metadata(metadata_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads sample metadata including 'stage' information.
    """
    if metadata_path is None:
        metadata_path = PROCESSED_DATA_DIR / "processed_metadata.json"
    
    if not metadata_path.exists():
        # Fallback to JSON or CSV if specific file missing, checking common names
        possible_paths = [
            PROCESSED_DATA_DIR / "metadata.json",
            PROCESSED_DATA_DIR / "sample_metadata.csv"
        ]
        for p in possible_paths:
            if p.exists():
                metadata_path = p
                break
        else:
            logger.error("No metadata file found to determine sample stages.")
            raise FileNotFoundError("No metadata file found.")
    
    logger.info(f"Loading metadata from {metadata_path}")
    if metadata_path.suffix == '.json':
        with open(metadata_path, 'r') as f:
            data = json.load(f)
            # Handle different JSON structures (list of dicts or dict of dicts)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame.from_dict(data, orient='index')
    else:
        df = pd.read_csv(metadata_path)
    
    return df

def calculate_spearman_correlation_matrix(taxon_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the Spearman correlation matrix for the taxon abundance data.
    """
    logger.info("Calculating Spearman correlation matrix...")
    # Use scipy spearmanr, handle potential NaNs if any
    corr_matrix, p_matrix = spearmanr(taxon_data, axis=0, nan_policy='omit')
    
    # Convert to DataFrames for easier handling
    corr_df = pd.DataFrame(corr_matrix, index=taxon_data.columns, columns=taxon_data.columns)
    p_df = pd.DataFrame(p_matrix, index=taxon_data.columns, columns=taxon_data.columns)
    
    return corr_df, p_df

def check_under_determined(n_samples: int, n_taxa: int) -> bool:
    """
    Checks if the dataset is under-determined (n_samples < n_taxa).
    Returns True if under-determined.
    """
    is_under_determined = n_samples < n_taxa
    if is_under_determined:
        logger.warning(f"Dataset is under-determined: {n_samples} samples < {n_taxa} taxa. Modularity calculation may be skipped or flagged.")
    return is_under_determined

def construct_network_graph(corr_matrix: pd.DataFrame, p_matrix: pd.DataFrame, threshold: float = 0.6, p_threshold: float = 0.01) -> nx.Graph:
    """
    Constructs a network graph based on correlation threshold and p-value.
    Edges are added if |rho| >= threshold and p <= p_threshold.
    """
    G = nx.Graph()
    
    # Add nodes
    G.add_nodes_from(corr_matrix.columns)
    
    # Add edges
    taxa = corr_matrix.columns
    for i in range(len(taxa)):
        for j in range(i + 1, len(taxa)):
            taxon_a = taxa[i]
            taxon_b = taxa[j]
            
            rho = corr_matrix.loc[taxon_a, taxon_b]
            p_val = p_matrix.loc[taxon_a, taxon_b]
            
            if abs(rho) >= threshold and p_val <= p_threshold:
                G.add_edge(taxon_a, taxon_b, weight=abs(rho), correlation=rho, p_value=p_val)
    
    logger.info(f"Constructed network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    return G

def calculate_modularity(G: nx.Graph) -> float:
    """
    Calculates the modularity of the network using the Louvain method (via community detection).
    Returns the modularity score.
    """
    if G.number_of_edges() == 0:
        logger.warning("No edges in graph, modularity is 0.")
        return 0.0
    
    try:
        import community as community_louvain
        partition = community_louvain.best_partition(G)
        modularity = community_louvain.modularity(partition, G)
        return modularity
    except ImportError:
        logger.warning("python-louvain package not found. Attempting fallback or raising error.")
        # Fallback: simple modularity calculation if no community package
        # Or raise error if strict dependency is required
        raise ImportError("The 'python-louvain' package is required for modularity calculation. Install it via pip.")
    except Exception as e:
        logger.error(f"Error calculating modularity: {e}")
        return 0.0

def calculate_delta_modularity(early_modularity: float, mature_modularity: float) -> float:
    """
    Calculates the signed delta (Δmodularity) between early and mature stages.
    Δ = Modularity_early - Modularity_mature
    """
    delta = early_modularity - mature_modularity
    logger.info(f"Delta Modularity (Early - Mature): {delta:.4f}")
    return delta

def save_modularity_results(early_mod: float, mature_mod: float, delta_mod: float, output_path: Optional[Path] = None):
    """
    Saves the modularity results to a JSON file.
    """
    if output_path is None:
        output_path = OUTPUT_FILE
    
    results = {
        "early_stage_modularity": early_mod,
        "mature_stage_modularity": mature_mod,
        "delta_modularity": delta_mod,
        "description": "Signed delta (Δmodularity) = Early - Mature"
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Modularity results saved to {output_path}")

def perform_sensitivity_analysis(corr_matrix: pd.DataFrame, p_matrix: pd.DataFrame, metadata_df: pd.DataFrame, 
                                 thresholds: List[float] = [0.5, 0.6, 0.7, 0.8], 
                                 output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Performs sensitivity analysis by sweeping correlation thresholds.
    Calculates Δmodularity for each threshold.
    """
    if output_path is None:
        output_path = PROCESSED_DATA_DIR / "network_sensitivity_report.json"
    
    results = {
        "thresholds_tested": thresholds,
        "delta_modularity_values": [],
        "variance": 0.0
    }
    
    # Filter metadata for early and mature stages
    # Assuming 'stage' column exists and values are 'early', 'mature', etc.
    # If 'stage' is not exactly these, adjust logic or rely on T012/T013 filtering
    early_samples = metadata_df[metadata_df['stage'] == 'early'].index.tolist()
    mature_samples = metadata_df[metadata_df['stage'] == 'mature'].index.tolist()
    
    if not early_samples or not mature_samples:
        logger.error("Could not separate samples into 'early' and 'mature' stages for sensitivity analysis.")
        return results

    for thresh in thresholds:
        # Filter correlation matrix for early samples
        early_df = corr_matrix.loc[early_samples, early_samples] if 'early' in corr_matrix.index else corr_matrix # Fallback if index mismatch
        # Actually, we need to re-calculate correlation for the SUBSET of samples if the matrix was global
        # But the task description implies using the global matrix or re-calculating per stage?
        # "Calculate network modularity ... between early vs. mature stages" implies separate networks.
        # The correlation matrix calculated in calculate_spearman_correlation_matrix is usually global (taxa x taxa).
        # To get stage-specific networks, we need to calculate correlation on the subset of samples for that stage.
        
        # Re-calculate correlation for Early Stage
        early_taxa_data = pd.read_csv(PROCESSED_DATA_DIR / "feature_table_filtered.csv", index_col=0).loc[early_samples]
        early_corr, _ = spearmanr(early_taxa_data, axis=0, nan_policy='omit')
        early_corr_df = pd.DataFrame(early_corr, index=early_taxa_data.columns, columns=early_taxa_data.columns)
        
        # Re-calculate correlation for Mature Stage
        mature_taxa_data = pd.read_csv(PROCESSED_DATA_DIR / "feature_table_filtered.csv", index_col=0).loc[mature_samples]
        mature_corr, _ = spearmanr(mature_taxa_data, axis=0, nan_policy='omit')
        mature_corr_df = pd.DataFrame(mature_corr, index=mature_taxa_data.columns, columns=mature_taxa_data.columns)
        
        # Construct graphs and calculate modularity
        try:
            G_early = construct_network_graph(early_corr_df, p_matrix, threshold=thresh) # p_matrix might need recalculation too, but assuming global p is okay or re-calc
            # Re-calculate p for subset to be safe
            _, early_p = spearmanr(early_taxa_data, axis=0, nan_policy='omit')
            early_p_df = pd.DataFrame(early_p, index=early_taxa_data.columns, columns=early_taxa_data.columns)
            G_early = construct_network_graph(early_corr_df, early_p_df, threshold=thresh)
            
            G_mature = construct_network_graph(mature_corr_df, p_matrix, threshold=thresh)
            _, mature_p = spearmanr(mature_taxa_data, axis=0, nan_policy='omit')
            mature_p_df = pd.DataFrame(mature_p, index=mature_taxa_data.columns, columns=mature_taxa_data.columns)
            G_mature = construct_network_graph(mature_corr_df, mature_p_df, threshold=thresh)
            
            mod_early = calculate_modularity(G_early)
            mod_mature = calculate_modularity(G_mature)
            delta = mod_early - mod_mature
            
            results["delta_modularity_values"].append({
                "threshold": thresh,
                "early_modularity": mod_early,
                "mature_modularity": mod_mature,
                "delta": delta
            })
        except Exception as e:
            logger.warning(f"Could not calculate modularity for threshold {thresh}: {e}")
            results["delta_modularity_values"].append({
                "threshold": thresh,
                "error": str(e)
            })
    
    # Calculate variance of delta values (ignoring errors)
    valid_deltas = [x["delta"] for x in results["delta_modularity_values"] if "delta" in x]
    if len(valid_deltas) > 1:
        results["variance"] = float(np.var(valid_deltas))
    else:
        results["variance"] = 0.0
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis results saved to {output_path}")
    return results

def main():
    """
    Main execution flow for T031: Calculate network modularity and delta.
    """
    try:
        # 1. Load Data
        # We need the global feature table to split by stage
        feature_table_path = PROCESSED_DATA_DIR / "feature_table_filtered.csv"
        metadata_path = PROCESSED_DATA_DIR / "processed_metadata.json"
        
        if not feature_table_path.exists():
            logger.error("Feature table not found. Ensure T012/T013 has run.")
            sys.exit(1)
        
        if not metadata_path.exists():
            logger.error("Metadata not found. Ensure T012 has run.")
            sys.exit(1)

        feature_df = pd.read_csv(feature_table_path, index_col=0)
        metadata_df = load_sample_metadata(metadata_path)

        # Ensure 'stage' column exists
        if 'stage' not in metadata_df.columns:
            logger.error("Metadata must contain a 'stage' column.")
            sys.exit(1)

        # 2. Split by Stage
        early_samples = metadata_df[metadata_df['stage'] == 'early'].index.tolist()
        mature_samples = metadata_df[metadata_df['stage'] == 'mature'].index.tolist()

        if not early_samples or not mature_samples:
            logger.error("Could not find samples for both 'early' and 'mature' stages.")
            sys.exit(1)

        logger.info(f"Found {len(early_samples)} early samples and {len(mature_samples)} mature samples.")

        # 3. Calculate Correlations and Modularity for Early Stage
        logger.info("Processing Early Stage...")
        early_taxa_df = feature_df.loc[early_samples]
        early_corr, early_p = spearmanr(early_taxa_df, axis=0, nan_policy='omit')
        early_corr_df = pd.DataFrame(early_corr, index=early_taxa_df.columns, columns=early_taxa_df.columns)
        early_p_df = pd.DataFrame(early_p, index=early_taxa_df.columns, columns=early_taxa_df.columns)
        
        G_early = construct_network_graph(early_corr_df, early_p_df, threshold=0.6, p_threshold=0.01)
        mod_early = calculate_modularity(G_early)
        logger.info(f"Early Stage Modularity: {mod_early:.4f}")

        # 4. Calculate Correlations and Modularity for Mature Stage
        logger.info("Processing Mature Stage...")
        mature_taxa_df = feature_df.loc[mature_samples]
        mature_corr, mature_p = spearmanr(mature_taxa_df, axis=0, nan_policy='omit')
        mature_corr_df = pd.DataFrame(mature_corr, index=mature_taxa_df.columns, columns=mature_taxa_df.columns)
        mature_p_df = pd.DataFrame(mature_p, index=mature_taxa_df.columns, columns=mature_taxa_df.columns)
        
        G_mature = construct_network_graph(mature_corr_df, mature_p_df, threshold=0.6, p_threshold=0.01)
        mod_mature = calculate_modularity(G_mature)
        logger.info(f"Mature Stage Modularity: {mod_mature:.4f}")

        # 5. Calculate Delta
        delta_mod = calculate_delta_modularity(mod_early, mod_mature)

        # 6. Save Results
        save_modularity_results(mod_early, mod_mature, delta_mod)

        # 7. Perform Sensitivity Analysis (T030 dependency)
        # Re-calling logic here or calling the function if it handles file paths correctly
        # The function perform_sensitivity_analysis re-reads the file, which is fine.
        perform_sensitivity_analysis(early_corr_df, early_p_df, metadata_df)

        logger.info("T031 and T030 execution completed successfully.")

    except Exception as e:
        logger.critical(f"Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()