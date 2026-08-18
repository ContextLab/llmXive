"""
Versioning script for llmXive pipeline.
Computes SHA-256 hashes for data/code artifacts and updates a state YAML file.
Implements explicit invalidation of stale review records when hashes change.
"""
import os
import hashlib
import yaml
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Default paths relative to project root
DEFAULT_STATE_FILE = "state/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig.yaml"
DEFAULT_REVIEW_STATE_FILE = "state/reviews.yaml"
DEFAULT_TARGETS = [
    "data/raw",
    "data/processed",
    "code",
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_hash(dir_path: Path) -> Dict[str, str]:
    """Compute hashes for all files in a directory recursively."""
    hashes = {}
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file() and not file_path.name.startswith("."):
            # Skip hidden files
            relative_path = file_path.relative_to(dir_path)
            hashes[str(relative_path)] = compute_sha256(file_path)
    return hashes

def load_state(state_file: Path) -> Dict[str, Any]:
    """Load existing state file or return empty structure."""
    if state_file.exists():
        with open(state_file, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_state(state: Dict[str, Any], state_file: Path) -> None:
    """Save state to YAML file."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def load_reviews(reviews_file: Path) -> Dict[str, Any]:
    """Load existing reviews state file."""
    if reviews_file.exists():
        with open(reviews_file, "r") as f:
            return yaml.safe_load(f) or {}
    return {"records": []}

def save_reviews(reviews: Dict[str, Any], reviews_file: Path) -> None:
    """Save reviews state to YAML file."""
    reviews_file.parent.mkdir(parents=True, exist_ok=True)
    with open(reviews_file, "w") as f:
        yaml.dump(reviews, f, default_flow_style=False, sort_keys=False)

def invalidate_stale_reviews(
    current_hashes: Dict[str, Any],
    previous_hashes: Dict[str, Any],
    reviews_file: Path
) -> List[str]:
    """
    Explicitly invalidate stale review records when artifact hashes change.
    
    Args:
        current_hashes: Current artifact hashes
        previous_hashes: Previous artifact hashes from state
        reviews_file: Path to reviews state file
        
    Returns:
        List of invalidated record IDs
    """
    invalidated_ids = []
    
    if not reviews_file.exists():
        logger.info("No reviews file found. Skipping invalidation logic.")
        return invalidated_ids
        
    reviews_data = load_reviews(reviews_file)
    records = reviews_data.get("records", [])
    
    # Determine which artifacts have changed
    changed_artifacts = set()
    for artifact_name, artifact_info in current_hashes.items():
        current_hash = artifact_info.get("hash", "")
        prev_info = previous_hashes.get(artifact_name)
        prev_hash = prev_info.get("hash", "") if prev_info else ""
        
        if current_hash != prev_hash:
            changed_artifacts.add(artifact_name)
            logger.info(f"Artifact changed: {artifact_name} (hash: {current_hash[:16]}... -> {prev_hash[:16]}...)")
    
    if not changed_artifacts:
        logger.info("No artifacts changed. No invalidation needed.")
        return invalidated_ids
        
    # Invalidate records that reference changed artifacts
    valid_records = []
    for record in records:
        record_id = record.get("id", "unknown")
        record_artifacts = set(record.get("artifacts", []))
        
        # Check if this record references any changed artifact
        if record_artifacts & changed_artifacts:
            invalidated_ids.append(record_id)
            record["status"] = "invalidated"
            record["invalidation_reason"] = f"Artifact hash change: {', '.join(sorted(changed_artifacts & record_artifacts))}"
            record["invalidated_at"] = datetime.utcnow().isoformat()
            logger.warning(f"Invalidated review record {record_id} due to artifact changes.")
        else:
            valid_records.append(record)
    
    # Update reviews file
    reviews_data["records"] = valid_records + [r for r in records if r.get("id") in invalidated_ids]
    save_reviews(reviews_data, reviews_file)
    
    logger.info(f"Explicit invalidation logic executed. {len(invalidated_ids)} record(s) invalidated.")
    return invalidated_ids

def update_version_state(
    targets: List[str],
    state_file: Optional[Path] = None,
    reviews_file: Optional[Path] = None,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Compute hashes for target paths and update state file.
    Explicitly invalidates stale review records when hashes change.

    Args:
        targets: List of relative paths to hash (files or directories)
        state_file: Path to state YAML file (default: state/projects/PROJ-786-...yaml)
        reviews_file: Path to reviews YAML file (default: state/reviews.yaml)
        project_root: Project root directory (default: current working directory)

    Returns:
        Updated state dictionary
    """
    if project_root is None:
        project_root = Path.cwd()

    if state_file is None:
        state_file = project_root / DEFAULT_STATE_FILE
    else:
        state_file = Path(state_file)

    if reviews_file is None:
        reviews_file = project_root / DEFAULT_REVIEW_STATE_FILE
    else:
        reviews_file = Path(reviews_file)

    # Ensure paths are relative to project_root if they aren't absolute
    if not state_file.is_absolute():
        state_file = project_root / state_file
    if not reviews_file.is_absolute():
        reviews_file = project_root / reviews_file

    # Load current state and previous hashes for comparison
    state = load_state(state_file)
    previous_hashes = state.get("artifacts", {})

    # Initialize or update metadata
    state["last_updated"] = datetime.utcnow().isoformat()
    state["project"] = "PROJ-786-multi-property-trade-offs-in-alloy-desig"
    state["artifacts"] = {}

    for target in targets:
        target_path = project_root / target
        if not target_path.exists():
            logger.warning(f"Target path does not exist: {target_path}")
            continue

        if target_path.is_file():
            # Single file
            relative_name = target_path.name
            artifact_hash = compute_sha256(target_path)
            state["artifacts"][relative_name] = {
                "type": "file",
                "hash": artifact_hash,
                "path": str(target_path.relative_to(project_root))
            }
        elif target_path.is_dir():
            # Directory - hash all contents
            dir_hashes = compute_directory_hash(target_path)
            if dir_hashes:
                # Compute a combined hash for the directory
                combined_content = "\n".join(
                    f"{k}:{v}" for k, v in sorted(dir_hashes.items())
                )
                combined_hash = hashlib.sha256(combined_content.encode()).hexdigest()
                state["artifacts"][target] = {
                    "type": "directory",
                    "hash": combined_hash,
                    "files": dir_hashes,
                    "path": str(target_path.relative_to(project_root))
                }

    # Save updated state before invalidation (so we have the new hashes)
    save_state(state, state_file)
    
    # Explicitly invalidate stale review records
    invalidated = invalidate_stale_reviews(
        current_hashes=state["artifacts"],
        previous_hashes=previous_hashes,
        reviews_file=reviews_file
    )
    
    # Update state with invalidation summary
    state["last_invalidation"] = {
        "timestamp": datetime.utcnow().isoformat(),
        "records_invalidated": len(invalidated),
        "invalidated_ids": invalidated,
        "changed_artifacts": [
            name for name, info in state["artifacts"].items()
            if name in previous_hashes and info.get("hash") != previous_hashes[name].get("hash")
        ]
    }
    
    # Re-save state with invalidation info
    save_state(state, state_file)
    
    return state

def main():
    parser = argparse.ArgumentParser(
        description="Compute SHA-256 hashes for artifacts, update state YAML, and invalidate stale reviews"
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        default=DEFAULT_TARGETS,
        help="Paths to hash (relative to project root)"
    )
    parser.add_argument(
        "--state-file",
        default=DEFAULT_STATE_FILE,
        help="Path to state YAML file"
    )
    parser.add_argument(
        "--reviews-file",
        default=DEFAULT_REVIEW_STATE_FILE,
        help="Path to reviews YAML file for invalidation"
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Print the updated state to stdout"
    )

    args = parser.parse_args()

    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    state = update_version_state(
        targets=args.targets,
        state_file=args.state_file,
        reviews_file=args.reviews_file,
        project_root=project_root
    )

    print(f"\n{'='*60}")
    print(f"VERSIONING UPDATE COMPLETE")
    print(f"{'='*60}")
    print(f"Project: {state['project']}")
    print(f"Updated at: {state['last_updated']}")
    print(f"Artifacts hashed: {len(state['artifacts'])}")
    
    if "last_invalidation" in state:
        inv = state["last_invalidation"]
        print(f"\nInvalidation Summary:")
        print(f"  Timestamp: {inv['timestamp']}")
        print(f"  Records invalidated: {inv['records_invalidated']}")
        if inv['invalidated_ids']:
            print(f"  Invalidated IDs: {inv['invalidated_ids']}")
        if inv['changed_artifacts']:
            print(f"  Changed artifacts: {inv['changed_artifacts']}")
    
    if args.show:
        print(f"\nFull State YAML:")
        print(yaml.dump(state, default_flow_style=False))
    else:
        print(f"\nState updated successfully at {args.state_file}")
        print(f"Log: Invalidation logic executed for {state.get('last_invalidation', {}).get('records_invalidated', 0)} record(s).")

if __name__ == "__main__":
    main()
