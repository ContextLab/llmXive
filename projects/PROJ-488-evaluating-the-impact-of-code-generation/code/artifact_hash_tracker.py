"""
Artifact Hash Tracker for PROJ-488-evaluating-the-impact-of-code-generation.

This module implements the tracking of artifact hashes (SHA-256) for major outputs
including datasets, metrics, statistics, and figures. It updates the central
state file: state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml
"""
import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union

# Import existing project utilities
from state_tracker import load_state_file, save_state_file, compute_file_hash, register_artifact_hash
from logging_config import setup_logger, get_logger

# Define project paths
PROJECT_ROOT = Path(__file__).parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
METRICS_DIR = PROJECT_ROOT / "data" / "metrics"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures"

# Initialize logger
logger = setup_logger("artifact_hash_tracker", level=logging.INFO)


def compute_hash_for_path(path: Union[str, Path]) -> Optional[str]:
    """
    Compute SHA-256 hash for a file or directory.
    
    Args:
        path: Path to file or directory
        
    Returns:
        SHA-256 hex string or None if path doesn't exist
    """
    path = Path(path)
    if not path.exists():
        logger.warning(f"Path does not exist: {path}")
        return None
    
    if path.is_file():
        return compute_file_hash(path)
    elif path.is_dir():
        # For directories, we compute a combined hash of all files
        return compute_directory_hash(path)
    return None


def compute_directory_hash(dir_path: Path) -> Optional[str]:
    """
    Compute a combined SHA-256 hash for all files in a directory.
    Files are processed in sorted order for reproducibility.
    
    Args:
        dir_path: Path to directory
        
    Returns:
        SHA-256 hex string or None if directory is empty or doesn't exist
    """
    if not dir_path.exists() or not dir_path.is_dir():
        return None
    
    hasher = hashlib.sha256()
    files = sorted(dir_path.rglob("*"))
    
    if not files:
        logger.warning(f"Directory is empty: {dir_path}")
        return None
    
    for file_path in files:
        if file_path.is_file():
            # Include relative path in hash for context
            relative_path = file_path.relative_to(dir_path)
            hasher.update(str(relative_path).encode('utf-8'))
            hasher.update(b"::")
            
            # Read file content
            try:
                with open(file_path, 'rb') as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                continue
    
    return hasher.hexdigest()


def track_dataset_artifacts() -> Dict[str, str]:
    """
    Track hashes for dataset artifacts.
    
    Returns:
        Dictionary of artifact names to their hashes
    """
    artifacts = {}
    
    # Check for processed datasets
    processed_dirs = [
        DATA_DIR / "processed" / "codesearchnet",
        DATA_DIR / "processed" / "codegen"
    ]
    
    for dir_path in processed_dirs:
        if dir_path.exists():
            hash_val = compute_directory_hash(dir_path)
            if hash_val:
                artifacts[f"dataset_{dir_path.name}"] = hash_val
                logger.info(f"Tracked dataset hash for {dir_path.name}: {hash_val[:16]}...")
    
    # Check for checksums file
    checksums_file = DATA_DIR / "checksums.json"
    if checksums_file.exists():
        hash_val = compute_file_hash(checksums_file)
        if hash_val:
            artifacts["checksums"] = hash_val
            logger.info(f"Tracked checksums file hash: {hash_val[:16]}...")
    
    return artifacts


def track_metric_artifacts() -> Dict[str, str]:
    """
    Track hashes for metric artifacts.
    
    Returns:
        Dictionary of artifact names to their hashes
    """
    artifacts = {}
    
    if not METRICS_DIR.exists():
        logger.info("Metrics directory not found, skipping metric tracking")
        return artifacts
    
    # Track individual metric files
    for metric_file in METRICS_DIR.glob("*.csv"):
        hash_val = compute_file_hash(metric_file)
        if hash_val:
            artifacts[f"metrics_{metric_file.stem}"] = hash_val
            logger.info(f"Tracked metric file hash for {metric_file.stem}: {hash_val[:16]}...")
    
    # Track aggregate metrics if they exist
    aggregate_file = METRICS_DIR / "aggregate_metrics.json"
    if aggregate_file.exists():
        hash_val = compute_file_hash(aggregate_file)
        if hash_val:
            artifacts["aggregate_metrics"] = hash_val
            logger.info(f"Tracked aggregate metrics hash: {hash_val[:16]}...")
    
    return artifacts


def track_statistical_artifacts() -> Dict[str, str]:
    """
    Track hashes for statistical analysis artifacts.
    
    Returns:
        Dictionary of artifact names to their hashes
    """
    artifacts = {}
    
    # Check for statistical results
    stat_files = [
        RESULTS_DIR / "statistical_results.json",
        RESULTS_DIR / "cliffs_delta_results.json",
        RESULTS_DIR / "bh_correction_results.json"
    ]
    
    for stat_file in stat_files:
        if stat_file.exists():
            hash_val = compute_file_hash(stat_file)
            if hash_val:
                artifacts[f"stats_{stat_file.stem}"] = hash_val
                logger.info(f"Tracked statistical file hash for {stat_file.stem}: {hash_val[:16]}...")
    
    # Check for pilot study results
    pilot_file = RESULTS_DIR / "pilot_study.md"
    if pilot_file.exists():
        hash_val = compute_file_hash(pilot_file)
        if hash_val:
            artifacts["pilot_study"] = hash_val
            logger.info(f"Tracked pilot study hash: {hash_val[:16]}...")
    
    return artifacts


def track_figure_artifacts() -> Dict[str, str]:
    """
    Track hashes for figure artifacts.
    
    Returns:
        Dictionary of artifact names to their hashes
    """
    artifacts = {}
    
    if not FIGURES_DIR.exists():
        logger.info("Figures directory not found, skipping figure tracking")
        return artifacts
    
    # Track all figure files
    for figure_file in FIGURES_DIR.glob("*"):
        if figure_file.is_file():
            hash_val = compute_file_hash(figure_file)
            if hash_val:
                artifacts[f"figure_{figure_file.stem}"] = hash_val
                logger.info(f"Tracked figure hash for {figure_file.stem}: {hash_val[:16]}...")
    
    return artifacts


def update_state_with_all_artifacts() -> bool:
    """
    Update the state file with hashes for all major artifacts.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load current state
        state = load_state_file(STATE_FILE_PATH)
        if not state:
            logger.error("Failed to load state file")
            return False
        
        # Ensure artifact_hashes section exists
        if "artifact_hashes" not in state:
            state["artifact_hashes"] = {}
        
        # Collect all artifact hashes
        all_artifacts = {}
        all_artifacts.update(track_dataset_artifacts())
        all_artifacts.update(track_metric_artifacts())
        all_artifacts.update(track_statistical_artifacts())
        all_artifacts.update(track_figure_artifacts())
        
        # Update state with new hashes
        timestamp = datetime.now().isoformat()
        state["artifact_hashes"]["last_updated"] = timestamp
        state["artifact_hashes"]["artifacts"] = all_artifacts
        
        # Update the overall timestamp
        state["updated_at"] = timestamp
        
        # Save updated state
        save_state_file(STATE_FILE_PATH, state)
        logger.info(f"Successfully updated state file with {len(all_artifacts)} artifact hashes")
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating state with artifact hashes: {e}")
        return False


def verify_artifact_integrity(artifact_name: str) -> bool:
    """
    Verify the integrity of a specific artifact by comparing its current hash
    with the stored hash in the state file.
    
    Args:
        artifact_name: Name of the artifact to verify
        
    Returns:
        True if integrity is verified, False otherwise
    """
    try:
        state = load_state_file(STATE_FILE_PATH)
        if not state or "artifact_hashes" not in state:
            logger.error("State file missing artifact_hashes section")
            return False
        
        if "artifacts" not in state["artifact_hashes"]:
            logger.error("No artifacts found in state file")
            return False
        
        stored_hash = state["artifact_hashes"]["artifacts"].get(artifact_name)
        if not stored_hash:
            logger.warning(f"No stored hash found for artifact: {artifact_name}")
            return False
        
        # Determine artifact path based on name
        if artifact_name.startswith("dataset_"):
            dir_name = artifact_name.replace("dataset_", "")
            dir_path = DATA_DIR / "processed" / dir_name
            if dir_path.exists():
                current_hash = compute_directory_hash(dir_path)
            else:
                logger.error(f"Dataset directory not found: {dir_path}")
                return False
        
        elif artifact_name.startswith("metrics_"):
            file_name = artifact_name.replace("metrics_", "") + ".csv"
            file_path = METRICS_DIR / file_name
            if file_path.exists():
                current_hash = compute_file_hash(file_path)
            else:
                logger.error(f"Metric file not found: {file_path}")
                return False
        
        elif artifact_name.startswith("stats_"):
            file_name = artifact_name.replace("stats_", "")
            possible_paths = [
                RESULTS_DIR / f"{file_name}.json",
                RESULTS_DIR / f"{file_name}.md"
            ]
            current_hash = None
            for path in possible_paths:
                if path.exists():
                    current_hash = compute_file_hash(path)
                    break
            if not current_hash:
                logger.error(f"Statistical file not found: {file_name}")
                return False
        
        elif artifact_name.startswith("figure_"):
            file_name = artifact_name.replace("figure_", "")
            # Try common extensions
            for ext in ['.png', '.pdf', '.svg']:
                file_path = FIGURES_DIR / f"{file_name}{ext}"
                if file_path.exists():
                    current_hash = compute_file_hash(file_path)
                    break
            if not current_hash:
                logger.error(f"Figure file not found: {file_name}")
                return False
        
        elif artifact_name == "checksums":
            file_path = DATA_DIR / "checksums.json"
            if file_path.exists():
                current_hash = compute_file_hash(file_path)
            else:
                logger.error("Checksums file not found")
                return False
        
        elif artifact_name in ["aggregate_metrics", "pilot_study"]:
            if artifact_name == "aggregate_metrics":
                file_path = METRICS_DIR / "aggregate_metrics.json"
            else:
                file_path = RESULTS_DIR / "pilot_study.md"
            
            if file_path.exists():
                current_hash = compute_file_hash(file_path)
            else:
                logger.error(f"{artifact_name} file not found")
                return False
        
        else:
            logger.error(f"Unknown artifact type: {artifact_name}")
            return False
        
        if current_hash == stored_hash:
            logger.info(f"Artifact integrity verified: {artifact_name}")
            return True
        else:
            logger.error(f"Artifact integrity FAILED for {artifact_name}: stored={stored_hash[:16]}... current={current_hash[:16]}...")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying artifact integrity: {e}")
        return False


def main():
    """
    Main entry point for artifact hash tracking.
    Updates the state file with hashes for all major artifacts.
    """
    logger.info("Starting artifact hash tracking")
    
    success = update_state_with_all_artifacts()
    
    if success:
        logger.info("Artifact hash tracking completed successfully")
        # Print summary
        state = load_state_file(STATE_FILE_PATH)
        if state and "artifact_hashes" in state:
            artifacts = state["artifact_hashes"].get("artifacts", {})
            logger.info(f"Total artifacts tracked: {len(artifacts)}")
            for name, hash_val in artifacts.items():
                logger.info(f"  - {name}: {hash_val[:16]}...")
    else:
        logger.error("Artifact hash tracking failed")
        sys.exit(1)


if __name__ == "__main__":
    main()