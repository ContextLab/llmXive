"""
Versioning module for llmXive project state management.
Computes SHA-256 hashes for data/code artifacts and updates project state.
"""
import os
import hashlib
import yaml
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging for this module
logger = logging.getLogger(__name__)

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string representation of the SHA-256 hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {str(e)}")

def compute_directory_hash(dir_path: str, extensions: Optional[List[str]] = None) -> str:
    """
    Compute a combined SHA-256 hash for all files in a directory.
    
    Args:
        dir_path: Path to the directory
        extensions: Optional list of file extensions to include (e.g., ['.py', '.csv'])
                   If None, all files are included
                   
    Returns:
        Hexadecimal string representation of the combined hash
        
    Raises:
        FileNotFoundError: If the directory does not exist
    """
    path = Path(dir_path)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
        
    combined_hash = hashlib.sha256()
    
    # Sort files for deterministic ordering
    files = sorted(path.rglob('*'))
    
    for file_path in files:
        if file_path.is_file():
            # Filter by extension if specified
            if extensions is None or file_path.suffix in extensions:
                file_hash = compute_sha256(str(file_path))
                # Include relative path in hash to detect renames
                rel_path = str(file_path.relative_to(path))
                combined_hash.update(rel_path.encode('utf-8'))
                combined_hash.update(file_hash.encode('utf-8'))
                
    return combined_hash.hexdigest()

def load_state(state_path: str) -> Dict[str, Any]:
    """
    Load project state from YAML file.
    
    Args:
        state_path: Path to the state YAML file
        
    Returns:
        Dictionary containing the project state
        
    Raises:
        FileNotFoundError: If the state file does not exist
        yaml.YAMLError: If the file is not valid YAML
    """
    path = Path(state_path)
    if not path.exists():
        # Initialize empty state structure if file doesn't exist
        logger.info(f"State file not found, creating new state: {state_path}")
        return {
            "projects": {},
            "last_updated": None
        }
        
    try:
        with open(path, 'r') as f:
            state = yaml.safe_load(f)
            if state is None:
                return {"projects": {}, "last_updated": None}
            return state
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file {state_path}: {str(e)}")

def save_state(state: Dict[str, Any], state_path: str) -> None:
    """
    Save project state to YAML file.
    
    Args:
        state: Dictionary containing the project state
        state_path: Path to the state YAML file
        
    Raises:
        IOError: If the file cannot be written
    """
    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(path, 'w') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State saved to {state_path}")
    except IOError as e:
        raise IOError(f"Error writing state file {state_path}: {str(e)}")

def load_reviews(reviews_path: str) -> Dict[str, Any]:
    """
    Load review records from YAML file.
    
    Args:
        reviews_path: Path to the reviews YAML file
        
    Returns:
        Dictionary containing review records
    """
    path = Path(reviews_path)
    if not path.exists():
        logger.info(f"Reviews file not found: {reviews_path}")
        return {"reviews": []}
        
    try:
        with open(path, 'r') as f:
            reviews = yaml.safe_load(f)
            if reviews is None:
                return {"reviews": []}
            return reviews
    except Exception as e:
        logger.warning(f"Error loading reviews file {reviews_path}: {str(e)}")
        return {"reviews": []}

def save_reviews(reviews: Dict[str, Any], reviews_path: str) -> None:
    """
    Save review records to YAML file.
    
    Args:
        reviews: Dictionary containing review records
        reviews_path: Path to the reviews YAML file
    """
    path = Path(reviews_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        yaml.dump(reviews, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Reviews saved to {reviews_path}")

def invalidate_stale_reviews(state: Dict[str, Any], reviews: Dict[str, Any], 
                             project_id: str, artifact_hashes: Dict[str, str]) -> Dict[str, Any]:
    """
    Invalidate review records for artifacts whose hashes have changed.
    
    IMPORTANT: This function is NOT called by the versioning script itself.
    Per Constitution Principle V, review invalidation is the sole responsibility
    of the Advancement-Evaluator Agent. This function is provided for that agent
    to use when needed.
    
    Args:
        state: Current project state
        reviews: Current review records
        project_id: Project identifier
        artifact_hashes: Current artifact hashes from state
        
    Returns:
        Updated reviews dictionary with stale reviews marked as invalid
    """
    # This is a no-op in the versioning script context.
    # The actual invalidation logic belongs to the Advancement-Evaluator Agent.
    logger.info("Review invalidation skipped - handled by Advancement-Evaluator Agent")
    return reviews

def update_version_state(state_path: str, project_id: str, 
                         artifacts_to_hash: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Update the project state with new artifact hashes.
    
    Args:
        state_path: Path to the state YAML file
        project_id: Project identifier
        artifacts_to_hash: List of artifact paths to hash. If None, hashes all
                          standard project directories (code/, data/, tests/)
                          
    Returns:
        Updated state dictionary
        
    Raises:
        FileNotFoundError: If an artifact to hash does not exist
    """
    state = load_state(state_path)
    
    # Initialize project entry if it doesn't exist
    if project_id not in state.get("projects", {}):
        state["projects"][project_id] = {
            "artifact_hashes": {},
            "updated_at": None,
            "version": 1
        }
    
    project_state = state["projects"][project_id]
    current_hashes = project_state.get("artifact_hashes", {})
    
    # Define default directories to hash if none specified
    if artifacts_to_hash is None:
        artifacts_to_hash = [
            "code",
            "data/processed",
            "data/raw",
            "tests"
        ]
    
    new_hashes = {}
    hashed_count = 0
    
    for artifact_path in artifacts_to_hash:
        full_path = Path(artifact_path)
        
        if not full_path.exists():
            logger.warning(f"Artifact path does not exist, skipping: {artifact_path}")
            continue
        
        try:
            if full_path.is_file():
                  file_hash = compute_sha256(str(full_path))
                  new_hashes[artifact_path] = file_hash
                  logger.info(f"Hashed file: {artifact_path} -> {file_hash[:16]}...")
                  hashed_count += 1
            elif full_path.is_dir():
                  dir_hash = compute_directory_hash(str(full_path))
                  new_hashes[artifact_path] = dir_hash
                  logger.info(f"Hashed directory: {artifact_path} -> {dir_hash[:16]}...")
                  hashed_count += 1
        except Exception as e:
            logger.error(f"Error hashing {artifact_path}: {str(e)}")
            raise
    
    # Update state
    project_state["artifact_hashes"] = new_hashes
    project_state["updated_at"] = datetime.utcnow().isoformat() + "Z"
    project_state["version"] = project_state.get("version", 0) + 1
    state["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    # Save updated state
    save_state(state, state_path)
    
    logger.info(f"Successfully updated state for {project_id}. Hashed {hashed_count} artifacts.")
    return state

def main():
    """
    Main entry point for the versioning script.
    """
    parser = argparse.ArgumentParser(
        description="Compute SHA-256 hashes for project artifacts and update state."
    )
    parser.add_argument(
        "--state-path",
        type=str,
        default="state/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig.yaml",
        help="Path to the project state YAML file"
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default="PROJ-786-multi-property-trade-offs-in-alloy-desig",
        help="Project identifier"
    )
    parser.add_argument(
        "--artifacts",
        type=str,
        nargs="*",
        default=None,
        help="List of artifact paths to hash (directories or files). If omitted, "
             "defaults to code/, data/processed, data/raw, tests/"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info(f"Starting versioning update for project: {args.project_id}")
    logger.info(f"State file: {args.state_path}")
    
    try:
        updated_state = update_version_state(
            state_path=args.state_path,
            project_id=args.project_id,
            artifacts_to_hash=args.artifacts
        )
        
        # Output summary
        print("\n" + "="*60)
        print("VERSIONING UPDATE COMPLETE")
        print("="*60)
        print(f"Project ID: {args.project_id}")
        print(f"Updated at: {updated_state['projects'][args.project_id]['updated_at']}")
        print(f"Version: {updated_state['projects'][args.project_id]['version']}")
        print(f"Artifacts hashed: {len(updated_state['projects'][args.project_id]['artifact_hashes'])}")
        
        print("\nArtifact Hashes:")
        for path, hash_val in updated_state['projects'][args.project_id]['artifact_hashes'].items():
            print(f"  {path}: {hash_val[:32]}...")
        
        print("="*60)
        logger.info("Versioning update completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Error during versioning update: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())
