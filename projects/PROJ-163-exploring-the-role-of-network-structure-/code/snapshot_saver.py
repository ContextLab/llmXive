"""
Module to save raw JSON calibration snapshots from IBM Quantum backends.
Handles timestamped filenames and SHA256 checksum generation.
"""
import json
import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config import load_config

logger = logging.getLogger(__name__)

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_data_raw_dir() -> Path:
    """
    Ensure the data/raw directory exists.

    Returns:
        Path object for the data/raw directory.
    """
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {raw_dir}")
    return raw_dir

def save_backend_snapshot(
    backend_name: str,
    properties_data: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> str:
    """
    Save a raw JSON snapshot of backend properties with timestamp and checksum.

    Args:
        backend_name: Name of the IBM Quantum backend (e.g., 'ibmq_manila').
        properties_data: Dictionary containing the raw calibration properties.
        output_dir: Optional directory to save the file. Defaults to data/raw/.

    Returns:
        Path to the saved JSON file.

    Raises:
        ValueError: If properties_data is empty or None.
        IOError: If the file cannot be written.
    """
    if not properties_data:
        raise ValueError("Cannot save empty or None properties data.")

    if output_dir is None:
        output_dir = ensure_data_raw_dir()

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{backend_name}_{timestamp}.json"
    file_path = output_dir / filename

    # Write JSON with indentation for readability
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(properties_data, f, indent=2, default=str)

    # Compute and log checksum
    checksum = compute_sha256(str(file_path))
    logger.info(f"Saved snapshot for {backend_name} to {file_path} (SHA256: {checksum})")

    # Optionally write a sidecar checksum file for verification
    checksum_path = output_dir / f"{backend_name}_{timestamp}.sha256"
    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  {filename}\n")

    return str(file_path)

def main():
    """
    Main entry point for saving snapshots.
    This script demonstrates saving a snapshot by loading config and
    fetching properties for a specific backend (e.g., 'ibmq_manila' if available).
    In a full pipeline, this would be called by fetcher.py after retrieving data.
    """
    logging.basicConfig(level=logging.INFO)
    
    config = load_config()
    service = config.setup_ibm_runtime()
    
    # Attempt to fetch a specific backend to demonstrate the saver
    # In a real run, this might iterate over a list of backends
    target_backend_name = "ibm_brisbane" # Using a generic modern backend name if available
    # Fallback to a common one if the specific one isn't available in the environment
    available_backends = [b.name for b in service.backends()]
    
    if target_backend_name not in available_backends:
        # Try to find any valid backend
        if available_backends:
            target_backend_name = available_backends[0]
        else:
            logger.error("No backends available to fetch.")
            return

    logger.info(f"Fetching properties for {target_backend_name}...")
    
    try:
        backend = service.backend(target_backend_name)
        properties = backend.properties()
        
        if properties:
            # Convert properties to a dictionary for saving
            props_dict = {
                "backend_name": properties.backend_name,
                "last_update_date": properties.last_update_date.isoformat() if properties.last_update_date else None,
                "qubits": [
                    {
                        "t1": q[0].value, "t2": q[1].value, "frequency": q[2].value,
                        "readout_error": q[3].value, "operational": bool(q[4].value)
                    } for q in properties.qubits
                ],
                "gates": [
                    {
                        "gate": g.gate, "qubits": g.qubits, 
                        "error": g.error, "parameters": g.parameters
                    } for g in properties.gates
                ],
                "general": [
                    {k: v for k, v in item.items()} for item in properties.general
                ]
            }
            
            file_path = save_backend_snapshot(target_backend_name, props_dict)
            logger.info(f"Successfully saved snapshot: {file_path}")
        else:
            logger.warning(f"No properties found for {target_backend_name}.")
            
    except Exception as e:
        logger.error(f"Failed to fetch or save properties for {target_backend_name}: {e}")
        raise

if __name__ == "__main__":
    main()
