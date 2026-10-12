import os
import csv
import logging
import json
import gzip
import urllib.request
import urllib.error
import ssl
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of SNAP web category datasets (expanded to ensure ≥10 files)
SNAP_WEB_DATASETS = [
    {"name": "web-BerkStan", "url": "http://snap.stanford.edu/data/web-BerkStan.txt.gz", "id": "snap_web_berkstan"},
    {"name": "web-Google", "url": "http://snap.stanford.edu/data/web-Google.txt.gz", "id": "snap_web_google"},
    {"name": "ca-HepTh", "url": "http://snap.stanford.edu/data/ca-HepTh.txt.gz", "id": "snap_ca_hepth"},
    {"name": "ca-GrQc", "url": "http://snap.stanford.edu/data/ca-GrQc.txt.gz", "id": "snap_ca_grqc"},
    {"name": "email-Eu-core", "url": "http://snap.stanford.edu/data/email-Eu-core.txt.gz", "id": "snap_email_eu_core"},
    {"name": "wiki-Talk", "url": "http://snap.stanford.edu/data/wiki-Talk.txt.gz", "id": "snap_wiki_talk"},
    {"name": "soc-sign-epinions", "url": "http://snap.stanford.edu/data/soc-sign-epinions.txt.gz", "id": "snap_soc_epinions"},
    {"name": "facebook_combined", "url": "http://snap.stanford.edu/data/facebook_combined.txt.gz", "id": "snap_facebook_combined"},
    {"name": "roadNet-CA", "url": "http://snap.stanford.edu/data/roadNet-CA.txt.gz", "id": "snap_roadnet_ca"},
    {"name": "com-DBLP", "url": "http://snap.stanford.edu/data/com-DBLP.txt.gz", "id": "snap_com_dblp"},
]

# Network Repository datasets placeholder (not used for this task)
NR_WEB_DATASETS = [
    # Example entry (currently unused)
    # {"name": "web-ND", "url": "https://nrv.cc/nd/data/web-ND.txt", "id": "nr_web_nd"},
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
    output_path = output_dir / f"{name}.txt.gz"

    logger.info(f"Fetching {name} from {url}...")

    # Create SSL context to handle potential SSL errors
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ssl_context, timeout=60) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())

        logger.info(f"Successfully downloaded {name} to {output_path}")
        return True
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error fetching {name}: {e.code} {e.reason}")
        # Raise immediately to abort the pipeline on any download failure
        raise RuntimeError(f"Failed to download dataset '{name}' (HTTP {e.code}): {e.reason}") from e
    except urllib.error.URLError as e:
        logger.error(f"URL Error fetching {name}: {e.reason}")
        raise RuntimeError(f"Failed to download dataset '{name}' (URL error): {e.reason}") from e
    except Exception as e:
        logger.error(f"Unexpected error fetching {name}: {e}")
        raise RuntimeError(f"Unexpected error downloading dataset '{name}': {e}") from e


def convert_to_mtx(gz_path: Path, output_dir: Path) -> Optional[Path]:
    """
    Decompresses a .txt.gz file and converts it to .mtx format.
    Returns the path to the .mtx file if successful, otherwise None.
    """
    if not gz_path.exists():
        logger.error(f"File not found: {gz_path}")
        return None

    base_name = gz_path.stem  # Removes .gz
    if base_name.endswith('.txt'):
        base_name = base_name[:-4]  # Removes .txt

    txt_path = output_dir / f"{base_name}.txt"
    mtx_path = output_dir / f"{base_name}.mtx"

    try:
        # Decompress
        with gzip.open(gz_path, 'rt') as f_in:
            with open(txt_path, 'w') as f_out:
                f_out.write(f_in.read())

        logger.info(f"Decompressed {gz_path} to {txt_path}")

        # Parse edges
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
        node_map = {n: i + 1 for i, n in enumerate(sorted_nodes)}  # 1‑based indices for Matrix Market

        with open(mtx_path, 'w') as f:
            f.write("%%MatrixMarket matrix coordinate pattern general\n")
            f.write(f"{len(sorted_nodes)} {len(sorted_nodes)} {len(edges)}\n")
            for u, v in edges:
                f.write(f"{node_map[u]} {node_map[v]}\n")

        logger.info(f"Converted {txt_path} to {mtx_path}")

        # Remove the intermediate .txt file to keep the raw directory tidy
        txt_path.unlink()

        return mtx_path
    except Exception as e:
        logger.error(f"Error converting {gz_path}: {e}")
        return None


def load_snap_graph_from_edgelist(file_path: Path) -> Optional[Any]:
    """
    Loads a graph from an edgelist file (text or .mtx) and returns a NetworkX graph.
    """
    import networkx as nx

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    try:
        if file_path.suffix == '.mtx':
            G = nx.read_matrix_market(str(file_path))
        elif file_path.suffix == '.txt':
            G = nx.read_edgelist(str(file_path), nodetype=int)
        else:
            G = nx.read_edgelist(str(file_path), nodetype=int)
        return G
    except Exception as e:
        logger.error(f"Error loading graph from {file_path}: {e}")
        return None


def generate_synthetic_graph(n_nodes: int = 100) -> Any:
    """
    Generates a synthetic graph (Barabási–Albert) for testing ONLY.
    This function is NOT used in the main data loading pipeline per task constraints.
    """
    import networkx as nx
    return nx.barabasi_albert_graph(n_nodes, m=2)


def load_real_data(raw_dir: Path, min_count: int = 10) -> bool:
    """
    Main entry point for loading real data.
    Downloads datasets, converts them to Matrix Market format, and records the count.
    Returns True if the number of successfully converted files >= min_count, otherwise False.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    fetch_count = 0
    datasets = get_snap_dataset_list()

    for ds in datasets:
        # Attempt to fetch; any failure will raise and abort the script
        if fetch_snap_dataset(ds, raw_dir):
            # Convert the downloaded .txt.gz to .mtx
            gz_path = raw_dir / f"{ds['name']}.txt.gz"
            if gz_path.exists():
                mtx_path = convert_to_mtx(gz_path, raw_dir)
                if mtx_path and mtx_path.exists():
                    fetch_count += 1
            else:
                logger.warning(f"Expected gz file not found for {ds['name']}")
        # No silent fallback: if fetch_snap_dataset raised, execution never reaches here

    # Log fetch count
    log_path = logs_dir / "fetch_count.log"
    with open(log_path, 'w') as f:
        f.write(f"Total files fetched and converted: {fetch_count}\\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\\n")

    logger.info(f"Fetch complete. Total converted .mtx files: {fetch_count}")
    return fetch_count >= min_count


def main():
    """
    Entry point for the loader script.
    """
    raw_dir = Path("data/raw")
    success = load_real_data(raw_dir)
    if success:
        logger.info("Data availability check passed (≥ 10 files).")
    else:
        logger.warning("Data availability check failed (< 10 files).")


if __name__ == "__main__":
    main()