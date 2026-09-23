"""
Fetcher module for retrieving IBM Quantum backend calibration data.

This module handles:
- Listing available backends
- Fetching backend properties with retry logic
- Validating data freshness
- Extracting topology and performance metrics
"""

import logging
import time
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.providers.models import BackendProperties

from config import load_config, setup_ibm_runtime
from logger import setup_logger

# Configure logging
logger = setup_logger(__name__)


def retry_with_exponential_backoff(
    func,
    max_attempts: int = 5,
    base_delay: float = 2.0,
    timeout: float = 30.0
):
    """
    Retry a function with exponential backoff for transient errors.

    Args:
        func: The function to retry.
        max_attempts: Maximum number of retry attempts.
        base_delay: Base delay in seconds between retries.
        timeout: Timeout in seconds for the operation.

    Returns:
        The result of the function if successful.

    Raises:
        Exception: If all retry attempts fail or timeout occurs.
    """
    attempt = 0
    last_exception = None

    while attempt < max_attempts:
        try:
            return func()
        except Exception as e:
            last_exception = e
            attempt += 1
            if attempt >= max_attempts:
                logger.error(f"Function failed after {max_attempts} attempts: {e}")
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)

    raise last_exception


def fetch_backends_list(service: QiskitRuntimeService) -> List[str]:
    """
    Retrieve all accessible backend names from the IBM Quantum service.

    Args:
        service: The QiskitRuntimeService instance.

    Returns:
        A list of backend names (strings).
    """
    try:
        backends = service.backends()
        return [backend.name for backend in backends]
    except Exception as e:
        logger.error(f"Failed to fetch backends list: {e}")
        raise


def fetch_backend_properties(
    service: QiskitRuntimeService,
    backend_name: str
) -> Optional[Dict[str, Any]]:
    """
    Fetch calibration properties for a specific backend with retry logic.

    Args:
        service: The QiskitRuntimeService instance.
        backend_name: The name of the backend.

    Returns:
        A dictionary containing backend properties, or None if fetch fails.

    Raises:
        Exception: If the fetch fails after all retry attempts.
    """
    def _fetch():
        backend = service.backend(backend_name)
        properties = backend.properties()
        if properties is None:
            raise ValueError(f"Properties are None for backend {backend_name}")
        return properties

    try:
        properties = retry_with_exponential_backoff(_fetch)
        # Convert BackendProperties to a JSON-serializable dict
        return properties.to_dict()
    except Exception as e:
        logger.warning(f"Device {backend_name} excluded: {e}")
        return None


def validate_data_freshness(
    properties_dict: Dict[str, Any],
    max_age_days: int = 30
) -> bool:
    """
    Validate that the calibration data is not older than max_age_days.

    Args:
        properties_dict: The backend properties dictionary.
        max_age_days: Maximum age of data in days.

    Returns:
        True if data is fresh, False otherwise.
    """
    if not properties_dict or "last_update_date" not in properties_dict:
        logger.warning("Missing last_update_date in properties")
        return False

    try:
        last_update = properties_dict["last_update_date"]
        # Handle different date formats
        if isinstance(last_update, str):
            # Try ISO format first
            try:
                update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            except ValueError:
                # Fallback to other common formats
                update_time = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S.%f")
        elif isinstance(last_update, datetime):
            update_time = last_update
        else:
            logger.warning(f"Unknown date format: {type(last_update)}")
            return False

        # Make update_time timezone-aware if naive
        if update_time.tzinfo is None:
            from datetime import timezone
            update_time = update_time.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age = now - update_time

        if age.days > max_age_days:
            logger.warning(f"Data for backend is {age.days} days old (>{max_age_days} days)")
            return False

        return True
    except Exception as e:
        logger.warning(f"Failed to validate data freshness: {e}")
        return False


def extract_topology_data(
    properties_dict: Dict[str, Any]
) -> Tuple[List[Tuple[int, int]], List[int]]:
    """
    Extract coupling map and qubit indices from raw JSON properties.

    Args:
        properties_dict: The backend properties dictionary.

    Returns:
        A tuple of (coupling_map, qubit_indices).
        coupling_map: List of (qubit_a, qubit_b) tuples.
        qubit_indices: List of qubit indices.
    """
    coupling_map = []
    qubit_indices = set()

    # Extract coupling map
    if "coupling_map" in properties_dict:
        coupling_map = properties_dict["coupling_map"]
        for edge in coupling_map:
            if len(edge) == 2:
                qubit_indices.add(edge[0])
                qubit_indices.add(edge[1])

    # Extract qubit indices if not from coupling map
    if not qubit_indices and "qubits" in properties_dict:
        for qubit_props in properties_dict["qubits"]:
            for prop in qubit_props:
                if "name" in prop:
                    # Parse qubit index from name like "q0", "q1"
                    try:
                        idx = int(prop["name"].replace("q", ""))
                        qubit_indices.add(idx)
                    except (ValueError, AttributeError):
                        pass

    qubit_indices = sorted(list(qubit_indices))
    return coupling_map, qubit_indices


def extract_performance_metrics(
    properties_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract performance metrics (T1, T2, CX errors, readout errors) from raw JSON.

    Args:
        properties_dict: The backend properties dictionary.

    Returns:
        A dictionary containing:
            - t1_values: List of T1 times (seconds)
            - t2_values: List of T2 times (seconds)
            - cx_errors: List of CX gate errors
            - readout_errors: List of readout errors
            - t1_mean: Mean T1 time
            - t2_mean: Mean T2 time
            - cx_error_mean: Mean CX error
            - readout_error_mean: Mean readout error
    """
    t1_values = []
    t2_values = []
    cx_errors = []
    readout_errors = []

    if not properties_dict or "qubits" not in properties_dict:
        logger.warning("No qubit properties found")
        return {
            "t1_values": [],
            "t2_values": [],
            "cx_errors": [],
            "readout_errors": [],
            "t1_mean": None,
            "t2_mean": None,
            "cx_error_mean": None,
            "readout_error_mean": None
        }

    # Extract T1 and T2 from qubit properties
    for qubit_props in properties_dict["qubits"]:
        for prop in qubit_props:
            name = prop.get("name", "")
            value = prop.get("value")

            if value is None:
                continue

            if name == "T1":
                t1_values.append(value)
            elif name == "T2":
                t2_values.append(value)

    # Extract CX gate errors from gates
    if "gates" in properties_dict:
        for gate in properties_dict["gates"]:
            if gate.get("gate") == "cx":
                for param in gate.get("parameters", []):
                    if param.get("name") == "gate_error":
                        error = param.get("value")
                        if error is not None:
                            cx_errors.append(error)

    # Extract readout errors
    if "gates" in properties_dict:
        for gate in properties_dict["gates"]:
            if gate.get("gate") == "measure":
                for param in gate.get("parameters", []):
                    if param.get("name") == "readout_error":
                        error = param.get("value")
                        if error is not None:
                            readout_errors.append(error)

    # Calculate means
    t1_mean = sum(t1_values) / len(t1_values) if t1_values else None
    t2_mean = sum(t2_values) / len(t2_values) if t2_values else None
    cx_error_mean = sum(cx_errors) / len(cx_errors) if cx_errors else None
    readout_error_mean = sum(readout_errors) / len(readout_errors) if readout_errors else None

    return {
        "t1_values": t1_values,
        "t2_values": t2_values,
        "cx_errors": cx_errors,
        "readout_errors": readout_errors,
        "t1_mean": t1_mean,
        "t2_mean": t2_mean,
        "cx_error_mean": cx_error_mean,
        "readout_error_mean": readout_error_mean
    }


def fetch_all_backends(
    backend_names: List[str],
    max_age_days: int = 30
) -> List[Dict[str, Any]]:
    """
    Fetch properties for all specified backends and filter by freshness.

    Args:
        backend_names: List of backend names to fetch.
        max_age_days: Maximum age of data in days.

    Returns:
        A list of dictionaries containing device data for fresh backends.
    """
    config = load_config()
    service = setup_ibm_runtime(config)

    results = []
    for backend_name in backend_names:
        logger.info(f"Fetching properties for {backend_name}...")

        properties = fetch_backend_properties(service, backend_name)
        if properties is None:
            continue

        if not validate_data_freshness(properties, max_age_days):
            continue

        # Extract topology and performance
        coupling_map, qubit_indices = extract_topology_data(properties)
        performance = extract_performance_metrics(properties)

        device_data = {
            "device_id": backend_name,
            "timestamp": properties.get("last_update_date"),
            "coupling_map": coupling_map,
            "qubit_indices": qubit_indices,
            **performance
        }
        results.append(device_data)

    return results


def main():
    """
    Main entry point for fetching backend properties.

    This script demonstrates the extraction of performance metrics.
    """
    config = load_config()
    service = setup_ibm_runtime(config)

    # Get list of backends
    backend_names = fetch_backends_list(service)
    logger.info(f"Found {len(backend_names)} accessible backends")

    # Fetch and process a subset for demonstration
    sample_backends = backend_names[:3]  # Limit to first 3 for demo
    results = fetch_all_backends(sample_backends)

    logger.info(f"Successfully processed {len(results)} backends")
    for result in results:
        logger.info(f"Device: {result['device_id']}, "
                   f"T1 mean: {result['t1_mean']}, "
                   f"T2 mean: {result['t2_mean']}, "
                   f"CX error mean: {result['cx_error_mean']}")


if __name__ == "__main__":
    main()