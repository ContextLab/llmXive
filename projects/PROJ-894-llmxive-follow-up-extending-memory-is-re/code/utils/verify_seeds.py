"""
Verify Noise Injection Reproducibility (Task T042 / T039)

This script verifies that the noise injection process is deterministic.
It performs the following steps:
1. Loads the raw graph data from data/intermediate/graphs_raw.json.
2. Runs the noise injection process twice with the same seed (42).
3. Computes the SHA-256 hash of the resulting JSON output for both runs.
4. Compares the hashes. If they match, reproducibility is confirmed.
5. Saves the verification result to data/audit/reproducibility_report.json.
6. Writes the verified noisy graph to data/processed/graphs/graph_noise_42.json
   to satisfy the pipeline's dependency requirements.

Note: This script assumes that data/intermediate/graphs_raw.json exists.
If it does not, it attempts to run the data_loader to generate it first,
or fails loudly if the real source is missing (per T035).
"""

import os
import json
import hashlib
import logging
import argparse
import sys
from pathlib import Path

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data_loader import load_graphs, inject_noise, save_noisy_graphs
from graph_utils import validate_graph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SEED = 42
NOISE_RATIO = 0.1
RAW_GRAPHS_PATH = project_root / "data" / "intermediate" / "graphs_raw.json"
NOISY_GRAPHS_OUTPUT = project_root / "data" / "processed" / "graphs" / "graph_noise_42.json"
AUDIT_DIR = project_root / "data" / "audit"
REPORT_PATH = AUDIT_DIR / "reproducibility_report.json"

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file's contents."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None

def run_noise_injection(graphs: dict, seed: int, noise_ratio: float) -> dict:
    """
    Apply noise injection to the provided graphs dictionary.
    Returns a new dictionary with the same keys but noisy graph values.
    """
    noisy_graphs = {}
    for task_id, graph_data in graphs.items():
        # graph_data is expected to be a list of edges or a dict representing the graph
        # Based on T011a-1 spec: values are lists of edges (dict: {"source":..., "target":..., "relation_string":...})
        # We need to reconstruct the graph to apply inject_noise if it expects an nx.Graph
        # However, T011b inject_noise expects a graph object.
        # Let's assume load_graphs returns a dict of task_id -> nx.DiGraph or similar structure
        # If it returns raw edges, we need to build the graph here.
        
        # Check if graph_data is already a networkx graph (unlikely if loaded from JSON)
        # The spec for T011a-1 says: "Convert extracted triples into JSON serialization... values are lists of edges"
        # So load_graphs likely returns a dict of lists of edges.
        
        # We need to reconstruct the graph to inject noise
        import networkx as nx
        G = nx.DiGraph()
        if isinstance(graph_data, list):
            for edge in graph_data:
                G.add_edge(edge['source'], edge['target'], relation=edge.get('relation_string', ''))
        elif isinstance(graph_data, dict):
            # If it's already a serialized graph dict, we might need to handle differently
            # But standard T011a-1 output is list of edges
            pass
        
        noisy_G = inject_noise(G, noise_ratio, seed)
        
        # Convert back to serializable format (list of edges)
        noisy_edges = []
        for u, v, data in noisy_G.edges(data=True):
            noisy_edges.append({
                'source': u,
                'target': v,
                'relation_string': data.get('relation_string', '')
            })
        noisy_graphs[task_id] = noisy_edges
        
    return noisy_graphs

def main():
    logger.info(f"Starting reproducibility verification for seed={SEED}")
    
    # Ensure output directories exist
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "processed" / "graphs").mkdir(parents=True, exist_ok=True)

    # Step 1: Load raw graphs
    if not RAW_GRAPHS_PATH.exists():
        logger.error(f"Raw graphs file not found at {RAW_GRAPHS_PATH}.")
        logger.error("Please run 'python code/data_loader.py --download --generate-graphs --seed 42' first.")
        sys.exit(1)

    graphs = load_graphs(RAW_GRAPHS_PATH)
    logger.info(f"Loaded {len(graphs)} graphs from {RAW_GRAPHS_PATH}")

    # Step 2: Run injection twice
    logger.info(f"Running noise injection (Run 1) with seed={SEED}...")
    noisy_graphs_run1 = run_noise_injection(graphs, SEED, NOISE_RATIO)
    
    # Serialize Run 1 to a temporary string to hash
    # We sort keys to ensure deterministic JSON serialization
    json_str_run1 = json.dumps(noisy_graphs_run1, sort_keys=True)
    hash_run1 = hashlib.sha256(json_str_run1.encode('utf-8')).hexdigest()
    logger.info(f"Run 1 Hash: {hash_run1}")

    logger.info(f"Running noise injection (Run 2) with seed={SEED}...")
    noisy_graphs_run2 = run_noise_injection(graphs, SEED, NOISE_RATIO)
    
    # Serialize Run 2
    json_str_run2 = json.dumps(noisy_graphs_run2, sort_keys=True)
    hash_run2 = hashlib.sha256(json_str_run2.encode('utf-8')).hexdigest()
    logger.info(f"Run 2 Hash: {hash_run2}")

    # Step 3: Compare
    is_reproducible = hash_run1 == hash_run2
    
    if is_reproducible:
        logger.info("SUCCESS: Noise injection is reproducible. Hashes match.")
        
        # Step 4: Save the verified graph to the expected location
        save_noisy_graphs(noisy_graphs_run1, NOISY_GRAPHS_OUTPUT)
        logger.info(f"Verified noisy graph saved to {NOISY_GRAPHS_OUTPUT}")
        
        # Step 5: Write report
        report = {
            "seed": SEED,
            "noise_ratio": NOISE_RATIO,
            "hash_run_1": hash_run1,
            "hash_run_2": hash_run2,
            "is_reproducible": True,
            "output_file": str(NOISY_GRAPHS_OUTPUT),
            "timestamp": str(Path(NOISY_GRAPHS_OUTPUT).stat().st_mtime)
        }
        with open(REPORT_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Reproducibility report saved to {REPORT_PATH}")
        
    else:
        logger.error("FAILURE: Noise injection is NOT reproducible. Hashes do not match.")
        logger.error("This indicates a non-deterministic element in the noise injection process.")
        report = {
            "seed": SEED,
            "noise_ratio": NOISE_RATIO,
            "hash_run_1": hash_run1,
            "hash_run_2": hash_run2,
            "is_reproducible": False,
            "output_file": None
        }
        with open(REPORT_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()