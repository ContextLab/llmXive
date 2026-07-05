"""
Script to generate the project manifest.json for the audit pipeline.
This script is intended to be run after the pipeline produces its output artifacts.
"""
import argparse
import logging
import sys
from pathlib import Path

from code.src.utils.manifest import generate_manifest
from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Generate manifest.json with SHA256 hashes for pipeline artifacts."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/manifest.json",
        help="Path to the output manifest.json file."
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Base directory for computing relative paths (default: current directory)."
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="List of file paths to include in the manifest."
    )

    args = parser.parse_args()

    artifact_paths = [Path(p) for p in args.files]
    output_path = Path(args.output)
    base_dir = Path(args.base_dir)

    logger.info(f"Generating manifest at {output_path} for {len(artifact_paths)} files.")
    
    try:
        manifest = generate_manifest(artifact_paths, output_path, base_dir)
        logger.info(f"Manifest generation successful. Included {len(manifest['artifacts'])} artifacts.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Failed to generate manifest: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())