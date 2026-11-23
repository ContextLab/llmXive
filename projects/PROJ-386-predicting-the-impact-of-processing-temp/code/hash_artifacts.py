"""
Artifact hashing and checksum management for the project.
Provides utilities to calculate file hashes, hash directories, and save manifests.
"""
import os
import sys
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import yaml

# Project root relative to code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-386-predicting-the-impact-of-processing-temp.yaml"


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the hash of a file.
    
    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hex digest of the file hash
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot calculate hash: file not found at {file_path}")
        
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
            
    return hash_func.hexdigest()


def hash_directory(dir_path: Path, algorithm: str = "sha256", exclude_patterns: Optional[list] = None) -> Dict[str, str]:
    """
    Calculate hashes for all files in a directory recursively.
    
    Args:
        dir_path: Path to the directory
        algorithm: Hash algorithm to use
        exclude_patterns: List of filename patterns to exclude
        
    Returns:
        Dictionary mapping relative file paths to their hashes
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
        
    exclude_patterns = exclude_patterns or []
    hashes = {}
    
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            # Check exclusion patterns
            should_exclude = False
            rel_name = file_path.name
            for pattern in exclude_patterns:
                if pattern in rel_name:
                    should_exclude = True
                    break
                    
            if not should_exclude:
                try:
                    rel_path = file_path.relative_to(dir_path)
                    hashes[str(rel_path)] = calculate_file_hash(file_path, algorithm)
                except ValueError:
                    # Skip files outside the directory
                    continue
                    
    return hashes


def load_state() -> Dict[str, Any]:
    """
    Load the project state YAML file.
    
    Returns:
        Dictionary containing the project state
    """
    if not STATE_FILE_PATH.exists():
        raise FileNotFoundError(f"State file not found: {STATE_FILE_PATH}")
        
    with open(STATE_FILE_PATH, "r") as f:
        return yaml.safe_load(f)


def save_state(state: Dict[str, Any]) -> None:
    """
    Save the project state to the YAML file.
    
    Args:
        state: Dictionary containing the project state
    """
    STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(STATE_FILE_PATH, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def update_artifact_checksum(artifact_name: str, file_path: str) -> bool:
    """
    Update the checksum for a specific artifact in the state file.
    
    Args:
        artifact_name: The logical name of the artifact (e.g., 'data_ingestion')
        file_path: Relative path to the artifact file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        state = load_state()
        
        if artifact_name not in state.get("artifact_registry", {}):
            print(f"Warning: Artifact '{artifact_name}' not found in registry")
            return False
            
        full_path = PROJECT_ROOT / file_path
        
        if not full_path.exists():
            print(f"Warning: Artifact file not found at {full_path}")
            return False
            
        # Get hash algorithm from state or default to sha256
        algo = state["artifact_registry"][artifact_name].get("hash_algorithm", "sha256")
        checksum = calculate_file_hash(full_path, algo)
        
        # Update state
        state["artifact_registry"][artifact_name]["checksum"] = checksum
        state["artifact_registry"][artifact_name]["generated_at"] = datetime.utcnow().isoformat()
        
        # Update validation check if applicable
        if artifact_name == "collinearity_report":
            state["validation_checks"]["collinearity_report_exists"] = True
            
        save_state(state)
        print(f"Updated checksum for {artifact_name}: {checksum[:16]}...")
        return True
        
    except Exception as e:
        print(f"Error updating artifact checksum: {e}")
        return False


def save_manifest(output_path: Optional[Path] = None) -> None:
    """
    Generate and save a manifest of all artifacts and their checksums.
    
    Args:
        output_path: Optional path to save the manifest (defaults to data/artifacts/manifest.json)
    """
    state = load_state()
    manifest = {
        "generated_at": datetime.utcnow().isoformat(),
        "project_id": state["project_id"],
        "schema_version": state["schema_version"],
        "artifacts": {}
    }
    
    for name, info in state.get("artifact_registry", {}).items():
        if info.get("checksum"):
            manifest["artifacts"][name] = {
                "path": info["path"],
                "checksum": info["checksum"],
                "algorithm": info.get("hash_algorithm", "sha256"),
                "generated_at": info.get("generated_at"),
                "parent_artifacts": info.get("parent_artifacts", [])
            }
            
    output_path = output_path or PROJECT_ROOT / "data" / "artifacts" / "manifest.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Manifest saved to {output_path}")


def main():
    """CLI entry point for artifact hashing operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage artifact hashes and checksums")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Update checksum command
    update_parser = subparsers.add_parser("update", help="Update checksum for an artifact")
    update_parser.add_argument("artifact_name", help="Name of the artifact (e.g., data_ingestion)")
    update_parser.add_argument("file_path", help="Relative path to the artifact file")
    
    # Generate manifest command
    manifest_parser = subparsers.add_parser("manifest", help="Generate artifact manifest")
    manifest_parser.add_argument("--output", "-o", help="Output path for manifest")
    
    args = parser.parse_args()
    
    if args.command == "update":
        success = update_artifact_checksum(args.artifact_name, args.file_path)
        sys.exit(0 if success else 1)
    elif args.command == "manifest":
        output_path = Path(args.output) if args.output else None
        save_manifest(output_path)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
