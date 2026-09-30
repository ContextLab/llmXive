import logging
import time
import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import csv

from config import load_config
from logging_config import get_logger

# Configure logging
logger = get_logger(__name__)

def retry_with_exponential_backoff(func, max_attempts=5, base_delay=2.0, timeout=30):
    """
    Retry a function with exponential backoff.
    """
    attempt = 0
    while attempt < max_attempts:
        try:
            return func()
        except Exception as e:
            attempt += 1
            if attempt == max_attempts:
                logger.error(f"Failed after {max_attempts} attempts: {e}")
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)

def rate_limit_handler(response):
    """
    Handle rate limiting by checking for 429 status code.
    """
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        logger.warning(f"Rate limited. Waiting for {retry_after} seconds.")
        time.sleep(retry_after)
        return True
    return False

def fetch_backends_list(backend_client):
    """
    Retrieve all accessible backend names.
    """
    try:
        backends = backend_client.backends()
        return [backend.name for backend in backends if backend.operational]
    except Exception as e:
        logger.error(f"Failed to fetch backends list: {e}")
        raise

def fetch_backend_properties(backend_name, backend_client):
    """
    Fetch backend properties with retry logic and error handling.
    """
    def _fetch():
        backend = backend_client.backend(backend_name)
        props = backend.properties()
        if not props:
            raise ValueError(f"No properties found for {backend_name}")
        return props

    try:
        props = retry_with_exponential_backoff(_fetch)
        return props
    except Exception as e:
        logger.warning(f"Device {backend_name} excluded: {e}")
        return None

def validate_data_freshness(properties, max_age_days=30):
    """
    Validate that the data is fresh (<= 30 days old).
    """
    if not properties:
        return False
    last_update = properties.last_update_date
    now = datetime.now(last_update.tzinfo)
    age = now - last_update
    return age <= timedelta(days=max_age_days)

def extract_topology_data(properties):
    """
    Extract coupling map and qubit indices from raw JSON.
    """
    coupling_map = properties.coupling_map
    qubit_count = len(properties.qubits)
    return {
        "coupling_map": coupling_map,
        "qubit_count": qubit_count
    }

def extract_performance_metrics(properties):
    """
    Extract T1, T2, cx gate errors, readout errors.
    """
    t1_values = []
    t2_values = []
    cx_errors = []
    readout_errors = []

    for qubit in properties.qubits:
        for prop in qubit:
            if prop.name == 'T1':
                t1_values.append(prop.value)
            elif prop.name == 'T2':
                t2_values.append(prop.value)

    for gate in properties.gates:
        if gate.gate == 'cx':
            if gate.parameters and gate.parameters[0].name == 'gate_error':
                cx_errors.append(gate.parameters[0].value)
            if gate.parameters and len(gate.parameters) > 1 and gate.parameters[1].name == 'readout_error':
                readout_errors.append(gate.parameters[1].value)

    return {
        "t1_mean": sum(t1_values) / len(t1_values) if t1_values else None,
        "t2_mean": sum(t2_values) / len(t2_values) if t2_values else None,
        "cx_error_mean": sum(cx_errors) / len(cx_errors) if cx_errors else None,
        "readout_error_mean": sum(readout_errors) / len(readout_errors) if readout_errors else None
    }

def extract_chip_family(backend_name):
    """
    Extract chip family from backend name or properties.
    """
    if 'falcon' in backend_name.lower():
        return 'Falcon'
    elif 'hummingbird' in backend_name.lower():
        return 'Hummingbird'
    elif 'eagle' in backend_name.lower():
        return 'Eagle'
    elif 'osprey' in backend_name.lower():
        return 'Osprey'
    elif 'condor' in backend_name.lower():
        return 'Condor'
    else:
        return 'Unknown'

def fetch_all_backends(backend_client):
    """
    Fetch all accessible backends and their properties.
    """
    backends = fetch_backends_list(backend_client)
    all_data = []

    for backend_name in backends:
        logger.info(f"Fetching properties for {backend_name}...")
        props = fetch_backend_properties(backend_name, backend_client)
        if not props:
            continue

        if not validate_data_freshness(props):
            logger.warning(f"Data for {backend_name} is too old, skipping.")
            continue

        topology = extract_topology_data(props)
        performance = extract_performance_metrics(props)
        chip_family = extract_chip_family(backend_name)

        all_data.append({
            "device_id": backend_name,
            "timestamp": props.last_update_date.isoformat(),
            "coupling_map": topology["coupling_map"],
            "t1_mean": performance["t1_mean"],
            "t2_mean": performance["t2_mean"],
            "cx_error_mean": performance["cx_error_mean"],
            "readout_error_mean": performance["readout_error_mean"],
            "chip_family": chip_family
        })

    return all_data

def process_historical_data(historical_dir: str, output_path: str):
    """
    Aggregate historical snapshots into a single CSV.
    
    Reads all JSON files from `historical_dir` (format: {device_id}_{YYYYMMDD}.json),
    extracts performance metrics, and writes them to `output_path` as a CSV.
    
    Args:
        historical_dir: Path to directory containing historical JSON snapshots.
        output_path: Path to the output CSV file.
    
    Returns:
        None
    """
    historical_path = Path(historical_dir)
    if not historical_path.exists():
        logger.error(f"Historical directory {historical_dir} does not exist.")
        raise FileNotFoundError(f"Historical directory {historical_dir} does not exist.")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    # Iterate over all JSON files in the directory
    json_files = list(historical_path.glob("*.json"))
    if not json_files:
        logger.warning(f"No JSON files found in {historical_dir}.")
        # Write empty CSV with headers to ensure schema compliance
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["device_id", "date", "t1_mean", "t2_mean", "cx_error_mean", "readout_error_mean", "chip_family"])
        return

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Extract device_id and date from filename
            filename = json_file.stem
            # Expected format: {device_id}_{YYYYMMDD}
            parts = filename.rsplit('_', 1)
            if len(parts) != 2:
                logger.warning(f"Skipping file with unexpected format: {filename}")
                continue
            
            device_id = parts[0]
            date_str = parts[1]
            
            # Parse date
            try:
                date_obj = datetime.strptime(date_str, "%Y%m%d")
            except ValueError:
                logger.warning(f"Skipping file with invalid date format: {filename}")
                continue

            # Extract metrics from JSON content
            # The JSON structure is expected to match the snapshot format:
            # { "device_id": "...", "timestamp": "...", "t1_mean": ..., ... }
            t1 = data.get("t1_mean")
            t2 = data.get("t2_mean")
            cx_err = data.get("cx_error_mean")
            readout_err = data.get("readout_error_mean")
            chip_family = data.get("chip_family", "Unknown")

            # Validate presence of required metrics
            if any(v is None for v in [t1, t2, cx_err, readout_err]):
                logger.warning(f"Missing metrics in {filename}, skipping.")
                continue

            rows.append({
                "device_id": device_id,
                "date": date_str,
                "t1_mean": t1,
                "t2_mean": t2,
                "cx_error_mean": cx_err,
                "readout_error_mean": readout_err,
                "chip_family": chip_family
            })

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {json_file}, skipping.")
        except Exception as e:
            logger.error(f"Error processing {json_file}: {e}")

    # Write to CSV
    fieldnames = ["device_id", "date", "t1_mean", "t2_mean", "cx_error_mean", "readout_error_mean", "chip_family"]
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Successfully wrote {len(rows)} rows to {output_path}")

def main():
    """
    Main entry point for fetching and processing historical data.
    """
    config = load_config()
    if not config.ibmq_token:
        logger.error("IBMQ_TOKEN not found in environment variables.")
        return

    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        service = QiskitRuntimeService(channel="ibm_quantum", token=config.ibmq_token)
    except Exception as e:
        logger.error(f"Failed to initialize QiskitRuntimeService: {e}")
        return

    # Fetch current data (for T016)
    # all_data = fetch_all_backends(service)
    # ... save snapshots ...

    # Process historical data (T020)
    historical_dir = "data/historical"
    output_csv = "data/processed/historical_performance_metrics.csv"
    
    try:
        process_historical_data(historical_dir, output_csv)
    except FileNotFoundError as e:
        logger.error(str(e))
        # If directory doesn't exist, we might need to fetch first (T018/T019)
        # For this task, we assume T019 has run.
        return

if __name__ == "__main__":
    main()
