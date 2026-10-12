"""
TDA Computation Pipeline: Graph Construction and Shortest-Path Filtration.

Implements FR-001: Convert SMILES to molecular graphs and compute persistence diagrams
using shortest-path filtration, and FR-002: Vectorise each diagram to a 10×10
persistence image (σ = 0.1) as the baseline required by the specification.

This script is now CLI‑compatible with the quickstart run‑book. It accepts an
optional ``--resolution`` argument (default 10) and writes the resulting feature
matrix to ``data/processed/persistence_images_<resolution>x<resolution>.csv``.
Invalid SMILES are logged to ``data/logs/invalid_smiles.log``.

Dependencies:
- rdkit
- networkx (added to ``requirements.txt``)
- pandas, numpy
- project utilities in ``code/utils``.
"""

import argparse
import json
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

from utils.graph_builder import build_graph, validate_graph, Graph
from utils.persistence_utils import (
    compute_shortest_path_matrix,
    build_shortest_path_filtration,
    compute_persistence_diagram,
    vectorize,
    handle_empty_diagram,
)

# Suppress RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')


def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Configure logging for the TDA computation pipeline."""
    logger = logging.getLogger("tda_computation")
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers if the logger is reused
    if not logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def setup_invalid_smiles_logger(log_file: str) -> logging.Logger:
    """Setup a dedicated logger for invalid SMILES entries."""
    logger = logging.getLogger("invalid_smiles")
    logger.setLevel(logging.ERROR)

    if not logger.handlers:
        handler = logging.FileHandler(log_file)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)

    return logger


def log_invalid_smiles(logger: logging.Logger, smiles: str, error: str) -> None:
    """Log an invalid SMILES entry to the dedicated logger."""
    logger.error(f"Invalid SMILES: {smiles} | Error: {error}")


def vectorize_diagram_to_image(
    diagram: List[tuple],
    resolution: int = 10,
) -> np.ndarray:
    """
    Vectorise a persistence diagram into a persistence image.

    Args:
        diagram: List of (birth, death) tuples.
        resolution: Grid resolution (e.g., 10 for 10×10).

    Returns:
        np.ndarray of shape (resolution, resolution).
    """
    if not diagram:
        return handle_empty_diagram(resolution)

    try:
        # Ensure diagram is a list of (birth, death) pairs
        arr = np.array(diagram, dtype=float)
        if arr.shape[1] != 2:
            return handle_empty_diagram(resolution)
    except Exception:
        return handle_empty_diagram(resolution)

    # The utility expects (birth, death) ordering
    return vectorize(list(map(tuple, arr.tolist())), resolution)


def flatten_image(image: np.ndarray) -> np.ndarray:
    """Flatten a 2‑D image to a 1‑D vector."""
    return image.ravel()


def compute_persistence_features(
    diagram: List[tuple],
    resolution: int,
) -> np.ndarray:
    """
    Compute a single persistence image for the given resolution and flatten it.

    Returns:
        1‑D numpy array of length ``resolution * resolution``.
    """
    img = vectorize_diagram_to_image(diagram, resolution=resolution)
    return flatten_image(img)


def process_molecule(
    smiles: str,
    molecule_id: str,
    logger: logging.Logger,
    invalid_logger: Optional[logging.Logger] = None,
    resolution: int = 10,
) -> Optional[Dict[str, Any]]:
    """
    Process a single molecule:
    1. Build a NetworkX graph from the SMILES.
    2. Compute the shortest‑path distance matrix.
    3. Build the filtration.
    4. Compute the persistence diagram.
    5. Vectorise to a persistence image of the requested resolution.

    Returns a dictionary with ``molecule_id`` and ``features`` (the flattened
    image) or ``None`` if any step fails.
    """
    try:
        # 1. Build Graph
        graph = build_graph(smiles)
        if graph is None:
            if invalid_logger:
                log_invalid_smiles(invalid_logger, smiles, "Graph construction failed")
            logger.warning(f"Graph construction failed for {molecule_id}")
            return None

        # 2. Validate Graph
        if not validate_graph(graph):
            if invalid_logger:
                log_invalid_smiles(invalid_logger, smiles, "Graph validation failed")
            logger.warning(f"Graph validation failed for {molecule_id}")
            return None

        # 3. Compute shortest‑path matrix (dense is fine for typical molecules)
        sp_matrix = compute_shortest_path_matrix(graph, use_sparse=False)

        # 4. Build filtration from the distance matrix
        filtration = build_shortest_path_filtration(sp_matrix)

        # 5. Compute persistence diagram
        diagram = compute_persistence_diagram(filtration)

        # 6. Vectorise
        features = compute_persistence_features(diagram, resolution=resolution)

        return {"molecule_id": molecule_id, "features": features}
    except Exception as exc:
        if invalid_logger:
            log_invalid_smiles(invalid_logger, smiles, f"Unhandled error: {exc}")
        logger.error(f"Unhandled exception for {molecule_id}: {traceback.format_exc()}")
        return None


def generate_tda_features_csv(
    input_df: pd.DataFrame,
    output_path: Path,
    invalid_log_path: Path,
    resolution: int = 10,
) -> tuple[int, int]:
    """
    Iterate over all molecules in ``input_df`` and write a CSV containing
    ``molecule_id`` and the flattened persistence‑image vector.

    Returns a tuple ``(processed_count, failed_count)``.
    """
    logger = setup_logging()
    invalid_logger = setup_invalid_smiles_logger(str(invalid_log_path))

    logger.info(
        f"Generating persistence‑image features (resolution={resolution}) for {len(input_df)} molecules..."
    )

    records = []
    processed = 0
    failed = 0

    for idx, row in input_df.iterrows():
        smiles = row["smiles"]
        mol_id = row.get("molecule_id", f"mol_{idx}")

        result = process_molecule(
            smiles,
            mol_id,
            logger,
            invalid_logger,
            resolution=resolution,
        )

        if result is None:
            failed += 1
            continue

        # Build row dict: molecule_id + 100 pixel columns
        row_dict = {"molecule_id": result["molecule_id"]}
        for i, val in enumerate(result["features"]):
            row_dict[f"pixel_{i}"] = float(val)
        records.append(row_dict)
        processed += 1

        if processed % 200 == 0:
            logger.info(f"Processed {processed} molecules (failed so far: {failed})")

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if records:
        out_df = pd.DataFrame(records)
        out_df.to_csv(output_path, index=False)
        logger.info(f"Wrote {len(out_df)} feature rows to {output_path}")
    else:
        # Touch an empty file with header (molecule_id + pixel columns)
        header = ["molecule_id"] + [f"pixel_{i}" for i in range(resolution * resolution)]
        pd.DataFrame(columns=header).to_csv(output_path, index=False)
        logger.warning("No valid molecules processed; created empty CSV with header.")

    return processed, failed


def main() -> None:
    """Entry point for TDA computation."""
    parser = argparse.ArgumentParser(
        description="Compute baseline TDA persistence‑image features."
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=10,
        help="Grid resolution for the persistence image (e.g., 10 for 10×10).",
    )
    args = parser.parse_args()

    # Resolve project directories
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    logs_dir = data_dir / "logs"

    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Load the filtered ESOL dataset produced by T001
    filtered_path = processed_dir / "filtered_esol.csv"
    if not filtered_path.exists():
        print(
            f"Error: Expected filtered dataset at {filtered_path} (produced by T001)."
        )
        sys.exit(1)

    try:
        df = pd.read_csv(filtered_path)
    except Exception as exc:
        print(f"Failed to read filtered ESOL CSV: {exc}")
        sys.exit(1)

    # Ensure a molecule_id column exists
    if "molecule_id" not in df.columns:
        df["molecule_id"] = df.index.astype(str)

    # Define output filenames
    resolution = args.resolution
    output_csv = processed_dir / f"persistence_images_{resolution}x{resolution}.csv"
    invalid_log = logs_dir / "invalid_smiles.log"

    start = time.time()
    proc_cnt, fail_cnt = generate_tda_features_csv(
        df,
        output_csv,
        invalid_log,
        resolution=resolution,
    )
    elapsed = time.time() - start

    print(
        f"TDA feature generation completed in {elapsed:.2f}s – processed: {proc_cnt}, failed: {fail_cnt}"
    )
    if proc_cnt == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
