import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import networkx as nx
from sklearn.metrics import pairwise_distances

# Custom logging formatter if not already defined globally, 
# though T038b suggests standardizing. We ensure it exists locally or import if available.
try:
    from utils import log_under_determined_flag
except ImportError:
    log_under_determined_flag = None

class CustomFormatter(logging.Formatter):
    def format(self, record):
        log_message = f"[{record.levelname}] [{record.name}] {record.getMessage()}"
        return log_message

def setup_logging():
    logger = logging.getLogger("04_network")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(CustomFormatter())
        logger.addHandler(handler)
    return logger

def load_processed_taxon_data(file_path: str) -> pd.DataFrame:
    """Load the filtered feature table (taxon abundance data)."""
    logger = logging.getLogger("04_network")
    if not os.path.exists(file_path):
        logger.error(f"Feature table not found: {file_path}. Ensure T012/T013 has run.")
        sys.exit(1)
    try:
        df = pd.read_csv(file_path, index_col=0)
        logger.info(f"Loaded taxon data with shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Error loading taxon data: {e}")
        sys.exit(1)

def load_sample_metadata(file_path: str) -> pd.DataFrame:
    """Load sample metadata to determine stages."""
    logger = logging.getLogger("04_network")
    if not os.path.exists(file_path):
        logger.error(f"Metadata file not found: {file_path}")
        sys.exit(1)
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded metadata with shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Error loading metadata: {e}")
        sys.exit(1)

def calculate_spearman_correlation_matrix(taxon_data: pd.DataFrame) -> pd.DataFrame:
    """Calculate Spearman correlation matrix between taxa."""
    logger = logging.getLogger("04_network")
    logger.info("Calculating Spearman correlation matrix...")
    # Transpose to have taxa as rows for correlation if they are currently columns
    # Assuming columns are taxa
    corr_matrix, p_matrix = spearmanr(taxon_data, axis=1)
    # Convert to DataFrame
    corr_df = pd.DataFrame(corr_matrix, index=taxon_data.index, columns=taxon_data.index)
    logger.info(f"Correlation matrix calculated: {corr_df.shape}")
    return corr_df

def check_under_determined(n_samples: int, n_taxa: int) -> Tuple[bool, str]:
    """
    Check if the dataset is under-determined (n_samples < n_taxa).
    Returns (is_under_determined, reason_message).
    """
    logger = logging.getLogger("04_network")
    if n_samples < n_taxa:
        logger.warning(f"UNDER-DETERMINED: n_samples ({n_samples}) < n_taxa ({n_taxa}).")
        if log_under_determined_flag:
            log_under_determined_flag(f"n_samples={n_samples}, n_taxa={n_taxa}")
        return True, f"n_samples ({n_samples}) < n_taxa ({n_taxa})"
    return False, ""

def construct_network_graph(corr_matrix: pd.DataFrame, threshold: float = 0.6) -> nx.Graph:
    """Construct a network graph based on correlation threshold."""
    logger = logging.getLogger("04_network")
    G = nx.Graph()
    # Add nodes
    G.add_nodes_from(corr_matrix.index)
    
    # Add edges
    edges_added = 0
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            val = corr_matrix.iloc[i, j]
            if abs(val) >= threshold:
                G.add_edge(corr_matrix.index[i], corr_matrix.columns[j], weight=val)
                edges_added += 1
    
    logger.info(f"Network constructed with {G.number_of_nodes()} nodes and {edges_added} edges.")
    return G

def calculate_modularity(G: nx.Graph) -> float:
    """Calculate modularity of the network."""
    logger = logging.getLogger("04_network")
    if G.number_of_edges() == 0:
        logger.warning("No edges in network, modularity is 0.")
        return 0.0
    try:
        # Use Louvain method for community detection
        partition = nx.community.louvain_communities(G, seed=42)
        modularity = nx.community.modularity(G, partition)
        logger.info(f"Modularity calculated: {modularity:.4f}")
        return modularity
    except Exception as e:
        logger.error(f"Error calculating modularity: {e}")
        return 0.0

def calculate_delta_modularity(early_mod: float, mature_mod: float) -> float:
    """Calculate the signed delta between early and mature modularity."""
    logger = logging.getLogger("04_network")
    delta = early_mod - mature_mod
    logger.info(f"Delta Modularity (Early - Mature): {delta:.4f}")
    return delta

def save_modularity_results(output_path: str, early_mod: float, mature_mod: float, delta: float, flag: str):
    """Save modularity results to JSON."""
    logger = logging.getLogger("04_network")
    result = {
        "modularity_early": early_mod,
        "modularity_mature": mature_mod,
        "delta": delta,
        "flag": flag
    }
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Modularity results saved to {output_path}")

def perform_sensitivity_analysis(corr_matrix: pd.DataFrame, thresholds: List[float]) -> Dict[str, Any]:
    """Perform sensitivity analysis by sweeping thresholds."""
    logger = logging.getLogger("04_network")
    results = []
    for t in thresholds:
        G = construct_network_graph(corr_matrix, threshold=t)
        mod = calculate_modularity(G)
        results.append({"threshold": t, "modularity": mod})
    return results

def save_network_analysis_fallback(output_path: str, reason: str):
    """
    T049: Save the fallback network analysis report when under-determined.
    """
    logger = logging.getLogger("04_network")
    report = {
        "status": "STABILITY_UNASSESSABLE",
        "reason": reason,
        "delta": None,
        "stability_assessment": "UNASSESSABLE"
    }
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Network analysis fallback report saved to {output_path}")

def main():
    logger = setup_logging()
    logger.info("Starting Network Analysis Pipeline (T049)...")

    # Paths
    base_dir = Path(__file__).parent.parent
    taxon_data_path = base_dir / "data" / "processed" / "filtered_feature_table.csv"
    metadata_path = base_dir / "data" / "processed" / "sample_metadata.csv"
    output_dir = base_dir / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    network_analysis_path = output_dir / "network_analysis.json"
    modularity_delta_path = output_dir / "modularity_delta.json"

    # Load Data
    try:
        taxon_data = load_processed_taxon_data(str(taxon_data_path))
        metadata = load_sample_metadata(str(metadata_path))
    except SystemExit:
        # Error already logged
        sys.exit(1)

    # Check Under-Determined
    n_samples = taxon_data.shape[0]
    n_taxa = taxon_data.shape[1]
    is_under_determined, reason = check_under_determined(n_samples, n_taxa)

    if is_under_determined:
        # T049: Implement Under-Determined Network Fallback Strategy
        logger.warning("T049 Fallback: Network is under-determined. Skipping full construction.")
        save_network_analysis_fallback(str(network_analysis_path), reason)
        
        # Also save modularity_delta with nulls as per T031 requirement
        save_modularity_results(str(modularity_delta_path), None, None, None, "UNDER-DETERMINED")
        
        logger.info("Pipeline finished with UNDER-DETERMINED status. Output files created.")
        return

    # Normal Execution
    logger.info("Dataset is determined. Proceeding with network construction.")
    
    # Split by stage (assuming 'stage' column exists in metadata and matches index)
    # We need to ensure metadata index matches taxon_data index
    if metadata.index.name != 'sample_id':
        metadata.set_index('sample_id', inplace=True)
    
    # Filter for Early and Mature
    early_samples = metadata[metadata['stage'] == 'early'].index
    mature_samples = metadata[metadata['stage'] == 'mature'].index

    early_data = taxon_data.loc[early_samples]
    mature_data = taxon_data.loc[mature_samples]

    # Calculate Correlations
    corr_early = calculate_spearman_correlation_matrix(early_data)
    corr_mature = calculate_spearman_correlation_matrix(mature_data)

    # Construct Graphs
    G_early = construct_network_graph(corr_early)
    G_mature = construct_network_graph(corr_mature)

    # Calculate Modularity
    mod_early = calculate_modularity(G_early)
    mod_mature = calculate_modularity(G_mature)
    delta = calculate_delta_modularity(mod_early, mod_mature)

    # Save Modularity Results
    save_modularity_results(str(modularity_delta_path), mod_early, mod_mature, delta, "PASS")

    # Save Full Network Analysis (Edges, etc.)
    edges_list = []
    for u, v, data in G_early.edges(data=True):
        edges_list.append({"source": u, "target": v, "weight": data['weight'], "stage": "early"})
    for u, v, data in G_mature.edges(data=True):
        edges_list.append({"source": u, "target": v, "weight": data['weight'], "stage": "mature"})

    full_network_report = {
        "status": "PASS",
        "modularity_early": mod_early,
        "modularity_mature": mod_mature,
        "delta": delta,
        "stability_assessment": "CALCULATED",
        "edges": edges_list
    }
    with open(str(network_analysis_path), 'w') as f:
        json.dump(full_network_report, f, indent=2)
    
    logger.info("Network analysis complete. All artifacts saved.")

if __name__ == "__main__":
    main()