"""
Finalize the manifest by recording SHAP subset hashes and report artifacts.

This script reads the SHAP results (including LOFO model hashes) and the 
generated reports (shap_report.md, performance_metrics.json), computes their 
file hashes, and registers them in state/manifest.json.
"""
import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path if running as script
if 'code' not in sys.path[0]:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.utils.manifest_manager import load_manifest, save_manifest, compute_file_hash
from src.models.explain import main as explain_main
from src.utils.generate_metrics import main as generate_metrics_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
STATE_DIR = PROJECT_ROOT / "state"
MANIFEST_PATH = STATE_DIR / "manifest.json"
DATA_DIR = PROJECT_ROOT / "data"

# Expected artifacts to record
SHAP_ARTIFACTS = [
    "shap_values.pkl",
    "shap_summary_data.json",
    "shap_report.md",
    "performance_metrics.json"
]

# LOFO models directory
LOFO_MODELS_DIR = DATA_DIR / "models" / "lofo_models"

def get_lofo_model_hashes() -> List[Dict[str, Any]]:
    """
    Compute hashes for all LOFO models trained in T025/T030.
    Returns a list of dictionaries with 'path' and 'hash'.
    """
    hashes = []
    if not LOFO_MODELS_DIR.exists():
        logger.warning(f"LOFO models directory not found: {LOFO_MODELS_DIR}")
        return hashes
    
    for model_file in LOFO_MODELS_DIR.glob("*.pkl"):
        file_hash = compute_file_hash(model_file)
        hashes.append({
            "path": str(model_file.relative_to(PROJECT_ROOT)),
            "hash": file_hash,
            "type": "lofo_model"
        })
    return hashes

def record_shap_artifacts() -> List[Dict[str, Any]]:
    """
    Compute hashes for SHAP-related artifacts and reports.
    """
    artifacts = []
    
    for artifact_name in SHAP_ARTIFACTS:
        artifact_path = ARTIFACTS_DIR / artifact_name
        if artifact_path.exists():
            file_hash = compute_file_hash(artifact_path)
            artifacts.append({
                "path": str(artifact_path.relative_to(PROJECT_ROOT)),
                "hash": file_hash,
                "type": "shap_report_or_data"
            })
            logger.info(f"Recorded artifact: {artifact_name} -> {file_hash}")
        else:
            logger.warning(f"SHAP artifact not found: {artifact_path}")
    
    return artifacts

def update_manifest_with_shap_hashes(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the manifest with SHAP subset hashes and report artifacts.
    """
    # Ensure the shap_artifacts section exists
    if "shap_artifacts" not in manifest:
        manifest["shap_artifacts"] = {}
    
    # Record LOFO model hashes
    lofo_hashes = get_lofo_model_hashes()
    manifest["shap_artifacts"]["lofo_models"] = lofo_hashes
    
    # Record report and data hashes
    report_hashes = record_shap_artifacts()
    manifest["shap_artifacts"]["reports"] = report_hashes
    
    # Update timestamp
    manifest["last_updated"] = "shap_finalization"
    
    return manifest

def main():
    """
    Main entry point for finalizing the manifest with SHAP artifacts.
    """
    logger.info("Starting SHAP artifact hash recording...")
    
    # Ensure directories exist
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load existing manifest
    if MANIFEST_PATH.exists():
        manifest = load_manifest()
    else:
        logger.error(f"Manifest not found at {MANIFEST_PATH}. Run initialization first.")
        return 1
    
    # Update manifest with SHAP hashes
    updated_manifest = update_manifest_with_shap_hashes(manifest)
    
    # Save updated manifest
    save_manifest(updated_manifest)
    logger.info("Manifest updated successfully with SHAP artifact hashes.")
    
    # Verify the update
    final_manifest = load_manifest()
    if "shap_artifacts" in final_manifest:
        logger.info(f"Verification: Found {len(final_manifest['shap_artifacts'].get('lofo_models', []))} LOFO models")
        logger.info(f"Verification: Found {len(final_manifest['shap_artifacts'].get('reports', []))} SHAP reports")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
