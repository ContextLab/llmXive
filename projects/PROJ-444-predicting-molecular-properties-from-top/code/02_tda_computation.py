"""
02_tda_computation.py
Compute baseline topological (persistence image) features for molecules in the filtered ESOL CSV.
Generates:
  - data/processed/topological_features_<grid>x<grid>.csv
    (columns: molecule_id (string), target_property, target_value, pixel_0 … pixel_{grid*grid-1})
Logs invalid SMILES to data/logs/invalid_smiles.log.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np
import networkx as nx
from rdkit import Chem

# Local utilities
from utils import persistence_utils as pu
from utils import graph_builder as gb

# ----------------------------------------------------------------------
# Logging utilities
# ----------------------------------------------------------------------
def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Configure a module‑level logger."""
    logger = logging.getLogger("tda_computation")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

# ----------------------------------------------------------------------
# Core molecular‑graph construction
# ----------------------------------------------------------------------
def build_molecular_graph(smiles: str) -> nx.Graph:
    """
    Convert a SMILES string into a NetworkX undirected graph where nodes are atom indices
    and edges correspond to chemical bonds.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("Invalid SMILES")
    # Ensure aromaticity/valence perception
    Chem.SanitizeMol(mol)

    G = nx.Graph()
    for atom in mol.GetAtoms():
        G.add_node(atom.GetIdx())
    for bond in mol.GetBonds():
        a1 = bond.GetBeginAtomIdx()
        a2 = bond.GetEndAtomIdx()
        G.add_edge(a1, a2)
    return G

# ----------------------------------------------------------------------
# Per‑molecule processing
# ----------------------------------------------------------------------
def process_molecule(row: pd.Series, resolution: int, logger: logging.Logger) -> Optional[dict]:
    """
    Process a single molecule:
      * validate SMILES,
      * compute persistence image,
      * return a dict ready for CSV output.

    The returned dict contains:
      - molecule_id (string)
      - target_property (string, always "logP")
      - target_value (float)
      - pixel_<i> columns for each flattened pixel (i = 0 … resolution*resolution‑1)
    """
    smiles = row["smiles"]
    molecule_id = str(smiles)  # ensure string per spec

    if not gb.is_valid_molecule(smiles):
        logger.info(f"Skipping invalid SMILES: {smiles}")
        return None

    try:
        G = build_molecular_graph(smiles)
    except Exception as e:
        gb.log_invalid_smiles(smiles, f"Graph construction failed: {e}")
        return None

    try:
        dist_matrix = gb.compute_shortest_path_matrix(G)
    except Exception as e:
        gb.log_invalid_smiles(smiles, f"Shortest‑path computation error: {e}")
        return None

    # Compute persistence diagram
    diagram = pu.compute_persistence_diagram(dist_matrix)

    # Vectorize diagram into a persistence image
    image = pu.vectorize(diagram, resolution=resolution, sigma=1.0)

    # Flatten image to 1‑D list
    flat = image.ravel().tolist()

    # Assemble result dict
    result = {
        "molecule_id": molecule_id,
        "target_property": "logP",
        "target_value": float(row["logP"]),
    }

    # Add pixel columns
    for idx, val in enumerate(flat):
        result[f"pixel_{idx}"] = float(val)

    return result

# ----------------------------------------------------------------------
# Batch feature generation
# ----------------------------------------------------------------------
def generate_tda_features(
    input_df: pd.DataFrame,
    output_dir: Path,
    resolution: int,
    logger: logging.Logger,
) -> dict:
    """
    Iterate over ``input_df`` and write a single CSV file:
      data/processed/topological_features_<resolution>x<resolution>.csv

    Returns a summary dict with processing counts and the path of the CSV.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Destination CSV path
    csv_path = output_dir / f"topological_features_{resolution}x{resolution}.csv"

    processed = 0
    failed = 0
    rows = []

    for _, row in input_df.iterrows():
        res = process_molecule(row, resolution, logger)
        if res is None:
            failed += 1
            continue
        processed += 1
        rows.append(res)

    # Write CSV
    df_out = pd.DataFrame(rows)
    # Ensure deterministic column order: molecule_id, target_property, target_value, then pixel_*
    pixel_cols = [c for c in df_out.columns if c.startswith("pixel_")]
    ordered_cols = ["molecule_id", "target_property", "target_value"] + sorted(pixel_cols, key=lambda x: int(x.split("_")[1]))
    df_out = df_out[ordered_cols]
    df_out.to_csv(csv_path, index=False)

    summary = {
        "processed": processed,
        "failed": failed,
        "output_path": str(csv_path),
    }
    return summary

# ----------------------------------------------------------------------
# CLI handling
# ----------------------------------------------------------------------
def _parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute TDA (persistence image) features.")
    parser.add_argument(
        "--grid",
        type=int,
        default=10,
        help="Resolution of the persistence image (grid size, e.g., 10 for 10x10).",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/filtered_esol.csv",
        help="Path to the filtered ESOL CSV.",
    )
    parser.add_argument(
        "--log",
        type=str,
        default="data/logs/invalid_smiles.log",
        help="Path to the invalid SMILES log file.",
    )
    return parser.parse_args()

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    args = _parse_cli_args()

    logger = setup_logging()
    # Ensure the invalid‑SMILES logger is ready (creates the log file if needed)
    gb.setup_invalid_smiles_logger(args.log)

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    df = pd.read_csv(input_path)
    required_cols = {"smiles", "logP"}
    if not required_cols.issubset(df.columns):
        logger.error(f"Input CSV must contain columns {required_cols}.")
        sys.exit(1)

    output_dir = Path("data/processed")
    summary = generate_tda_features(df, output_dir, resolution=args.grid, logger=logger)

    logger.info(
        f"TDA computation completed: {summary['processed']} processed, {summary['failed']} failed."
    )
    logger.info(f"TDA CSV written to {summary['output_path']}")

if __name__ == "__main__":
    main()