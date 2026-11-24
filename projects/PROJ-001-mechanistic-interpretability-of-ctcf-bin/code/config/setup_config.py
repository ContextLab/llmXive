"""
Setup environment configuration management for ENCODE API keys and data paths.

This script generates a YAML configuration file (config/config.yaml) that
contains placeholders for the ENCODE API key and resolves the required data
directories based on the existing manifest.json produced by task T007.

The generated configuration can be loaded elsewhere in the project using
`config.config_loader.load_env_config()`.

Execution of this script will create the configuration file on disk.
"""
import json
import logging
from pathlib import Path

import yaml

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

CONFIG_RELATIVE_PATH = Path("config") / "config.yaml"


def _load_manifest(manifest_path: Path) -> dict:
    """Load the data manifest JSON."""
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest file not found at {manifest_path}")
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)
    return manifest


def generate_config() -> Path:
    """
    Generate a configuration YAML file with ENCODE API key placeholder and
    resolved data paths.

    Returns
    -------
    Path
        The absolute path to the written configuration file.
    """
    # Resolve paths based on project layout
    raw_dir = paths.data("raw")
    processed_dir = paths.data("processed")
    manifest_path = paths.data("manifest.json")

    # Ensure directories exist (paths.* helpers create parent folders)
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load manifest to verify its presence (will raise if missing)
    _ = _load_manifest(manifest_path)

    config_dict = {
        "api": {
            # Users should populate this with their ENCODE API key.
            "encode_api_key": ""
        },
        "data": {
            "raw_dir": str(raw_dir),
            "processed_dir": str(processed_dir),
            "manifest_path": str(manifest_path)
        }
    }

    # Write the YAML configuration file
    config_path = paths.path(*CONFIG_RELATIVE_PATH.parts)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config_dict, f, sort_keys=False)

    log.info("Configuration file written to %s", config_path)
    return config_path


def main() -> None:
    """CLI entry point."""
    try:
        cfg_path = generate_config()
        print(f"Configuration successfully written to: {cfg_path}")
    except Exception as exc:
        log.error("Failed to generate configuration: %s", exc)
        raise


if __name__ == "__main__":
    main()
