import os
import csv
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import urllib.request
import urllib.error
import ssl
import tarfile
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SNAP_WEB_CATEGORY_URL = "https://snap.stanford.edu/data/web-Slashdot0902.txt.gz" 
# Note: SNAP web category is often large. We will fetch a specific, smaller, representative web graph.
# Using the 'web-BerkStan' dataset as a verified, accessible real source for the 'web' category.
# This is a real dataset from SNAP: http://snap.stanford.edu/data/web-BerkStan.html
SNAP_WEB_DATASETS = [
    {"name": "web-BerkStan", "url": "http://snap.stanford.edu/data/web-BerkStan.txt.gz", "id": "snap_web_berkstan"},
    {"name": "web-Google", "url": "http://snap.stanford.edu/data/web-Google.txt.gz", "id": "snap_web_google"},
]

# Network Repository datasets (subset of web category)
# Using 'web-ND' (Network Data) as a representative example.
# Note: Direct download links for Network Repository can be unstable. 
# We will use a known stable URL for a small web graph if possible, or fallback to a verified SNAP list.
# For robustness, we focus on the SNAP list as the primary "real" source for this task.
NR_WEB_DATASETS = [
    {"name": "web-ND", "url": "https://nrv.cc/nd/data/web-ND.txt", "id": "nr_web_nd"}, # Hypothetical stable URL, might fail
]

def get_snap_dataset_list() -> List[Dict[str, Any]]:
    """
    Returns a list of SNAP web category datasets to fetch.
    """
    return SNAP_WEB_DATASETS

def fetch_snap_dataset(dataset_info: Dict[str, Any], output_dir: Path) -> bool:
    """
    Fetches a single dataset from the provided URL.
    Returns True if successful, False otherwise.
    """
    name = dataset_info["name"]
    url = dataset_info["url"]
    dataset_id = dataset_info["id"]
    output_path = output_dir / f"{name}.txt.gz"
    
    logger.info(f"Fetching {name} from {url}...")
    
    # Create SSL context to handle potential SSL errors
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        # Use urllib with custom SSL context
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ssl_context, timeout=60) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        
        logger.info(f"Successfully downloaded {name} to {output_path}")
        return True
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error fetching {name}: {e.code} {e.reason}")
        return False
    except urllib.error.URLError as e:
        logger.error(f"URL Error fetching {name}: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error fetching {name}: {e}")
        return False

def convert_to_mtx(gz_path: Path, output_dir: Path) -> Optional[Path]:
    """
    Decompresses a .txt.gz file and converts it to .mtx format if necessary.
    For SNAP web graphs (edge list format), we will keep them as .txt or convert to .mtx if strictly required.
    The task asks for .mtx files. We will convert the edge list to Matrix Market format.
    """
    if not gz_path.exists():
        logger.error(f"File not found: {gz_path}")
        return None

    base_name = gz_path.stem # Removes .gz
    if base_name.endswith('.txt'):
        base_name = base_name[:-4] # Removes .txt
    
    txt_path = output_dir / f"{base_name}.txt"
    mtx_path = output_dir / f"{base_name}.mtx"

    try:
        # Decompress
        with gzip.open(gz_path, 'rt') as f_in:
            with open(txt_path, 'w') as f_out:
                f_out.write(f_in.read())
        
        logger.info(f"Decompressed {gz_path} to {txt_path}")

        # Convert to Matrix Market format (.mtx)
        # SNAP web graphs are typically in format: source destination (1-based or 0-based)
        # We will assume 1-based for Matrix Market format unless detected otherwise.
        # Matrix Market Header:
        # %%MatrixMarket matrix coordinate pattern general
        
        nodes = set()
        edges = []
        
        with open(txt_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        u, v = int(parts[0]), int(parts[1])
                        nodes.add(u)
                        nodes.add(v)
                        edges.append((u, v))
                    except ValueError:
                        continue
        
        if not edges:
            logger.warning(f"No edges found in {txt_path}")
            return None

        sorted_nodes = sorted(list(nodes))
        node_map = {n: i+1 for i, n in enumerate(sorted_nodes)} # Map to 1-based index
        
        with open(mtx_path, 'w') as f:
            f.write("%%MatrixMarket matrix coordinate pattern general\n")
            f.write(f"{len(sorted_nodes)} {len(sorted_nodes)} {len(edges)}\n")
            for u, v in edges:
                f.write(f"{node_map[u]} {node_map[v]}\n")
        
        logger.info(f"Converted {txt_path} to {mtx_path}")
        
        # Cleanup intermediate txt file
        txt_path.unlink()
        
        return mtx_path

    except Exception as e:
        logger.error(f"Error converting {gz_path}: {e}")
        return None

def load_snap_graph_from_edgelist(file_path: Path) -> Optional[Any]:
    """
    Loads a graph from an edgelist file (text or mtx).
    Returns a NetworkX graph.
    """
    import networkx as nx
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    try:
        if file_path.suffix == '.mtx':
            G = nx.read_matrix_market(str(file_path))
        elif file_path.suffix == '.txt':
            # SNAP format: source destination
            G = nx.read_edgelist(str(file_path), nodetype=int)
        else:
            # Try reading as edgelist regardless of extension
            G = nx.read_edgelist(str(file_path), nodetype=int)
        
        return G
    except Exception as e:
        logger.error(f"Error loading graph from {file_path}: {e}")
        return None

def generate_synthetic_graph(n_nodes: int = 100) -> Any:
    """
    Generates a synthetic graph (Barabasi-Albert) for testing ONLY.
    This function is NOT used in the main data loading pipeline per task constraints.
    """
    import networkx as nx
    return nx.barabasi_albert_graph(n_nodes, m=2)

def load_real_data(raw_dir: Path, min_count: int = 10) -> bool:
    """
    Main entry point for loading real data.
    Fetches datasets, converts them, and records the count.
    Returns True if count >= min_count, False otherwise.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    fetch_count = 0
    datasets = get_snap_dataset_list()
    
    for ds in datasets:
        if fetch_snap_dataset(ds, raw_dir):
            # Try to convert to mtx
            gz_files = list(raw_dir.glob(f"{ds['name']}.txt.gz"))
            if gz_files:
                convert_to_mtx(gz_files[0], raw_dir)
            fetch_count += 1
        else:
            logger.warning(f"Failed to fetch {ds['name']}")
    
    # Log fetch count
    log_path = logs_dir / "fetch_count.log"
    with open(log_path, 'w') as f:
        f.write(f"Total files fetched: {fetch_count}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
    
    logger.info(f"Fetch complete. Total files: {fetch_count}")
    return fetch_count >= min_count

def main():
    """
    Entry point for the loader script.
    """
    import datetime
    raw_dir = Path("data/raw")
    result = load_real_data(raw_dir)
    if result:
        logger.info("Data availability check passed (>= 10 files).")
    else:
        logger.warning("Data availability check failed (< 10 files).")

if __name__ == "__main__":
    main()
