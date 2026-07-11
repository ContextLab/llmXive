"""
Pipeline script to update project state by hashing artifacts and writing
the state file to state/projects/<project_id>.yaml.

This script computes SHA-256 hashes for all relevant output artifacts
(embeddings, metrics, reports) and updates the project's state manifest.
"""
import os
import sys
import json
import hashlib
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils.logging import setup_logging, get_logger, log_info, log_error, log_debug

# Constants
PROJECT_ID = "PROJ-823-llmxive-follow-up-extending-multabench-b"
STATE_DIR = project_root / "state" / "projects"
DATA_DIR = project_root / "data"
ARTIFACTS_DIR = project_root / "data" / "artifacts"
PROCESSED_DIR = project_root / "data" / "processed"

# Patterns of files to hash (relative to DATA_DIR or ARTIFACTS_DIR)
ARTIFACT_PATTERNS = [
    "processed/embeddings_*.parquet",
    "processed/metadata_stats_summary.csv",
    "artifacts/frozen_baseline_aggregated_*.json",
    "artifacts/metrics_conditioned_*.json",
    "artifacts/gpu_tuned_baselines.csv",
    "artifacts/correlation_report_*.json",
    "artifacts/fdr_adjusted_pvalues.json",
    "artifacts/t_test_results.json",
]

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        log_error(f"Failed to compute hash for {file_path}: {e}")
        return ""

def find_artifacts(base_dir: Path, patterns: List[str]) -> List[Path]:
    """Find all files matching the given glob patterns."""
    artifacts = []
    for pattern in patterns:
        matches = list(base_dir.glob(pattern))
        artifacts.extend(matches)
    return sorted(artifacts)

def hash_artifacts(base_dir: Path, patterns: List[str]) -> Dict[str, Dict[str, str]]:
    """Compute hashes for all matching artifacts."""
    artifacts = find_artifacts(base_dir, patterns)
    result = {}
    for artifact_path in artifacts:
        rel_path = str(artifact_path.relative_to(base_dir))
        file_hash = compute_sha256(artifact_path)
        if file_hash:
            result[rel_path] = {
                "hash": file_hash,
                "size_bytes": artifact_path.stat().st_size,
                "modified_at": datetime.fromtimestamp(
                    artifact_path.stat().st_mtime
                ).isoformat(),
            }
    return result

def load_existing_state(state_path: Path) -> Dict[str, Any]:
    """Load existing state file if it exists."""
    if state_path.exists():
        try:
            with open(state_path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            log_error(f"Failed to load existing state: {e}")
            return {}
    return {}

def save_state(state: Dict[str, Any], state_path: Path) -> None:
    """Save state to YAML file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    log_info(f"State saved to {state_path}")

def build_state(project_id: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    """Build the complete state dictionary."""
    ensure_directories()
    
    state = {
        "project_id": project_id,
        "updated_at": datetime.now().isoformat(),
        "run_id": run_id or "latest",
        "artifacts": {
            "data": {},
            "artifacts": {},
        },
        "status": "completed",
        "pipeline_version": "1.0.0",
    }

    # Hash data artifacts
    data_hashes = hash_artifacts(DATA_DIR, [
        "processed/*.parquet",
        "processed/*.csv",
    ])
    state["artifacts"]["data"] = data_hashes

    # Hash analysis artifacts
    artifact_hashes = hash_artifacts(ARTIFACTS_DIR, [
        "*.json",
        "*.csv",
    ])
    state["artifacts"]["artifacts"] = artifact_hashes

    # Summary statistics
    state["summary"] = {
        "total_data_artifacts": len(data_hashes),
        "total_analysis_artifacts": len(artifact_hashes),
        "data_artifacts_list": list(data_hashes.keys()),
        "analysis_artifacts_list": list(artifact_hashes.keys()),
    }

    return state

def main():
    """Main entry point for updating project state."""
    logger = setup_logging(level="INFO")
    log_info(f"Starting state update for project: {PROJECT_ID}")

    # Determine run_id from arguments or use 'latest'
    import argparse
    parser = argparse.ArgumentParser(description="Update project state with artifact hashes")
    parser.add_argument(
        "--run_id",
        type=str,
        default=None,
        help="Run ID to associate with this state update"
    )
    args = parser.parse_args()

    run_id = args.run_id if args.run_id else datetime.now().strftime("%Y%m%d_%H%M%S")

    # Build and save state
    state = build_state(PROJECT_ID, run_id)
    state_path = STATE_DIR / f"{PROJECT_ID}.yaml"
    save_state(state, state_path)

    log_info("State update completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())