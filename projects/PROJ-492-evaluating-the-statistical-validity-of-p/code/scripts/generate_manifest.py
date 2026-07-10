"""
Script to generate manifest.json with SHA256 hashes for all artifacts.
This script is invoked by the pipeline to fulfill FR-024.
"""
import argparse
import logging
import sys
from pathlib import Path

from code.src.utils.manifest import generate_manifest
from code.src.utils.logger import get_default_logger


def main():
    """Entry point for manifest generation script."""
    parser = argparse.ArgumentParser(
        description="Generate manifest.json with SHA256 hashes for pipeline artifacts"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory containing the artifacts to hash (default: output/)",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=None,
        help="Path to write the manifest (default: <output-dir>/manifest.json)",
    )

    args = parser.parse_args()
    logger = get_default_logger()

    try:
        logger.info(f"Starting manifest generation for: {args.output_dir}")

        manifest = generate_manifest(
            output_dir=args.output_dir,
            manifest_path=args.manifest_path,
            logger=logger,
        )

        logger.info("Manifest generation completed successfully")
        print(f"Manifest created at: {args.manifest_path or args.output_dir / 'manifest.json'}")
        print(f"Total files hashed: {manifest['total_files']}")

        return 0

    except Exception as e:
        logger.error(f"Manifest generation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
