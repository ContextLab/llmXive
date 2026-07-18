"""
Reproducibility verification script for the Emotional Contagion project.

This script verifies that the pipeline is reproducible by:
1. Recording checksums of all artifacts from a previous run
2. Re-running the pipeline (or key components)
3. Comparing checksums to ensure deterministic results

Usage:
    python code/utils/reproducibility_checker.py
"""

import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.artifact_checksums import compute_file_hash, find_artifacts, record_checksums
from utils.logging_config import get_logger
from config.settings import get_config

# Configure logging
logger = get_logger("reproducibility_checker")

# Artifact directories to check
ARTIFACT_DIRECTORIES = [
    "data/processed",
    "data/raw",
    "state",
    "figures"
]

# Configuration file for reproducibility tracking
REPRODUCIBILITY_STATE_FILE = "state/projects/PROJ-139-the-influence-of-emotional-contagion-on-reproducibility.yaml"

def load_previous_checksums(state_file: Path) -> Optional[Dict[str, Any]]:
    """Load previously recorded checksums from state file."""
    if not state_file.exists():
        logger.warning(f"Previous checksums file not found: {state_file}")
        return None
    
    try:
        import yaml
        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)
            logger.info(f"Loaded previous checksums from {state_file}")
            return data
    except Exception as e:
        logger.error(f"Failed to load checksums file: {e}")
        return None

def compute_current_checksums(artifact_dirs: List[str], project_root: Path) -> Dict[str, str]:
    """Compute checksums for all artifacts in specified directories."""
    checksums = {}
    
    for dir_path in artifact_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            logger.warning(f"Directory not found: {full_path}")
            continue
        
        artifacts = find_artifacts(full_path)
        for artifact in artifacts:
            try:
                hash_value = compute_file_hash(artifact)
                rel_path = str(artifact.relative_to(project_root))
                checksums[rel_path] = hash_value
                logger.debug(f"Computed hash for {rel_path}: {hash_value[:16]}...")
            except Exception as e:
                logger.error(f"Failed to compute hash for {artifact}: {e}")
    
    return checksums

def compare_checksums(
    previous: Dict[str, str],
    current: Dict[str, str],
    tolerance: float = 0.0
) -> Dict[str, Any]:
    """Compare two sets of checksums and return detailed comparison results."""
    results = {
        "matched": [],
        "mismatched": [],
        "new": [],
        "missing": [],
        "match_rate": 0.0
    }
    
    all_keys = set(previous.keys()) | set(current.keys())
    matched_count = 0
    
    for key in sorted(all_keys):
        if key in previous and key in current:
            if previous[key] == current[key]:
                results["matched"].append(key)
                matched_count += 1
            else:
                results["mismatched"].append({
                    "path": key,
                    "previous_hash": previous[key],
                    "current_hash": current[key]
                })
        elif key in current:
            results["new"].append(key)
        else:
            results["missing"].append(key)
    
    if len(all_keys) > 0:
        results["match_rate"] = matched_count / len(all_keys)
    
    return results

def save_reproducibility_report(
    results: Dict[str, Any],
    previous_checksums: Dict[str, str],
    current_checksums: Dict[str, str],
    output_file: Path,
    project_root: Path
):
    """Save detailed reproducibility report to YAML file."""
    import yaml
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "project_id": "PROJ-139-the-influence-of-emotional-contagion-on",
        "task_id": "T028",
        "verification_status": "passed" if results["match_rate"] == 1.0 else "failed",
        "summary": {
            "total_artifacts_checked": len(set(previous_checksums.keys()) | set(current_checksums.keys())),
            "matched_artifacts": len(results["matched"]),
            "mismatched_artifacts": len(results["mismatched"]),
            "new_artifacts": len(results["new"]),
            "missing_artifacts": len(results["missing"]),
            "match_rate": results["match_rate"]
        },
        "details": {
            "matched_files": results["matched"],
            "mismatched_files": results["mismatched"],
            "new_files": results["new"],
            "missing_files": results["missing"]
        },
        "previous_checksums": previous_checksums,
        "current_checksums": current_checksums
    }
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Reproducibility report saved to {output_file}")
    return report

def re_run_pipeline_components(project_root: Path, config: Any) -> bool:
    """
    Re-run key pipeline components to generate fresh artifacts for comparison.
    
    This function orchestrates re-running the main pipeline stages:
    1. Data extraction (T009)
    2. Sentiment analysis (T013)
    3. Metrics computation (T015)
    4. Statistical modeling (T020)
    
    Returns True if all components ran successfully, False otherwise.
    """
    logger.info("Starting pipeline re-execution for reproducibility verification...")
    
    try:
        # Re-run data extraction
        logger.info("Re-running data extraction...")
        from data.extract import main as extract_main
        extract_main()
        
        # Re-run sentiment analysis
        logger.info("Re-running sentiment analysis...")
        from data.sentiment import main as sentiment_main
        sentiment_main()
        
        # Re-run metrics computation
        logger.info("Re-running metrics computation...")
        from data.metrics import main as metrics_main
        metrics_main()
        
        # Re-run statistical modeling
        logger.info("Re-running statistical modeling...")
        from data.modeling import main as modeling_main
        modeling_main()
        
        logger.info("Pipeline re-execution completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Pipeline re-execution failed: {e}")
        logger.error("Reproducibility verification cannot proceed without successful re-run")
        return False

def verify_reproducibility(project_root: Path = None) -> Dict[str, Any]:
    """
    Main function to verify reproducibility of the pipeline.
    
    Steps:
    1. Load previous checksums from state file
    2. Re-run pipeline components
    3. Compute current checksums
    4. Compare checksums
    5. Generate report
    
    Returns verification results.
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent.parent
    
    logger.info("=" * 60)
    logger.info("Starting Reproducibility Verification for PROJ-139")
    logger.info("=" * 60)
    
    # Load previous checksums
    state_file = project_root / REPRODUCIBILITY_STATE_FILE
    previous_checksums = load_previous_checksums(state_file)
    
    if previous_checksums is None:
        logger.error("No previous checksums found. Run the pipeline first to generate artifacts.")
        return {"status": "failed", "reason": "No previous checksums found"}
    
    # Re-run pipeline components
    config = get_config()
    pipeline_success = re_run_pipeline_components(project_root, config)
    
    if not pipeline_success:
        logger.error("Pipeline re-execution failed. Cannot verify reproducibility.")
        return {"status": "failed", "reason": "Pipeline re-execution failed"}
    
    # Compute current checksums
    logger.info("Computing current artifact checksums...")
    current_checksums = compute_current_checksums(ARTIFACT_DIRECTORIES, project_root)
    
    if not current_checksums:
        logger.error("No current artifacts found. Pipeline may not have produced outputs.")
        return {"status": "failed", "reason": "No current artifacts found"}
    
    # Compare checksums
    logger.info("Comparing checksums...")
    comparison_results = compare_checksums(previous_checksums, current_checksums)
    
    # Save report
    report_file = project_root / "state/projects/PROJ-139-reproducibility_report.yaml"
    report = save_reproducibility_report(
        comparison_results,
        previous_checksums,
        current_checksums,
        report_file,
        project_root
    )
    
    # Log summary
    logger.info("=" * 60)
    logger.info("REPRODUCIBILITY VERIFICATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total artifacts checked: {report['summary']['total_artifacts_checked']}")
    logger.info(f"Matched: {report['summary']['matched_artifacts']}")
    logger.info(f"Mismatched: {report['summary']['mismatched_artifacts']}")
    logger.info(f"New: {report['summary']['new_artifacts']}")
    logger.info(f"Missing: {report['summary']['missing_artifacts']}")
    logger.info(f"Match rate: {report['summary']['match_rate']:.2%}")
    logger.info(f"Status: {report['verification_status'].upper()}")
    logger.info("=" * 60)
    
    if report['verification_status'] == 'passed':
        logger.info("SUCCESS: All artifacts are reproducible!")
    else:
        logger.warning("WARNING: Some artifacts differ from previous run.")
        if report['details']['mismatched_files']:
            logger.warning("Mismatched files:")
            for item in report['details']['mismatched_files'][:5]:
                logger.warning(f"  - {item['path']}")
        if report['details']['new_files']:
            logger.warning("New files (not in previous run):")
            for f in report['details']['new_files'][:5]:
                logger.warning(f"  - {f}")
        if report['details']['missing_files']:
            logger.warning("Missing files (in previous run but not now):")
            for f in report['details']['missing_files'][:5]:
                logger.warning(f"  - {f}")
    
    return report

def main():
    """Entry point for reproducibility verification."""
    try:
        report = verify_reproducibility()
        
        # Exit with appropriate code
        if report.get('verification_status') == 'passed':
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Reproducibility verification failed with exception: {e}", exc_info=True)
        sys.exit(2)

if __name__ == "__main__":
    main()
