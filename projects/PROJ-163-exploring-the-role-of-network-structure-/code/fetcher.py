"""
Fetcher Module for IBM Quantum Calibration Data (US1)

Implements logic to retrieve, validate, and extract data from IBM Quantum backends.
Includes retry logic, data freshness validation, and extraction of topology/metrics.
"""
import logging
import time
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from qiskit_ibm_runtime import QiskitRuntimeService
from logger import setup_logger
from config import load_config, setup_ibm_runtime
from snapshot_saver import save_backend_snapshot

logger = setup_logger(__name__)

# Configuration constants
MAX_RETRIES = 3
BASE_DELAY = 2.0  # seconds
REQUEST_TIMEOUT = 60  # seconds
MAX_DATA_AGE_DAYS = 30

def retry_with_exponential_backoff(func, max_retries: int = MAX_RETRIES, base_delay: float = BASE_DELAY):
    """
    Decorator to retry a function with exponential backoff.
    Handles 503 errors and timeouts specifically.
    """
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                # Check for specific retryable errors (503, Timeout)
                error_str = str(e).lower()
                if attempt < max_retries and ('503' in error_str or 'timeout' in error_str or 'rate limit' in error_str):
                    delay = base_delay ** attempt
                    logger.warning(f"Attempt {attempt} failed with {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Attempt {attempt} failed with {e}. Giving up.")
                    raise
        raise last_exception
    return wrapper

def fetch_backends_list(service: QiskitRuntimeService) -> List[str]:
    """Retrieve all accessible backend names."""
    logger.info("Fetching list of accessible backends...")
    try:
        backends = service.backends()
        return [b.name for b in backends]
    except Exception as e:
        logger.error(f"Failed to fetch backends list: {e}")
        raise

@retry_with_exponential_backoff
def fetch_backend_properties(service: QiskitRuntimeService, device_id: str) -> Dict[str, Any]:
    """
    Fetch raw properties for a specific backend.
    Handles 503 errors and malformed data.
    """
    logger.info(f"Fetching properties for {device_id}...")
    try:
        # QiskitRuntimeService method to get properties
        # Note: The exact method might vary slightly by SDK version, 
        # but 'properties' is the standard attribute on backend objects 
        # or a method call like backend.properties()
        backend = service.backend(device_id)
        props = backend.properties()
        
        if props is None:
            logger.warning(f"Properties returned None for {device_id}.")
            return {}
        
        # Convert to dict if it's a custom object, or return as is if already dict-like
        # Qiskit properties object usually has a to_dict() or similar, 
        # but often we just need the raw structure for snapshotting.
        # We ensure we return a JSON-serializable structure.
        if hasattr(props, 'to_dict'):
            return props.to_dict()
        return props
    except Exception as e:
        logger.warning(f"Failed to fetch properties for {device_id}: {e}. Excluding device.")
        return {}

def validate_data_freshness(properties: Dict[str, Any], max_age_days: int = MAX_DATA_AGE_DAYS) -> bool:
    """
    Validate that the data is not older than max_age_days.
    Returns True if fresh, False otherwise.
    """
    if not properties:
        return False
    
    # Look for 'last_update_date' or similar timestamp in properties
    # IBM Quantum properties structure usually contains 'last_update_date'
    last_update = properties.get('last_update_date')
    
    if not last_update:
        logger.warning("No last_update_date found in properties. Assuming stale.")
        return False

    # Handle different date formats if necessary, but Qiskit usually returns datetime
    if isinstance(last_update, datetime):
        update_dt = last_update
    else:
        # Fallback parsing if string
        try:
            update_dt = datetime.fromisoformat(str(last_update).replace('Z', '+00:00'))
        except ValueError:
            logger.warning("Could not parse last_update_date. Assuming stale.")
            return False

    now = datetime.now(update_dt.tzinfo) if update_dt.tzinfo else datetime.utcnow()
    age = now - update_dt

    if age > timedelta(days=max_age_days):
        logger.info(f"Data for device is {age.days} days old (> {max_age_days}). Excluding.")
        return False

    return True

def extract_topology_data(properties: Dict[str, Any]) -> Tuple[List[List[int]], List[int]]:
    """
    Extract coupling_map and qubit indices from raw JSON.
    Returns (coupling_map, qubit_indices)
    """
    # Coupling map is usually a list of [source, target] pairs
    coupling_map = properties.get('coupling_map', [])
    
    # Qubit indices are usually 0 to N-1, but we can extract from qubits list
    qubits = properties.get('qubits', [])
    qubit_indices = list(range(len(qubits))) if qubits else []

    return coupling_map, qubit_indices

def extract_performance_metrics(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract T1, T2, gate_errors, and readout_errors from raw JSON.
    Returns a dictionary of metrics.
    """
    metrics = {
        't1': [],
        't2': [],
        'gate_errors': [],
        'readout_errors': []
    }

    qubits = properties.get('qubits', [])
    gates = properties.get('gates', [])

    # Extract T1, T2
    for i, qubit in enumerate(qubits):
        t1_val = None
        t2_val = None
        for item in qubit:
            if item.get('name') == 'T1':
                t1_val = item.get('value')
            elif item.get('name') == 'T2':
                t2_val = item.get('value')
        
        if t1_val is not None:
            metrics['t1'].append({'qubit': i, 'value': t1_val, 'unit': 's'})
        if t2_val is not None:
            metrics['t2'].append({'qubit': i, 'value': t2_val, 'unit': 's'})

    # Extract Gate Errors (CX)
    for gate in gates:
        if gate.get('gate') == 'cx':
            for item in gate.get('parameters', []):
                if item.get('name') == 'gate_error':
                    metrics['gate_errors'].append({
                        'qubits': gate.get('qubits'),
                        'value': item.get('value')
                    })

    # Extract Readout Errors
    for i, qubit in enumerate(qubits):
        for item in qubit:
            if item.get('name') == 'readout_error':
                metrics['readout_errors'].append({
                    'qubit': i,
                    'value': item.get('value')
                })

    return metrics

def fetch_all_backends():
    """
    Main orchestration function to fetch data for all accessible backends,
    validate freshness, and save raw snapshots.
    """
    logger.info("Starting full backend fetch and snapshot process.")
    
    config = load_config()
    service = setup_ibm_runtime(config)
    
    if not service:
        logger.error("Failed to initialize IBM Quantum Runtime service.")
        return

    backends = fetch_backends_list(service)
    logger.info(f"Found {len(backends)} accessible backends.")

    valid_devices = []
    
    for device_id in backends:
        try:
            props = fetch_backend_properties(service, device_id)
            
            if not props:
                continue

            if not validate_data_freshness(props):
                continue

            # Save raw snapshot
            save_backend_snapshot(device_id, props)
            
            # Extract and store for downstream processing (in memory for now, 
            # or could be written to a processed CSV immediately if needed)
            coupling_map, qubits = extract_topology_data(props)
            metrics = extract_performance_metrics(props)
            
            valid_devices.append({
                'device_id': device_id,
                'properties': props,
                'coupling_map': coupling_map,
                'qubits': qubits,
                'metrics': metrics
            })
            
        except Exception as e:
            logger.error(f"Error processing {device_id}: {e}")
            continue

    logger.info(f"Successfully processed and saved {len(valid_devices)} valid devices.")
    return valid_devices

def main():
    """Entry point for the fetcher script."""
    fetch_all_backends()

if __name__ == "__main__":
    main()
