"""
Data loading module for fetching real network data from SNAP.
Implements real data fetching with strict fail-loudly behavior.
"""
import os
import csv
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import urllib.request
import tarfile
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# SNAP dataset configuration - small, well-known datasets
SNAP_DATASETS = [
    {"id": "email-Enron", "url": "http://snap.stanford.edu/data/email-Enron.txt.gz"},
    {"id": "ca-Grqc", "url": "http://snap.stanford.edu/data/ca-Grqc.txt.gz"},
    {"id": "ca-HepTh", "url": "http://snap.stanford.edu/data/ca-HepTh.txt.gz"},
    {"id": "web-Eu", "url": "http://snap.stanford.edu/data/web-Eu.txt.gz"},
    {"id": "socfb-Reed98", "url": "http://snap.stanford.edu/data/socfb-Reed98.txt.gz"},
    {"id": "socfb-Princeton12", "url": "http://snap.stanford.edu/data/socfb-Princeton12.txt.gz"},
    {"id": "socfb-Yale12", "url": "http://snap.stanford.edu/data/socfb-Yale12.txt.gz"},
    {"id": "socfb-Stanford12", "url": "http://snap.stanford.edu/data/socfb-Stanford12.txt.gz"},
    {"id": "socfb-Berkeley12", "url": "http://snap.stanford.edu/data/socfb-Berkeley12.txt.gz"},
    {"id": "socfb-UCLA12", "url": "http://snap.stanford.edu/data/socfb-UCLA12.txt.gz"},
    {"id": "socfb-UCSB12", "url": "http://snap.stanford.edu/data/socfb-UCSB12.txt.gz"},
    {"id": "socfb-Cornell12", "url": "http://snap.stanford.edu/data/socfb-Cornell12.txt.gz"},
]

def get_snap_dataset_list() -> List[Dict[str, str]]:
    """
    Returns the list of SNAP datasets to fetch.
    
    Returns:
        List of dictionaries containing dataset id and URL
    """
    return SNAP_DATASETS.copy()

def fetch_snap_dataset(dataset_info: Dict[str, str], output_dir: Path) -> Optional[Path]:
    """
    Fetches a single SNAP dataset from the provided URL.
    
    Args:
        dataset_info: Dictionary with 'id' and 'url' keys
        output_dir: Directory to save the downloaded file
        
    Returns:
        Path to the downloaded file, or None if fetch failed
        
    Raises:
        RuntimeError: If fetch fails (fail-loudly behavior)
    """
    dataset_id = dataset_info['id']
    url = dataset_info['url']
    output_file = output_dir / f"{dataset_id}.txt.gz"
    
    logger.info(f"Fetching {dataset_id} from {url}")
    
    try:
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Download the file
        urllib.request.urlretrieve(url, output_file)
        
        if not output_file.exists():
            raise RuntimeError(f"Download failed: {output_file} does not exist")
        
        logger.info(f"Successfully downloaded {dataset_id}: {output_file.stat().st_size} bytes")
        return output_file
        
    except Exception as e:
        logger.error(f"Failed to fetch {dataset_id}: {str(e)}")
        raise RuntimeError(f"Failed to fetch dataset {dataset_id}: {str(e)}")

def load_snap_graph_from_edgelist(file_path: Path):
    """
    Loads a graph from an edgelist file (SNAP format).
    
    Args:
        file_path: Path to the edgelist file
        
    Returns:
        NetworkX graph object
        
    Note:
        This function is defined for API compatibility but actual graph
        loading is handled by src/topology.py which uses NetworkX directly.
    """
    import networkx as nx
    G = nx.read_edgelist(str(file_path), create_using=nx.Graph(), nodetype=int)
    return G

def generate_synthetic_graph(n_nodes: int, graph_type: str = "barabasi"):
    """
    Generates a synthetic graph for testing purposes.
    
    Args:
        n_nodes: Number of nodes
        graph_type: Type of graph ('barabasi', 'erdos_renyi', 'watts_strogatz')
        
    Returns:
        NetworkX graph object
        
    Note:
        This function is defined for API compatibility but is NOT used
        for actual data loading. Real data must come from SNAP.
    """
    import networkx as nx
    
    if graph_type == "barabasi":
        return nx.barabasi_albert_graph(n_nodes, 3)
    elif graph_type == "erdos_renyi":
        return nx.erdos_renyi_graph(n_nodes, 0.1)
    elif graph_type == "watts_strogatz":
        return nx.watts_strogatz_graph(n_nodes, 4, 0.1)
    else:
        raise ValueError(f"Unknown graph type: {graph_type}")

def load_real_data(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point for loading real data from SNAP.
    
    Fetches all configured datasets, saves them to data/raw/,
    and returns metadata about the fetch operation.
    
    Args:
        config_path: Optional path to config.yaml (not used in this implementation)
        
    Returns:
        Dictionary containing fetch results and metadata
        
    Raises:
        RuntimeError: If any dataset fetch fails
    """
    from config import get_paths
    
    paths = get_paths()
    raw_dir = paths['raw_data']
    log_dir = paths['logs']
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get dataset list
    datasets = get_snap_dataset_list()
    logger.info(f"Attempting to fetch {len(datasets)} datasets from SNAP")
    
    results = {
        'fetched': [],
        'failed': [],
        'total_count': 0
    }
    
    # Fetch each dataset
    for dataset_info in datasets:
        try:
            file_path = fetch_snap_dataset(dataset_info, raw_dir)
            if file_path:
                results['fetched'].append({
                    'id': dataset_info['id'],
                    'path': str(file_path),
                    'size_bytes': file_path.stat().st_size
                })
        except Exception as e:
            logger.error(f"Failed to fetch {dataset_info['id']}: {str(e)}")
            results['failed'].append({
                'id': dataset_info['id'],
                'error': str(e)
            })
            # Fail loudly - don't continue if any fetch fails
            raise RuntimeError(f"Dataset fetch failed for {dataset_info['id']}: {str(e)}")
    
    # Count files in data/raw/
    raw_files = list(raw_dir.glob("*.txt.gz"))
    results['total_count'] = len(raw_files)
    
    # Write fetch count to log
    fetch_count_log = log_dir / "fetch_count.log"
    with open(fetch_count_log, 'w') as f:
        f.write(f"Total files in data/raw/: {results['total_count']}\n")
        f.write(f"Successfully fetched: {len(results['fetched'])}\n")
        f.write(f"Failed: {len(results['failed'])}\n")
        f.write(f"Timestamp: {__import__('datetime').datetime.now().isoformat()}\n")
    
    logger.info(f"Fetch complete: {results['total_count']} files in data/raw/")
    logger.info(f"Fetch count logged to {fetch_count_log}")
    
    return results

def main():
    """
    Command-line entry point for data loading.
    """
    import sys
    import json
    
    try:
        results = load_real_data()
        print(json.dumps(results, indent=2))
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
