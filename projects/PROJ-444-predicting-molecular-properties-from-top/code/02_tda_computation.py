"""
TDA Computation Pipeline: Graph Construction, Shortest-Path Filtration,
and Persistence-Image Generation.

Implements FR-001 (shortest-path distance filtration) and FR-002
(baseline 10x10 persistence images, kernel_bandwidth sigma = 1.0).

Output CSV columns (per feature_matrix.schema.yaml / data-model.md):
  * molecule_id        (string)
  * target_property    (constant string, e.g. "logP")
  * target_value       (float)
  * features           (JSON-serialised array<float>, length grid^2)
  * feature_names      (JSON-serialised array<string>, length grid^2)
  * pixel_0 .. pixel_{grid^2-1}  (flat float columns for convenience)

The file is written to data/processed/topological_features_{g}x{g}.csv
(plus a legacy copy persistence_images_{g}x{g}.csv) and a durable,
non-gitignored copy is written to data/results/ together with a
summary JSON of measured run statistics.
"""

import argparse
import json
import logging
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
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

# Kernel bandwidth mandated by data-model.md (sigma = 1.0)
KERNEL_BANDWIDTH = 1.0

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
    Convert a SMILES string to a graph, compute its persistence diagram
    (shortest-path distance filtration), and vectorise it into a
    persistence image of size ``resolution`` x ``resolution`` using
    kernel bandwidth sigma = 1.0.
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

        # 1. Shortest-path filtration (distance matrix)
        dist_matrix = build_shortest_path_filtration(graph)

        # 2. Persistence diagram
        diagram = compute_persistence_diagram(dist_matrix)

        # 3. Vectorise to persistence image (sigma = 1.0, FR-002 / data-model.md)
        if not diagram:
            image = handle_empty_diagram(resolution=resolution)
        else:
            image = vectorize(
                diagram, resolution=resolution, sigma=KERNEL_BANDWIDTH
            )

        features = np.asarray(image, dtype=float).ravel()
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
) -> tuple:
    """
    Iterate over ``input_df`` and write a CSV containing:
        * molecule_id (string)
        * target_property (constant string, e.g. "logP")
        * target_value (float from the input dataframe)
        * features (JSON array<float> of length resolution^2)
        * feature_names (JSON array<string> of length resolution^2)
        * pixel_0 ... pixel_{resolution^2-1}
    Two CSV files are written: a primary file matching the task
    specification and a legacy file kept for backward compatibility
    with downstream scripts.
    Returns a tuple ``(processed, failed)``.
    """
    logger = setup_logging()
    invalid_logger = setup_invalid_smiles_logger(str(invalid_log_path))

    logger.info(
        "Generating TDA features (grid %dx%d, sigma=%.1f) for %d molecules..."
        % (resolution, resolution, KERNEL_BANDWIDTH, len(input_df))
    )

    feature_names = [f"pixel_{i}" for i in range(resolution * resolution)]

    records = []
    processed = 0
    failed = 0

    for idx, row in input_df.iterrows():
        smiles = row["smiles"]
        mol_id = row.get("molecule_id", f"mol_{idx}")
        target_value = row.get(target_property_name)

        result = process_molecule(
            smiles,
            str(mol_id),
            logger,
            invalid_logger,
            resolution=resolution,
        )

        if result is None:
            failed += 1
            continue

        features = [float(v) for v in result["features"]]
        row_dict = {
            "molecule_id": str(result["molecule_id"]),
            "target_property": target_property_name,
            "target_value": float(target_value),
            # Schema-mandated array columns (serialised as JSON strings)
            "features": json.dumps(features),
            "feature_names": json.dumps(feature_names),
        }
        for i, val in enumerate(features):
            row_dict[feature_names[i]] = val

        records.append(row_dict)
        processed += 1

        if processed % 500 == 0:
            logger.info("Processed %d molecules (failed: %d)" % (processed, failed))

    # Ensure output directories exist
    output_path_primary.parent.mkdir(parents=True, exist_ok=True)
    output_path_legacy.parent.mkdir(parents=True, exist_ok=True)

    header = (
        ["molecule_id", "target_property", "target_value", "features", "feature_names"]
        + feature_names
    )

    if records:
        out_df = pd.DataFrame(records, columns=header)
        out_df["molecule_id"] = out_df["molecule_id"].astype(str)
        out_df.to_csv(output_path_primary, index=False)
        out_df.to_csv(output_path_legacy, index=False)
        logger.info(
            "Wrote %d feature rows to %s and %s"
            % (len(out_df), output_path_primary, output_path_legacy)
        )
    else:
        pd.DataFrame(columns=header).to_csv(output_path_primary, index=False)
        pd.DataFrame(columns=header).to_csv(output_path_legacy, index=False)
        logger.warning("No valid molecules processed; created empty CSVs with header.")

    return processed, failed


def _parse_cli_args() -> argparse.Namespace:
    """
    Parse command-line arguments. ``--grid`` is the preferred argument
    name (as used in the quick-start documentation); ``--resolution``
    is retained for backward compatibility.
    """
    parser = argparse.ArgumentParser(
        description="Compute baseline TDA (persistence-image) features."
    )
    parser.add_argument(
        "--grid",
        type=int,
        help="Grid size for the persistence image (e.g., 10 for 10x10).",
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
    df["molecule_id"] = df["molecule_id"].astype(str)

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

    # ------------------------------------------------------------------
    # Durable, non-gitignored evidence copy under data/results/
    # ------------------------------------------------------------------
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    durable_csv = results_dir / f"topological_features_{grid_size}x{grid_size}.csv"

    out_df = pd.read_csv(primary_output)
    out_df.to_csv(durable_csv, index=False)

    pixel_cols = [c for c in out_df.columns if c.startswith("pixel_")]
    pixel_block = out_df[pixel_cols].to_numpy(dtype=float)
    summary = {
        "grid_size": grid_size,
        "kernel_bandwidth": KERNEL_BANDWIDTH,
        "filtration": "shortest_path_distance",
        "n_input_molecules": int(len(df)),
        "n_processed": int(proc_cnt),
        "n_failed": int(fail_cnt),
        "n_feature_columns": int(len(pixel_cols)),
        "nan_count": int(out_df.isnull().sum().sum()),
        "feature_mean": float(pixel_block.mean()),
        "feature_std": float(pixel_block.std()),
        "feature_max": float(pixel_block.max()),
        "mean_l2_norm": float(
            np.linalg.norm(pixel_block, axis=1).mean()
        ),
        "target_property": "logP",
        "target_value_mean": float(out_df["target_value"].astype(float).mean()),
        "target_value_std": float(out_df["target_value"].astype(float).std()),
        "elapsed_seconds": float(elapsed),
        "durable_copy": str(durable_csv.relative_to(project_root)),
    }
    summary_path = results_dir / f"tda_summary_{grid_size}x{grid_size}.json"
    with summary_path.open("w") as f:
        json.dump(summary, f, indent=2)

    print(
        "TDA feature generation completed in %.2fs - processed: %d, failed: %d"
        % (elapsed, proc_cnt, fail_cnt)
    )
    print(f"Durable evidence copy: {durable_csv}")
    print(f"Run summary: {summary_path}")
    if proc_cnt == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
