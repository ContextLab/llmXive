import logging
import time
import json
import os
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Callable, TypeVar
from functools import wraps
import requests

from config import IBMQuantumConfig, load_config, setup_ibm_runtime
from logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

# Constants for rate limiting
RATE_LIMIT_MIN_GAP_SECONDS = 2.0
MAX_RETRIES = 5
BASE_DELAY = 2.0
MAX_DELAY = 30.0
REQUEST_TIMEOUT = 30

# Track last request time per device/endpoint to enforce minimum gap
_last_request_timestamps: Dict[str, float] = {}

T = TypeVar('T')

def rate_limit_handler(func: Callable[..., T]) -> Callable[..., T]:
    """
    Wrapper that enforces a minimum 2-second gap between requests to the same endpoint/device.
    Tracks request timestamps globally per (device_id, endpoint) key.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        # Identify the key for rate limiting.
        # We assume the first argument or a specific kwarg identifies the device/endpoint.
        # For fetch_backends_list, we use a global key. For fetch_backend_properties, we use device_id.
        key = "global"
        if args:
            # If first arg is a string (likely device_id), use it
            if isinstance(args[0], str):
                key = args[0]
            # If it's a dict with 'device_id', use that
            elif isinstance(args[0], dict) and 'device_id' in args[0]:
                key = args[0]['device_id']
        
        # Enforce minimum gap
        current_time = time.time()
        last_time = _last_request_timestamps.get(key, 0.0)
        gap = current_time - last_time
        
        if gap < RATE_LIMIT_MIN_GAP_SECONDS:
            sleep_time = RATE_LIMIT_MIN_GAP_SECONDS - gap
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s before request to {key}")
            time.sleep(sleep_time)
        
        # Update timestamp
        _last_request_timestamps[key] = time.time()
        
        return func(*args, **kwargs)
    return wrapper

def retry_with_exponential_backoff(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to retry a function with exponential backoff and jitter for 429/503 errors.
    Max attempts: 5
    Base delay: 2.0s
    Max delay: 30.0s
    Timeout: 30s
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        last_exception = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.HTTPError, ConnectionError, Timeout) as e:
                status_code = getattr(e, 'response', None).status_code if hasattr(e, 'response') else None
                
                # Only retry on 429 (Too Many Requests) or 503 (Service Unavailable)
                if status_code not in [429, 503] and status_code is not None:
                    raise e
                if status_code is None and not isinstance(e, (ConnectionError, Timeout)):
                    raise e
                
                if attempt == MAX_RETRIES:
                    logger.error(f"Max retries ({MAX_RETRIES}) exceeded for {func.__name__}. Last error: {e}")
                    raise e
                
                # Calculate delay with exponential backoff and jitter
                delay = min(MAX_DELAY, BASE_DELAY * (2 ** (attempt - 1)))
                jitter = random.uniform(0, 0.1 * delay)
                total_delay = delay + jitter
                
                logger.warning(
                    f"Attempt {attempt}/{MAX_RETRIES} failed for {func.__name__} "
                    f"(Status: {status_code}). Retrying in {total_delay:.2f}s..."
                )
                time.sleep(total_delay)
                last_exception = e
        
        # Should not reach here, but just in case
        raise last_exception
    return wrapper

@rate_limit_handler
@retry_with_exponential_backoff
def fetch_backends_list() -> List[str]:
    """
    Fetches the list of accessible backend names from IBM Quantum.
    """
    config = load_config()
    if not config.ibmq_token:
        logger.warning("IBMQ_TOKEN not set. Using mock backend list for testing.")
        # Fallback to mock list if token is missing (for CI/testing only)
        return ["ibmq_manila", "ibmq_quito"]
    
    try:
        # Using the IBM Qiskit Runtime client if available, otherwise direct API
        from qiskit_ibm_runtime import QiskitRuntimeService
        service = QiskitRuntimeService(channel="ibm_quantum", token=config.ibmq_token)
        backends = service.backends()
        return [b.name for b in backends]
    except Exception as e:
        logger.error(f"Failed to fetch backends list: {e}")
        raise

@rate_limit_handler
@retry_with_exponential_backoff
def fetch_backend_properties(device_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches the latest calibration properties for a specific device.
    """
    config = load_config()
    if not config.ibmq_token:
        # Fallback to mock data if token is missing (for CI/testing only)
        logger.warning(f"IBMQ_TOKEN not set. Using mock properties for {device_id}.")
        return {
            "device_id": device_id,
            "timestamp": datetime.now().isoformat(),
            "coupling_map": [[0, 1], [1, 2]],
            "properties": {
                "qubits": [
                    {"name": "T1", "value": 100.0, "unit": "us"},
                    {"name": "T2", "value": 100.0, "unit": "us"},
                    {"name": "readout_error", "value": 0.05}
                ],
                "gates": [
                    {"gate": "cx", "qubits": [0, 1], "error": 0.01}
                ]
            }
        }
    
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        service = QiskitRuntimeService(channel="ibm_quantum", token=config.ibmq_token)
        backend = service.backend(device_id)
        properties = backend.properties()
        
        if properties:
            # Convert to dict for easier processing
            return {
                "device_id": device_id,
                "timestamp": properties.last_update_date.isoformat(),
                "coupling_map": backend.coupling_map.get_edges() if backend.coupling_map else [],
                "properties": properties.to_dict()
            }
        else:
            logger.warning(f"No properties found for {device_id}")
            return None
    except Exception as e:
        logger.error(f"Failed to fetch properties for {device_id}: {e}")
        raise

def validate_data_freshness(timestamp_str: str, max_age_days: int = 30) -> bool:
    """
    Validates if the data timestamp is within the acceptable age (default 30 days).
    Returns True if fresh, False if stale.
    """
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        age = now - timestamp
        return age.days <= max_age_days
    except ValueError:
        logger.warning(f"Invalid timestamp format: {timestamp_str}")
        return False

def extract_topology_data(properties: Dict[str, Any]) -> Tuple[List[List[int]], List[int]]:
    """
    Extracts coupling map and qubit indices from raw properties.
    """
    coupling_map = properties.get("coupling_map", [])
    # Ensure coupling_map is a list of lists
    if not isinstance(coupling_map, list):
        coupling_map = []
    
    qubit_indices = set()
    for edge in coupling_map:
        if isinstance(edge, (list, tuple)) and len(edge) == 2:
            qubit_indices.add(edge[0])
            qubit_indices.add(edge[1])
    
    return coupling_map, sorted(list(qubit_indices))

def extract_performance_metrics(properties: Dict[str, Any]) -> Dict[str, float]:
    """
    Extracts T1, T2, cx gate errors, and readout errors from raw properties.
    """
    metrics = {
        "t1_mean": 0.0,
        "t2_mean": 0.0,
        "cx_error_mean": 0.0,
        "readout_error_mean": 0.0,
        "t1_count": 0,
        "t2_count": 0,
        "cx_error_count": 0,
        "readout_error_count": 0
    }
    
    qubits = properties.get("properties", {}).get("qubits", [])
    for qubit in qubits:
        for item in qubit:
            if item["name"] == "T1":
                metrics["t1_mean"] += item["value"]
                metrics["t1_count"] += 1
            elif item["name"] == "T2":
                metrics["t2_mean"] += item["value"]
                metrics["t2_count"] += 1
    
    gates = properties.get("properties", {}).get("gates", [])
    for gate in gates:
        if gate["gate"] == "cx":
            metrics["cx_error_mean"] += gate["error"]
            metrics["cx_error_count"] += 1
        elif gate["gate"] == "readout":
            metrics["readout_error_mean"] += gate["error"]
            metrics["readout_error_count"] += 1
    
    # Calculate means
    if metrics["t1_count"] > 0:
        metrics["t1_mean"] /= metrics["t1_count"]
    if metrics["t2_count"] > 0:
        metrics["t2_mean"] /= metrics["t2_count"]
    if metrics["cx_error_count"] > 0:
        metrics["cx_error_mean"] /= metrics["cx_error_count"]
    if metrics["readout_error_count"] > 0:
        metrics["readout_error_mean"] /= metrics["readout_error_count"]
    
    return metrics

def fetch_all_backends() -> List[Dict[str, Any]]:
    """
    Fetches properties for all accessible backends, filters stale data, and returns a list of processed dicts.
    """
    backend_names = fetch_backends_list()
    results = []
    
    for name in backend_names:
        try:
            props = fetch_backend_properties(name)
            if props is None:
                continue
            
            if not validate_data_freshness(props["timestamp"]):
                logger.warning(f"Device {name} has stale data (>30 days). Excluding.")
                continue
            
            topology, qubits = extract_topology_data(props)
            perf_metrics = extract_performance_metrics(props)
            
            results.append({
                "device_id": name,
                "timestamp": props["timestamp"],
                "coupling_map": topology,
                "qubits": qubits,
                **perf_metrics
            })
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
            continue
    
    return results

def main():
    """
    Main entry point for fetching and processing backend properties.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting backend properties fetch...")
    
    try:
        all_data = fetch_all_backends()
        logger.info(f"Successfully fetched {len(all_data)} backends.")
        
        # Save raw snapshots (T016 logic would go here, but we focus on fetcher logic)
        # For now, just print summary
        for item in all_data:
            logger.info(f"Device: {item['device_id']}, T1: {item['t1_mean']:.2f}, CX Error: {item['cx_error_mean']:.4f}")
            
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise

if __name__ == "__main__":
    main()
