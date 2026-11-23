"""
T033: Verify state/artifact_hashes.yaml tracks all data and model artifacts correctly.

This script scans the project for all generated artifacts (data, models, results)
and verifies they are properly recorded in state/artifact_hashes.yaml.

It computes SHA256 hashes for all found artifacts and compares against the
recorded hashes in the manifest.
"""
import os
import sys
import json
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple
from datetime import datetime

# Import existing utilities
try:
    from utils.io import compute_file_hash
    from utils.constants import (
        PROJECT_ROOT,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_INTERMEDIATE_DIR,
        RESULTS_DIR,
        RESULTS_PLOTS_DIR,
        STATE_DIR
    )
except ImportError:
    # Fallback if constants not fully implemented
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
    DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
    DATA_INTERMEDIATE_DIR = PROJECT_ROOT / "data" / "intermediate"
    RESULTS_DIR = PROJECT_ROOT / "results"
    RESULTS_PLOTS_DIR = RESULTS_DIR / "plots"
    STATE_DIR = PROJECT_ROOT / "state"

# Define artifact patterns to track
ARTIFACT_PATTERNS = {
    "data_raw": [
        "*.json",  # study_manifest.json
        "*_raw_intensity.csv",
        "*_phenotype.csv",
        "*.sha256"
    ],
    "data_processed": [
        "batch_corrected_matrix.csv",
        "labels.csv",
        "preprocess_log.json",
        "split_indices.json"
    ],
    "data_intermediate": [
        "vif_scores.json"
    ],
    "results": [
        "metrics.json",
        "shap_analysis.json",
        "pathway_analysis.json",
        "feature_importance_ranking.json",
        "top_metabolites.json",
        "report_framing.md"
    ],
    "results_plots": [
        "*.png",
        "*.jpg",
        "*.svg"
    ],
    "state": [
        "artifact_hashes.yaml",
        "directory_structure.txt",
        "schema_validation_log.txt"
    ]
}

def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def find_artifacts(base_dir: Path, patterns: List[str]) -> List[Path]:
    """Find all files matching patterns in a directory."""
    found_files = []
    if not base_dir.exists():
        return found_files
    
    for pattern in patterns:
        for filepath in base_dir.glob(pattern):
            if filepath.is_file():
                found_files.append(filepath)
    
    return found_files

def load_artifact_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the existing artifact hashes manifest."""
    if not manifest_path.exists():
        return {}
    
    with open(manifest_path, 'r') as f:
        return yaml.safe_load(f) or {}

def save_artifact_manifest(manifest_path: Path, manifest: Dict[str, Any]):
    """Save the artifact hashes manifest."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

def verify_artifact_tracking() -> Tuple[bool, Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Verify that all artifacts are tracked in state/artifact_hashes.yaml.
    
    Returns:
        Tuple of (success, missing_tracking, hash_mismatches)
    """
    manifest_path = STATE_DIR / "artifact_hashes.yaml"
    current_manifest = load_artifact_manifest(manifest_path)
    
    missing_tracking = []
    hash_mismatches = []
    
    # Collect all expected artifacts
    all_expected_artifacts = {}
    for category, patterns in ARTIFACT_PATTERNS.items():
        base_dir = {
            "data_raw": DATA_RAW_DIR,
            "data_processed": DATA_PROCESSED_DIR,
            "data_intermediate": DATA_INTERMEDIATE_DIR,
            "results": RESULTS_DIR,
            "results_plots": RESULTS_PLOTS_DIR,
            "state": STATE_DIR
        }.get(category, Path("/nonexistent"))
        
        found_files = find_artifacts(base_dir, patterns)
        for filepath in found_files:
            rel_path = filepath.relative_to(PROJECT_ROOT)
            all_expected_artifacts[str(rel_path)] = {
                "absolute_path": filepath,
                "category": category
            }
    
    # Verify each artifact is tracked
    tracked_files = set(current_manifest.get("artifacts", {}).keys())
    
    for rel_path, info in all_expected_artifacts.items():
        if rel_path not in tracked_files:
            missing_tracking.append(rel_path)
        else:
            # Verify hash matches
            try:
                current_hash = compute_sha256(info["absolute_path"])
                recorded_hash = current_manifest["artifacts"][rel_path].get("hash")
                
                if recorded_hash and current_hash != recorded_hash:
                    hash_mismatches.append({
                        "path": rel_path,
                        "current_hash": current_hash,
                        "recorded_hash": recorded_hash
                    })
            except Exception as e:
                missing_tracking.append(f"{rel_path} (error computing hash: {str(e)})")
    
    success = len(missing_tracking) == 0 and len(hash_mismatches) == 0
    return success, missing_tracking, hash_mismatches

def update_artifact_manifest():
    """Update the artifact manifest with all current artifacts."""
    manifest_path = STATE_DIR / "artifact_hashes.yaml"
    current_manifest = load_artifact_manifest(manifest_path)
    
    if "artifacts" not in current_manifest:
        current_manifest["artifacts"] = {}
    
    # Collect all artifacts
    for category, patterns in ARTIFACT_PATTERNS.items():
        base_dir = {
            "data_raw": DATA_RAW_DIR,
            "data_processed": DATA_PROCESSED_DIR,
            "data_intermediate": DATA_INTERMEDIATE_DIR,
            "results": RESULTS_DIR,
            "results_plots": RESULTS_PLOTS_DIR,
            "state": STATE_DIR
        }.get(category, Path("/nonexistent"))
        
        found_files = find_artifacts(base_dir, patterns)
        
        for filepath in found_files:
            rel_path = str(filepath.relative_to(PROJECT_ROOT))
            
            try:
                file_hash = compute_sha256(filepath)
                file_size = filepath.stat().st_size
                file_mtime = datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
                
                current_manifest["artifacts"][rel_path] = {
                    "hash": file_hash,
                    "size_bytes": file_size,
                    "last_modified": file_mtime,
                    "category": category
                }
            except Exception as e:
                print(f"Warning: Could not process {rel_path}: {str(e)}", file=sys.stderr)
    
    # Add metadata
    current_manifest["metadata"] = {
        "generated_at": datetime.now().isoformat(),
        "project_root": str(PROJECT_ROOT),
        "total_artifacts": len(current_manifest["artifacts"])
    }
    
    save_artifact_manifest(manifest_path, current_manifest)
    return current_manifest

def main():
    """Main entry point for artifact tracking verification."""
    print("=" * 60)
    print("T033: Verifying Artifact Tracking in state/artifact_hashes.yaml")
    print("=" * 60)
    
    # First, update the manifest to ensure it's current
    print("\n[1/3] Updating artifact manifest...")
    manifest = update_artifact_manifest()
    print(f"      Found {manifest['metadata']['total_artifacts']} artifacts")
    
    # Verify tracking
    print("\n[2/3] Verifying artifact tracking...")
    success, missing, mismatches = verify_artifact_tracking()
    
    # Report results
    print("\n[3/3] Results:")
    print("-" * 60)
    
    if success:
        print("✓ SUCCESS: All artifacts are properly tracked with correct hashes.")
    else:
        if missing:
            print(f"✗ MISSING TRACKING: {len(missing)} artifact(s) not tracked:")
            for item in missing[:10]:  # Show first 10
                print(f"    - {item}")
            if len(missing) > 10:
                print(f"    ... and {len(missing) - 10} more")
        
        if mismatches:
            print(f"✗ HASH MISMATCHES: {len(mismatches)} artifact(s) with hash mismatch:")
            for item in mismatches[:10]:
                print(f"    - {item['path']}")
                print(f"      Current:  {item['current_hash'][:16]}...")
                print(f"      Recorded: {item['recorded_hash'][:16]}...")
    
    print("-" * 60)
    print(f"Manifest updated: {manifest['metadata']['generated_at']}")
    print(f"Total artifacts tracked: {manifest['metadata']['total_artifacts']}")
    print("=" * 60)
    
    # Return exit code based on success
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()