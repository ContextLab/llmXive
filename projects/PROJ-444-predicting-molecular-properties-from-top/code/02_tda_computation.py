"""
TDA Computation Pipeline: Graph Construction, Shortest‑Path Filtration,
and Persistence‑Image Generation.

Implements FR‑001 (shortest‑path distance filtration) and FR‑002
(baseline 10×10 persistence images). The script now accepts both
``--grid`` and ``--resolution`` CLI arguments (default 10) to match the
quick‑start run‑book. It writes the resulting feature matrix to two
locations for backward compatibility:

  * data/processed/topological_features_{grid}x{grid}.csv
  * data/processed/persistence_images_{grid}x{grid}.csv

The CSV includes the required ``target_property`` and ``target_value``
columns as defined in ``feature_matrix.schema.yaml``. Invalid SMILES are
logged to ``data/logs/invalid_smiles.log``; molecules that cannot be
processed receive a zero‑vector fallback via ``handle_empty_diagram``.
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
    """Configure a logger for the TDA pipeline."""
    logger = logging.getLogger("tda_computation")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger


def setup_invalid_smiles_logger(log_file: str) -> logging.Logger:
    """Logger that records SMILES that cannot be processed."""
    logger = logging.getLogger("invalid_smiles")
    logger.setLevel(logging.ERROR)
    if not logger.handlers:
        handler = logging.FileHandler(log_file)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
    return logger


def process_molecule(
    smiles: str,
    molecule_id: str,
    logger: logging.Logger,
    invalid_logger: Optional[logging.Logger] = None,
    resolution: int = 10,
) -> Optional[Dict[str, Any]]:
    """
    Convert a SMILES string to a graph, compute its persistence diagram,
    and vectorise it into a persistence image of size ``resolution``×``resolution``.
    Returns a dict with ``molecule_id`` and the flattened feature vector,
    or ``None`` if the molecule cannot be processed.
    """
    try:
        graph = build_graph(smiles)
        if graph is None or not validate_graph(graph):
            if invalid_logger:
                invalid_logger.error(
                    f"Invalid SMILES (graph construction/validation failed): {smiles}"
                )
            return None

        # 1. Shortest‑path filtration (distance matrix)
        dist_matrix = build_shortest_path_filtration(graph)

        # 2. Persistence diagram
        diagram = compute_persistence_diagram(dist_matrix)

        # 3. Vectorise to persistence image
        if not diagram:
            image = handle_empty_diagram(resolution=resolution)
        else:
            # Use σ = 1.0 as required by the specification (kernel_bandwidth = 1.0)
            image = vectorize(diagram, resolution=resolution, sigma=1.0)

        features = image.ravel()
        return {"molecule_id": molecule_id, "features": features}
    except Exception as exc:
        if invalid_logger:
            invalid_logger.error(f"Exception for SMILES {smiles}: {exc}")
        logger.error(
            f"Unhandled exception while processing {molecule_id}: {traceback.format_exc()}"
        )
        return None


def generate_tda_features_csv(
    input_df: pd.DataFrame,
    output_path_primary: Path,
    output_path_legacy: Path,
    invalid_log_path: Path,
    resolution: int = 10,
    target_property_name: str = "logP",
) -> tuple[int, int]:
    """
    Iterate over ``input_df`` and write a CSV containing:
        * molecule_id (string)
        * target_property (constant string, e.g. "logP")
        * target_value   (float from the input dataframe)
        * pixel_0 … pixel_{resolution*resolution‑1}
    Two CSV files are written: a primary file matching the task
    specification and a legacy file kept for backward compatibility
    with downstream scripts.
    Returns a tuple ``(processed, failed)``.
    """
    logger = setup_logging()
    invalid_logger = setup_invalid_smiles_logger(str(invalid_log_path))

    logger.info(
        f"Generating TDA features (grid {resolution}×{resolution}) for {len(input_df)} molecules..."
    )

    records = []
    processed = 0
    failed = 0

    for idx, row in input_df.iterrows():
        smiles = row["smiles"]
        mol_id = row.get("molecule_id", f"mol_{idx}")
        target_value = row.get(target_property_name)

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

        row_dict = {
            "molecule_id": result["molecule_id"],
            "target_property": target_property_name,
            "target_value": float(target_value) if pd.notnull(target_value) else np.nan,
        }
        for i, val in enumerate(result["features"]):
            row_dict[f"pixel_{i}"] = float(val)

        records.append(row_dict)
        processed += 1

        if processed % 500 == 0:
            logger.info(f"Processed {processed} molecules (failed: {failed})")

    # Ensure output directories exist
    output_path_primary.parent.mkdir(parents=True, exist_ok=True)
    output_path_legacy.parent.mkdir(parents=True, exist_ok=True)

    if records:
        out_df = pd.DataFrame(records)
        # Write primary file
        out_df.to_csv(output_path_primary, index=False)
        # Write legacy file for compatibility with existing code
        out_df.to_csv(output_path_legacy, index=False)
        logger.info(
            f"Wrote {len(out_df)} feature rows to {output_path_primary} "
            f"and {output_path_legacy}"
        )
    else:
        # Write empty CSV with correct header
        header = [
            "molecule_id",
            "target_property",
            "target_value",
        ] + [f"pixel_{i}" for i in range(resolution * resolution)]
        pd.DataFrame(columns=header).to_csv(output_path_primary, index=False)
        pd.DataFrame(columns=header).to_csv(output_path_legacy, index=False)
        logger.warning(
            "No valid molecules processed; created empty CSVs with header."
        )

    return processed, failed


def _parse_cli_args() -> argparse.Namespace:
    """
    Parse command‑line arguments. ``--grid`` is the preferred argument
    name (as used in the quick‑start documentation); ``--resolution``
    is retained for backward compatibility.
    """
    parser = argparse.ArgumentParser(
        description="Compute baseline TDA (persistence‑image) features."
    )
    parser.add_argument(
        "--grid",
        type=int,
        help="Grid size for the persistence image (e.g., 10 for 10×10).",
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=10,
        help="Alias for --grid; retained for backward compatibility.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_cli_args()

    # Resolve which grid size to use
    grid_size = args.grid if args.grid is not None else args.resolution
    if grid_size <= 0:
        print("Error: --grid / --resolution must be a positive integer.")
        sys.exit(1)

    project_root = Path(__file__).parent.parent
    filtered_path = project_root / "data" / "processed" / "filtered_esol.csv"
    if not filtered_path.is_file():
        print(f"Error: Expected filtered dataset at {filtered_path}")
        sys.exit(1)

    df = pd.read_csv(filtered_path)
    if "molecule_id" not in df.columns:
        df["molecule_id"] = df.index.astype(str)

    # Define output paths
    primary_output = (
        project_root
        / "data"
        / "processed"
        / f"topological_features_{grid_size}x{grid_size}.csv"
    )
    legacy_output = (
        project_root
        / "data"
        / "processed"
        / f"persistence_images_{grid_size}x{grid_size}.csv"
    )
    invalid_log = project_root / "data" / "logs" / "invalid_smiles.log"
    invalid_log.parent.mkdir(parents=True, exist_ok=True)

    start = time.time()
    proc_cnt, fail_cnt = generate_tda_features_csv(
        df,
        primary_output,
        legacy_output,
        invalid_log,
        resolution=grid_size,
        target_property_name="logP",
    )
    elapsed = time.time() - start

    print(
        f"TDA feature generation completed in {elapsed:.2f}s – "
        f"processed: {proc_cnt}, failed: {fail_cnt}"
    )
    if proc_cnt == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
