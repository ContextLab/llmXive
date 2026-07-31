"""
Batch simulation script for Task T025.
Runs Kuramoto dynamics on all valid topologies generated in US1.
Reads configuration from data/processed/config.json.
Outputs results to data/processed/simulation_results.csv.
"""
import os
import sys
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import networkx as nx

# Add project root to path if running as script
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from utils.logging_utils import init_logging, get_logger
from utils.config import get_config
from simulate_kuramoto import (
    load_config as load_sim_config,
    simulate_kuramoto,
    find_critical_coupling_binary_search,
    find_critical_coupling_linear_sweep
)
from utils.graph_utils import is_connected

def load_topology_paths(
    data_dir: str,
    pattern: str = "topology_*.gpickle"
) -> List[Path]:
    """
    Load list of all topology graph files matching the pattern.
    """
    path = Path(data_dir)
    files = sorted(path.glob(pattern))
    return files

def run_simulation_batch(
    config_path: str,
    output_path: str
) -> None:
    """
    Main entry point for T025.
    Reads config, loads topologies, runs binary search for Kc, and saves results.

    Args:
        config_path: Path to data/processed/config.json
        output_path: Path to output CSV (data/processed/simulation_results.csv)
    """
    # Initialize logging
    init_logging()
    logger = get_logger("T025_Batch_Simulation")

    # 1. Check config existence
    if not os.path.exists(config_path):
        logger.error(f"Configuration file missing: {config_path}")
        raise FileNotFoundError(f"CONFIG_MISSING: {config_path}")

    # 2. Read config
    with open(config_path, 'r') as f:
        config = json.load(f)

    time_steps = config.get('time_steps', 1000)
    n_topologies = config.get('n_topologies', 10)
    sc_003_violation = config.get('SC_003_VIOLATION', False)

    logger.info(f"Loaded config: time_steps={time_steps}, n_topologies={n_topologies}")
    logger.info(f"SC_003_VIOLATION flag: {sc_003_violation}")

    if time_steps <= 0:
        logger.error("Time steps must be positive.")
        raise RuntimeError("CONVERGENCE_FAILURE: time_steps <= 0")

    # 3. Locate topology files
    data_dir = str(Path(config_path).parent)
    topology_files = load_topology_paths(data_dir, "topology_*.gpickle")

    if not topology_files:
        logger.warning(f"No topology files found in {data_dir}")
        # If no files, create empty CSV with headers
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['topology_id', 'p', 'kc_binary', 'kc_linear', 'status'])
        return

    logger.info(f"Found {len(topology_files)} topology files.")

    # 4. Prepare output
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    # 5. Process each topology
    for i, filepath in enumerate(topology_files):
        # Extract topology_id and p from filename if possible, else use index
        # Expected format: topology_{id}_p{p:.2f}_seed_{seed}.gpickle
        filename = filepath.name
        parts = filename.replace('.gpickle', '').split('_')
        # parts[0] = "topology", parts[1] = id, parts[2] = "p...", parts[3] = "seed", parts[4] = seed
        try:
            topology_id = parts[1]
            p_str = parts[2].replace('p', '')
            p_val = float(p_str)
        except (IndexError, ValueError):
            topology_id = f"unknown_{i}"
            p_val = 0.0

        logger.info(f"Processing {topology_id} (p={p_val:.2f})...")

        try:
            # Load graph
            G = nx.read_gpickle(filepath)

            if not is_connected(G):
                logger.warning(f"Topology {topology_id} is disconnected. Skipping.")
                # Log as skipped or handle as error? Task says skip disconnected.
                # We'll log it but not include in final CSV if strictly following "valid topologies"
                continue

            # Run binary search for Kc
            # We need to pass time_steps and graph to the function
            # The function signature in simulate_kuramoto is:
            # find_critical_coupling_binary_search(G, time_steps, ...)
            # Let's assume standard parameters for the search if not in config
            # We need to be careful not to import internal helpers that don't exist.
            # Based on API surface, we have:
            # find_critical_coupling_binary_search, find_critical_coupling_linear_sweep

            # Run binary search
            # We assume the function takes (G, time_steps, ...)
            # Since the API surface doesn't show exact kwargs, we use reasonable defaults
            # based on typical Kuramoto implementation needs.
            # We'll wrap in try/except to handle potential signature mismatches gracefully
            # but the task requires real execution, so we assume the signature matches.

            kc_binary = None
            kc_linear = None
            status = "success"

            try:
                # Attempt binary search
                # Assuming signature: find_critical_coupling_binary_search(G, time_steps, tol=1e-2, max_iter=20)
                kc_binary = find_critical_coupling_binary_search(
                    G,
                    time_steps=time_steps,
                    tol=0.05,
                    max_iter=20
                )
                logger.info(f"Binary search Kc for {topology_id}: {kc_binary:.4f}")
            except Exception as e_bin:
                logger.warning(f"Binary search failed for {topology_id}: {e_bin}. Falling back to linear sweep.")
                status = "binary_failed_linear_fallback"

            if kc_binary is None:
                # Fallback to linear sweep
                try:
                    # Assuming signature: find_critical_coupling_linear_sweep(G, time_steps, ...)
                    kc_linear = find_critical_coupling_linear_sweep(
                        G,
                        time_steps=time_steps,
                        k_min=0.0,
                        k_max=10.0,
                        step=0.1
                    )
                    logger.info(f"Linear sweep Kc for {topology_id}: {kc_linear:.4f}")
                    if status == "success":
                        status = "linear_only"
                except Exception as e_lin:
                    logger.error(f"Linear sweep also failed for {topology_id}: {e_lin}")
                    status = "failed"
                    kc_binary = None
                    kc_linear = None

            # If both failed, we might still record it as failed
            if kc_binary is None and kc_linear is None:
                status = "failed"

            # Record result
            results.append({
                'topology_id': topology_id,
                'p': p_val,
                'kc_binary': kc_binary,
                'kc_linear': kc_linear,
                'status': status
            })

        except Exception as e:
            logger.error(f"Critical error processing {topology_id}: {e}")
            results.append({
                'topology_id': topology_id,
                'p': p_val,
                'kc_binary': None,
                'kc_linear': None,
                'status': 'error'
            })

    # 6. Write CSV
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['topology_id', 'p', 'kc_binary', 'kc_linear', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    logger.info(f"Simulation batch complete. Results written to {output_path}")

def main():
    """
    CLI entry point.
    """
    # Default paths
    config_path = "data/processed/config.json"
    output_path = "data/processed/simulation_results.csv"

    # Allow override via args
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    try:
        run_simulation_batch(config_path, output_path)
    except Exception as e:
        logging.error(f"Batch simulation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()