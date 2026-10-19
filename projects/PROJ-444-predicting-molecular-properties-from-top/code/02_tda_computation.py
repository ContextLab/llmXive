"""
02_tda_computation.py
Compute topological (persistence image) features for molecules in the filtered ESOL CSV.
Generates:
  - data/processed/tda_features.csv          (full feature matrix with JSON columns)
  - data/processed/persistence_images_10x10.csv (flattened pixel columns for baseline)
Logs invalid SMILES to data/logs/invalid_smiles.log.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd
import numpy as np
import networkx as nx
from rdkit import Chem
from rdkit.Chem import rdmolops

# Local utilities
from utils import persistence_utils as pu
from utils import graph_builder as gb


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


def process_molecule(row: pd.Series, resolution: int, logger: logging.Logger) -> Optional[dict]:
    """
    Process a single molecule: validate SMILES, compute persistence image,
    and return a dictionary with all required fields for CSV output.

    Returns None if the molecule cannot be processed.
    """
    smiles = row["smiles"]
    molecule_id = str(smiles)  # molecule_id must be a string per spec

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
    except MemoryError as me:
        gb.log_invalid_smiles(smiles, f"Memory error for shortest‑path matrix: {me}")
        return None
    except Exception as e:
        gb.log_invalid_smiles(smiles, f"Shortest‑path computation error: {e}")
        return None

    # Persistence diagram
    diagram = pu.compute_persistence_diagram(dist_matrix)

    # Vectorize with required bandwidth sigma=1.0
    image = pu.vectorize(diagram, resolution=resolution, sigma=1.0)

    # Flatten image to 1‑D list
    flat = image.ravel().tolist()

    # Feature names for flattened columns
    feature_names = [f"img_{resolution}_{i}" for i in range(resolution * resolution)]

    # Assemble result dict
    result = {
        "molecule_id": molecule_id,
        "target_property": "logP",
        "target_value": float(row["logP"]),
        "features": json.dumps(flat),
        "feature_names": json.dumps(feature_names),
    }
    # Add flattened pixel columns for the legacy CSV
    for idx, val in enumerate(flat):
        result[f"pixel_{idx}"] = val
    # Also add explicit img_* columns for the baseline CSV
    for idx, val in enumerate(flat):
        result[f"img_{resolution}_{idx}"] = val
    return result


def generate_tda_features(input_df: pd.DataFrame,
                          output_dir: Path,
                          resolution: int,
                          logger: logging.Logger) -> dict:
    """
    Iterate over ``input_df`` and write two CSV files:
      * tda_features.csv – contains JSON columns ``features`` and ``feature_names``.
      * persistence_images_{resolution}x{resolution}.csv – flattened pixel columns.

    Returns a summary dict with counts.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare output paths
    tda_path = output_dir / "tda_features.csv"
    pix_path = output_dir / f"persistence_images_{resolution}x{resolution}.csv"

    processed = 0
    failed = 0
    rows_tda = []
    rows_pix = []

    for _, row in input_df.iterrows():
        res = process_molecule(row, resolution, logger)
        if res is None:
            failed += 1
            continue
        processed += 1
        # Row for tda_features.csv (JSON columns + metadata)
        rows_tda.append({
            "molecule_id": res["molecule_id"],
            "target_property": res["target_property"],
            "target_value": res["target_value"],
            "features": res["features"],
            "feature_names": res["feature_names"],
        })
        # Row for pixel‑wise CSV
        pixel_row = {"molecule_id": res["molecule_id"]}
        for idx in range(resolution * resolution):
            pixel_row[f"img_{resolution}_{idx}"] = res[f"img_{resolution}_{idx}"]
        rows_pix.append(pixel_row)

    # Write the two files
    pd.DataFrame(rows_tda).to_csv(tda_path, index=False)
    pd.DataFrame(rows_pix).to_csv(pix_path, index=False)

    summary = {
        "processed": processed,
        "failed": failed,
        "tda_path": str(tda_path),
        "pixel_path": str(pix_path),
    }
    return summary


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


def main() -> None:
    args = _parse_cli_args()

    logger = setup_logging()
    # Ensure the invalid‑SMILES logger is ready
    gb.setup_invalid_smiles_logger(args.log)

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    df = pd.read_csv(input_path)
    if "smiles" not in df.columns or "logP" not in df.columns:
        logger.error("Input CSV must contain 'smiles' and 'logP' columns.")
        sys.exit(1)

    output_dir = Path("data/processed")
    summary = generate_tda_features(df, output_dir, resolution=args.grid, logger=logger)

    logger.info(
        f"TDA computation completed: {summary['processed']} processed, {summary['failed']} failed."
    )
    logger.info(f"TDA CSV written to {summary['tda_path']}")
    logger.info(f"Pixel CSV written to {summary['pixel_path']}")


if __name__ == "__main__":
    main()
