"""
Real-data loading module for network synchronization research.
Fetches networks from SNAP (Stanford Network Analysis Project) and handles
sample size constraints per FR-004 and task T005 requirements.
"""
import os
import csv
import logging
import random
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import networkx as nx
from datasets import load_dataset
from config import load_config, get_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Minimum samples for regression analysis (FR-004)
MIN_SAMPLES_FOR_REGRESSION = 10
TARGET_SAMPLE_SIZE = 30

def get_snap_dataset_list() -> List[Dict[str, Any]]:
    """
    Fetch the list of available SNAP datasets.
    Uses the 'snap_net' dataset from HuggingFace which mirrors SNAP.
    
    Returns:
        List of dicts with 'id', 'name', 'size', 'url' keys.
    """
    try:
        # Load the SNAP dataset metadata from HuggingFace
        # This dataset contains a list of network graphs available on SNAP
        ds = load_dataset("snap_net", split="train", streaming=True)
        
        datasets = []
        # Iterate through the first 50 entries to get a manageable list
        # In a full run, this would iterate all or use a specific filter
        count = 0
        for item in ds:
            if count >= 50:
                break
            
            # Construct the download URL for the edge list
            # SNAP datasets are typically in 'data/<name>.txt' format on their site
            # but HuggingFace 'snap_net' might have different structure.
            # We will construct the standard SNAP URL pattern for the edge list.
            dataset_id = item.get('id', '')
            dataset_name = item.get('name', dataset_id)
            
            # Standard SNAP URL pattern for edge lists
            url = f"https://snap.stanford.edu/data/{dataset_name}.txt.gz"
            
            datasets.append({
                'id': dataset_id,
                'name': dataset_name,
                'size': item.get('size', 0),
                'url': url,
                'hf_id': item.get('hf_id', '') # If available in the HF split
            })
            count += 1
        
        # Sort alphabetically by filename as per SC-003 (T017b requirement)
        datasets.sort(key=lambda x: x['name'].lower())
        
        logger.info(f"Retrieved {len(datasets)} SNAP datasets.")
        return datasets
        
    except Exception as e:
        logger.error(f"Failed to fetch SNAP dataset list: {e}")
        # Fallback to a hardcoded list of known small SNAP networks if HF fails
        # This ensures the pipeline can at least attempt to run if HF is down
        # but strictly speaking, we prefer the real fetch.
        logger.warning("Falling back to hardcoded known SNAP networks for testing.")
        known_networks = [
            {'id': 'email-Eu-core', 'name': 'email-Eu-core', 'size': 1005, 'url': 'https://snap.stanford.edu/data/email-Eu-core.txt'},
            {'id': 'ca-GrQc', 'name': 'ca-GrQc', 'size': 5242, 'url': 'https://snap.stanford.edu/data/ca-GrQc.txt'},
            {'id': 'ca-HepPh', 'name': 'ca-HepPh', 'size': 11204, 'url': 'https://snap.stanford.edu/data/ca-HepPh.txt'},
            {'id': 'soc-Epinions1', 'name': 'soc-Epinions1', 'size': 75879, 'url': 'https://snap.stanford.edu/data/soc-Epinions1.txt'},
            {'id': 'web-BerkStan', 'name': 'web-BerkStan', 'size': 685230, 'url': 'https://snap.stanford.edu/data/web-BerkStan.txt'},
            {'id': 'soc-Slashdot0811', 'name': 'soc-Slashdot0811', 'size': 821611, 'url': 'https://snap.stanford.edu/data/soc-Slashdot0811.txt'},
            {'id': 'soc-Slashdot0902', 'name': 'soc-Slashdot0902', 'size': 821611, 'url': 'https://snap.stanford.edu/data/soc-Slashdot0902.txt'},
            {'id': 'wiki-Vote', 'name': 'wiki-Vote', 'size': 7115, 'url': 'https://snap.stanford.edu/data/wiki-Vote.txt'},
            {'id': 'ca-AstroPh', 'name': 'ca-AstroPh', 'size': 18772, 'url': 'https://snap.stanford.edu/data/ca-AstroPh.txt'},
            {'id': 'ca-CondMat', 'name': 'ca-CondMat', 'size': 23133, 'url': 'https://snap.stanford.edu/data/ca-CondMat.txt'},
        ]
        known_networks.sort(key=lambda x: x['name'].lower())
        return known_networks

def load_snap_graph_from_edgelist(url: str, dataset_name: str) -> Optional[nx.Graph]:
    """
    Download and load a SNAP graph from a URL.
    
    Args:
        url: Direct URL to the edge list file.
        dataset_name: Name of the dataset for logging.
        
    Returns:
        NetworkX Graph or None if loading fails.
    """
    try:
        logger.info(f"Downloading {dataset_name} from {url}...")
        
        # Use networkx to read directly from URL (supports http/https)
        # SNAP files are typically simple edge lists, sometimes with headers
        G = nx.read_edgelist(
            url,
            create_using=nx.Graph,
            nodetype=int,
            data=(('weight', float),)
        )
        
        logger.info(f"Loaded graph {dataset_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
        
    except Exception as e:
        logger.error(f"Failed to load graph {dataset_name} from {url}: {e}")
        return None

def generate_synthetic_graph(n_nodes: int, target_edges: Optional[int] = None) -> nx.Graph:
    """
    Generate a synthetic graph to augment the dataset if real N < 30.
    Uses Barabási-Albert model to mimic scale-free properties of real networks.
    
    Args:
        n_nodes: Number of nodes to generate.
        target_edges: Optional target number of edges (m parameter in BA).
        
    Returns:
        NetworkX Graph.
    """
    if target_edges is None:
        target_edges = 3 # Standard for BA model
    
    logger.info(f"Generating synthetic Barabási-Albert graph with {n_nodes} nodes...")
    G = nx.barabasi_albert_graph(n_nodes, target_edges)
    logger.info(f"Synthetic graph generated: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G

def load_real_data() -> Tuple[List[nx.Graph], int, bool]:
    """
    Main entry point for loading real data.
    Implements the logic from T005:
    1. Fetch real data.
    2. If real N >= 30, proceed.
    3. If 10 <= real N < 30, generate synthetic data to reach N=30.
    4. If real N < 10, stop and warn (no synthetic data).
    
    Returns:
        Tuple of (list_of_graphs, final_count, skip_regression_flag)
        skip_regression_flag is True if N < 10.
    """
    config = load_config()
    paths = get_paths()
    
    # Get list of datasets
    datasets = get_snap_dataset_list()
    if not datasets:
        logger.error("No datasets available to load.")
        return [], 0, True
    
    graphs = []
    successful_loads = 0
    failed_loads = 0
    
    logger.info(f"Attempting to load {len(datasets)} networks...")
    
    for ds in datasets:
        G = load_snap_graph_from_edgelist(ds['url'], ds['name'])
        if G is not None and G.number_of_nodes() >= 2:
            graphs.append(G)
            successful_loads += 1
        else:
            failed_loads += 1
    
    real_n = len(graphs)
    logger.info(f"Successfully loaded {real_n} real networks. ({failed_loads} failed)")
    
    skip_regression = False
    
    if real_n >= TARGET_SAMPLE_SIZE:
        logger.info(f"Real data count ({real_n}) >= {TARGET_SAMPLE_SIZE}. Proceeding with full dataset.")
        return graphs, real_n, False
        
    elif real_n >= MIN_SAMPLES_FOR_REGRESSION:
        # 10 <= real N < 30
        needed = TARGET_SAMPLE_SIZE - real_n
        logger.warning(f"Real data count ({real_n}) is between {MIN_SAMPLES_FOR_REGRESSION} and {TARGET_SAMPLE_SIZE}.")
        logger.warning(f"Generating {needed} synthetic graphs to reach {TARGET_SAMPLE_SIZE}.")
        
        # Generate synthetic graphs
        synthetic_graphs = []
        for i in range(needed):
            # Vary size slightly to add diversity
            n_nodes = random.randint(50, 200)
            synth_G = generate_synthetic_graph(n_nodes)
            synthetic_graphs.append(synth_G)
        
        graphs.extend(synthetic_graphs)
        
        # Save synthetic fallback file as required by T005
        synthetic_path = paths['data'] / "synthetic_fallback_N30.csv"
        synthetic_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(synthetic_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'type', 'nodes', 'edges', 'source'])
            for i, G in enumerate(synthetic_graphs):
                writer.writerow([
                    f"synthetic_{i:03d}",
                    "BarabasiAlbert",
                    G.number_of_nodes(),
                    G.number_of_edges(),
                    "generated"
                ])
        
        logger.info(f"Saved synthetic fallback list to {synthetic_path}")
        return graphs, TARGET_SAMPLE_SIZE, False
        
    else:
        # real N < 10
        logger.warning(f"CRITICAL: Real data count ({real_n}) is below minimum threshold ({MIN_SAMPLES_FOR_REGRESSION}).")
        logger.warning("Per FR-004, regression analysis will be skipped.")
        logger.warning("No synthetic data will be generated for regression in this case.")
        skip_regression = True
        return graphs, real_n, True