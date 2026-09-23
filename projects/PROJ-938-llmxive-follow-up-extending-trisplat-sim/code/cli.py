"""
CLI entry point for the TriSplat extension pipeline.

Handles arguments for view count, timeout, seed, and state updates.
"""
import argparse
import json
import os
import sys
import hashlib
from pathlib import Path
import logging
from typing import List

# Add parent directory to path for imports if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_file(project_id: str, artifact_paths: List[str], state_dir: Path):
    """
    Update the project state YAML file with artifact checksums.
    Filters files > 100MB before hashing to avoid long runtimes on large mesh files.
    Recursively hashes all files in the provided paths (typically data/processed/).
    """
    import yaml
    state_file = state_dir / f"projects/{project_id}.yaml"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    state_data = {"artifacts": {}}
    max_size_bytes = 100 * 1024 * 1024  # 100MB limit
    
    for path in artifact_paths:
        p = Path(path)
        if not p.exists():
            logging.warning(f"Artifact not found: {path}")
            continue
        
        # Check file size before hashing
        try:
            file_size = p.stat().st_size
        except OSError as e:
            logging.error(f"Could not get size for {path}: {e}")
            continue

        if file_size > max_size_bytes:
            logging.info(f"Skipping large file for hashing (>{max_size_bytes/1024/1024:.1f}MB): {path}")
            state_data["artifacts"][str(p)] = {
                "skipped": True, 
                "reason": f"size > 100MB ({file_size} bytes)"
            }
            continue
        
        try:
            checksum = compute_sha256(str(p))
            state_data["artifacts"][str(p)] = {
                "sha256": checksum, 
                "size": file_size
            }
            logging.debug(f"Hashed {path}: {checksum[:16]}...")
        except Exception as e:
            logging.error(f"Failed to hash {path}: {e}")
            state_data["artifacts"][str(p)] = {"error": str(e)}
    
    with open(state_file, "w") as f:
        yaml.dump(state_data, f)
    logging.info(f"State updated: {state_file}")

def run_pipeline(args):
    """
    Execute the main pipeline logic based on CLI arguments.
    Delegates to run_batch_orchestration or single scene run.
    """
    from experiments.run_batch import run_batch_orchestration, setup_logging
    from data.loader import load_real_estate_10k_streaming
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Validate inputs
    if args.views:
        view_counts = [int(v) for v in args.views.split(',')]
    else:
        view_counts = [2] # Default
        
    logger.info(f"Starting pipeline with views: {view_counts}, seed: {args.seed}")
    
    # If specific scene logic is needed, load here
    # For now, delegate to batch orchestrator which handles scene selection
    if args.batch or len(view_counts) > 1:
        run_batch_orchestration(
            view_counts=view_counts,
            timeout=args.timeout,
            seed=args.seed,
            max_scenes=args.max_scenes or 20
        )
    else:
        logger.warning("Single view mode not fully implemented in CLI wrapper. Use --batch or specify multiple views.")

def main():
    parser = argparse.ArgumentParser(description="llmXive TriSplat Extension Pipeline")
    parser.add_argument("--views", type=str, help="Comma-separated list of view counts (e.g., '2,3,4')")
    parser.add_argument("--timeout", type=int, default=3600, help="Wall-clock timeout in seconds")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--update-state", action="store_true", help="Update state file with artifact checksums")
    parser.add_argument("--batch", action="store_true", help="Run batch orchestration")
    parser.add_argument("--max-scenes", type=int, help="Maximum number of scenes to process (default 20)")
    
    args = parser.parse_args()
    
    if args.update_state:
        # Update state for all processed artifacts in data/processed
        # This satisfies T050: Artifact Hashing Logic
        data_processed = Path("data/processed")
        if data_processed.exists():
            # Recursively find all files in data/processed
            artifacts = [str(p) for p in data_processed.rglob("*") if p.is_file()]
            logging.info(f"Found {len(artifacts)} files in data/processed to hash.")
            update_state_file("PROJ-938-llmxive-follow-up-extending-trisplat-sim", artifacts, Path("state"))
        else:
            logging.warning("data/processed directory not found. Nothing to update.")
    else:
        run_pipeline(args)

if __name__ == "__main__":
    main()