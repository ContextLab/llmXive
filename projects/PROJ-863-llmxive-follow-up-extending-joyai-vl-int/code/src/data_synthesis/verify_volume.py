"""
Volume Verification Module for llmXive.

Verifies that the generated dataset meets the required volume thresholds.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

from src.utils.logging import get_logger
from src.utils.env_config import load_environment_config

logger = get_logger(__name__)

def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """Load the manifest file."""
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        return json.load(f)

def calculate_total_duration(manifest: Dict[str, Any]) -> float:
    """
    Calculate the total duration of all chunks in the manifest.

    Args:
        manifest: The manifest dictionary.

    Returns:
        Total duration in seconds.
    """
    total = 0.0
    for chunk in manifest.get("chunks", []):
        total += chunk.get("end_time", 0) - chunk.get("start_time", 0)
    return total

def verify_volume(manifest_path: str, required_seconds: float = 180000.0, ci_mode: bool = False) -> bool:
    """
    Verify that the dataset meets the required volume.

    Args:
        manifest_path: Path to the manifest file.
        required_seconds: Required total duration in seconds (default: 50 hours).
        ci_mode: If True, use a lower threshold for CI runs.

    Returns:
        True if volume is sufficient, False otherwise.
    """
    load_environment_config()
    
    manifest = load_manifest(manifest_path)
    total_duration = calculate_total_duration(manifest)

    threshold = 180000.0 if not ci_mode else 3600.0  # 50h vs 1h for CI

    logger.info(f"Total duration: {total_duration:.2f} seconds ({total_duration/3600:.2f} hours)")
    logger.info(f"Required threshold: {threshold:.2f} seconds ({threshold/3600:.2f} hours)")

    if total_duration >= threshold:
        logger.info("Volume verification PASSED.")
        return True
    else:
        logger.error(f"Volume verification FAILED. Expected >= {threshold} seconds, got {total_duration} seconds.")
        return False

def main():
    """CLI entry point for volume verification."""
    import argparse

    parser = argparse.ArgumentParser(description="Verify dataset volume.")
    parser.add_argument("--manifest", type=str, default="data/manifest.json", help="Path to manifest file")
    parser.add_argument("--ci", action="store_true", help="Run in CI mode (lower threshold)")
    
    args = parser.parse_args()

    success = verify_volume(args.manifest, ci_mode=args.ci)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
