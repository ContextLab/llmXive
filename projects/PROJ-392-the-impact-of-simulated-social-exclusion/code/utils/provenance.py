import datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Constants for pipeline versioning (hardcoded for reproducibility)
PIPELINE_VERSION = "1.0.0"
PIPELINE_NAME = "llmXive-social-exclusion-preprocessing"

def generate_provenance_record(
    input_file: str,
    output_file: str,
    parameters: Optional[Dict[str, Any]] = None,
    software_versions: Optional[Dict[str, str]] = None,
    checksums: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Generate a machine-readable provenance record for a single processing step.

    Args:
        input_file: Path to the input file (relative or absolute).
        output_file: Path to the output file (relative or absolute).
        parameters: Dictionary of parameters used in the processing step.
        software_versions: Dictionary of software tools and their versions.
        checksums: Dictionary of checksums for input and output files.

    Returns:
        A dictionary representing the provenance record.
    """
    record = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@type": "File",
        "name": os.path.basename(output_file),
        "path": str(output_file),
        "dateCreated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pipeline": {
            "name": PIPELINE_NAME,
            "version": PIPELINE_VERSION,
        },
        "parameters": parameters or {},
        "software": software_versions or {},
        "checksums": checksums or {},
        "inputs": [str(input_file)],
        "outputs": [str(output_file)],
    }

    # Add host info if available
    try:
        import platform
        record["host"] = {
            "platform": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        }
    except Exception:
        pass

    return record

def write_provenance_sidecar(
    output_file: str,
    record: Dict[str, Any],
    sidecar_dir: Optional[Path] = None,
) -> Path:
    """
    Write a YAML sidecar file for the given output file.

    The sidecar file will be named <output_file_basename>.provenance.yaml
    and placed in the same directory as the output file, or in a specified
    sidecar directory.

    Args:
        output_file: Path to the output file.
        record: The provenance record dictionary.
        sidecar_dir: Optional directory to place the sidecar file. If None,
                     the sidecar is placed next to the output file.

    Returns:
        Path to the created sidecar file.
    """
    output_path = Path(output_file)
    if sidecar_dir:
        sidecar_path = sidecar_dir / f"{output_path.stem}.provenance.yaml"
    else:
        sidecar_path = output_path.parent / f"{output_path.stem}.provenance.yaml"

    # Ensure parent directory exists
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)

    with open(sidecar_path, "w", encoding="utf-8") as f:
        yaml.dump(record, f, default_flow_style=False, sort_keys=False)

    return sidecar_path

def main():
    """
    Command-line interface for generating provenance sidecars.

    Usage:
        python -m code.utils.provenance --input <input_file> --output <output_file>
                                        [--params <json_string>]
                                        [--software <json_string>]
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Generate YAML provenance sidecars for preprocessed fMRI files."
    )
    parser.add_argument(
        "--input", required=True, help="Path to the input file (e.g., raw NIfTI)."
    )
    parser.add_argument(
        "--output", required=True, help="Path to the output file (e.g., preprocessed NIfTI)."
    )
    parser.add_argument(
        "--params",
        type=str,
        default="{}",
        help="JSON string of processing parameters (e.g., {'smoothing': 6}).",
    )
    parser.add_argument(
        "--software",
        type=str,
        default="{}",
        help="JSON string of software versions (e.g., {'fmriprep': '23.1.0'}).",
    )
    parser.add_argument(
        "--sidecar-dir",
        type=str,
        default=None,
        help="Directory to place sidecar files. Defaults to output file directory.",
    )

    args = parser.parse_args()

    try:
        params = json.loads(args.params)
        software = json.loads(args.software)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON arguments: {e}", file=sys.stderr)
        sys.exit(1)

    # Compute checksums if files exist
    checksums = {}
    for label, path in [("input", args.input), ("output", args.output)]:
        p = Path(path)
        if p.exists():
          # Use a simple hash for demonstration; in production, use SHA256
          checksums[label] = hashlib.md5(p.read_bytes()).hexdigest()
        else:
          checksums[label] = "not_found"

    record = generate_provenance_record(
        input_file=args.input,
        output_file=args.output,
        parameters=params,
        software_versions=software,
        checksums=checksums,
    )

    sidecar_dir = Path(args.sidecar_dir) if args.sidecar_dir else None
    sidecar_path = write_provenance_sidecar(args.output, record, sidecar_dir)

    print(f"Provenance sidecar written to: {sidecar_path}")


if __name__ == "__main__":
    main()