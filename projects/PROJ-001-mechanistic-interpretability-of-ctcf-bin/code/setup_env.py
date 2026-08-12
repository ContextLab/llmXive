import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "code" / "config" / "environment.yaml"
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.json"
OUTPUT_DIRS = {
    "raw": PROJECT_ROOT / "data" / "raw",
    "processed": PROJECT_ROOT / "data" / "processed",
    "models": PROJECT_ROOT / "data" / "models",
    "interpretation": PROJECT_ROOT / "data" / "interpretation",
    "figures": PROJECT_ROOT / "figures",
}

def load_env_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load environment configuration from a YAML file.
    If the file does not exist, returns a default structure with placeholders.
    """
    path = config_path or CONFIG_PATH
    if not path.exists():
        return {
            "encode_api_key": os.getenv("ENCODE_API_KEY", ""),
            "data_paths": {
                "raw": str(OUTPUT_DIRS["raw"]),
                "processed": str(OUTPUT_DIRS["processed"]),
                "models": str(OUTPUT_DIRS["models"]),
            },
            "logging": {"level": "INFO", "file": str(PROJECT_ROOT / "logs" / "pipeline.log")},
        }

    with open(path, "r") as f:
        return yaml.safe_load(f)

def validate_manifest_exists(manifest_path: Optional[Path] = None) -> bool:
    """
    Verify that the data manifest exists as required by downstream tasks.
    """
    path = manifest_path or MANIFEST_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Data manifest not found at {path}. "
            "Please ensure Phase 2 (Data Gap Resolution) has completed successfully."
        )
    return True

def get_encode_api_key(config: Dict[str, Any]) -> str:
    """
    Retrieve the ENCODE API key from config or environment variable.
    Raises an error if not found, as it is required for data ingestion.
    """
    key = config.get("encode_api_key") or os.getenv("ENCODE_API_KEY")
    if not key:
        raise ValueError(
            "ENCODE API key not found. Set it in 'code/config/environment.yaml' "
            "or as the 'ENCODE_API_KEY' environment variable."
        )
    return key

def get_data_paths(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Retrieve data paths from config, falling back to defaults if missing.
    """
    paths = config.get("data_paths", {})
    defaults = {
        "raw": str(OUTPUT_DIRS["raw"]),
        "processed": str(OUTPUT_DIRS["processed"]),
        "models": str(OUTPUT_DIRS["models"]),
        "interpretation": str(OUTPUT_DIRS["interpretation"]),
        "figures": str(OUTPUT_DIRS["figures"]),
    }
    return {k: paths.get(k, v) for k, v in defaults.items()}

def ensure_directories(paths: Dict[str, str]) -> None:
    """
    Create all necessary directories if they do not exist.
    """
    for dir_path in paths.values():
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    # Ensure logs directory exists
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

def write_sample_config(output_path: Optional[Path] = None) -> Path:
    """
    Write a sample environment configuration file if one does not exist.
    """
    path = output_path or CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    sample_config = {
        "encode_api_key": "YOUR_ENCODE_API_KEY_HERE",
        "data_paths": {
            "raw": str(OUTPUT_DIRS["raw"]),
            "processed": str(OUTPUT_DIRS["processed"]),
            "models": str(OUTPUT_DIRS["models"]),
            "interpretation": str(OUTPUT_DIRS["interpretation"]),
            "figures": str(OUTPUT_DIRS["figures"]),
        },
        "logging": {
            "level": "INFO",
            "file": str(PROJECT_ROOT / "logs" / "pipeline.log"),
        },
        "notes": [
            "Replace 'YOUR_ENCODE_API_KEY_HERE' with your actual ENCODE API key.",
            "This key is required to download ChIP-seq and ATAC-seq data.",
            "Paths are relative to the project root but can be absolute.",
        ],
    }

    with open(path, "w") as f:
        yaml.dump(sample_config, f, default_flow_style=False)

    return path

def main() -> None:
    """
    Main entry point for environment setup.
    Validates manifest, ensures directories, and writes sample config if needed.
    """
    print("Initializing environment configuration...")

    # Ensure config exists
    if not CONFIG_PATH.exists():
        print("No config found. Creating sample configuration file...")
        write_sample_config()
        print(f"Sample config written to {CONFIG_PATH}. Please update with your API key.")
        sys.exit(1)

    # Load config
    config = load_env_config()

    # Validate manifest
    try:
        validate_manifest_exists()
        print("Data manifest found. Proceeding.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Get API key (will raise if missing)
    try:
        api_key = get_encode_api_key(config)
        if api_key == "YOUR_ENCODE_API_KEY_HERE":
            print("Warning: ENCODE API key is still a placeholder. Please update config.")
            # Do not exit here, as the key might be in the environment
        else:
            print("ENCODE API key configured.")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Get paths and ensure directories
    paths = get_data_paths(config)
    ensure_directories(paths)
    print(f"Directories ensured: {list(paths.keys())}")

    # Log configuration summary (without sensitive data)
    print("Environment setup complete.")
    print(f"  Config: {CONFIG_PATH}")
    print(f"  Manifest: {MANIFEST_PATH}")
    print(f"  Data paths: {paths}")

if __name__ == "__main__":
    main()
