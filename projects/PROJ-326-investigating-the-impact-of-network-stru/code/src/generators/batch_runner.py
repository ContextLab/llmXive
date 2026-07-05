"""
Batch generation script for producing per-topology-class batches of synthetic spin networks.

This script generates batches of graphs for Erdős-Rényi, Watts-Strogatz, and Barabási-Albert
topologies, utilizing the timeout utility for safety and the metadata module for logging.

Outputs:
  - data/raw/er_batch_{run_id}.json
  - data/raw/sw_batch_{run_id}.json
  - data/raw/sf_batch_{run_id}.json
  - data/metadata/graph_{id}.json (for each generated graph)
"""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import networkx as nx
import numpy as np

from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.generators.timeout import enforce_timeout, TimeoutError
from code.src.generators.metadata import save_graph_metadata, log_generation_batch
from code.src.utils.config import load_config, get_config_value, ensure_paths_exist
from code.src.utils.reproducibility import generate_run_id, ensure_data_directory
from code.src.utils.io import save_graph_gpickle
from code.src.utils.logging import log_run, log_metric

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration if not provided
DEFAULT_CONFIG = {
    'batch': {
        'er': {'n': 100, 'p': 0.05, 'count': 10},
        'sw': {'n': 100, 'k': 4, 'p': 0.1, 'count': 10},
        'sf': {'n': 100, 'm': 2, 'count': 10}
    },
    'timeout': 300,  # seconds
    'seed': None
}

def generate_batch(
    generator_class: Any,
    topology_type: str,
    params: Dict[str, Any],
    count: int,
    run_id: str,
    timeout_seconds: int,
    base_seed: Optional[int] = None
) -> List[str]:
    """
    Generate a batch of graphs using the specified generator.
    
    Args:
        generator_class: The generator class to use (ErdosRenyiGenerator, etc.)
        topology_type: String identifier for the topology type
        params: Parameters for the generator
        count: Number of graphs to generate
        run_id: Unique run identifier
        timeout_seconds: Timeout in seconds for each graph generation
        base_seed: Base random seed for reproducibility
        
    Returns:
        List of file paths for the generated graphs
    """
    logger.info(f"Starting batch generation for {topology_type}: {count} graphs")
    
    # Initialize generator
    generator = generator_class(**params)
    
    generated_files = []
    failed_count = 0
    
    for i in range(count):
        # Update seed for each graph if base_seed is provided
        if base_seed is not None:
            graph_seed = base_seed + i
            np.random.seed(graph_seed)
            if hasattr(generator, 'rng'):
                generator.rng = np.random.default_rng(graph_seed)
            else:
                generator.seed = graph_seed
        
        graph_start_time = time.time()
        
        try:
            # Enforce timeout for graph generation
            graph, metadata = enforce_timeout(
                generator.generate,
                timeout_seconds=timeout_seconds,
                fallback_value=(None, {"error": "timeout"})
            )
            
            if graph is None:
                logger.warning(f"Graph {i} generation failed or timed out")
                failed_count += 1
                continue
            
            # Generate unique graph ID
            graph_id = f"{topology_type}_{run_id}_{i:04d}"
            
            # Extract metrics
            from code.src.generators.metrics import extract_all_metrics
            metrics = extract_all_metrics(graph)
            metadata.update(metrics)
            
            # Save graph to file
            data_dir = ensure_data_directory('raw')
            graph_path = data_dir / f"{graph_id}.gpickle"
            save_graph_gpickle(graph, graph_path)
            
            # Save metadata
            metadata_path = save_graph_metadata(graph_id, metadata)
            
            # Log generation
            log_run({
                'graph_id': graph_id,
                'topology': topology_type,
                'path': str(graph_path),
                'seed': graph_seed if base_seed is not None else None,
                'generation_time': time.time() - graph_start_time,
                'metrics': metrics
            })
            
            generated_files.append(str(graph_path))
            logger.info(f"Generated {graph_id} in {time.time() - graph_start_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error generating graph {i}: {str(e)}", exc_info=True)
            failed_count += 1
            continue
    
    # Log batch summary
    log_generation_batch(
        topology_type=topology_type,
        run_id=run_id,
        total_requested=count,
        total_success=len(generated_files),
        total_failed=failed_count
    )
    
    logger.info(f"Batch generation complete for {topology_type}: {len(generated_files)}/{count} successful")
    return generated_files

def main():
    """Main entry point for batch generation."""
    parser = argparse.ArgumentParser(description='Generate batch of synthetic spin networks')
    parser.add_argument('--config', type=str, default='code/config.yaml',
                      help='Path to configuration file')
    parser.add_argument('--seed', type=int, default=None,
                      help='Random seed for reproducibility')
    parser.add_argument('--timeout', type=int, default=300,
                      help='Timeout in seconds for each graph generation')
    parser.add_argument('--topology', type=str, choices=['er', 'sw', 'sf', 'all'],
                      default='all', help='Topology type to generate')
    parser.add_argument('--count', type=int, default=None,
                      help='Number of graphs to generate per topology (overrides config)')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.warning(f"Could not load config from {args.config}: {str(e)}. Using defaults.")
        config = DEFAULT_CONFIG
    
    # Merge with command line arguments
    if args.seed is not None:
        config.setdefault('batch', {})['seed'] = args.seed
    if args.count is not None:
        for topology in ['er', 'sw', 'sf']:
            if topology in config.get('batch', {}):
                config['batch'][topology]['count'] = args.count
    
    # Ensure data directories exist
    ensure_paths_exist(config)
    
    # Generate run ID
    run_id = generate_run_id()
    logger.info(f"Starting batch generation with run_id: {run_id}")
    
    # Set global seed if provided
    if 'seed' in config.get('batch', {}) or args.seed is not None:
        seed = config.get('batch', {}).get('seed', args.seed)
        np.random.seed(seed)
        logger.info(f"Using global seed: {seed}")
    
    # Define generators and their parameters
    generators = {
        'er': {
            'class': ErdosRenyiGenerator,
            'params_key': 'er',
            'default_params': {'n': 100, 'p': 0.05}
        },
        'sw': {
            'class': WattsStrogatzGenerator,
            'params_key': 'sw',
            'default_params': {'n': 100, 'k': 4, 'p': 0.1}
        },
        'sf': {
            'class': BarabasiAlbertGenerator,
            'params_key': 'sf',
            'default_params': {'n': 100, 'm': 2}
        }
    }
    
    # Determine which topologies to generate
    topologies_to_generate = []
    if args.topology == 'all':
        topologies_to_generate = ['er', 'sw', 'sf']
    else:
        topologies_to_generate = [args.topology]
    
    # Generate batches
    all_generated_files = {}
    for topology in topologies_to_generate:
        if topology not in generators:
            logger.error(f"Unknown topology type: {topology}")
            continue
        
        gen_info = generators[topology]
        batch_config = config.get('batch', {}).get(gen_info['params_key'], {})
        
        # Merge default params with config params
        params = {**gen_info['default_params'], **batch_config}
        count = params.pop('count', 10)
        
        logger.info(f"Generating {count} {topology} graphs")
        
        files = generate_batch(
            generator_class=gen_info['class'],
            topology_type=topology,
            params=params,
            count=count,
            run_id=run_id,
            timeout_seconds=args.timeout,
            base_seed=config.get('batch', {}).get('seed', args.seed)
        )
        
        all_generated_files[topology] = files
    
    # Save manifest
    manifest = {
        'run_id': run_id,
        'timestamp': datetime.now().isoformat(),
        'config': config,
        'topologies': {
            topology: {
                'count': len(files),
                'files': files
            }
            for topology, files in all_generated_files.items()
        }
    }
    
    manifest_path = ensure_data_directory('raw') / f"batch_manifest_{run_id}.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Batch generation complete. Manifest saved to {manifest_path}")
    
    # Log final metrics
    total_graphs = sum(len(files) for files in all_generated_files.values())
    log_metric('total_graphs_generated', total_graphs)
    log_metric('run_id', run_id)
    
    return 0 if total_graphs > 0 else 1

if __name__ == '__main__':
    sys.exit(main())