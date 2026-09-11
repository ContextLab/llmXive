"""
Task T017: Generate structured CSV `data/processed/raw_calibration.csv` containing all valid device metrics.

This script loads raw JSON calibration snapshots from `data/raw/`, extracts
performance metrics and topology data, and writes a unified CSV file.
"""
import json
import os
import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Paths
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
OUTPUT_FILE = PROCESSED_DIR / "raw_calibration.csv"

def load_raw_snapshots() -> List[Dict[str, Any]]:
    """
    Load all JSON calibration snapshots from data/raw/.
    
    Returns a list of dictionaries, each representing one device's calibration data.
    Raises FileNotFoundError if no snapshots exist.
    """
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"Raw data directory {RAW_DIR} does not exist. Run T016 first.")
    
    json_files = list(RAW_DIR.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {RAW_DIR}. Run T016 first.")
    
    snapshots = []
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Store the source filename for reference if needed
                data["_source_file"] = file_path.name
                snapshots.append(data)
        except json.JSONDecodeError as e:
            logger.warning(f"Skipping invalid JSON file {file_path.name}: {e}")
            continue
        except Exception as e:
            logger.error(f"Error reading {file_path.name}: {e}")
            continue
    
    if not snapshots:
        raise RuntimeError("No valid snapshots could be loaded from data/raw/.")
    
    logger.info(f"Loaded {len(snapshots)} valid snapshots from {RAW_DIR}.")
    return snapshots

def extract_device_metrics(snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract standardized metrics from a raw calibration snapshot.
    
    Expected fields in snapshot:
    - backend_name (str)
    - last_update_date (str or datetime)
    - qubits (list of lists of dicts)
    - gates (list of dicts)
    - coupling_map (list of lists)
    
    Returns a dict of flat metrics or None if critical data is missing.
    """
    if "backend_name" not in snapshot:
        logger.warning("Skipping snapshot: missing 'backend_name'")
        return None
    
    device_id = snapshot["backend_name"]
    update_date_str = snapshot.get("last_update_date", "")
    
    # Parse date
    try:
        if isinstance(update_date_str, str):
            # Handle common ISO formats
            update_date = datetime.fromisoformat(update_date_str.replace('Z', '+00:00'))
        elif isinstance(update_date_str, datetime):
            update_date = update_date_str
        else:
            update_date = datetime.now()
    except Exception:
        update_date = datetime.now()
    
    metrics = {
        "device_id": device_id,
        "timestamp": update_date.isoformat(),
        "num_qubits": 0,
        "avg_t1": None,
        "avg_t2": None,
        "avg_gate_error": None,
        "avg_readout_error": None,
        "coupling_map_size": 0,
        "topology_type": "unknown",
    }
    
    # Extract Qubit Metrics (T1, T2)
    qubits = snapshot.get("qubits", [])
    if qubits:
        t1_values = []
        t2_values = []
        for qubit_props in qubits:
            for prop in qubit_props:
                if prop.get("name") == "T1":
                    val = prop.get("value")
                    if val is not None:
                        t1_values.append(val)
                elif prop.get("name") == "T2":
                    val = prop.get("value")
                    if val is not None:
                        t2_values.append(val)
        
        if t1_values:
            metrics["avg_t1"] = sum(t1_values) / len(t1_values)
        if t2_values:
            metrics["avg_t2"] = sum(t2_values) / len(t2_values)
        metrics["num_qubits"] = len(qubits)
    
    # Extract Gate Errors
    gates = snapshot.get("gates", [])
    gate_errors = []
    for gate in gates:
        if gate.get("gate") == "cx" or gate.get("gate") == "cz": # Common 2-qubit gates
            for param in gate.get("parameters", []):
                if param.get("name") == "gate_error":
                    val = param.get("value")
                    if val is not None:
                        gate_errors.append(val)
        # Also check single qubit gates if needed, but CX is usually the focus
        else:
            for param in gate.get("parameters", []):
                if param.get("name") == "gate_error":
                    val = param.get("value")
                    if val is not None:
                        gate_errors.append(val)
    
    if gate_errors:
        metrics["avg_gate_error"] = sum(gate_errors) / len(gate_errors)
    
    # Extract Readout Errors
    # Readout errors are often stored in qubits list with name "readout_error"
    readout_errors = []
    for qubit_props in qubits:
        for prop in qubit_props:
            if prop.get("name") == "readout_error":
                val = prop.get("value")
                if val is not None:
                    readout_errors.append(val)
    
    if readout_errors:
        metrics["avg_readout_error"] = sum(readout_errors) / len(readout_errors)
    
    # Extract Topology Info
    coupling_map = snapshot.get("coupling_map", [])
    metrics["coupling_map_size"] = len(coupling_map)
    
    # Infer topology type (simple heuristic)
    if not coupling_map:
        metrics["topology_type"] = "none"
    elif len(coupling_map) == metrics["num_qubits"] - 1:
        # Could be a line or star, but simplistic check
        metrics["topology_type"] = "sparse"
    else:
        # Heuristic: if edges > qubits, likely dense or grid
        metrics["topology_type"] = "dense"
    
    return metrics

def process_snapshot(snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single snapshot and return a flat dictionary of metrics.
    """
    return extract_device_metrics(snapshot)

def main():
    """
    Main entry point: Load raw snapshots, process them, and write to CSV.
    """
    logger.info("Starting T017: Generate calibration CSV")
    
    # Ensure output directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        snapshots = load_raw_snapshots()
    except (FileNotFoundError, RuntimeError) as e:
        logger.error(f"Failed to load snapshots: {e}")
        raise
    
    processed_rows = []
    for snapshot in snapshots:
        try:
            row = process_snapshot(snapshot)
            if row:
                processed_rows.append(row)
        except Exception as e:
            logger.error(f"Error processing snapshot {snapshot.get('backend_name', 'unknown')}: {e}")
            continue
    
    if not processed_rows:
        logger.warning("No valid rows generated. CSV will be empty.")
    
    # Define CSV columns
    fieldnames = [
        "device_id", "timestamp", "num_qubits", "avg_t1", "avg_t2",
        "avg_gate_error", "avg_readout_error", "coupling_map_size", "topology_type"
    ]
    
    logger.info(f"Writing {len(processed_rows)} rows to {OUTPUT_FILE}")
    
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in processed_rows:
            # Ensure all fields are present (None becomes empty string or null in CSV)
            clean_row = {k: (v if v is not None else "") for k, v in row.items()}
            writer.writerow(clean_row)
    
    logger.info(f"T017 Complete: {OUTPUT_FILE} created.")

if __name__ == "__main__":
    main()