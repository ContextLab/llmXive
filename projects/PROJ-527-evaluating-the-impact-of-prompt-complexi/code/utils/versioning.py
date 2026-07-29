"""
Artifact versioning utility for the llmXive pipeline.

This module manages the state file that tracks generated artifacts,
their checksums, and metadata for reproducibility.
"""
import os
import yaml
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import get_project_id, Paths
from utils.logger import get_logger


logger = get_logger(__name__)


def get_state_file_path() -> Path:
    """
    Determine the path to the project state YAML file.
    
    The filename is derived from the project ID as per task requirements.
    Returns the full path to `state/projects/<project_id>.yaml`.
    """
    project_id = get_project_id()
    # Ensure the directory exists
    state_dir = Paths.state / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{project_id}.yaml"
    return state_dir / filename


def load_state_file() -> Dict[str, Any]:
    """
    Load the existing state file or return a fresh structure if it doesn't exist.
    """
    path = get_state_file_path()
    if not path.exists():
        return {
            "project_id": get_project_id(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None,
            "artifacts": [],
            "metadata": {}
        }
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data is None:
                return {
                    "project_id": get_project_id(),
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": None,
                    "artifacts": [],
                    "metadata": {}
                }
            return data
    except Exception as e:
        logger.error(f"Failed to load state file {path}: {e}")
        raise


def compute_artifact_checksums(file_paths: List[Path]) -> Dict[str, str]:
    """
    Compute SHA-256 checksums for a list of file paths.
    
    Args:
        file_paths: List of Path objects to checksum.
        
    Returns:
        Dictionary mapping relative path string to hex checksum.
    """
    checksums = {}
    for p in file_paths:
        if not p.exists():
            logger.warning(f"File not found for checksum: {p}")
            continue
        
        sha256_hash = hashlib.sha256()
        try:
            with open(p, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            # Store relative path from project root for portability
            rel_path = str(p.relative_to(Paths.root))
            checksums[rel_path] = sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to checksum {p}: {e}")
    
    return checksums


def update_state_file(
    artifacts: List[Dict[str, Any]], 
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Update the project state YAML file with new artifact records and metadata.
    
    Args:
        artifacts: List of artifact dictionaries to append/update.
        metadata: Optional dictionary of additional metadata to merge.
    """
    state = load_state_file()
    
    # Update timestamp
    now = datetime.utcnow().isoformat()
    state["updated_at"] = now
    
    # Merge metadata if provided
    if metadata:
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"].update(metadata)
    
    # Append or update artifacts
    existing_ids = {a.get("id") for a in state.get("artifacts", [])}
    for artifact in artifacts:
        art_id = artifact.get("id")
        if art_id and art_id in existing_ids:
            # Update existing
            idx = next(
                (i for i, a in enumerate(state["artifacts"]) if a.get("id") == art_id),
                None
            )
            if idx is not None:
                state["artifacts"][idx].update(artifact)
            else:
                state["artifacts"].append(artifact)
        else:
            # New artifact
            if not art_id:
                artifact["id"] = f"art_{now.replace(':', '-').replace('.', '-')}"
            state["artifacts"].append(artifact)
    
    # Write back
    path = get_state_file_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        logger.info(f"Updated state file: {path}")
    except Exception as e:
        logger.error(f"Failed to write state file {path}: {e}")
        raise


def record_data_generation_state(
    output_files: List[Path],
    generation_params: Optional[Dict[str, Any]] = None
) -> None:
    """
    Record the state of data generation artifacts into the project YAML.
    
    This function computes checksums for the provided output files and
    updates the state file at `state/projects/<project_id>.yaml`.
    
    Args:
        output_files: List of file paths that were generated.
        generation_params: Dictionary of parameters used during generation.
    """
    if not output_files:
        logger.warning("No output files provided to record_data_generation_state")
        return

    checksums = compute_artifact_checksums(output_files)
    
    artifacts = []
    for file_path in output_files:
        rel_path = str(file_path.relative_to(Paths.root))
        checksum = checksums.get(rel_path, "unknown")
        
        # Extract file stats
        stat = file_path.stat()
        
        artifact_record = {
            "id": f"gen_{file_path.stem}_{int(stat.st_mtime)}",
            "path": rel_path,
            "checksum": checksum,
            "size_bytes": stat.st_size,
            "created_at": datetime.utcfromtimestamp(stat.st_mtime).isoformat(),
            "type": "generated_data"
        }
        artifacts.append(artifact_record)
    
    metadata = generation_params or {}
    metadata["generation_timestamp"] = datetime.utcnow().isoformat()
    metadata["file_count"] = len(output_files)
    
    update_state_file(artifacts, metadata)
    logger.info(f"Recorded {len(output_files)} artifacts in state file.")


def main() -> None:
    """
    CLI entry point for the versioning utility.
    
    Usage:
        python -m code.utils.versioning --record data/processed/prompt_variants.parquet
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Manage project artifact versioning")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Record command
    record_parser = subparsers.add_parser("record", help="Record data generation artifacts")
    record_parser.add_argument(
        "files", 
        nargs="+", 
        help="Paths to generated files to record"
    )
    record_parser.add_argument(
        "--params",
        type=str,
        default="{}",
        help="JSON string of generation parameters"
    )

    args = parser.parse_args()

    if args.command == "record":
        try:
            import json
            params = json.loads(args.params)
            file_paths = [Paths.root / p for p in args.files]
            record_data_generation_state(file_paths, params)
            print(f"Successfully recorded artifacts for project {get_project_id()}")
        except Exception as e:
            logger.error(f"Record failed: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()