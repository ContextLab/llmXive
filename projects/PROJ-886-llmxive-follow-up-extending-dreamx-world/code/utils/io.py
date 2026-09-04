import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union, Tuple

logger = logging.getLogger(__name__)

def ensure_directories(paths: list) -> None:
    """Ensure that a list of directory paths exist."""
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {path}")

def compute_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute checksum of a file for integrity verification.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal checksum string
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def log_operation(operation: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a standardized operation record.
    
    Args:
        operation: Operation name
        details: Optional dictionary of operation details
    """
    log_msg = f"Operation: {operation}"
    if details:
        log_msg += f" | Details: {json.dumps(details)}"
    logger.info(log_msg)

def load_dreamx_world_data(
    data_dir: Union[str, Path],
    subset: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load DreamX-World dataset from the specified directory.
    
    Args:
        data_dir: Path to the data directory
        subset: Optional subset name to load
        
    Returns:
        Dictionary containing dataset data
        
    Raises:
        FileNotFoundError: If data directory or files are missing
    """
    data_path = Path(data_dir)
    
    if not data_path.exists():
        raise FileNotFoundError(f"DreamX-World data directory not found: {data_path}")
    
    # Check for required files
    required_files = ["metadata.json", "trajectories.json"]
    for req_file in required_files:
        if not (data_path / req_file).exists():
            raise FileNotFoundError(f"Required file missing: {data_path / req_file}")
    
    # Load metadata
    with open(data_path / "metadata.json", "r") as f:
        metadata = json.load(f)
    
    # Load trajectories
    with open(data_path / "trajectories.json", "r") as f:
        trajectories = json.load(f)
    
    result = {
        "metadata": metadata,
        "trajectories": trajectories,
        "source": "dreamx_world"
    }
    
    if subset:
        result["trajectories"] = [t for t in trajectories if t.get("subset") == subset]
    
    log_operation("load_dreamx_world_data", {
        "data_dir": str(data_path),
        "subset": subset,
        "trajectory_count": len(result["trajectories"])
    })
    
    return result

def load_scannet_fallback(
    data_dir: Union[str, Path],
    subset: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load ScanNet fallback dataset from the specified directory.
    
    Args:
        data_dir: Path to the data directory
        subset: Optional subset name to load
        
    Returns:
        Dictionary containing dataset data
        
    Raises:
        FileNotFoundError: If data directory or files are missing
    """
    data_path = Path(data_dir)
    
    if not data_path.exists():
        raise FileNotFoundError(f"ScanNet fallback data directory not found: {data_path}")
    
    # Check for required files
    required_files = ["metadata.json", "scans.json"]
    for req_file in required_files:
        if not (data_path / req_file).exists():
            raise FileNotFoundError(f"Required file missing: {data_path / req_file}")
    
    # Load metadata
    with open(data_path / "metadata.json", "r") as f:
        metadata = json.load(f)
    
    # Load scans
    with open(data_path / "scans.json", "r") as f:
        scans = json.load(f)
    
    result = {
        "metadata": metadata,
        "scans": scans,
        "source": "scannet_fallback"
    }
    
    if subset:
        result["scans"] = [s for s in scans if s.get("subset") == subset]
    
    log_operation("load_scannet_fallback", {
        "data_dir": str(data_path),
        "subset": subset,
        "scan_count": len(result["scans"])
    })
    
    return result

def load_data(
    primary_path: Union[str, Path],
    fallback_path: Union[str, Path],
    primary_name: str = "DreamX-World",
    fallback_name: str = "ScanNet"
) -> Tuple[Dict[str, Any], str]:
    """
    Load data with fallback protocol (T007/T008).
    
    Attempts to load from primary source first, then falls back to secondary.
    MUST fail loudly if neither source is available.
    NEVER uses synthetic data.
    
    Args:
        primary_path: Path to primary data source
        fallback_path: Path to fallback data source
        primary_name: Name of primary source for logging
        fallback_name: Name of fallback source for logging
        
    Returns:
        Tuple of (data_dict, source_name)
        
    Raises:
        FileNotFoundError: If neither source is available
    """
    primary_path = Path(primary_path)
    fallback_path = Path(fallback_path)
    
    # Try primary source
    if primary_path.exists():
        try:
            if "dreamx" in primary_name.lower():
                data = load_dreamx_world_data(primary_path)
            else:
                data = load_scannet_fallback(primary_path)
            
            log_operation("load_data", {
                "source": primary_name,
                "path": str(primary_path),
                "status": "success"
            })
            return data, primary_name
        except Exception as e:
            logger.warning(f"Primary source ({primary_name}) failed: {e}")
    
    # Try fallback source
    if fallback_path.exists():
        try:
            if "scannet" in fallback_name.lower():
                data = load_scannet_fallback(fallback_path)
            else:
                data = load_dreamx_world_data(fallback_path)
            
            log_operation("load_data", {
                "source": fallback_name,
                "path": str(fallback_path),
                "status": "success",
                "fallback_used": True
            })
            return data, fallback_name
        except Exception as e:
            logger.warning(f"Fallback source ({fallback_name}) failed: {e}")
    
    # Both sources failed - fail loudly
    error_msg = (
        f"CRITICAL: Data loading failed for both sources.\n"
        f"  Primary ({primary_name}): {primary_path} - {'Missing' if not primary_path.exists() else 'Load error'}\n"
        f"  Fallback ({fallback_name}): {fallback_path} - {'Missing' if not fallback_path.exists() else 'Load error'}\n"
        f"  Aborting execution. No synthetic data will be generated."
    )
    logger.error(error_msg)
    raise FileNotFoundError(error_msg)

def save_results(
    results: Dict[str, Any],
    output_path: Union[str, Path],
    checksum: bool = True
) -> str:
    """
    Save results to a JSON file with optional checksum.
    
    Args:
        results: Dictionary of results to save
        output_path: Path to save the file
        checksum: Whether to compute and log checksum
        
    Returns:
        Path to the saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    log_operation("save_results", {
        "path": str(output_path),
        "keys": list(results.keys())
    })
    
    if checksum:
        checksum_value = compute_file_checksum(output_path)
        logger.info(f"Results checksum: {checksum_value}")
    
    return str(output_path)
