import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import time
import json
import os

# Import from local project modules
from config import load_config, IBMQuantumConfig

logger = logging.getLogger(__name__)

# Configuration for retry logic
MAX_RETRIES = 3
BACKOFF_FACTOR = 2
REQUEST_TIMEOUT = 60

def retry_with_exponential_backoff(func, max_attempts: int = MAX_RETRIES, backoff_factor: int = BACKOFF_FACTOR, timeout: int = REQUEST_TIMEOUT):
    """
    Decorator to retry a function with exponential backoff.
    Handles 503 errors specifically as per T013a.
    """
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(f"Attempting {func.__name__} (attempt {attempt}/{max_attempts})")
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                last_exception = e
                # Check if it's a 503-like error or generic timeout
                # Assuming the underlying qiskit-ibm-runtime raises specific exceptions or we catch generic ones
                # For this implementation, we assume standard HTTP errors or connection errors
                error_code = getattr(e, 'status_code', None) if hasattr(e, 'status_code') else None
                if error_code == 503 or "503" in str(e):
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"503 error encountered. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    # For other errors, we might not retry or retry based on config
                    # For now, re-raise if not 503 to fail fast on other issues
                    raise e
        raise last_exception
    return wrapper

def fetch_backends_list() -> List[str]:
    """
    Retrieves all accessible backend names.
    Uses Qiskit IBM Runtime to fetch the list.
    """
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        config = load_config()
        service = QiskitRuntimeService(channel="ibm_quantum", token=config.ibm_token)
        # Get backends, filtering for those that are operational
        backends = service.backends()
        return [b.name for b in backends if b.operational]
    except Exception as e:
        logger.error(f"Failed to fetch backends list: {e}")
        raise

@retry_with_exponential_backoff
def fetch_backend_properties(backend_name: str) -> Dict[str, Any]:
    """
    Fetches raw calibration properties for a specific backend.
    Handles 503 errors and malformed data.
    """
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        config = load_config()
        service = QiskitRuntimeService(channel="ibm_quantum", token=config.ibm_token)
        backend = service.backend(backend_name)
        properties = backend.properties()
        if not properties:
            raise ValueError(f"No properties found for {backend_name}")
        
        # Convert to dict for easier processing
        # The properties object has methods like to_dict() or direct attribute access
        # depending on the version. We assume a dict-like structure or convert it.
        if hasattr(properties, 'to_dict'):
            return properties.to_dict()
        return properties
    except Exception as e:
        logger.warning(f"Failed to fetch properties for {backend_name}: {e}")
        raise

def validate_data_freshness(properties: Dict[str, Any], max_age_days: int = 30) -> bool:
    """
    Validates that the calibration data is fresh (<= max_age_days).
    Returns True if fresh, False otherwise.
    """
    if not properties:
        return False
    
    # The 'last_update_date' is typically a string in ISO format
    last_update = properties.get('last_update_date')
    if not last_update:
        logger.warning("No last_update_date found in properties.")
        return False
    
    try:
        # Parse ISO format string
        if isinstance(last_update, str):
            update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
        else:
            # Handle if it's already a datetime object
            update_time = last_update
        
        now = datetime.now(update_time.tzinfo) if update_time.tzinfo else datetime.now()
        age = now - update_time
        
        if age > timedelta(days=max_age_days):
            logger.info(f"Data for device is {age.days} days old (> {max_age_days}).")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error parsing date {last_update}: {e}")
        return False

def extract_topology_data(raw_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts coupling_map and qubit indices from raw JSON properties.
    
    Args:
        raw_json: The raw dictionary from backend.properties()
    
    Returns:
        A dictionary containing:
            - 'device_id': str
            - 'coupling_map': List[List[int]]
            - 'qubit_indices': List[int]
            - 'num_qubits': int
    """
    device_id = raw_json.get('backend_name') or raw_json.get('backend_version')
    if not device_id:
        raise ValueError("Could not identify device_id from raw JSON")
    
    coupling_map = raw_json.get('coupling_map', [])
    
    # Ensure coupling_map is a list of lists
    if not isinstance(coupling_map, list):
        logger.warning(f"Invalid coupling_map format for {device_id}: {type(coupling_map)}")
        coupling_map = []
    
    # Extract all unique qubit indices involved in the coupling map
    qubit_indices = set()
    for edge in coupling_map:
        if isinstance(edge, (list, tuple)) and len(edge) >= 2:
            qubit_indices.add(edge[0])
            qubit_indices.add(edge[1])
    
    # Also check 'n_qubits' if available to include isolated qubits if any (though usually coupling_map covers active ones)
    # However, standard IBM data usually lists all qubits in the map if they are part of the topology.
    # If we have n_qubits, we might want to ensure we don't miss isolated ones, but for topology,
    # the coupling_map is the definitive source of edges.
    
    result = {
        "device_id": str(device_id),
        "coupling_map": coupling_map,
        "qubit_indices": sorted(list(qubit_indices)),
        "num_qubits": len(qubit_indices)
    }
    
    logger.debug(f"Extracted topology for {device_id}: {len(coupling_map)} edges, {len(qubit_indices)} qubits.")
    return result

def extract_performance_metrics(raw_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts T1, T2, gate_errors, and readout_errors from raw JSON.
    
    Args:
        raw_json: The raw dictionary from backend.properties()
    
    Returns:
        A dictionary containing extracted metrics keyed by qubit/gate.
    """
    device_id = raw_json.get('backend_name')
    qubits = raw_json.get('qubits', [])
    gates = raw_json.get('gates', [])
    
    metrics = {
        "device_id": str(device_id),
        "t1": {},
        "t2": {},
        "gate_errors": {},
        "readout_errors": {}
    }
    
    # Parse Qubit properties (T1, T2)
    for qubit_data in qubits:
        qubit_idx = qubit_data.get('name')
        if not isinstance(qubit_idx, int):
            continue
        
        for prop in qubit_data:
            if prop.get('name') == 'T1':
                metrics["t1"][qubit_idx] = prop.get('value')
            elif prop.get('name') == 'T2':
                metrics["t2"][qubit_idx] = prop.get('value')
    
    # Parse Gate properties (error rates)
    for gate in gates:
        gate_name = gate.get('gate')
        qubits_list = gate.get('qubits', [])
        for prop in gate.get('parameters', []):
            if prop.get('name') == 'gate_error':
                key = f"{gate_name}_{'-'.join(map(str, qubits_list))}"
                metrics["gate_errors"][key] = prop.get('value')
    
    # Parse Readout properties
    # Readout errors are often stored in the 'qubits' list under 'readout_error' or similar
    # but sometimes in a separate 'readout' section. IBM properties usually put it in qubits.
    for qubit_data in qubits:
        qubit_idx = qubit_data.get('name')
        if not isinstance(qubit_idx, int):
            continue
        for prop in qubit_data:
            if prop.get('name') == 'readout_error':
                metrics["readout_errors"][qubit_idx] = prop.get('value')
    
    return metrics

def fetch_all_backends() -> List[Dict[str, Any]]:
    """
    Orchestrates the fetching of all backends, filtering by freshness,
    and extracting topology and performance data.
    """
    backend_names = fetch_backends_list()
    logger.info(f"Found {len(backend_names)} operational backends.")
    
    results = []
    for name in backend_names:
        try:
            props = fetch_backend_properties(name)
            
            if not validate_data_freshness(props):
                logger.info(f"Skipping {name}: data too old.")
                continue
            
            topology = extract_topology_data(props)
            performance = extract_performance_metrics(props)
            
            results.append({
                "topology": topology,
                "performance": performance,
                "raw_timestamp": props.get('last_update_date')
            })
        except Exception as e:
            logger.error(f"Failed to process {name}: {e}")
            continue
    
    logger.info(f"Successfully processed {len(results)} backends.")
    return results