"""
Provenance generation utilities for the fMRI analysis pipeline.

This module generates machine-readable YAML sidecars for every preprocessed file,
recording pipeline version, parameters, and execution context to satisfy
Constitution Principle VI (Provenance).
"""

import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# Pipeline version for tracking
PIPELINE_VERSION = "1.0.0"
PIPELINE_NAME = "social-exclusion-reward-pipeline"


def generate_provenance_sidecar(
    input_file: str,
    output_file: str,
    pipeline_version: str = PIPELINE_VERSION,
    pipeline_name: str = PIPELINE_NAME,
    parameters: Optional[Dict[str, Any]] = None,
    software_versions: Optional[Dict[str, str]] = None,
    execution_id: Optional[str] = None,
) -> str:
    """
    Generate a YAML provenance sidecar file for a processed data file.

    Args:
        input_file: Path to the input file (raw/intermediate data)
        output_file: Path to the output file (processed data)
        pipeline_version: Version of the processing pipeline
        pipeline_name: Name of the pipeline
        parameters: Dictionary of processing parameters used
        software_versions: Dictionary of software versions (e.g., {'nibabel': '5.1.0'})
        execution_id: Unique execution identifier (auto-generated if None)

    Returns:
        Path to the generated YAML sidecar file

    Sidecar naming convention: {output_file}_provenance.yaml
    """
    if execution_id is None:
        execution_id = str(uuid.uuid4())

    timestamp = datetime.now(timezone.utc).isoformat()

    # Build provenance data structure
    provenance_data = {
        "@context": {
            "prov": "http://www.w3.org/ns/prov#",
            "schema": "http://schema.org/",
            "dct": "http://purl.org/dc/terms/",
        },
        "id": execution_id,
        "type": "prov:Activity",
        "dct:identifier": execution_id,
        "dct:title": f"{pipeline_name} execution",
        "dct:created": timestamp,
        "dct:modified": timestamp,
        "prov:startedAtTime": timestamp,
        "prov:endedAtTime": timestamp,
        "pipeline": {
            "name": pipeline_name,
            "version": pipeline_version,
        },
        "parameters": parameters or {},
        "software": software_versions or {},
        "inputs": [
            {
                "path": str(input_file),
                "type": "prov:Entity",
            }
        ],
        "outputs": [
            {
                "path": str(output_file),
                "type": "prov:Entity",
                "generatedAtTime": timestamp,
            }
        ],
        "provenance_version": "1.0",
    }

    # Generate sidecar file path
    output_path = Path(output_file)
    sidecar_path = output_path.with_name(
        f"{output_path.stem}_provenance{output_path.suffix}.yaml"
    )

    # Write YAML sidecar
    with open(sidecar_path, "w", encoding="utf-8") as f:
        yaml.dump(
            provenance_data,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    return str(sidecar_path)


def generate_provenance_manifest(
    output_dir: str,
    manifest_path: Optional[str] = None,
    pipeline_version: str = PIPELINE_VERSION,
    pipeline_name: str = PIPELINE_NAME,
) -> str:
    """
    Generate a manifest file listing all provenance sidecars in a directory.

    Args:
        output_dir: Directory containing processed files and their sidecars
        manifest_path: Path for the manifest file (default: {output_dir}/provenance_manifest.yaml)
        pipeline_version: Version of the pipeline
        pipeline_name: Name of the pipeline

    Returns:
        Path to the generated manifest file
    """
    output_path = Path(output_dir)
    if manifest_path is None:
        manifest_path = str(output_path / "provenance_manifest.yaml")

    # Find all provenance sidecars
    sidecars = list(output_path.glob("*_provenance*.yaml"))

    manifest_data = {
        "@context": {
            "prov": "http://www.w3.org/ns/prov#",
            "schema": "http://schema.org/",
            "dct": "http://purl.org/dc/terms/",
        },
        "pipeline": {
            "name": pipeline_name,
            "version": pipeline_version,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest_id": str(uuid.uuid4()),
        "total_sidecars": len(sidecars),
        "sidecars": [],
    }

    for sidecar in sorted(sidecars):
        # Load sidecar to extract metadata
        try:
            with open(sidecar, "r", encoding="utf-8") as f:
                sidecar_data = yaml.safe_load(f)

            # Extract key information
            sidecar_entry = {
                "file": str(sidecar),
                "execution_id": sidecar_data.get("id", "unknown"),
                "created": sidecar_data.get("dct:created", "unknown"),
                "input_file": sidecar_data.get("inputs", [{}])[0].get("path", "unknown"),
                "output_file": sidecar_data.get("outputs", [{}])[0].get("path", "unknown"),
            }
            manifest_data["sidecars"].append(sidecar_entry)
        except Exception as e:
            # Log error but continue processing
            manifest_data["sidecars"].append(
                {
                    "file": str(sidecar),
                    "error": str(e),
                }
            )

    # Write manifest
    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.dump(
            manifest_data,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    return str(manifest_path)


def get_software_versions() -> Dict[str, str]:
    """
    Get versions of key software dependencies used in the pipeline.

    Returns:
        Dictionary mapping package names to versions
    """
    versions = {}

    # Try to import and get versions
    packages = ["nibabel", "numpy", "pandas", "nilearn", "scipy", "statsmodels"]

    for package in packages:
        try:
            module = __import__(package)
            if hasattr(module, "__version__"):
                versions[package] = module.__version__
            elif hasattr(module, "version"):
                versions[package] = module.version.version
        except (ImportError, AttributeError):
            versions[package] = "not installed"

    return versions


def main():
    """
    Command-line interface for provenance generation.

    Usage:
        python -m code.utils.provenance --input input.nii.gz --output output.nii.gz --params '{"smoothing": 6}'
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Generate provenance sidecar for processed fMRI files"
    )
    parser.add_argument(
        "--input", "-i", required=True, help="Input file path"
    )
    parser.add_argument(
        "--output", "-o", required=True, help="Output file path"
    )
    parser.add_argument(
        "--params",
        "-p",
        type=json.loads,
        default={},
        help="JSON string of processing parameters",
    )
    parser.add_argument(
        "--pipeline-version",
        default=PIPELINE_VERSION,
        help=f"Pipeline version (default: {PIPELINE_VERSION})",
    )
    parser.add_argument(
        "--manifest-dir",
        help="Generate manifest in this directory after creating sidecar",
    )

    args = parser.parse_args()

    # Get software versions
    software_versions = get_software_versions()

    # Generate sidecar
    sidecar_path = generate_provenance_sidecar(
        input_file=args.input,
        output_file=args.output,
        parameters=args.params,
        software_versions=software_versions,
        pipeline_version=args.pipeline_version,
    )

    print(f"Generated provenance sidecar: {sidecar_path}")

    # Generate manifest if requested
    if args.manifest_dir:
        manifest_path = generate_provenance_manifest(
            output_dir=args.manifest_dir,
            pipeline_version=args.pipeline_version,
        )
        print(f"Generated provenance manifest: {manifest_path}")


if __name__ == "__main__":
    main()
