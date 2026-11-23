"""
Project configuration module for OSM Urban Heat Island analysis.
Contains city definitions, CRS settings, path constants, and memory safety thresholds.
Includes API key rotation logic and secure storage management.
"""
import os
import time
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- API Key Rotation Configuration ---
# T040: API Key Rotation Logic
# Thresholds for key rotation (in seconds)
KEY_ROTATION_THRESHOLD_DAYS = 90
KEY_ROTATION_THRESHOLD_SECONDS = KEY_ROTATION_THRESHOLD_DAYS * 24 * 60 * 60

# Path to store key metadata (rotation timestamps, versions)
KEY_METADATA_PATH = PROJECT_ROOT / "data" / "results" / "key_metadata.json"

# --- Memory Safety Thresholds ---
# T038b: Tuned MAX_BLOCKS to ensure peak memory < 6GB (Safety Check Threshold).
# Based on profiling (T038a) and raster dimensions (approx 10,000 x 10,000 pixels at 30m),
# a block grid of 20x20 (400 blocks) keeps the in-memory matrix for spatial CV and
# GWR under the 6GB limit while preserving spatial autocorrelation structure.
MAX_BLOCKS = 400

# Memory safety limit in MB (6GB)
MEMORY_LIMIT_MB = 6144

# --- Data Thresholds ---
MISSING_DATA_THRESHOLD = 0.10  # 10%
TIME_WINDOW_THRESHOLD = 5  # Years
GWR_BANDWIDTHS = [500, 1000, 2000, 5000]  # meters

# --- City Definitions ---
# Format: name: (min_lon, min_lat, max_lon, max_lat) in EPSG:4326
CITIES: Dict[str, Tuple[float, float, float, float]] = {
    "nyc": (-74.2591, 40.4774, -73.7002, 40.9176),
    "la": (-118.6681, 33.7037, -118.1553, 34.3373),
    "chicago": (-87.9403, 41.6445, -87.5241, 42.0230),
}

# --- CRS Settings ---
# Target CRS for analysis (Web Mercator)
TARGET_CRS = "EPSG:3857"
# Resolution in meters
TARGET_RESOLUTION = 30  # 30 meters

# --- Path Constants ---
# Relative paths from project root
PATHS = {
    "data_raw": "data/raw",
    "data_processed": "data/processed",
    "data_results": "data/results",
    "code": "code",
    "tests": "tests",
    "docs": "docs",
    "specs": "specs",
}

def get_path(relative_path: str) -> Path:
    """Get absolute path for a project-relative path."""
    return PROJECT_ROOT / relative_path

def get_city_bounds(city_name: str) -> Tuple[float, float, float, float]:
    """Get bounding box for a city."""
    if city_name.lower() not in CITIES:
        raise ValueError(f"City '{city_name}' not found in CITIES config.")
    return CITIES[city_name.lower()]

def get_city_crs(city_name: str) -> str:
    """Get CRS for a city (defaults to Target CRS)."""
    return TARGET_CRS

def get_city_utm_zone(city_name: str) -> str:
    """Get UTM zone for a city (simplified logic, returns EPSG:3857 as fallback)."""
    # In a real implementation, calculate UTM zone from lon/lat
    # For this project, we use EPSG:3857 as the unified analysis CRS
    return TARGET_CRS

def load_env_vars() -> Dict[str, Optional[str]]:
    """Load and validate environment variables."""
    keys = ["OVERPASS_API_KEY", "AWS_ACCESS_KEY", "AWS_SECRET_KEY"]
    env_vars = {}
    for key in keys:
        val = os.getenv(key)
        env_vars[key] = val
        if val is None:
            # Do not raise here, let downstream tasks handle missing keys
            # or use a specific validation function if needed.
            pass
    return env_vars

def save_config_to_json(output_path: Optional[Path] = None) -> Path:
    """Save current configuration to a JSON file."""
    if output_path is None:
        output_path = get_path("data/results/config_snapshot.json")
    
    config_data = {
        "max_blocks": MAX_BLOCKS,
        "memory_limit_mb": MEMORY_LIMIT_MB,
        "cities": list(CITIES.keys()),
        "target_crs": TARGET_CRS,
        "target_resolution": TARGET_RESOLUTION,
        "missing_data_threshold": MISSING_DATA_THRESHOLD,
        "time_window_threshold": TIME_WINDOW_THRESHOLD,
        "gwr_bandwidths": GWR_BANDWIDTHS,
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(config_data, f, indent=2)
    
    return output_path

# --- API Key Rotation and Secure Storage Logic (T040) ---

def _load_key_metadata() -> Dict:
    """Load key rotation metadata from disk. Returns empty dict if file doesn't exist."""
    if not KEY_METADATA_PATH.exists():
        return {}
    try:
        with open(KEY_METADATA_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def _save_key_metadata(metadata: Dict) -> None:
    """Save key rotation metadata to disk."""
    KEY_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(KEY_METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

def _get_key_hash(key: str) -> str:
    """Generate a secure hash of the API key for comparison (never store plain text)."""
    return hashlib.sha256(key.encode()).hexdigest()

def register_api_key(service: str, key: str) -> bool:
    """
    Register a new API key for a given service.
    Updates metadata with current timestamp and key hash.
    
    Args:
        service: Service name (e.g., 'OVERPASS', 'AWS')
        key: The API key string
        
    Returns:
        True if registration successful, False otherwise
    """
    if not key:
        return False
    
    metadata = _load_key_metadata()
    current_time = int(time.time())
    
    # Store versioned entry
    if service not in metadata:
        metadata[service] = {"versions": []}
    
    # Create new version entry
    new_version = {
        "hash": _get_key_hash(key),
        "registered_at": current_time,
        "last_used": current_time
    }
    
    # Prepend new version
    metadata[service]["versions"].insert(0, new_version)
    
    # Keep only last 3 versions for rotation history
    if len(metadata[service]["versions"]) > 3:
        metadata[service]["versions"] = metadata[service]["versions"][:3]
    
    _save_key_metadata(metadata)
    return True

def rotate_api_key(service: str, new_key: str) -> bool:
    """
    Rotate an API key for a given service.
    Validates the new key and updates metadata.
    
    Args:
        service: Service name
        new_key: The new API key string
        
    Returns:
        True if rotation successful, False otherwise
    """
    return register_api_key(service, new_key)

def check_key_expiration(service: str) -> Tuple[bool, str]:
    """
    Check if an API key has exceeded the rotation threshold.
    
    Args:
        service: Service name
        
    Returns:
        Tuple of (is_expired, message)
    """
    metadata = _load_key_metadata()
    
    if service not in metadata or not metadata[service].get("versions"):
        return True, f"No registered key found for {service}"
    
    # Get the most recent version
    latest_version = metadata[service]["versions"][0]
    registered_at = latest_version.get("registered_at", 0)
    current_time = int(time.time())
    
    age_seconds = current_time - registered_at
    age_days = age_seconds / (24 * 60 * 60)
    
    if age_seconds > KEY_ROTATION_THRESHOLD_SECONDS:
        return True, f"Key for {service} is {age_days:.1f} days old (threshold: {KEY_ROTATION_THRESHOLD_DAYS} days)"
    
    return False, f"Key for {service} is {age_days:.1f} days old (valid)"

def validate_api_key(service: str) -> Tuple[bool, str]:
    """
    Validate that an API key exists in environment and hasn't expired.
    
    Args:
        service: Service name (e.g., 'OVERPASS', 'AWS')
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Map service to env var name
    env_map = {
        "OVERPASS": "OVERPASS_API_KEY",
        "AWS": "AWS_ACCESS_KEY"
    }
    
    env_var = env_map.get(service.upper())
    if not env_var:
        return False, f"Unknown service: {service}"
    
    key = os.getenv(env_var)
    if not key:
        return False, f"Environment variable {env_var} is not set"
    
    # Check expiration
    is_expired, msg = check_key_expiration(service)
    if is_expired:
        return False, f"Key validation failed: {msg}"
    
    # Verify hash matches registered key (if registered)
    metadata = _load_key_metadata()
    if service in metadata and metadata[service].get("versions"):
        registered_hash = metadata[service]["versions"][0].get("hash")
        current_hash = _get_key_hash(key)
        if registered_hash and registered_hash != current_hash:
            # Key in env doesn't match registered key - likely rotated externally
            # Register the new key automatically
            register_api_key(service, key)
            return True, f"Key for {service} validated and updated (external rotation detected)"
    
    return True, f"Key for {service} is valid"

def get_api_key_status() -> Dict[str, Dict]:
    """
    Get status of all registered API keys.
    
    Returns:
        Dictionary mapping service names to their status
    """
    metadata = _load_key_metadata()
    status = {}
    
    env_map = {
        "OVERPASS": "OVERPASS_API_KEY",
        "AWS": "AWS_ACCESS_KEY"
    }
    
    for service, env_var in env_map.items():
        key_exists = os.getenv(env_var) is not None
        is_expired, msg = check_key_expiration(service)
        
        status[service] = {
            "key_exists": key_exists,
            "is_expired": is_expired,
            "message": msg,
            "registered_versions": len(metadata.get(service, {}).get("versions", []))
        }
    
    return status

def generate_key_report() -> str:
    """
    Generate a human-readable report of API key status.
    
    Returns:
        Formatted string report
    """
    lines = ["API Key Status Report", "=" * 40]
    status = get_api_key_status()
    
    for service, info in status.items():
        lines.append(f"\n{service}:")
        lines.append(f"  Key Exists: {info['key_exists']}")
        lines.append(f"  Status: {'EXPIRED' if info['is_expired'] else 'VALID'}")
        lines.append(f"  Message: {info['message']}")
        lines.append(f"  Registered Versions: {info['registered_versions']}")
    
    return "\n".join(lines)

def main():
    """Main entry point for CLI usage of key management."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python config.py [check|rotate|report]")
        print("  check   - Check status of all keys")
        print("  rotate  - Prompt for new key (interactive)")
        print("  report  - Generate detailed status report")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "check":
        status = get_api_key_status()
        for service, info in status.items():
            print(f"{service}: {'EXPIRED' if info['is_expired'] else 'VALID'} - {info['message']}")
    
    elif command == "rotate":
        service = input("Enter service name (OVERPASS/AWS): ").upper()
        new_key = input("Enter new API key: ")
        if register_api_key(service, new_key):
            print(f"Successfully registered new key for {service}")
        else:
            print("Failed to register key")
    
    elif command == "report":
        print(generate_key_report())
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
