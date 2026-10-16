"""
Script to generate ``data/processed/performance_metrics.csv`` from the raw
JSON snapshots stored under ``data/raw/``.
The CSV contains one row per device snapshot with the following columns:

    device_id, timestamp, t1_mean, t2_mean, cx_error_mean,
    readout_error_mean, chip_family

The script extracts the required performance metrics directly from the
IBM Quantum ``BackendProperties`` dictionary representation.
"""
import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from llmxive_toolkit import paths, get_logger
from fetcher import extract_chip_family

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper to compute performance metrics from the raw property dict
# ----------------------------------------------------------------------
def _compute_metrics(props: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Compute mean T1, T2, CX gate error and readout error from the raw
    ``BackendProperties`` dictionary.

    Returns a dict with keys matching the CSV column names, or ``None``
    if any required metric is missing.
    """
    # Helper to safely extract a float list
    def _extract_qubit_vals(qubit_list: List[Any], name: str) -> List[float]:
        vals = []
        for qubit in qubit_list:
            for param in qubit:
                if isinstance(param, dict) and param.get("name") == name:
                    val = param.get("value")
                    if isinstance(val, (int, float)):
                        vals.append(float(val))
        return vals

    def _extract_gate_vals(gates: List[Any], gate_name: str, param_name: str) -> List[float]:
        vals = []
        for gate in gates:
            if isinstance(gate, dict) and gate.get("gate") == gate_name:
                for param in gate.get("parameters", []):
                    if isinstance(param, dict) and param.get("name") == param_name:
                        val = param.get("value")
                        if isinstance(val, (int, float)):
                            vals.append(float(val))
        return vals

    qubits = props.get("qubits", [])
    gates = props.get("gates", [])

    t1_vals = _extract_qubit_vals(qubits, "T1")
    t2_vals = _extract_qubit_vals(qubits, "T2")
    cx_err_vals = _extract_gate_vals(gates, "cx", "gate_error")
    ro_err_vals = _extract_gate_vals(gates, "cx", "readout_error")

    # If any of the metric lists are empty we consider the snapshot incomplete
    if not (t1_vals and t2_vals and cx_err_vals and ro_err_vals):
        return None

    return {
        "t1_mean": sum(t1_vals) / len(t1_vals),
        "t2_mean": sum(t2_vals) / len(t2_vals),
        "cx_error_mean": sum(cx_err_vals) / len(cx_err_vals),
        "readout_error_mean": sum(ro_err_vals) / len(ro_err_vals),
    }

# ----------------------------------------------------------------------
# Main processing function
# ----------------------------------------------------------------------
def generate_performance_csv(
    raw_dir: Path = paths.data("raw"),
    output_path: Path = paths.data("processed", "performance_metrics.csv"),
) -> None:
    """
    Read all ``*.json`` files in ``raw_dir``, compute the performance
    metrics for each device, and write the aggregated CSV to
    ``output_path``.
    """
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

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for json_file in raw_dir.glob("*.json"):
            try:
                with json_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.warning(f"Skipping unreadable JSON file {json_file}: {e}")
                continue

            # Determine device identifier – prefer the explicit field if present
            device_id = data.get("backend_name") or data.get("device_id")
            if not device_id:
                # Fallback to filename parsing
                device_id = json_file.stem.split("_")[0]

            # Timestamp – attempt to use the calibration timestamp if provided,
            # otherwise fall back to the file's modification time.
            timestamp = data.get("last_update_date")
            if not timestamp:
                timestamp = datetime.fromtimestamp(json_file.stat().st_mtime).isoformat()

            metrics = _compute_metrics(data)
            if metrics is None:
                logger.info(f"Skipping {json_file.name}: incomplete metric data.")
                continue

            chip_family = extract_chip_family(device_id)

            row = {
                "device_id": device_id,
                "timestamp": timestamp,
                "t1_mean": metrics["t1_mean"],
                "t2_mean": metrics["t2_mean"],
                "cx_error_mean": metrics["cx_error_mean"],
                "readout_error_mean": metrics["readout_error_mean"],
                "chip_family": chip_family,
            }
            writer.writerow(row)
            logger.debug(f"Wrote metrics for {device_id}")

    logger.info(f"Performance metrics CSV written to {output_path}")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main():
    """
    CLI wrapper – generates ``performance_metrics.csv``.
    """
    generate_performance_csv()

if __name__ == "__main__":
    main()
