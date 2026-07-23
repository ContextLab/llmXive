import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from code.config import load_config, get_organisms, get_path, ensure_dirs
from code.data_loader import load_local_network, load_local_essentiality, map_ids
from code.network_analysis import process_organism_networks
from code.statistics import calculate_spearman_correlation

logger = logging.getLogger(__name__)

def run_pipeline_for_organism(organism_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the full analysis pipeline for a single organism.
    
    Steps:
    1. Load Network (from local file or fetch)
    2. Load Essentiality Labels
    3. Map IDs (Handle missing overlaps)
    4. Compute Centralities (Handle disconnected networks)
    5. Calculate Correlations
    6. Return results
    """
    logger.info(f"Starting pipeline for {organism_id}")
    
    data_dir = get_path(config, 'data_dir')
    results_dir = get_path(config, 'results_dir')
    confidence_threshold = config.get('confidence_threshold', 700)
    
    # 1. Load Network
    network_file = Path(data_dir) / f"{organism_id}_network.json"
    try:
        adjacency_list = load_local_network(network_file)
        logger.info(f"Loaded network for {organism_id} with {len(adjacency_list)} nodes.")
    except Exception as e:
        logger.error(f"Failed to load network for {organism_id}: {e}")
        return {"organism": organism_id, "error": str(e), "status": "failed"}

    # 2. Load Essentiality
    essentiality_file = Path(data_dir) / f"{organism_id}_essentiality.json"
    try:
        essentiality_raw = load_local_essentiality(essentiality_file)
        logger.info(f"Loaded essentiality for {organism_id} with {len(essentiality_raw)} genes.")
    except Exception as e:
        logger.error(f"Failed to load essentiality for {organism_id}: {e}")
        return {"organism": organism_id, "error": str(e), "status": "failed"}

    # 3. Map IDs
    string_genes = set(adjacency_list.keys())
    deg_genes = set(essentiality_raw.keys())
    mapping, coverage = map_ids(string_genes, deg_genes)
    
    if not mapping:
        logger.warning(f"No gene overlap found for {organism_id}. Skipping correlation calculation.")
        return {
            "organism": organism_id,
            "status": "skipped",
            "reason": "No gene overlap between network and essentiality data",
            "mapping_coverage_percent": 0.0
        }

    # Filter data to mapped genes
    mapped_essentiality = {g: essentiality_raw[g] for g in mapping.keys() if g in essentiality_raw}
    filtered_adjacency = {}
    for node, neighbors in adjacency_list.items():
        if node in mapping:
            # Only keep neighbors that are also in the mapping
            filtered_neighbors = [n for n in neighbors if n in mapping]
            filtered_adjacency[node] = filtered_neighbors

    # 4. Compute Centralities
    # Prepare data for process_organism_networks
    organism_data = {
        "organism_id": organism_id,
        "adjacency_list": filtered_adjacency
    }
    
    try:
        centralities = process_organism_networks(organism_data)
    except Exception as e:
        logger.error(f"Centrality computation failed for {organism_id}: {e}")
        return {"organism": organism_id, "error": str(e), "status": "failed"}

    # 5. Calculate Correlations
    # We need to align centralities and essentiality labels by gene ID
    common_genes = set(centralities['degree'].keys()).intersection(mapped_essentiality.keys())
    
    if not common_genes:
        logger.warning(f"No common genes after filtering for {organism_id}.")
        return {
            "organism": organism_id,
            "status": "skipped",
            "reason": "No common genes for correlation after filtering",
            "mapping_coverage_percent": coverage
        }

    results = {}
    for metric_name in ['degree', 'eigenvector', 'betweenness']:
        centrality_values = [centralities[metric_name].get(g, 0.0) for g in common_genes]
        essentiality_values = [mapped_essentiality.get(g, 0) for g in common_genes]
        
        rho, p_value = calculate_spearman_correlation(centrality_values, essentiality_values)
        
        results[metric_name] = {
            "rho": float(rho),
            "p_value": float(p_value),
            "sample_size": len(common_genes)
        }
        logger.info(f"{organism_id} - {metric_name}: rho={rho:.4f}, p={p_value:.4f}")

    return {
        "organism": organism_id,
        "status": "success",
        "mapping_coverage_percent": coverage,
        "correlations": results,
        "sample_size": len(common_genes)
    }

def main():
    """
    Main orchestration loop.
    Loads config, runs pipeline for each organism, saves results.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = load_config()
    organisms = get_organisms(config)
    results_dir = get_path(config, 'results_dir')
    ensure_dirs(results_dir)
    
    all_results = []
    
    for organism_id in organisms:
        result = run_pipeline_for_organism(organism_id, config)
        all_results.append(result)
    
    output_file = Path(results_dir) / "correlations.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Pipeline complete. Results saved to {output_file}")

if __name__ == "__main__":
    main()
