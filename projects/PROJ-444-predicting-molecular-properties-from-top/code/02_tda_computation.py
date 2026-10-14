"""
TDA Computation Pipeline: Graph Construction and Shortest-Path Filtration.

Implements FR-001: Convert SMILES to molecular graphs and compute persistence diagrams
using shortest-path filtration, and FR-002: Vectorise each diagram to a 10×10
persistence image (σ=0.1) as the baseline required by the specification.
"""

import argparse
import logging
import sys
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
from rdkit import RDLogger

# Ensure project utils are importable
_code_dir = Path(__file__).parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

from utils.graph_builder import build_graph, validate_graph
from utils.persistence_utils import (
    build_shortest_path_filtration,
    compute_persistence_diagram,
    vectorize,
    handle_empty_diagram,
)

RDLogger.DisableLog('rdApp.*')

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger("tda_computation")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger

def setup_invalid_smiles_logger(log_file: str) -> logging.Logger:
    logger = logging.getLogger("invalid_smiles")
    logger.setLevel(logging.ERROR)
    if not logger.handlers:
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
    return logger

def process_molecule(
    smiles: str,
    molecule_id: str,
    logger: logging.Logger,
    invalid_logger: Optional[logging.Logger] = None,
    resolution: int = 10,
) -> Optional[Dict[str, Any]]:
    try:
        graph = build_graph(smiles)
        if graph is None or not validate_graph(graph):
            if invalid_logger:
                invalid_logger.error(f"Invalid SMILES: {smiles} | Error: Graph construction/validation failed")
            return None

        # 1. Shortest-path filtration (Distance Matrix)
        dist_matrix = build_shortest_path_filtration(graph)
        
        # 2. Compute persistence diagram
        diagram = compute_persistence_diagram(dist_matrix)

        # 3. Vectorize to persistence image (σ=0.1)
        image = vectorize(diagram, resolution=resolution, sigma=0.1)
        features = image.ravel()

        return {"molecule_id": molecule_id, "features": features}
    except Exception as exc:
        if invalid_logger:
            invalid_logger.error(f"Invalid SMILES: {smiles} | Error: {exc}")
        logger.error(f"Unhandled exception for {molecule_id}: {traceback.format_exc()}")
        return None

def generate_tda_features_csv(
    input_df: pd.DataFrame,
    output_path: Path,
    invalid_log_path: Path,
    resolution: int = 10,
) -> tuple[int, int]:
    logger = setup_logging()
    invalid_logger = setup_invalid_smiles_logger(str(invalid_log_path))

    logger.info(f"Generating persistence-image features (resolution={resolution}) for {len(input_df)} molecules...")

    records = []
    processed = 0
    failed = 0

    for idx, row in input_df.iterrows():
        smiles = row["smiles"]
        mol_id = row.get("molecule_id", f"mol_{idx}")

        result = process_molecule(smiles, mol_id, logger, invalid_logger, resolution=resolution)

        if result is None:
            failed += 1
            continue

        row_dict = {"molecule_id": result["molecule_id"]}
        for i, val in enumerate(result["features"]):
            row_dict[f"pixel_{i}"] = float(val)
        records.append(row_dict)
        processed += 1

        if processed % 500 == 0:
            logger.info(f"Processed {processed} molecules (failed: {failed})")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if records:
        out_df = pd.DataFrame(records)
        out_df.to_csv(output_path, index=False)
        logger.info(f"Wrote {len(out_df)} feature rows to {output_path}")
    else:
        header = ["molecule_id"] + [f"pixel_{i}" for i in range(resolution * resolution)]
        pd.DataFrame(columns=header).to_csv(output_path, index=False)
        logger.warning("No valid molecules processed; created empty CSV with header.")

    return processed, failed

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolution", type=int, default=10)
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    filtered_path = project_root / "data/processed/filtered_esol.csv"
    if not filtered_path.exists():
        print(f"Error: Expected filtered dataset at {filtered_path}")
        sys.exit(1)

    df = pd.read_csv(filtered_path)
    if "molecule_id" not in df.columns:
        df["molecule_id"] = df.index.astype(str)

    resolution = args.resolution
    output_csv = project_root / f"data/processed/persistence_images_{resolution}x{resolution}.csv"
    invalid_log = project_root / "data/logs/invalid_smiles.log"
    invalid_log.parent.mkdir(parents=True, exist_ok=True)

    start = time.time()
    proc_cnt, fail_cnt = generate_tda_features_csv(df, output_csv, invalid_log, resolution=resolution)
    elapsed = time.time() - start

    print(f"TDA feature generation completed in {elapsed:.2f}s – processed: {proc_cnt}, failed: {fail_cnt}")
    if proc_cnt == 0:
        sys.exit(1)

if __name__ == "__main__":
    main()