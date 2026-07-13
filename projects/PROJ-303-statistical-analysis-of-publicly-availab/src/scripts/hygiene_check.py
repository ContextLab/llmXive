"""
Hygiene Check Script for llmXive Pipeline.

Computes SHA-256 hashes for all raw data files in the project's data/raw directory
and writes the results to a YAML file in state/projects/<project_id>/hygiene.yaml.

This script depends on T005-exec (citation validation) having passed, ensuring
that the data sources are valid before hashing.
"""

import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

import yaml

# Import config from the project's src module
from src.config import get_config


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}")


def scan_raw_data_directory(data_dir: Path) -> List[Path]:
    """
    Recursively scan the raw data directory for all files.

    Args:
        data_dir: Path to the raw data directory.

    Returns:
        List of paths to all files found.
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {data_dir}")

    files = []
    for root, _, filenames in os.walk(data_dir):
        for filename in filenames:
            # Skip hidden files or temporary files
            if filename.startswith('.') or filename.endswith('.tmp'):
                continue
            files.append(Path(root) / filename)

    if not files:
        raise ValueError(f"No files found in raw data directory: {data_dir}")

    return files


def generate_hygiene_report(file_paths: List[Path], project_id: str) -> Dict[str, Any]:
    """
    Generate the hygiene report dictionary.

    Args:
        file_paths: List of file paths to hash.
        project_id: The project identifier.

    Returns:
        Dictionary containing the report structure.
    """
    report = {
        "project_id": project_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success",
        "files": []
    }

    for file_path in sorted(file_paths):
        relative_path = file_path.relative_to(file_path.parents[2]) if len(file_path.parents) >= 3 else file_path
        file_hash = compute_sha256(file_path)
        file_size = file_path.stat().st_size

        report["files"].append({
            "path": str(relative_path),
            "size_bytes": file_size,
            "sha256": file_hash
        })

    # Calculate aggregate checksums for integrity verification
    combined_hash_input = "".join([f["sha256"] for f in report["files"]])
    report["aggregate_hash"] = hashlib.sha256(combined_hash_input.encode()).hexdigest()
    report["total_files"] = len(report["files"])

    return report


def write_hygiene_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Write the hygiene report to a YAML file.

    Args:
        report: The report dictionary.
        output_path: Path where the YAML file should be written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)
        print(f"Hygiene report written to: {output_path}")
    except IOError as e:
        raise RuntimeError(f"Failed to write hygiene report: {e}")


def main() -> int:
    """
    Main entry point for the hygiene check script.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        config = get_config()
        project_id = config.get("project_id", "unknown")
        raw_data_dir = config.get("raw_data_dir", "data/raw")
        state_dir = config.get("state_dir", "state/projects")

        # Ensure paths are Path objects
        raw_data_path = Path(raw_data_dir)
        state_path = Path(state_dir)

        print(f"Starting hygiene check for project: {project_id}")
        print(f"Scanning raw data directory: {raw_data_path}")

        # Scan for files
        files = scan_raw_data_directory(raw_data_path)
        print(f"Found {len(files)} files to hash.")

        # Generate report
        report = generate_hygiene_report(files, project_id)

        # Determine output path
        output_file_name = f"{project_id}_hygiene.yaml"
        output_path = state_path / project_id / output_file_name

        # Write report
        write_hygiene_report(report, output_path)

        print("Hygiene check completed successfully.")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Critical Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
