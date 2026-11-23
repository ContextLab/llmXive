"""
Pipeline Runner for processing halo data.

This module provides utilities to iterate over raw halo data, compute shape
metrics, validate them, and write the results to CSV files. It is used by
the processing stage of the pipeline (main.py) and exercised by unit tests
in `code/tests/test_pipeline_runner.py`.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Any, Generator

import numpy as np
import pandas as pd

from processing.inertia_tensor import compute_reduced_inertia_tensor, compute_eigenvalues_and_eigenvectors
from processing.shape_metrics import (
    compute_shape_metrics_from_halo,
    filter_halo_by_particle_count,
    validate_shape_metrics,
    get_exclusion_reason,
)

# Placeholder for the real data fetcher. In production this would download
# or stream the TNG halo catalog. Tests patch this function.
def fetch_tng_halo_data(snapshot_id: int = 0) -> List[Dict[str, Any]]:
    """
    Retrieve raw halo data for a given snapshot.

    Args:
        snapshot_id: Identifier of the simulation snapshot.

    Returns:
        List of halo dictionaries. Each dictionary must contain at least:
            - 'halo_id': unique identifier
            - 'num_particles': number of DM particles
            - 'pos': list of particle positions (N x 3)
            - 'mass': halo mass
    """
    raise NotImplementedError(
        "fetch_tng_halo_data must be implemented to retrieve real data. "
        "During tests this function is patched."
    )

def iterate_haloes(
    halo_list: List[Dict[str, Any]], chunk_size: int = 100
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Yield successive chunks from a list of halo dictionaries.

    Args:
        halo_list: Complete list of halo dicts.
        chunk_size: Number of haloes per chunk.

    Yields:
        Sublists of halo dictionaries of length <= chunk_size.
    """
    for i in range(0, len(halo_list), chunk_size):
        yield halo_list[i : i + chunk_size]

def validate_shape_metrics_chunk(
    records: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Separate valid and excluded halo shape records.

    A record is considered excluded if it already contains the key
    ``excluded`` set to ``True`` or if its shape metrics fall outside the
    physically meaningful bounds defined in ``shape_metrics.validate_shape_metrics``.

    Args:
        records: List of dictionaries each containing at least the keys
                 ``b_a_ratio``, ``c_a_ratio`` and ``triaxiality``.

    Returns:
        (valid_records, excluded_records)
    """
    valid: List[Dict[str, Any]] = []
    excluded: List[Dict[str, Any]] = []

    for rec in records:
        # Preserve pre‑marked exclusions (e.g. low‑particle count)
        if rec.get("excluded"):
            excluded.append(rec)
            continue

        b_a = rec.get("b_a_ratio")
        c_a = rec.get("c_a_ratio")
        T = rec.get("triaxiality")

        is_valid, error = validate_shape_metrics(b_a, c_a, T)
        if is_valid:
            valid.append(rec)
        else:
            rec_copy = rec.copy()
            rec_copy["excluded"] = True
            rec_copy["exclusion_reason"] = error
            excluded.append(rec_copy)

    return valid, excluded

def write_halo_shapes_csv(
    records: List[Dict[str, Any]], output_path: Path
) -> None:
    """
    Write the list of valid halo shape records to a CSV file.

    The CSV columns are fixed to match ``halo_schema.schema.yaml``:
    ``halo_id, mass, b_a_ratio, c_a_ratio, triaxiality, particle_count``.

    Args:
        records: List of dictionaries with the required keys.
        output_path: Destination file path.
    """
    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Define column order
    columns = [
        "halo_id",
        "mass",
        "b_a_ratio",
        "c_a_ratio",
        "triaxiality",
        "particle_count",
    ]

    # Build DataFrame (will be empty if no records)
    df = pd.DataFrame(records, columns=columns)

    # Write CSV without index
    df.to_csv(output_path, index=False)

def write_exclusion_log(
    records: List[Dict[str, Any]], output_path: Path
) -> None:
    """
    Write a JSON log summarising excluded haloes.

    The JSON structure matches the expectations of the test suite:

    {
        "total_excluded": <int>,
        "excluded_haloes": [<record>, ...]
    }

    Args:
        records: List of excluded halo dictionaries.
        output_path: Destination file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log_content = {
        "total_excluded": len(records),
        "excluded_haloes": records,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(log_content, f, indent=2)

def run_pipeline(
    snapshot_id: int = 0,
    chunk_size: int = 100,
    min_particles: int = 10000,
    output_dir: str = "data/processed",
) -> Dict[str, int]:
    """
    End‑to‑end processing of halo data for a single snapshot.

    Steps:
    1. Fetch raw halo data (patched in tests).
    2. Iterate over the data in chunks.
    3. For each halo compute shape metrics using the reduced inertia tensor.
    4. Validate metrics and separate valid/excluded records.
    5. Write ``halo_shapes.csv`` and an exclusion log.

    Returns a dictionary with simple statistics used by the test suite.

    Args:
        snapshot_id: Identifier of the simulation snapshot.
        chunk_size: Number of haloes processed per iteration.
        min_particles: Minimum particle count for inclusion.
        output_dir: Directory (relative to project root) where output files are written.

    Returns:
        Dictionary with keys ``total_haloes``, ``valid_haloes`` and ``excluded_haloes``.
    """
    # Resolve absolute paths using pathlib
    output_path = Path(output_dir)
    halo_csv_path = output_path / "halo_shapes.csv"
    exclusion_json_path = output_path / "exclusion_log.json"

    # Fetch raw data
    raw_haloes = fetch_tng_halo_data(snapshot_id)

    total_haloes = len(raw_haloes)
    valid_records: List[Dict[str, Any]] = []
    excluded_records: List[Dict[str, Any]] = []

    for chunk in iterate_haloes(raw_haloes, chunk_size):
        for halo in chunk:
            halo_id = halo.get("halo_id")
            num_particles = halo.get("num_particles", 0)

            # Quick particle‑count filter
            if not filter_halo_by_particle_count(num_particles, min_particles):
                excluded_records.append(
                    {
                        "halo_id": halo_id,
                        "excluded": True,
                        "exclusion_reason": f"insufficient_particles ({num_particles} < {min_particles})",
                        "particle_count": num_particles,
                    }
                )
                continue

            # Positions must be a NumPy array of shape (N, 3)
            positions = np.asarray(halo.get("pos", []), dtype=float)

            # Optional masses
            masses = None
            if "mass_arr" in halo:
                masses = np.asarray(halo["mass_arr"], dtype=float)

            # Compute shape metrics using the high‑level helper
            metrics = compute_shape_metrics_from_halo(
                positions, masses=masses, min_particles=min_particles
            )

            if metrics is None:
                # Should not happen because we filtered by particle count,
                # but we guard against unexpected failures.
                excluded_records.append(
                    {
                        "halo_id": halo_id,
                        "excluded": True,
                        "exclusion_reason": "shape_computation_failed",
                        "particle_count": num_particles,
                    }
                )
                continue

            # Assemble a flat record for CSV output
            record = {
                "halo_id": halo_id,
                "mass": halo.get("mass"),
                "b_a_ratio": metrics["b_a_ratio"],
                "c_a_ratio": metrics["c_a_ratio"],
                "triaxiality": metrics["triaxiality"],
                "particle_count": metrics["particle_count"],
            }

            # Validate (this double‑checks the bounds)
            is_valid, error = validate_shape_metrics(
                record["b_a_ratio"], record["c_a_ratio"], record["triaxiality"]
            )
            if is_valid:
                valid_records.append(record)
            else:
                record["excluded"] = True
                record["exclusion_reason"] = error
                excluded_records.append(record)

    # Write outputs
    write_halo_shapes_csv(valid_records, halo_csv_path)
    write_exclusion_log(excluded_records, exclusion_json_path)

    return {
        "total_haloes": total_haloes,
        "valid_haloes": len(valid_records),
        "excluded_haloes": len(excluded_records),
    }
