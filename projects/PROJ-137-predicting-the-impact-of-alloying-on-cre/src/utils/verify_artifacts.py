"""
Artifact Verification and Hashing Script (Task T033).

This script verifies that all expected project artifacts (CSVs, plots, reports)
exist, computes their cryptographic hashes using src/utils/hash.py, and updates
the state manifest to ensure traceability and integrity (Constitution Principle V).
"""
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime

# Project root
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
FIGURES_DIR = ROOT / "data" / "outputs"
REPORTS_DIR = ROOT / "docs" / "reports"
MANIFEST_PATH = ROOT / "data" / "artifact_manifest.yaml"

# Expected artifacts based on tasks.md pipeline execution
EXPECTED_ARTIFACTS = [
    # Data outputs from US1
    {"path": "data/processed_alloy_data.csv", "type": "csv", "source_task": "T019"},
    {"path": "data/synthetic_data_raw.csv", "type": "csv", "source_task": "T016"},
    
    # Model outputs from US2
    {"path": "data/outputs/model_comparison_results.yaml", "type": "yaml", "source_task": "T025"},
    
    # SHAP/Interpretability outputs from US3
    {"path": "data/outputs/shap_summary_plot.png", "type": "png", "source_task": "T027"},
    {"path": "data/outputs/feature_importance.json", "type": "json", "source_task": "T027"},
    
    # Final Report
    {"path": "docs/reports/final_research_report.md", "type": "md", "source_task": "T028"},
]

def load_hash_utils():
    """Import hash utilities from src/utils/hash.py"""
    try:
        sys.path.insert(0, str(ROOT / "src"))
        from utils.hash import compute_file_hash, update_manifest
        return compute_file_hash, update_manifest
    except ImportError as e:
        print(f"ERROR: Could not import hash utilities: {e}")
        print("Ensure src/utils/hash.py exists and exposes compute_file_hash and update_manifest.")
        sys.exit(1)

def verify_artifacts(compute_hash_fn, update_manifest_fn):
    """
    Verify existence of all expected artifacts, compute hashes, and update manifest.
    """
    missing = []
    verified = []
    errors = []

    print(f"{'='*60}")
    print(f"Artifact Verification & Hashing (Task T033)")
    print(f"{'='*60}")
    print(f"Root: {ROOT}")
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"{'='*60}\n")

    # Ensure manifest exists
    if not MANIFEST_PATH.exists():
        print(f"[INIT] Creating new artifact manifest at {MANIFEST_PATH}")
        update_manifest_fn(MANIFEST_PATH, [])
    
    current_manifest = []
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, 'r') as f:
                current_manifest = yaml.safe_load(f) or []
        except Exception as e:
            print(f"[WARN] Could not load existing manifest: {e}")
            current_manifest = []

    for artifact_def in EXPECTED_ARTIFACTS:
        rel_path = artifact_def["path"]
        full_path = ROOT / rel_path
        artifact_type = artifact_def["type"]
        source_task = artifact_def["source_task"]

        print(f"Checking: {rel_path} (Type: {artifact_type}, Source: {source_task})")

        if not full_path.exists():
            missing.append(rel_path)
            print(f"  ❌ MISSING")
            continue

        try:
            # Compute hash
            file_hash = compute_hash_fn(full_path)
            file_size = full_path.stat().st_size
            mtime = datetime.fromtimestamp(full_path.stat().st_mtime).isoformat()

            entry = {
                "path": rel_path,
                "hash": file_hash,
                "size_bytes": file_size,
                "last_modified": mtime,
                "verified_task": source_task,
                "verified_at": datetime.now().isoformat()
            }

            # Check for existing entry to avoid duplicates if hash matches
            existing_idx = None
            for idx, entry in enumerate(current_manifest):
                if entry.get("path") == rel_path:
                    existing_idx = idx
                    break

            if existing_idx is not None:
                current_manifest[existing_idx] = entry
            else:
                current_manifest.append(entry)

            verified.append(entry)
            print(f"  ✅ VERIFIED | Hash: {file_hash[:16]}... | Size: {file_size} bytes")

        except Exception as e:
            errors.append({"path": rel_path, "error": str(e)})
            print(f"  ❌ ERROR: {e}")

    # Update manifest
    if verified or errors:
        try:
            update_manifest_fn(MANIFEST_PATH, current_manifest)
            print(f"\n[SUCCESS] Manifest updated at {MANIFEST_PATH}")
        except Exception as e:
            print(f"[ERROR] Failed to update manifest: {e}")
            sys.exit(1)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total Expected: {len(EXPECTED_ARTIFACTS)}")
    print(f"Verified: {len(verified)}")
    print(f"Missing: {len(missing)}")
    print(f"Errors: {len(errors)}")

    if missing:
        print(f"\n⚠️  MISSING ARTIFACTS:")
        for m in missing:
            print(f"   - {m}")

    if errors:
        print(f"\n⚠️  VERIFICATION ERRORS:")
        for e in errors:
            print(f"   - {e['path']}: {e['error']}")

    if missing or errors:
        print(f"\n❌ VERIFICATION FAILED")
        sys.exit(1)
    else:
        print(f"\n✅ ALL ARTIFACTS VERIFIED AND HASHED")
        return True

if __name__ == "__main__":
    compute_hash, update_manifest = load_hash_utils()
    verify_artifacts(compute_hash, update_manifest)
