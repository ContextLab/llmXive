"""
Thin entry‑point script that orchestrates the end‑to‑end pipeline.

The pipeline consists of the following high‑level steps:

1. Load configuration (``src.config.get_config``).
2. Ensure that a raw defect‑coordinate CSV exists; if not, generate a
   deterministic synthetic dataset (validation‑only mode).
3. Compute the proximity threshold (``src.data_ingestion.threshold.calculate_threshold``).
4. Load the defect coordinates, drop rows with missing ``x``/``y`` values,
   and log any dropped rows.
5. Construct a NetworkX graph for each sample
   (``src.graphs.constructor.build_graph_from_coordinates``).
6. Serialize the graph to a JSON‑compatible dict
   (``src.graphs.serializer.serialize_graph_to_dict``) and write it to
   ``data/processed/graphs/{sample_id}.json``.
7. Write a minimal summary JSON to ``data/results/end_to_end.json`` so
   that downstream tasks and integration tests have a concrete artifact.

The script is deliberately lightweight: it performs only the steps that have
concrete implementations at this stage of the project.  Later phases will
extend the workflow with metric extraction, statistical analysis, and
reporting.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd
import numpy as np

from llmxive_toolkit import paths, get_logger

# Project‑specific imports
from src.config import get_config, ConfigError
from src.data_ingestion.threshold import calculate_threshold, ThresholdCalculationError
from src.graphs.constructor import build_graph_from_coordinates, GraphConstructionError
from src.graphs.serializer import serialize_graph_to_dict, SerializationError
from src.data_ingestion.generate_synthetic import generate_synthetic_dataset

# Set up a top‑level logger for the script.
log = get_logger(__name__)

def _ensure_raw_data(output_dir: Path, seed: int) -> Path:
    """
    Ensure that a CSV with defect coordinates exists.

    If ``output_dir`` already contains at least one ``*.csv`` file, the
    function returns the first such file.  Otherwise it generates a
    deterministic synthetic dataset (validation‑only mode) and returns the
    path to the generated CSV.
    """
    csv_files = list(output_dir.glob("*.csv"))
    if csv_files:
        log.info(f"Found existing raw data CSV: {csv_files[0]}")
        return csv_files[0]

    # No real data – generate synthetic data.
    log.warning("No raw defect coordinate CSV found – generating synthetic data "
                "(validation‑only mode).")
    try:
        result = generate_synthetic_dataset(
            output_dir=str(output_dir),
            n_samples=5,
            grid_size=200,
            n_defects_per_sample=50,
            seed=seed,
        )
        csv_path = Path(result["coordinates"])
        log.info(f"Synthetic CSV generated at {csv_path}")
        return csv_path
    except Exception as exc:
        log.error(f"Failed to generate synthetic dataset: {exc}", exc_info=True)
        raise

def _load_and_clean(csv_path: Path) -> pd.DataFrame:
    """
    Load the CSV, drop rows with missing ``x`` or ``y`` values, and log
    warnings for each dropped row.

    Returns a DataFrame that always contains the columns ``x``, ``y``,
    and ``sample_id``.
    """
    df = pd.read_csv(csv_path)
    required = {"x", "y", "sample_id"}
    missing_cols = required - set(df.columns)
    if missing_cols:
        raise ValueError(f"CSV {csv_path} is missing required columns: {missing_cols}")

    # Identify rows with NaNs in x or y.
    mask = df["x"].isna() | df["y"].isna()
    dropped = df[mask]
    if not dropped.empty:
        for idx, row in dropped.iterrows():
            log.warning(f"[US1] Dropped row {idx}: missing coordinate "
                        f"(sample_id={row.get('sample_id')})")
    cleaned = df[~mask].reset_index(drop=True)
    log.info(f"Loaded {len(cleaned)} valid defect rows from {csv_path}")
    return cleaned

def _process_sample(sample_df: pd.DataFrame, threshold: float) -> dict:
    """
    Build and serialize a graph for a single sample.

    ``sample_df`` must contain columns ``x``, ``y``, and ``sample_id``.
    Returns the serialized JSON‑compatible dictionary.
    """
    sample_id = sample_df["sample_id"].iloc[0]
    coords = sample_df[["x", "y"]].to_numpy(dtype=float)

    try:
        G = build_graph_from_coordinates(
            coordinates=coords,
            threshold=threshold,
            sample_id=sample_id,
            material="graphene",  # Default material for synthetic data
        )
    except GraphConstructionError as exc:
        log.error(f"Graph construction failed for {sample_id}: {exc}")
        raise

    try:
        graph_dict = serialize_graph_to_dict(
            G,
            sample_id=sample_id,
            material="graphene",
            threshold=threshold,
            metadata=None,
        )
    except SerializationError as exc:
        log.error(f"Serialization failed for {sample_id}: {exc}")
        raise

    return graph_dict

def _write_graph_json(graph_dict: dict, sample_id: str) -> Path:
    """
    Write a single graph JSON file under ``data/processed/graphs``.
    Returns the path to the written file.
    """
    out_path = paths.data("processed", "graphs", f"{sample_id}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(graph_dict, f, indent=2)
    log.info(f"Wrote graph JSON for {sample_id} to {out_path}")
    return out_path

def main():
    parser = argparse.ArgumentParser(
        description="Run the end‑to‑end heat‑dissipation pipeline."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to the configuration YAML file.",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # 1. Load configuration
    # ------------------------------------------------------------------
    try:
        cfg = get_config(args.config)
    except ConfigError as exc:
        log.error(f"Failed to load configuration: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2. Ensure raw data exists (synthetic fallback if needed)
    # ------------------------------------------------------------------
    raw_dir = Path(cfg.data["raw"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    try:
        csv_path = _ensure_raw_data(raw_dir, seed=cfg.seed)
    except Exception:
        sys.exit(1)

    # ------------------------------------------------------------------
    # 3. Compute proximity threshold
    # ------------------------------------------------------------------
    try:
        threshold = calculate_threshold(
            material="graphene",  # Synthetic data uses graphene by default
            config_path=args.config,
        )
    except (ThresholdCalculationError, ConfigError) as exc:
        log.error(f"Threshold calculation failed: {exc}")
        sys.exit(1)

    log.info(f"Using proximity threshold = {threshold:.4f} nm")

    # ------------------------------------------------------------------
    # 4. Load and clean the defect coordinates
    # ------------------------------------------------------------------
    try:
        df = _load_and_clean(csv_path)
    except Exception as exc:
        log.error(f"Failed to load/clean data: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 5. Process each distinct sample
    # ------------------------------------------------------------------
    graph_paths = []
    for sample_id, sample_df in df.groupby("sample_id"):
        try:
            graph_dict = _process_sample(sample_df, threshold)
            out_path = _write_graph_json(graph_dict, sample_id)
            graph_paths.append(str(out_path))
        except Exception:
            log.error(f"Aborting pipeline due to error processing sample {sample_id}")
            sys.exit(1)

    # ------------------------------------------------------------------
    # 6. Write a minimal end‑to‑end result artifact
    # ------------------------------------------------------------------
    summary = {
        "config_path": args.config,
        "raw_csv": str(csv_path),
        "threshold_nm": threshold,
        "graphs_written": graph_paths,
        "sample_count": len(graph_paths),
    }
    result_path = paths.results("end_to_end.json")
    result_path.parent.mkdir(parents=True, exist_ok=True)
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    log.info(f"Pipeline completed successfully. Summary written to {result_path}")

if __name__ == "__main__":
    main()
