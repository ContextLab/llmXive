"""
Process raw IBM Quantum calibration JSON snapshots into a performance‑metrics CSV.

This script reads every ``*.json`` file under ``data/raw/``, extracts the
relevant performance statistics (mean T1, mean T2, mean CX gate error,
mean readout error) and writes a consolidated CSV to
``data/processed/performance_metrics.csv``.  The output conforms to the
JSON schema located at
``specs/001-exploring-the-role-of-network-structure/contracts/performance_metrics.schema.yaml``.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from llmxive_toolkit import paths, get_logger

# Set up a module‑level logger
log = get_logger(__name__)

def _load_json(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its content as a dict."""
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _mean(values: List[float]) -> float:
    """Return the arithmetic mean of a list of numbers."""
    if not values:
        raise ValueError("Cannot compute mean of empty list")
    return sum(values) / len(values)

def _extract_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute performance metrics from a raw calibration dictionary.

    Expected keys in ``data``:
      - ``device_id`` (str)
      - ``timestamp`` (ISO‑8601 string)
      - ``qubits``: list of qubit parameter lists
      - ``gates``: list of gate dictionaries
    """
    # --- T1 / T2 -------------------------------------------------------
    t1_vals, t2_vals = [], []
    for qubit_params in data.get("qubits", []):
        for param in qubit_params:
            name = param.get("name")
            if name == "T1":
                t1_vals.append(param.get("value", 0.0))
            elif name == "T2":
                t2_vals.append(param.get("value", 0.0))

    # --- CX gate error / readout error ---------------------------------
    cx_errs, ro_errs = [], []
    for gate in data.get("gates", []):
        if gate.get("gate") == "cx":
            for param in gate.get("parameters", []):
                pname = param.get("name")
                if pname == "gate_error":
                    cx_errs.append(param.get("value", 0.0))
                elif pname == "readout_error":
                    ro_errs.append(param.get("value", 0.0))

    # Guard against missing data – the original fetcher aborts on missing
    # fields, but for robustness we raise a clear error here.
    if not (t1_vals and t2_vals and cx_errs and ro_errs):
        raise ValueError(
            f"Incomplete performance data for device {data.get('device_id')}"
        )

    return {
        "device_id": data.get("device_id", "unknown_device"),
        "timestamp": data.get("timestamp", ""),
        "t1_mean": _mean(t1_vals),
        "t2_mean": _mean(t2_vals),
        "cx_error_mean": _mean(cx_errs),
        "readout_error_mean": _mean(ro_errs),
        # Chip family is derived from the device identifier; we reuse the
        # helper from ``fetcher`` for consistency.
        "chip_family": _derive_chip_family(data.get("device_id", "")),
    }

def _derive_chip_family(device_id: str) -> str:
    """
    Minimal replica of ``fetcher.extract_chip_family`` to avoid a circular
    import.  The logic mirrors the original implementation.
    """
    name = device_id.lower()
    if "falcon" in name:
        return "Falcon"
    if "hummingbird" in name:
        return "Hummingbird"
    if "eagle" in name:
        return "Eagle"
    if "osprey" in name:
        return "Osprey"
    if "condor" in name:
        return "Condor"
    return "Unknown"

def generate_performance_csv(
    raw_dir: Path = paths.data("raw"),
    output_path: Path = paths.data("processed", "performance_metrics.csv"),
) -> None:
    """
    Main entry point: iterate over all JSON snapshots in ``raw_dir`` and
    write the aggregated performance CSV to ``output_path``.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "device_id",
        "timestamp",
        "t1_mean",
        "t2_mean",
        "cx_error_mean",
        "readout_error_mean",
        "chip_family",
    ]

    rows = []
    for json_file in raw_dir.glob("*.json"):
        try:
            data = _load_json(json_file)
            metrics = _extract_metrics(data)
            rows.append(metrics)
            log.info(f"Processed {json_file.name}")
        except Exception as e:
            log.warning(f"Skipping {json_file.name}: {e}")

    if not rows:
        raise RuntimeError(f"No valid performance data found in {raw_dir}")

    # Write CSV
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        import csv

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    log.info(f"Performance metrics CSV written to {output_path}")

def main() -> None:
    """CLI entry point."""
    generate_performance_csv()

if __name__ == "__main__":
    # When executed directly, run the full pipeline.
    main()
