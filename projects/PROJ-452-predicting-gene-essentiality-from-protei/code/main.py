"""
main.py - Orchestration script for the gene essentiality prediction pipeline.

Coordinates data loading, network analysis, and statistical testing.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from code.config import load_config, get_organisms, get_path, ensure_dirs
from code.data_loader import load_essentiality_for_all_organisms, fetch_string_network, map_ids
from code.network_analysis import compute_all_centrality_metrics
from code.statistics import (
    calculate_spearman_correlation,
    generate_null_distribution_permutation,
    calculate_empirical_p_value,
    run_label_permutation_analysis,
    calculate_rewired_correlations,
    validate_graph_rewiring_model
)
from code.utils import setup_logging, compute_sha256

# Setup logging
logger = setup_logging(__name__)

def run_pipeline_for_organism(
    organism: str,
    config: Dict[str, Any],
    centrality_data: Dict[str, Dict[str, List[float]]],
    essentiality_data: Dict[str, Dict[str, int]]
) -> Dict[str, Any]:
    """
    Run the full analysis pipeline for a single organism.

    Args:
        organism: Organism identifier
        config: Configuration dictionary
        centrality_data: Pre-computed centrality data
        essentiality_data: Pre-loaded essentiality data

    Returns:
        Dictionary containing analysis results
    """
    logger.info(f"Starting pipeline for {organism}")
    
    results = {
        "organism": organism,
        "status": "success",
        "metrics": {}
    }

    # Get centrality and essentiality for this organism
    if organism not in centrality_data or organism not in essentiality_data:
        logger.warning(f"No data available for {organism}; skipping")
        results["status"] = "skipped"
        return results

    # Calculate correlations for each centrality metric
    for metric_name, centrality_vals in centrality_data[organism].items():
        essentiality_vals = essentiality_data[organism]
        
        # Filter to common genes
        common_genes = set(centrality_vals.keys()) & set(essentiality_vals.keys())
        
        if len(common_genes) < 2:
            logger.warning(f"Insufficient overlap for {organism}/{metric_name}; skipping")
            continue

        c_vals = [centrality_vals[g] for g in common_genes]
        e_vals = [essentiality_vals[g] for g in common_genes]

        corr, p_val = calculate_spearman_correlation(c_vals, e_vals)
        
        results["metrics"][metric_name] = {
            "spearman_rho": corr,
            "p_value": p_val,
            "sample_size": len(common_genes),
            "overlap_genes": list(common_genes)[:10]  # First 10 for reference
        }

        logger.info(f"{organism} - {metric_name}: rho={corr:.4f}, p={p_val:.4f}")

    # Run label permutation null model (T018a)
    n_permutations = config.get("null_model", {}).get("n_permutations", 1000)
    
    if organism in centrality_data and organism in essentiality_data:
        # Use degree centrality for permutation test
        if "degree_centrality" in centrality_data[organism]:
            centrality_vals = centrality_data[organism]["degree_centrality"]
            essentiality_vals = essentiality_data[organism]
            
            common_genes = set(centrality_vals.keys()) & set(essentiality_vals.keys())
            c_vals = [centrality_vals[g] for g in common_genes]
            e_vals = [essentiality_vals[g] for g in common_genes]

            # Generate null distribution
            null_dist = generate_null_distribution_permutation(
                c_vals, e_vals, n_permutations, seed=42
            )
            
            # Calculate empirical p-value for observed degree centrality
            if "degree_centrality" in results["metrics"]:
                observed_corr = results["metrics"]["degree_centrality"]["spearman_rho"]
                empirical_p = calculate_empirical_p_value(observed_corr, null_dist)
                
                results["metrics"]["degree_centrality"]["empirical_p_value"] = empirical_p
                results["metrics"]["degree_centrality"]["null_distribution_summary"] = {
                    "mean": float(np.mean(null_dist)),
                    "std": float(np.std(null_dist)),
                    "min": float(np.min(null_dist)),
                    "max": float(np.max(null_dist)),
                    "n_permutations": len(null_dist)
                }
                
                logger.info(f"{organism} - Degree centrality empirical p-value: {empirical_p:.4f}")

    return results

def main():
    """
    Main entry point: orchestrates the full pipeline.
    """
    logger.info("Starting gene essentiality prediction pipeline")
    
    # Load configuration
    config = load_config()
    organisms = get_organisms(config)
    results_dir = Path(get_path(config, "results"))
    ensure_dirs(results_dir)

    # Initialize data storage
    all_centrality_data = {}
    all_essentiality_data = {}

    # Load essentiality data for all organisms
    logger.info("Loading essentiality data...")
    essentiality_results = load_essentiality_for_all_organisms(organisms, config)
    for org, data in essentiality_results.items():
        all_essentiality_data[org] = data["labels"]

    # Load PPI networks and compute centralities
    logger.info("Loading networks and computing centralities...")
    for organism in organisms:
        logger.info(f"Processing {organism}...")
        
        # Fetch network
        network = fetch_string_network(organism, config)
        
        if network is None:
            logger.warning(f"Failed to load network for {organism}; skipping")
            continue

        # Map IDs
        mapped_network = map_ids(network, organism, config)
        
        if mapped_network is None:
            logger.warning(f"ID mapping failed for {organism}; skipping")
            continue

        # Compute centralities
        centrality_results = compute_all_centrality_metrics(mapped_network)
        all_centrality_data[organism] = centrality_results

    # Run analysis pipeline for each organism
    final_results = {}
    for organism in organisms:
        results = run_pipeline_for_organism(
            organism, config, all_centrality_data, all_essentiality_data
        )
        final_results[organism] = results

    # Save results to JSON
    output_file = results_dir / "correlations.json"
    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)

    logger.info(f"Results saved to {output_file}")
    
    # Update hash state
    from code.hash_checker import update_hash_state
    update_hash_state(config)

    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()
