import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from code.config import load_config, get_organisms, get_path, ensure_dirs
from code.data_loader import load_local_network, load_local_essentiality, map_ids, save_essentiality_data
from code.network_analysis import process_organism_networks
from code.statistics import calculate_spearman_correlation
from code.utils import setup_logging

logger = logging.getLogger(__name__)

def run_pipeline_for_organism(organism_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the full analysis pipeline for a single organism.
    
    Args:
        organism_id: The organism identifier.
        config: Configuration dictionary.
        
    Returns:
        Dictionary containing pipeline results.
    """
    logger.info(f"Starting pipeline for organism: {organism_id}")
    
    try:
        # Load network data
        network_data = load_local_network(organism_id)
        if not network_data:
            logger.warning(f"No network data found for {organism_id}. Skipping.")
            return {'organism': organism_id, 'status': 'skipped', 'reason': 'No network data'}
        
        # Load essentiality labels
        essentiality_labels = load_local_essentiality(organism_id)
        if not essentiality_labels:
            logger.warning(f"No essentiality labels found for {organism_id}. Skipping.")
            return {'organism': organism_id, 'status': 'skipped', 'reason': 'No essentiality data'}
        
        # Prepare network data structure for processing
        networks_data = {
            'adjacency_list': network_data,
            'mapped_genes': set(network_data.keys())
        }
        
        # Process network analysis with error handling for disconnected networks
        # and missing gene overlaps
        result = process_organism_networks(
            organism_id=organism_id,
            networks_data=networks_data,
            essentiality_labels=essentiality_labels,
            config=config
        )
        
        logger.info(f"Pipeline completed for {organism_id}: {result['status']}")
        return result
        
    except Exception as e:
        logger.error(f"Pipeline failed for {organism_id}: {e}", exc_info=True)
        return {
            'organism': organism_id,
            'status': 'error',
            'error': str(e)
        }

def main():
    """
    Main entry point for the pipeline.
    Runs analysis for all configured organisms.
    """
    setup_logging()
    logger.info("Starting gene essentiality prediction pipeline.")
    
    config = load_config()
    organisms = get_organisms(config)
    results = []
    
    for organism_id in organisms:
        result = run_pipeline_for_organism(organism_id, config)
        results.append(result)
    
    # Save results
    output_dir = get_path(config, 'results', 'correlations')
    ensure_dirs(output_dir)
    output_file = os.path.join(output_dir, 'correlations.json')
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Pipeline completed. Results saved to {output_file}")
    return results

if __name__ == "__main__":
    main()
