"""
Final verification of state/manifest.json integrity and artifact checksums.
This script ensures all artifacts registered in the manifest exist and match their recorded hashes.
"""
import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Import existing manifest manager utilities
from src.utils.manifest_manager import load_manifest, compute_file_hash, MANIFEST_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_artifact_integrity(artifact_path: str, expected_hash: str, project_root: Path) -> Tuple[bool, str]:
    """
    Verify a single artifact's existence and hash.
    
    Args:
        artifact_path: Relative path to the artifact
        expected_hash: Expected SHA-256 hash
        project_root: Project root directory
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    full_path = project_root / artifact_path
    
    if not full_path.exists():
        return False, f"Artifact missing: {artifact_path}"
    
    try:
        actual_hash = compute_file_hash(str(full_path))
        if actual_hash != expected_hash:
            return False, f"Hash mismatch for {artifact_path}: expected {expected_hash}, got {actual_hash}"
        return True, f"Verified: {artifact_path}"
    except Exception as e:
        return False, f"Error verifying {artifact_path}: {str(e)}"

def verify_manifest_integrity(project_root: Path) -> Tuple[bool, List[str], List[str]]:
    """
    Verify all artifacts in the manifest.
    
    Args:
        project_root: Project root directory
        
    Returns:
        Tuple of (overall_success, passed_artifacts, failed_artifacts)
    """
    manifest_path = project_root / MANIFEST_PATH
    
    if not manifest_path.exists():
        logger.error(f"Manifest file not found at {manifest_path}")
        return False, [], [f"Manifest missing: {MANIFEST_PATH}"]
    
    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        logger.error(f"Failed to load manifest: {str(e)}")
        return False, [], [f"Manifest load error: {str(e)}"]
    
    if not manifest or 'artifacts' not in manifest:
        logger.warning("Manifest exists but contains no artifacts")
        return True, [], []
    
    passed = []
    failed = []
    
    logger.info(f"Verifying {len(manifest['artifacts'])} artifacts...")
    
    for artifact_path, artifact_info in manifest['artifacts'].items():
        expected_hash = artifact_info.get('hash')
        if not expected_hash:
            failed.append(f"Missing hash for {artifact_path}")
            continue
        
        success, message = verify_artifact_integrity(artifact_path, expected_hash, project_root)
        if success:
            passed.append(message)
        else:
            failed.append(message)
    
    return len(failed) == 0, passed, failed

def generate_verification_report(
    project_root: Path, 
    success: bool, 
    passed: List[str], 
    failed: List[str]
) -> Dict[str, Any]:
    """
    Generate a verification report artifact.
    
    Args:
        project_root: Project root directory
        success: Overall verification success
        passed: List of passed verification messages
        failed: List of failed verification messages
        
    Returns:
        Report dictionary
    """
    report = {
        "verification_status": "PASSED" if success else "FAILED",
        "timestamp": None,  # Will be set by caller if needed
        "total_artifacts": len(passed) + len(failed),
        "passed_count": len(passed),
        "failed_count": len(failed),
        "passed_artifacts": passed,
        "failed_artifacts": failed,
        "manifest_path": str(MANIFEST_PATH)
    }
    
    return report

def save_verification_report(report: Dict[str, Any], project_root: Path) -> str:
    """
    Save the verification report to artifacts/.
    
    Args:
        report: Verification report dictionary
        project_root: Project root directory
        
    Returns:
        Path to the saved report
    """
    artifacts_dir = project_root / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = artifacts_dir / "manifest_verification_report.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Verification report saved to {report_path}")
    return str(report_path)

def main():
    """Main entry point for manifest verification."""
    project_root = Path.cwd()
    
    logger.info(f"Starting manifest verification for project at {project_root}")
    
    success, passed, failed = verify_manifest_integrity(project_root)
    
    report = generate_verification_report(project_root, success, passed, failed)
    report_path = save_verification_report(report, project_root)
    
    if success:
        logger.info(f"✅ Manifest verification PASSED: {len(passed)} artifacts verified")
    else:
        logger.error(f"❌ Manifest verification FAILED: {len(failed)} artifacts failed")
        for fail_msg in failed:
            logger.error(f"  - {fail_msg}")
    
    # Print summary
    print("\n" + "="*60)
    print("MANIFEST VERIFICATION SUMMARY")
    print("="*60)
    print(f"Status: {'PASSED' if success else 'FAILED'}")
    print(f"Total Artifacts: {len(passed) + len(failed)}")
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failed)}")
    print(f"Report: {report_path}")
    print("="*60)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
