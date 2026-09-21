"""
CLI entry point for the llmXive TriSplat extension pipeline.

Usage:
    python code/cli.py --views 3 --timeout 1800 --seed 42
    python code/cli.py --update-state
"""
import argparse
import json
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime
import yaml

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
STATE_DIR = PROJECT_ROOT / "state" / "projects"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None

def update_state_file():
    """
    Compute SHA-256 hashes for processed data files and update the project state YAML.
    Satisfies Constitution Principle III (Data Hygiene).
    """
    print("Updating project state with data checksums...")
    
    # Find all files in data/processed
    checksums = {}
    files_found = False
    
    for file_path in PROCESSED_DIR.rglob("*"):
        if file_path.is_file():
            files_found = True
            rel_path = file_path.relative_to(PROJECT_ROOT)
            checksum = compute_sha256(file_path)
            if checksum:
                checksums[str(rel_path)] = checksum
                print(f"  {rel_path}: {checksum[:16]}...")
            else:
                print(f"  Warning: Could not read {rel_path}")

    if not files_found:
        print("  No files found in data/processed to checksum.")
        # Even if no files, we might want to update the timestamp
    
    # Load or create state file
    state_file = STATE_DIR / "PROJ-938-llmxive-follow-up-extending-trisplat-sim.yaml"
    
    # Load existing state if it exists
    existing_state = {}
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                existing_state = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not read existing state file: {e}")
    
    # Build new state
    new_state = {
        "project_id": "PROJ-938-llmxive-follow-up-extending-trisplat-sim",
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "checksums": checksums
    }
    
    # Merge with existing state (preserve other fields if any)
    for key, value in existing_state.items():
        if key not in ["last_updated", "checksums"]:
            new_state[key] = value
    
    # Write updated state
    with open(state_file, "w") as f:
        yaml.dump(new_state, f, default_flow_style=False, sort_keys=False)

    print(f"State updated: {state_file}")
    return new_state

def run_pipeline(args):
    """
    Execute the main pipeline with the specified configuration.
    This function acts as the orchestrator entry point.
    """
    # Validate views (FR-002: Dynamic view count configuration)
    # T019: Explicit monocular input (1 view) error handling
    if args.views < 2:
        print("Error: Monocular input not supported. Minimum 2 views required.", file=sys.stderr)
        sys.exit(1)

    if args.views > 5:
        print(f"Warning: {args.views} views requested. Max supported is 5. Capping at 5.", file=sys.stderr)
        args.views = 5

    # Dynamic view count validation for supported range (2-5)
    valid_views = {2, 3, 4, 5}
    if args.views not in valid_views:
        print(f"Error: Unsupported view count {args.views}. Supported counts are: {sorted(valid_views)}", file=sys.stderr)
        sys.exit(1)

    print(f"Starting TriSplat Geometry-Only Pipeline")
    print(f"  Views: {args.views}")
    print(f"  Timeout: {args.timeout}s")
    print(f"  Seed: {args.seed}")
    
    # Configuration dictionary to pass to downstream modules
    config = {
        "views": args.views,
        "timeout": args.timeout,
        "seed": args.seed,
        "data_dir": str(DATA_DIR),
        "processed_dir": str(PROCESSED_DIR),
    }

    # Save config to data/processed for reproducibility
    config_path = PROCESSED_DIR / "pipeline_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Configuration saved to {config_path}")

    # Placeholder for actual pipeline execution logic
    # In a real implementation, this would import and call run_batch.py
    # from code.experiments.run_batch import run_experiment
    # run_experiment(config)
    
    print("Pipeline configuration validated. Ready to execute batch jobs.")

def main():
    parser = argparse.ArgumentParser(
        description="CLI for llmXive TriSplat Extension Pipeline"
    )
    
    group = parser.add_mutually_exclusive_group()
    
    # Pipeline arguments
    group.add_argument(
        "--views",
        type=int,
        default=3,
        help="Number of input views (2-5). Default: 3"
    )
    group.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Execution timeout in seconds. Default: 1800 (30 mins)"
    )
    group.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility. Default: 42"
    )
    
    # State update flag
    parser.add_argument(
        "--update-state",
        action="store_true",
        help="Compute checksums for data/processed and update project state file"
    )

    args = parser.parse_args()

    if args.update_state:
        update_state_file()
    else:
        run_pipeline(args)

if __name__ == "__main__":
    main()