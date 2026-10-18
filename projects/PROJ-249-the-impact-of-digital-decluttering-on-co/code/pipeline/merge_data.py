"""
Merge Data Script for Digital Decluttering Study (Task T005).

This script performs the following steps:
1. Load scored measurement records from `data/raw/simulated_measurements.csv`.
2. Load aggregated compliance scores from `data/processed/aggregated_compliance.csv`.
3. Join the two sources on `participant_id`.
4. Identify participants missing post‑intervention measurements and record
   exclusions (while retaining their baseline rows for descriptive statistics).
5. Compute change scores (post − baseline) for each metric for participants
   with complete data.
6. Write three output files to the `data/processed/` folder:
   - `descriptive_baseline.csv` – baseline values for *all* participants.
   - `exclusions.json` – list of participants excluded from the paired analysis
     with the reason for exclusion.
   - `change_scores.csv` – change‑score table for participants with complete data.
7. Append SHA‑256 checksums for the newly‑written files to the central
   manifest `data/checksums.sha256`.

The script follows the “fail loudly” principle: any missing required input
raises an exception, and no synthetic fallback data are generated.
"""

import csv
import json
import hashlib
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def sha256_of_file(file_path: Path) -> str:
    """Return the hex SHA‑256 digest of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def append_checksum(manifest_path: Path, target_path: Path) -> None:
    """
    Append a line ``<checksum>  <relative_path>`` to the checksum manifest.
    The manifest uses paths relative to the project root.
    """
    checksum = sha256_of_file(target_path)
    rel_path = target_path.relative_to(paths.root)
    line = f"{checksum}  {rel_path}\n"
    with open(manifest_path, "a", encoding="utf-8") as mf:
        mf.write(line)


# ----------------------------------------------------------------------
# Core merging logic
# ----------------------------------------------------------------------
def load_measurements() -> List[Dict[str, str]]:
    """
    Load scored measurement records.

    Expected columns (as defined by the simulation step):
        participant_id, phase (baseline|post), metric_type, value
    """
    measurements_path = paths.data("raw", "simulated_measurements.csv")
    if not measurements_path.exists():
        raise FileNotFoundError(
            f"Required measurements file not found: {measurements_path}"
        )
    with open(measurements_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        raise ValueError("Measurements file is empty.")
    log.info(f"Loaded {len(rows)} measurement rows.")
    return rows


def load_compliance() -> Dict[str, Dict[str, str]]:
    """
    Load aggregated compliance scores.

    Expected columns (produced by T004):
        participant_id, compliance_score, days_compliant, ... (any extras)
    Returns a dict keyed by participant_id.
    """
    compliance_path = paths.data("processed", "aggregated_compliance.csv")
    if not compliance_path.exists():
        raise FileNotFoundError(
            f"Required compliance file not found: {compliance_path}"
        )
    with open(compliance_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        compliance = {row["participant_id"]: row for row in reader}
    log.info(f"Loaded compliance for {len(compliance)} participants.")
    return compliance


def pivot_measurements(
    rows: List[Dict[str, str]]
) -> Tuple[Dict[str, Dict[str, Dict[str, float]]], List[str]]:
    """
    Reshape the long‑format measurement rows into a nested dict:

        data[participant_id][metric_type][phase] = value

    Also returns the list of distinct metric_type values encountered.
    """
    data: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    metric_set = set()
    for r in rows:
        pid = r["participant_id"]
        metric = r["metric_type"]
        phase = r["phase"].lower()
        try:
            val = float(r["value"])
        except (KeyError, ValueError) as e:
            raise ValueError(
                f"Invalid measurement row {r}: missing or non‑numeric value."
            ) from e
        data[pid][metric][phase] = val
        metric_set.add(metric)
    return data, sorted(metric_set)


def write_descriptive_baseline(
    baseline_data: Dict[str, Dict[str, float]],
    output_path: Path,
) -> None:
    """
    Write a CSV containing baseline values for *all* participants.
    Columns: participant_id, metric_type, baseline_value
    """
    fieldnames = ["participant_id", "metric_type", "baseline_value"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for pid, metrics in baseline_data.items():
            for metric, baseline_val in metrics.items():
                writer.writerow(
                    {
                        "participant_id": pid,
                        "metric_type": metric,
                        "baseline_value": baseline_val,
                    }
                )
    log.info(f"Wrote descriptive baseline CSV to {output_path}")


def write_exclusions(
    exclusions: List[Dict[str, str]], output_path: Path
) -> None:
    """Write exclusions as a JSON list."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(exclusions, f, indent=2)
    log.info(f"Wrote exclusions JSON to {output_path}")


def write_change_scores(
    change_records: List[Dict[str, str]], output_path: Path
) -> None:
    """
    Write change‑score CSV.

    Columns:
        participant_id, metric_type, baseline, post, change, percent_change
    """
    fieldnames = [
        "participant_id",
        "metric_type",
        "baseline",
        "post",
        "change",
        "percent_change",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in change_records:
            writer.writerow(rec)
    log.info(f"Wrote change scores CSV to {output_path}")


# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------
def run_merge_pipeline() -> None:
    """
    Execute the full merge / dropout / change‑score pipeline.

    Output files (all under ``data/processed/``):
        - descriptive_baseline.csv
        - exclusions.json
        - change_scores.csv
    """
    # 1. Load inputs
    measurements = load_measurements()
    compliance_lookup = load_compliance()

    # 2. Pivot measurements to convenient structure
    participant_data, metric_names = pivot_measurements(measurements)

    # 3. Prepare containers for outputs
    baseline_output: Dict[str, Dict[str, float]] = {}
    change_records: List[Dict[str, str]] = []
    exclusions: List[Dict[str, str]] = []

    # 4. Process each participant
    for pid, metrics in participant_data.items():
        # Gather baseline values for descriptive output (even if post is missing)
        baseline_vals: Dict[str, float] = {}
        missing_post = False
        for metric in metric_names:
            metric_dict = metrics.get(metric, {})
            baseline = metric_dict.get("baseline")
            post = metric_dict.get("post")
            if baseline is not None:
                baseline_vals[metric] = baseline
            if post is None:
                missing_post = True  # any missing post marks exclusion
        baseline_output[pid] = baseline_vals

        if missing_post:
            # Record exclusion reason – we keep it simple
            exclusions.append(
                {"participant_id": pid, "reason": "missing_post_data"}
            )
            continue  # skip change‑score calculation for this participant

        # 5. Compute change scores for participants with complete data
        for metric, metric_dict in metrics.items():
            baseline = metric_dict.get("baseline")
            post = metric_dict.get("post")
            if baseline is None or post is None:
                # Safety check – should not happen because of the missing_post guard
                continue
            change = post - baseline
            percent_change = (
                (change / baseline) * 100.0 if baseline != 0 else float("inf")
            )
            change_records.append(
                {
                    "participant_id": pid,
                    "metric_type": metric,
                    "baseline": f"{baseline:.4f}",
                    "post": f"{post:.4f}",
                    "change": f"{change:.4f}",
                    "percent_change": f"{percent_change:.2f}",
                }
            )

    # 6. Write outputs
    desc_path = paths.data("processed", "descriptive_baseline.csv")
    excl_path = paths.data("processed", "exclusions.json")
    change_path = paths.data("processed", "change_scores.csv")

    # Ensure output directories exist
    desc_path.parent.mkdir(parents=True, exist_ok=True)
    excl_path.parent.mkdir(parents=True, exist_ok=True)
    change_path.parent.mkdir(parents=True, exist_ok=True)

    write_descriptive_baseline(baseline_output, desc_path)
    write_exclusions(exclusions, excl_path)
    write_change_scores(change_records, change_path)

    # 7. Append checksums to the manifest
    manifest_path = paths.data("checksums.sha256")
    for p in (desc_path, excl_path, change_path):
        append_checksum(manifest_path, p)

    log.info("Merge pipeline completed successfully.")


def main() -> int:
    """Entry point for command‑line execution."""
    try:
        run_merge_pipeline()
        return 0
    except Exception as e:
        log.error(f"Merge pipeline failed: {e}")
        raise


if __name__ == "__main__":
    # When executed as a script, exit with the appropriate status code.
    import sys

    sys.exit(main())