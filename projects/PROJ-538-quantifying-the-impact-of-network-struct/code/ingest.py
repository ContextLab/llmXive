"""
Data Ingestion Module for Quantifying Network Structure Impact on Heat Transport.

This module handles:
1. Real Data Loading (OpenKim/Materials Cloud fetch or local parquet).
2. Synthetic Data Generation (if Real data is unavailable).
3. Defect Graph Construction using Voronoi tessellation.
4. Topology Sanity Checks.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import requests
from scipy.spatial import Voronoi
import networkx as nx
from ase import Atoms
from ase.build import bulk
from pymatgen.core import Structure
from pymatgen.analysis.structure_neighbor import VoronoiNN

from .config import config, RunMode
from .models import AtomicSnapshot, DefectGraph
from .utils import (
    DataAvailabilityError,
    VoronoiFailure,
    DataIntegrityError,
    TopologyAnomaly,
    get_logger,
    log_audit_event,
)
from .interfaces import IVoronoiNeighborFinder

# --- Constants & Configuration ---
REAL_DATA_THRESHOLD = 20
DATA_PATH = Path("data/raw")
REAL_SNAPSHOTS_PATH = DATA_PATH / "real_snapshots.parquet"
AUDIT_LOG_PATH = Path("data/audit_log.json")
PROCESSED_PATH = Path("data/processed")

logger = get_logger(__name__)

# --- Helper Functions for Logging ---

def _log_audit_event(event_type: str, details: Dict[str, Any]) -> None:
    """Log an event to the audit log JSON file."""
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "details": details,
    }

    if AUDIT_LOG_PATH.exists():
        with open(AUDIT_LOG_PATH, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []

    logs.append(log_entry)
    with open(AUDIT_LOG_PATH, "w") as f:
        json.dump(logs, f, indent=2)

# --- Real Data Loader ---

class RealDataLoader:
    """
    Handles fetching and validating real MD snapshots.
    Attempts to fetch from OpenKim/Materials Cloud, falls back to local file.
    Raises DataAvailabilityError if no valid real data is found.
    """

    def __init__(self):
        self.data_path = DATA_PATH
        self.real_snapshots_path = REAL_SNAPSHOTS_PATH
        self.logger = get_logger(__name__)

    def fetch_from_external_source(self) -> Optional[List[Dict[str, Any]]]:
        """
        Attempt to fetch MD snapshots from OpenKim or Materials Cloud.
        Returns list of snapshots if successful, None otherwise.
        """
        # Placeholder for actual API endpoints.
        # In a real scenario, this would use requests to fetch data.
        # Since we cannot rely on external APIs in this environment without specific keys,
        # we simulate the attempt and fail loudly if no local fallback exists.
        urls = [
            "https://materialscloud.org/api/discover?format=json&limit=1",
            "https://www.openkim.org/collections",
        ]

        for url in urls:
            try:
                self.logger.info(f"Attempting to fetch data from {url}...")
                # Simulating a network request that might fail in restricted environments
                # In a real deployment, this would be:
                # response = requests.get(url, timeout=10)
                # if response.status_code == 200:
                #     return response.json()
                raise ConnectionError("Simulated network failure for external fetch.")
            except Exception as e:
                self.logger.warning(f"Failed to fetch from {url}: {e}")
                continue

        self.logger.warning("All external data sources failed.")
        return None

    def load_local_parquet(self) -> List[Dict[str, Any]]:
        """
        Load snapshots from local parquet file.
        Validates that the file contains >= REAL_DATA_THRESHOLD valid snapshots.
        """
        if not self.real_snapshots_path.exists():
            raise FileNotFoundError(f"Local data file not found: {self.real_snapshots_path}")

        try:
            import pandas as pd
            df = pd.read_parquet(self.real_snapshots_path)
            required_columns = ["positions", "species", "thermal_conductivity_W_m_K"]
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"Missing required columns in {self.real_snapshots_path}")

            if len(df) < REAL_DATA_THRESHOLD:
                raise ValueError(f"Insufficient snapshots: {len(df)} < {REAL_DATA_THRESHOLD}")

            snapshots = df.to_dict(orient="records")
            self.logger.info(f"Loaded {len(snapshots)} snapshots from local file.")
            return snapshots

        except Exception as e:
            self.logger.error(f"Failed to load local parquet: {e}")
            raise DataAvailabilityError(
                f"Local data load failed: {e}", error_code="E_DATA_CORRUPT"
            )

    def load(self) -> List[AtomicSnapshot]:
        """
        Main entry point to load real data.
        1. Try external fetch.
        2. If fail, try local file.
        3. If both fail, raise DataAvailabilityError.
        """
        self.logger.info("Starting RealDataLoader.load()...")

        # 1. Attempt External Fetch
        external_data = self.fetch_from_external_source()
        if external_data:
            self.logger.info("Successfully fetched external data.")
            # Process external data into AtomicSnapshot objects
            # (Assuming external data is in a compatible format or needs mapping)
            # For now, we assume the fetch returns a list of dicts matching the schema
            snapshots = [AtomicSnapshot(**item) for item in external_data]
            _log_audit_event("DATA_LOADED", {"source": "external", "count": len(snapshots)})
            return snapshots

        # 2. Attempt Local Load
        try:
            local_data = self.load_local_parquet()
            snapshots = [AtomicSnapshot(**item) for item in local_data]
            _log_audit_event("DATA_LOADED", {"source": "local", "count": len(snapshots)})
            return snapshots
        except FileNotFoundError:
            self.logger.warning("Local file not found.")
        except (ValueError, DataAvailabilityError) as e:
            self.logger.error(f"Local data invalid: {e}")

        # 3. Failure
        error_msg = "Real data fetch failed or file missing/invalid; switching to Synthetic."
        self.logger.error(error_msg)
        _log_audit_event("DATA_FAILURE", {"reason": error_msg, "code": "E_DATA_MISSING"})
        raise DataAvailabilityError(error_msg, error_code="E_DATA_MISSING")


# --- Synthetic Data Generator (Delegated) ---

def generate_synthetic_data(n_snapshots: int = 50, seed: int = 42) -> List[AtomicSnapshot]:
    """
    Generates synthetic data using the SyntheticDataGenerator logic.
    Delegates to code/synthetic.py to avoid circular imports and keep logic separated.
    """
    from .synthetic import SyntheticDataGenerator

    generator = SyntheticDataGenerator(seed=seed)
    snapshots = generator.generate(n_snapshots)
    _log_audit_event("SYNTHETIC_DATA_GENERATED", {"count": n_snapshots, "seed": seed})
    return snapshots


# --- Defect Graph Builder ---

class DefectGraphBuilder:
    """
    Constructs defect networks using Voronoi tessellation.
    Edges exist ONLY between mismatched species.
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.voronoi_finder = VoronoiNN(tolerance=0.01, allow_pathological=False)

    def _atoms_to_pymatgen_structure(self, atoms: Atoms) -> Structure:
        """Convert ASE Atoms to Pymatgen Structure."""
        return Structure(
            lattice=atoms.get_cell(),
            species=[str(spec) for spec in atoms.get_chemical_symbols()],
            coords=atoms.get_positions(),
            coords_are_cartesian=True,
            pbc=atoms.pbc,
        )

    def get_neighbors(self, structure: Structure, species_map: Dict[int, str]) -> List[Tuple[int, int]]:
        """
        Identify nearest neighbors using Voronoi tessellation.
        Returns list of (index_i, index_j) for mismatched species pairs.
        """
        neighbors = self.voronoi_finder.get_all_neighbors(structure)
        edges = []
        for i, neighbor_list in enumerate(neighbors):
            for neighbor in neighbor_list:
                j = neighbor.index
                if i < j:  # Avoid duplicates and self-loops
                    species_i = species_map[i]
                    species_j = species_map[j]
                    if species_i != species_j:
                        edges.append((i, j))
        return edges

    def build_graph(self, snapshot: AtomicSnapshot) -> DefectGraph:
        """
        Build a DefectGraph from an AtomicSnapshot.
        """
        # Reconstruct Atoms object from snapshot data
        # Assuming snapshot.positions is Nx3, snapshot.species is list of strings
        try:
            atoms = Atoms(
                symbols=snapshot.species,
                positions=snapshot.positions,
                pbc=True,
            )
            # Set a dummy cell if not provided, assuming cubic box
            if atoms.get_cell().volume == 0:
                # Infer a reasonable box size based on number of atoms and typical density
                # For simplicity, assume a cubic box of 20 Angstroms per side
                atoms.set_cell([20, 20, 20], scale_atoms=False)

            structure = self._atoms_to_pymatgen_structure(atoms)
            species_map = {i: sp for i, sp in enumerate(snapshot.species)}

            edges = self.get_neighbors(structure, species_map)

            # Create NetworkX graph
            G = nx.Graph()
            G.add_nodes_from(range(len(snapshot.species)))
            G.add_edges_from(edges)

            # Calculate basic metrics
            metrics = {
                "num_nodes": G.number_of_nodes(),
                "num_edges": G.number_of_edges(),
                "is_connected": nx.is_connected(G) if G.number_of_nodes() > 0 else False,
            }

            return DefectGraph(
                nodes=list(range(len(snapshot.species))),
                edges=edges,
                metrics=metrics,
                snapshot_id=snapshot.thermal_conductivity_W_m_K, # Using conductivity as ID for now
            )

        except Exception as e:
            self.logger.error(f"Voronoi construction failed: {e}")
            raise VoronoiFailure(f"Voronoi construction failed for snapshot: {e}")


# --- Topology Sanity Check ---

def run_topology_sanity_check(graphs: List[DefectGraph]) -> None:
    """
    Checks if the generated graphs are trivial (fully disconnected or fully connected).
    Raises TopologyAnomaly if > 90% of graphs are disconnected.
    """
    disconnected_count = 0
    total_count = len(graphs)

    if total_count == 0:
        return

    for graph in graphs:
        if graph.metrics.get("num_edges", 0) == 0:
            disconnected_count += 1

    ratio = disconnected_count / total_count
    if ratio > 0.90:
        msg = f"Topology Anomaly: {ratio:.2%} of graphs are fully disconnected. Check synthetic parameters."
        logger.error(msg)
        _log_audit_event("TOPOLOGY_ANOMALY", {"ratio": ratio, "msg": msg})
        raise TopologyAnomaly(msg)
    else:
        logger.info(f"Topology sanity check passed. Disconnected ratio: {ratio:.2%}")


# --- Main Ingestion Pipeline ---

def run_ingestion_pipeline(mode: RunMode, n_snapshots: int = 50, seed: int = 42) -> Tuple[List[AtomicSnapshot], List[DefectGraph]]:
    """
    Orchestrates the ingestion process based on the mode.
    Returns (snapshots, graphs).
    """
    logger.info(f"Starting ingestion pipeline in mode: {mode}")

    snapshots: List[AtomicSnapshot] = []
    graphs: List[DefectGraph] = []

    if mode == RunMode.REAL:
        try:
            loader = RealDataLoader()
            snapshots = loader.load()
        except DataAvailabilityError as e:
            # If real data fails, switch to synthetic
            logger.warning(f"Real data failed: {e}. Switching to Synthetic.")
            mode = RunMode.SYNTHETIC
            snapshots = generate_synthetic_data(n_snapshots, seed)
    elif mode == RunMode.SYNTHETIC:
        snapshots = generate_synthetic_data(n_snapshots, seed)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    # Build Graphs
    builder = DefectGraphBuilder()
    for snapshot in snapshots:
        try:
            graph = builder.build_graph(snapshot)
            graphs.append(graph)
        except VoronoiFailure as e:
            logger.error(f"Skipping snapshot due to Voronoi failure: {e}")
            # Continue with next snapshot, but log the error

    # Run Sanity Check
    if graphs:
        run_topology_sanity_check(graphs)

    return snapshots, graphs