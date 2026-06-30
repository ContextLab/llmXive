"""
Main entry point for the reproducibility assessment pipeline.
Handles environment logging (FR-012) and orchestration of ingestion and metrics.
"""
import json
import logging
import os
import platform
import subprocess
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Import from existing API surface
from ingest import ingest_pipeline, load_manifest, validate_manifest
from metrics import calculate_all_metrics, calculate_deviation_index

# Configure logging
LOG_DIR = Path("artifacts/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "pipeline.log"),
    ],
)
logger = logging.getLogger(__name__)

def get_docker_hash() -> Optional[str]:
    """
    Attempt to retrieve the Docker image hash if running in a container.
    Returns None if not running in Docker or if the command fails.
    """
    try:
        # Check if we are in a container
        if os.path.exists("/.dockerenv"):
            # Try to get image ID from /proc/1/cgroup or docker inspect if available
            # Fallback: try to read the image ID from standard Docker paths
            image_id_path = "/etc/image-id"
            if os.path.exists(image_id_path):
                with open(image_id_path, "r") as f:
                    return f.read().strip()
            
            # Try to run docker inspect (might fail without permissions)
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.Id}}", "current"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
            
            # Fallback: hash of /proc/1/cgroup
            with open("/proc/1/cgroup", "r") as f:
                content = f.read()
                return hashlib.sha256(content.encode()).hexdigest()[:12]
    except Exception as e:
        logger.debug(f"Could not retrieve Docker hash: {e}")
    
    return None

def log_environment() -> Dict[str, Any]:
    """
    Capture and log environment details as per FR-012.
    Returns a dictionary of the environment snapshot.
    """
    env_info = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "python_version": sys.version,
        "platform": {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "docker_hash": get_docker_hash(),
        "libraries": {}
    }

    # List of critical libraries to version-check
    critical_libs = [
        "torch", "scikit-learn", "rdkit", "statsmodels", 
        "pandas", "numpy", "matplotlib", "pyyaml", "requests", 
        "scipy", "jsonschema"
    ]

    for lib_name in critical_libs:
        try:
            lib = __import__(lib_name)
            version = getattr(lib, "__version__", "unknown")
            env_info["libraries"][lib_name] = version
        except ImportError:
            env_info["libraries"][lib_name] = "not_installed"
        except Exception as e:
            env_info["libraries"][lib_name] = f"error: {e}"

    # Write to log file
    log_path = LOG_DIR / "env.log"
    with open(log_path, "w") as f:
        json.dump(env_info, f, indent=2)
    
    logger.info(f"Environment logged to {log_path}")
    return env_info

def main():
    """
    Orchestrate the pipeline:
    1. Log environment (FR-012)
    2. Load and validate manifest
    3. Ingest data
    4. Calculate metrics (placeholder for full pipeline integration)
    """
    logger.info("Starting reproducibility assessment pipeline...")
    
    # Step 1: Environment Logging (FR-012)
    env_snapshot = log_environment()
    logger.info(f"Python: {env_snapshot['python_version']}")
    if env_snapshot['docker_hash']:
        logger.info(f"Docker Hash: {env_snapshot['docker_hash']}")
    
    # Step 2: Load Manifest (Mocking for T008 context, assumes T009 will handle full logic)
    # In a full run, this would load from data/manifest.yaml
    manifest_path = Path("data/manifest.yaml")
    if manifest_path.exists():
        logger.info(f"Loading manifest from {manifest_path}")
        # ingest_pipeline handles the rest of the logic
        # ingest_pipeline() 
    else:
        logger.warning(f"Manifest not found at {manifest_path}. Skipping ingestion.")
    
    logger.info("Environment logging complete. Pipeline ready for execution.")
    return env_snapshot

if __name__ == "__main__":
    main()