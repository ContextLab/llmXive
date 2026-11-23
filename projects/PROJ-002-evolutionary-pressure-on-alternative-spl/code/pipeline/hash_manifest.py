"""
Artifact hashing and manifest generation for PROJ-002.
"""
import os
from code.utils.hash import generate_manifest
from code.utils.logger import setup_logger, log

setup_logger("pipeline.log", level="INFO")

def generate_pipeline_manifest(output_path: str = "artifacts_manifest.json") -> None:
    """
    Generate a manifest of all pipeline artifacts.

    Args:
        output_path: Path to write the manifest.
    """
    # Define artifacts to hash
    artifacts = [
        "data/raw/human/GRCh38.fa",
        "data/interim/psi_table.tsv",
        "data/processed/lse_list.tsv",
        "pipeline.log",
        "metadata.json",
        "lifecycle_manifest.json",
        "data/raw/tree/primate_tree.nwk",
    ]

    # Filter existing files
    existing_artifacts = [f for f in artifacts if os.path.exists(f)]
    log.info(f"Generating manifest for {len(existing_artifacts)} artifacts.")

    manifest = generate_manifest(existing_artifacts, output_path)
    log.info(f"Manifest written to {output_path}")

def main():
    """
    Main entry point for manifest generation.
    """
    generate_pipeline_manifest()

if __name__ == "__main__":
    main()
