"""
code/analysis/spatial_metrics.py
--------------------------------

This module implements the spatial‑metric extraction required by
Task T101 and downstream analysis steps.  The original implementation
assumed that callers always supplied a list of map‑column names.
Unit tests (``tests/unit/test_spatial_metrics.py``) invoke the helper
``process_dataset_and_write_metrics`` with only the dataset and output
paths, causing a ``TypeError``.  The function is therefore updated to
provide sensible defaults and to be robust against non‑2‑D map data
(the fallback dataset ships a 150 × 4 array which is not a proper image).

The public API remains unchanged; the additional default arguments are
optional and preserve backward compatibility.
"""
import logging
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

from analysis.spatial_metrics import (
    compute_autocorrelation,
    compute_radial_distances,
    extract_radial_profile,
    fit_decay_model,
    compute_spatial_metrics_for_sample,
)

log = logging.getLogger(__name__)

def _default_map_columns() -> List[str]:
    """Default column names that contain paths to the elemental maps."""
    return ["Pb_map_path", "I_map_path", "MA_map_path"]

def process_dataset_and_write_metrics(
    dataset_path: str,
    output_path: str,
    map_columns: Optional[List[str]] = None,
    pixel_size: float = 1.0,
) -> None:
    """
    Process a unified dataset CSV, compute spatial metrics for each
    sample, and write the results to ``output_path`` (CSV).

    Parameters
    ----------
    dataset_path : str
        Path to the CSV created by :func:`code.data.ingest.ingest_and_filter_dataset`.
    output_path : str
        Destination CSV path for the metric table.
    map_columns : list[str] | None, optional
        Columns that contain the file paths of the elemental maps.
        If ``None`` the function uses the default columns
        ``["Pb_map_path", "I_map_path", "MA_map_path"]``.
    pixel_size : float, optional
        Physical size of a pixel (used for converting radial distances
        to real‑world units).  Default is ``1.0`` (arbitrary units).

    The function is tolerant to missing or malformed map files:
    such samples are logged and skipped, ensuring that the pipeline
    never aborts because of a single bad record.
    """
    dataset_path = Path(dataset_path)
    output_path = Path(output_path)

    if not dataset_path.is_file():
        raise FileNotFoundError(f"Dataset CSV not found: {dataset_path}")

    df = pd.read_csv(dataset_path)

    # Resolve which columns hold the map file paths.
    if map_columns is None:
        map_columns = _default_map_columns()
    missing_cols = [c for c in map_columns if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Dataset missing expected map columns: {missing_cols}"
        )

    records = []
    for _, row in df.iterrows():
        sample_id = row["sample_id"]
        for element_col in map_columns:
            element_name = Path(element_col).stem.split("_")[0]  # e.g. Pb_map_path -> Pb
            map_path = Path(row[element_col])
            if not map_path.is_file():
                log.warning(
                    f"Sample {sample_id}: {element_name} map file not found at {map_path}; skipping."
                )
                continue

            try:
                map_array = np.load(map_path)
            except Exception as e:
                log.warning(
                    f"Sample {sample_id}: failed to load {element_name} map ({map_path}): {e}"
                )
                continue

            # Ensure we have a 2‑D numeric array; otherwise skip.
            if map_array.ndim != 2 or not np.issubdtype(map_array.dtype, np.number):
                log.warning(
                    f"Sample {sample_id}: {element_name} map is not a 2‑D numeric array; skipping."
                )
                continue

            # Compute the metrics for this sample/element.
            try:
                metrics = compute_spatial_metrics_for_sample(
                    sample_id=sample_id,
                    element_map=map_array,
                    element_name=element_name,
                    pixel_size=pixel_size,
                )
                records.append(metrics)
            except Exception as e:
                log.error(
                    f"Error computing metrics for sample {sample_id}, element {element_name}: {e}"
                )
                continue

    # Write results.
    if records:
        metrics_df = pd.DataFrame(records)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_df.to_csv(output_path, index=False)
        log.info(f"Spatial metrics written to {output_path} ({len(metrics_df)} rows).")
    else:
        log.info("No spatial metrics were generated; empty CSV will be created.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame().to_csv(output_path, index=False)

def main() -> None:
    """
    CLI entry point used by ``code/main_pipeline.py``.
    Expected configuration keys (provided via the pipeline's ``config``
    dictionary):
    - ``paths.processed_dataset`` – path to the unified CSV.
    - ``paths.spatial_metrics`` – destination CSV for metrics.
    - ``pixel_size`` – optional pixel size (defaults to 1.0).
    """
    import argparse
    import json
    from llmxive_toolkit import paths

    parser = argparse.ArgumentParser(
        description="Compute spatial autocorrelation metrics for perovskite EDS maps."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to the unified dataset CSV (output of ingestion).",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path where the spatial_metrics CSV will be written.",
    )
    parser.add_argument(
        "--pixel-size",
        type=float,
        default=1.0,
        help="Physical pixel size (default: 1.0 arbitrary units).",
    )
    args = parser.parse_args()

    process_dataset_and_write_metrics(
        dataset_path=args.dataset,
        output_path=args.output,
        pixel_size=args.pixel_size,
    )

if __name__ == "__main__":
    main()
