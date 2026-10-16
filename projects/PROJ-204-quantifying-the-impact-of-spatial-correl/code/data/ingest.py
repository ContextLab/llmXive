"""
code/data/ingest.py
-------------------

Implements the ingestion pipeline required by **Task T101**.
The script downloads raw EDS maps and performance metrics (using the
fallback public dataset when no verified source is available), aligns the
maps to a common pixel grid, masks defective regions, and writes a unified
CSV dataset together with ingestion statistics.

The implementation is deliberately self‑contained: it does **not** depend
on an external configuration file – the default project layout is used.
This makes the script runnable in isolation (e.g. via the quick‑start
command `python -m code.data.ingest`) and ensures that the required
artifacts are produced without additional setup.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger

from data.download import download_from_verified_source
from data.align import create_aligned_dataset
from preprocess.calibrate import calibrate_and_log

# Initialise a module‑level logger
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _write_ingestion_log(messages: List[str]) -> None:
    """Write a plain‑text log file summarising the ingestion run."""
    log_path = paths.results("ingestion_log.txt")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        for line in messages:
            f.write(line + "\n")

def _write_ingestion_stats(
    n_requested: int, n_processed: int, exclusions: List[Dict]
) -> None:
    """
    Write ``data/results/ingestion_stats.json`` with the overall success
    rate and per‑sample exclusion reasons.
    """
    stats = {
        "ingestion_success_rate": n_processed / n_requested if n_requested else 0.0,
        "total_requested": n_requested,
        "total_processed": n_processed,
        "exclusions": exclusions,
    }
    stats_path = paths.results("ingestion_stats.json")
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

# ----------------------------------------------------------------------
# Core pipeline
# ----------------------------------------------------------------------
def ingest_and_filter_dataset() -> pd.DataFrame:
    """
    Executes the full ingestion workflow and returns the unified
    DataFrame.  The function writes the following artifacts:

    * ``data/processed/unified_dataset.csv``
    * ``data/results/ingestion_stats.json``
    * ``data/results/ingestion_log.txt``

    Returns
    -------
    pd.DataFrame
        The unified dataset.
    """
    # ------------------------------------------------------------------
    # 1. Determine project directories (relative to the repository root)
    # ------------------------------------------------------------------
    raw_dir = paths.data("raw")
    processed_dir = paths.data("processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 2. Download raw data (fallback dataset is used automatically
    #    when the feasibility report contains ``verdict: halt``).
    # ------------------------------------------------------------------
    feasibility = {}  # the download module will handle the fallback
    try:
        samples = download_from_verified_source(feasibility)
    except Exception as e:
        log.error(f"Data download failed: {e}")
        raise

    n_requested = len(samples)
    log.info(f"Requested {n_requested} sample(s) for ingestion.")

    # ------------------------------------------------------------------
    # 3. Align elemental maps for each sample
    # ------------------------------------------------------------------
    aligned_samples: List[Dict] = []
    for sample in samples:
        try:
            element_files = [
                sample["pb_map_filename"],
                sample["i_map_filename"],
                sample["ma_map_filename"],
            ]
            aligned_maps = create_aligned_dataset(
                raw_dir=raw_dir,
                element_files=element_files,
                reference_key="Pb",
            )
            sample["aligned_maps"] = aligned_maps
            aligned_samples.append(sample)
        except Exception as e:
            log.warning(f"Alignment failed for sample {sample['sample_id']}: {e}")

    # ------------------------------------------------------------------
    # 4. Defect masking (calibration)
    # ------------------------------------------------------------------
    masked_samples: List[Dict] = []
    mask_exclusions: List[Dict] = []
    for sample in aligned_samples:
        try:
            aligned_maps = sample["aligned_maps"]
            masked_maps = {}
            mask_stats = {}
            for element, arr in aligned_maps.items():
                masked_arr, stats = calibrate_and_log(
                    image=arr,
                    dead_threshold=0.0,
                    artifact_sigma=3.0,
                    log_path=None,
                )
                masked_maps[element] = masked_arr
                mask_stats[element] = stats

            # Save masked arrays
            for element, arr in masked_maps.items():
                out_path = processed_dir / f"{sample['sample_id']}_{element}_masked.npy"
                np.save(out_path, arr)
                sample[f"masked_{element.lower()}_map_path"] = str(out_path)

            # Compute average masked‑pixel percentage across elements
            mask_percentages = [
                (stats["dead_pixel_fraction"] + stats["artifact_fraction"]) / 2.0
                for stats in mask_stats.values()
            ]
            sample["mask_percentage"] = float(np.mean(mask_percentages))
            masked_samples.append(sample)
        except Exception as e:
            log.warning(f"Masking failed for sample {sample['sample_id']}: {e}")
            mask_exclusions.append(
                {
                    "sample_id": sample["sample_id"],
                    "reason": f"Masking error: {str(e)}",
                }
            )

    # ------------------------------------------------------------------
    # 5. Assemble the unified CSV
    # ------------------------------------------------------------------
    records = []
    exclusions = []
    for s in masked_samples:
        # Verify performance metrics are present and numeric
        try:
            pce = float(s["pce"])
            j_sc = float(s["j_sc"])
            v_oc = float(s["v_oc"])
        except (KeyError, ValueError, TypeError):
            exclusions.append(
                {
                    "sample_id": s["sample_id"],
                    "reason": "Missing or non‑numeric performance metric",
                }
            )
            continue

        # Ensure all three masked map files exist
        required_paths = [
            s.get("masked_pb_map_path"),
            s.get("masked_i_map_path"),
            s.get("masked_ma_map_path"),
        ]
        if not all(p and Path(p).exists() for p in required_paths):
            exclusions.append(
                {
                    "sample_id": s["sample_id"],
                    "reason": "Missing masked map file(s)",
                }
            )
            continue

        record = {
            "sample_id": s["sample_id"],
            "Pb_map_path": s["masked_pb_map_path"],
            "I_map_path": s["masked_i_map_path"],
            "MA_map_path": s["masked_ma_map_path"],
            "pce": pce,
            "j_sc": j_sc,
            "v_oc": v_oc,
            "mask_percentage": s["mask_percentage"],
            # Place‑holders for fields not available in the fallback dataset
            "co_location_status": "unknown",
            "depth_validation_status": "unknown",
            "eds_status": "complete",
        }
        records.append(record)

    df = pd.DataFrame(records)
    unified_path = processed_dir / "unified_dataset.csv"
    df.to_csv(unified_path, index=False)
    log.info(f"Unified dataset written to {unified_path} ({len(df)} rows)")

    # ------------------------------------------------------------------
    # 6. Write logs and statistics
    # ------------------------------------------------------------------
    all_exclusions = exclusions + mask_exclusions
    _write_ingestion_log([f"{ex['sample_id']}: {ex['reason']}" for ex in all_exclusions])
    _write_ingestion_stats(
        n_requested=n_requested,
        n_processed=len(df),
        exclusions=all_exclusions,
    )

    return df

# ----------------------------------------------------------------------
# Command‑line entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI entry point – mirrors the behaviour expected by the quickstart
    documentation:

    ``python -m code.data.ingest``
    """
    ingest_and_filter_dataset()

if __name__ == "__main__":
    main()
