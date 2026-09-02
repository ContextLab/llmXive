"""
Task T017: Generate structured CSV `data/processed/raw_calibration.csv`
containing all valid device metrics from raw JSON snapshots.
"""
import json
import os
import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

def load_raw_snapshots(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all raw JSON calibration snapshots from the data/raw directory.
    Returns a list of dictionaries, each representing a device's calibration data.
    """
    if not raw_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        return []

    snapshots = []
    for file_path in raw_dir.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure we have the expected structure
                if 'backend_name' in data and 'properties' in data:
                    snapshots.append(data)
                else:
                    logger.warning(f"Skipping malformed snapshot: {file_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error reading {file_path}: {e}")

    return snapshots

def process_snapshot(snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract structured metrics from a raw calibration snapshot.
    Returns a dictionary of metrics or None if the snapshot is invalid.
    """
    try:
        backend_name = snapshot.get('backend_name')
        if not backend_name:
            return None

        properties = snapshot.get('properties', {})
        last_update_date = properties.get('last_update_date')

        # Extract qubit-specific metrics
        qubits = properties.get('qubits', [])
        if not qubits:
            logger.warning(f"No qubit data in snapshot for {backend_name}")
            return None

        # Aggregate metrics across qubits
        t1_values = []
        t2_values = []
        readout_error_values = []
        gate_errors = {}  # gate_name -> list of errors

        for qubit_idx, qubit_props in enumerate(qubits):
            for prop in qubit_props:
                name = prop.get('name')
                value = prop.get('value')
                unit = prop.get('unit')
                if value is None:
                    continue

                if name == 'T1':
                    t1_values.append(value)
                elif name == 'T2':
                    t2_values.append(value)
                elif name == 'readout_error':
                    readout_error_values.append(value)
                elif name == 'gate_error':
                    gate_name = prop.get('gate', 'unknown')
                    if gate_name not in gate_errors:
                        gate_errors[gate_name] = []
                    gate_errors[gate_name].append(value)

        # Calculate averages
        avg_t1 = sum(t1_values) / len(t1_values) if t1_values else None
        avg_t2 = sum(t2_values) / len(t2_values) if t2_values else None
        avg_readout_error = sum(readout_error_values) / len(readout_error_values) if readout_error_values else None

        # Calculate average gate errors
        avg_gate_errors = {}
        for gate, errors in gate_errors.items():
            avg_gate_errors[gate] = sum(errors) / len(errors) if errors else None

        # Extract coupling map
        coupling_map = properties.get('coupling_map', [])
        num_qubits = len(qubits)

        return {
            'device_id': backend_name,
            'num_qubits': num_qubits,
            'last_update_date': last_update_date,
            'avg_t1_us': avg_t1,
            'avg_t2_us': avg_t2,
            'avg_readout_error': avg_readout_error,
            'num_edges': len(coupling_map),
            'gate_errors': avg_gate_errors,
            'coupling_map': coupling_map
        }
    except Exception as e:
        logger.error(f"Error processing snapshot for {snapshot.get('backend_name', 'unknown')}: {e}")
        return None

def main():
    """
    Main entry point to generate the processed CSV file.
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / 'data' / 'raw'
    processed_dir = project_root / 'data' / 'processed'
    output_file = processed_dir / 'raw_calibration.csv'

    # Ensure processed directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load raw snapshots
    logger.info(f"Loading raw snapshots from {raw_dir}...")
    snapshots = load_raw_snapshots(raw_dir)

    if not snapshots:
        logger.error("No valid snapshots found. Cannot generate CSV.")
        return

    logger.info(f"Found {len(snapshots)} snapshots.")

    # Process snapshots
    processed_records = []
    for snapshot in snapshots:
        record = process_snapshot(snapshot)
        if record:
            processed_records.append(record)

    if not processed_records:
        logger.error("No valid records processed. Cannot generate CSV.")
        return

    logger.info(f"Processed {len(processed_records)} valid device records.")

    # Define CSV columns
    # Flatten gate_errors into separate columns if needed, but for now keep as JSON string
    fieldnames = [
        'device_id',
        'num_qubits',
        'last_update_date',
        'avg_t1_us',
        'avg_t2_us',
        'avg_readout_error',
        'num_edges',
        'gate_errors_json',  # Store as JSON string
        'coupling_map_json'   # Store as JSON string
    ]

    # Write to CSV
    logger.info(f"Writing processed data to {output_file}...")
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for record in processed_records:
            # Prepare row
            row = {
                'device_id': record['device_id'],
                'num_qubits': record['num_qubits'],
                'last_update_date': record['last_update_date'],
                'avg_t1_us': record['avg_t1_us'],
                'avg_t2_us': record['avg_t2_us'],
                'avg_readout_error': record['avg_readout_error'],
                'num_edges': record['num_edges'],
                'gate_errors_json': json.dumps(record['gate_errors']),
                'coupling_map_json': json.dumps(record['coupling_map'])
            }
            writer.writerow(row)

    logger.info(f"Successfully generated {output_file}")

if __name__ == '__main__':
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
