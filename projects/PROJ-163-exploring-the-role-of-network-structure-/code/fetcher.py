import logging
import time
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

import numpy as np
from qiskit.providers import IBMQuantumRuntime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def retry_with_exponential_backoff(
    func,
    max_attempts: int = 5,
    base_delay: float = 1.0,
    timeout: float = 30.0
):
    """
    Retry a function with exponential backoff for transient errors (e.g., 503).

    Args:
        func: The function to execute.
        max_attempts: Maximum number of retry attempts.
        base_delay: Base delay in seconds before the first retry.
        timeout: Timeout in seconds for the entire operation.

    Returns:
        The result of the function if successful.
    Raises:
        Exception: If the function fails after all attempts.
    """
    attempt = 0
    last_exception = None

    while attempt < max_attempts:
        try:
            return func()
        except Exception as e:
            last_exception = e
            attempt += 1
            if attempt == max_attempts:
                break

            # Check for specific error types that warrant retry
            error_code = getattr(e, 'status_code', None)
            if error_code == 503 or "503" in str(e):
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(
                    f"Transient error ({e}), retrying in {delay:.2f}s (attempt {attempt}/{max_attempts})"
                )
                time.sleep(delay)
            else:
                # Non-retryable error or unexpected error
                logger.error(f"Non-retryable error: {e}")
                raise

    if last_exception:
        raise last_exception

def fetch_backends_list() -> List[str]:
    """
    Retrieve all accessible backend names from IBM Quantum.

    Returns:
        List of backend names.
    """
    logger.info("Fetching list of accessible backends...")
    try:
        # Assuming IBMQuantumRuntime is initialized in config.py
        # If not, this function should accept a provider instance
        # For now, we assume a global provider or load it via config
        from config import setup_ibm_runtime
        provider = setup_ibm_runtime()
        backends = provider.backends()
        names = [b.name for b in backends]
        logger.info(f"Found {len(names)} backends")
        return names
    except Exception as e:
        logger.error(f"Failed to fetch backends list: {e}")
        raise

def fetch_backend_properties(backend_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch calibration properties for a specific backend.

    Args:
        backend_name: Name of the backend.

    Returns:
        Dictionary of backend properties or None if failed.
    """
    logger.info(f"Fetching properties for {backend_name}...")

    def _fetch():
        from config import setup_ibm_runtime
        provider = setup_ibm_runtime()
        backend = provider.get_backend(backend_name)
        return backend.properties()

    try:
        props = retry_with_exponential_backoff(_fetch)
        if props is None:
            logger.warning(f"Device {backend_name} excluded: No properties available")
            return None
        return props.to_dict()
    except Exception as e:
        logger.warning(f"Device {backend_name} excluded: {e}")
        return None

def validate_data_freshness(properties: Dict[str, Any], max_age_days: int = 30) -> bool:
    """
    Check if the calibration data is fresh enough.

    Args:
        properties: Backend properties dictionary.
        max_age_days: Maximum allowed age in days.

    Returns:
        True if data is fresh, False otherwise.
    """
    # IBM properties usually have a 'last_updated' or similar timestamp
    # We'll look for 'last_update_date' or parse from the structure
    try:
        last_update = properties.get('last_update_date')
        if not last_update:
            # Fallback: try to find a date field
            for key in ['date', 'timestamp', 'updated']:
                if key in properties:
                    last_update = properties[key]
                    break

        if not last_update:
            logger.warning("No update date found in properties")
            return False

        # Handle different date formats
        if isinstance(last_update, str):
            # Try parsing common formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S']:
                try:
                    dt = datetime.strptime(last_update, fmt)
                    break
                except ValueError:
                    continue
            else:
                # If all formats fail, try to extract date components
                # This is a fallback and might not be robust
                logger.warning(f"Could not parse date format: {last_update}")
                return False
        elif isinstance(last_update, datetime):
            dt = last_update
        else:
            logger.warning(f"Unexpected date type: {type(last_update)}")
            return False

        age = (datetime.now() - dt).days
        if age > max_age_days:
            logger.info(f"Data for backend is {age} days old (limit: {max_age_days})")
            return False
        return True
    except Exception as e:
        logger.warning(f"Could not validate freshness: {e}")
        return False

def extract_topology_data(properties: Dict[str, Any]) -> Tuple[List[int], List[Tuple[int, int]]]:
    """
    Extract qubit indices and coupling map from raw JSON properties.

    Args:
        properties: Backend properties dictionary.

    Returns:
        Tuple of (qubit_indices, coupling_map)
    """
    qubits = properties.get('qubits', [])
    qubit_indices = [q['name'] for q in qubits if 'name' in q]

    # Coupling map is often in 'coupling_map' or derived from 'gates'
    coupling_map = properties.get('coupling_map', [])

    # If coupling_map is not directly available, try to infer from gates
    if not coupling_map:
        gates = properties.get('gates', [])
        for gate in gates:
            if gate.get('gate') == 'cx':
                for param in gate.get('parameters', []):
                    if param.get('name') == 'coupling_map':
                        coupling_map = param.get('value', [])
                        break
            if coupling_map:
                break

    # Ensure coupling_map is a list of lists/tuples
    normalized_coupling_map = []
    for edge in coupling_map:
        if isinstance(edge, list):
            normalized_coupling_map.append(tuple(edge))
        elif isinstance(edge, tuple):
            normalized_coupling_map.append(edge)

    return qubit_indices, normalized_coupling_map

def extract_performance_metrics(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract performance metrics: T1, T2, cx gate errors, readout errors.

    Args:
        properties: Backend properties dictionary.

    Returns:
        Dictionary of extracted metrics.
    """
    metrics = {
        't1_mean': None,
        't2_mean': None,
        'cx_error_mean': None,
        'readout_error_mean': None,
        'coupling_map': None
    }

    try:
        qubits = properties.get('qubits', [])
        cx_gates = []
        readout_gates = []

        # Extract T1 and T2 from qubit properties
        t1_values = []
        t2_values = []

        for qubit in qubits:
            for prop in qubit.get('props', []):
                if prop.get('name') == 'T1':
                    val = prop.get('value')
                    if val is not None:
                        t1_values.append(val)
                elif prop.get('name') == 'T2':
                    val = prop.get('value')
                    if val is not None:
                        t2_values.append(val)

        # Extract CX gate errors
        gates = properties.get('gates', [])
        for gate in gates:
            if gate.get('gate') == 'cx':
                for param in gate.get('parameters', []):
                    if param.get('name') == 'gate_error':
                        val = param.get('value')
                        if val is not None:
                            cx_gates.append(val)
                # Also check for readout errors in the same gate entry if present
                for param in gate.get('parameters', []):
                    if param.get('name') == 'readout_error':
                        val = param.get('value')
                        if val is not None:
                            readout_gates.append(val)

        # Calculate means
        if t1_values:
            metrics['t1_mean'] = float(np.mean(t1_values))
        if t2_values:
            metrics['t2_mean'] = float(np.mean(t2_values))
        if cx_gates:
            metrics['cx_error_mean'] = float(np.mean(cx_gates))
        if readout_gates:
            metrics['readout_error_mean'] = float(np.mean(readout_gates))

        # Extract coupling map
        _, coupling_map = extract_topology_data(properties)
        metrics['coupling_map'] = coupling_map

    except Exception as e:
        logger.warning(f"Error extracting performance metrics: {e}")
        # Return partial metrics if possible
        pass

    return metrics

def fetch_all_backends(backend_names: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch properties for all given backends and extract metrics.

    Args:
        backend_names: List of backend names.

    Returns:
        List of dictionaries containing device_id and extracted metrics.
    """
    results = []

    for name in backend_names:
        logger.info(f"Processing {name}...")
        props = fetch_backend_properties(name)

        if props is None:
            continue

        if not validate_data_freshness(props):
            logger.info(f"Skipping {name}: data too old")
            continue

        # Extract metrics
        perf_metrics = extract_performance_metrics(props)
        topo_data = extract_topology_data(props)

        result = {
            'device_id': name,
            'properties': props,
            'metrics': perf_metrics,
            'topology': {
                'qubit_indices': topo_data[0],
                'coupling_map': topo_data[1]
            }
        }
        results.append(result)

    return results

def main():
    """
    Main entry point for fetching backend data.
    """
    logger.info("Starting backend data fetch...")
    try:
        backends = fetch_backends_list()
        if not backends:
            logger.warning("No backends found")
            return

        logger.info(f"Found {len(backends)} backends")
        results = fetch_all_backends(backends)
        logger.info(f"Successfully processed {len(results)} backends")

        # Save results (for demonstration, print first few)
        for res in results[:5]:
            print(f"Device: {res['device_id']}")
            print(f"  T1 Mean: {res['metrics']['t1_mean']}")
            print(f"  T2 Mean: {res['metrics']['t2_mean']}")
            print(f"  CX Error Mean: {res['metrics']['cx_error_mean']}")
            print(f"  Readout Error Mean: {res['metrics']['readout_error_mean']}")
            print(f"  Coupling Map Size: {len(res['topology']['coupling_map'])}")
            print()

    except Exception as e:
        logger.error(f"Failed to fetch backends: {e}")
        raise

if __name__ == "__main__":
    main()