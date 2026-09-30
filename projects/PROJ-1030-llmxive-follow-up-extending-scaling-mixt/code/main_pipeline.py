"""
Main pipeline orchestrator for the llmXive follow-up project.
Coordinates all phases: Feature Extraction, Labeling, Classification, and Audits.
Updates project state, generates manifests, and writes timing summaries.
"""
import os
import sys
import json
import hashlib
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config_manager import get_config
from utils.logging_config import get_logger, fail_loudly
from utils.retry import retry_with_backoff

# Import pipeline stage modules
from extract_features import main as extract_features_main
from generate_labels import main as generate_labels_main
from classification.train_classifier import main as train_classifier_main
from classification.compute_metrics import main as compute_metrics_main
from classification.feature_importance import main as feature_importance_main
from classification.visualize_importance import main as visualize_importance_main
from classification.compute_baseline import main as compute_baseline_main
from utils.prior_audit import main as run_prior_audit_main

# Constants
MANIFEST_FILE = PROJECT_ROOT / "state" / "manifest.yaml"
PROJECT_STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-1030-llmxive-follow-up-extending-scaling-mixt.yaml"
PIPELINE_SUMMARY_FILE = PROJECT_ROOT / "pipeline_run_summary.json"
PIPELINE_TIMING_FILE = PROJECT_ROOT / "pipeline_timing.json"
LOG_FILE = PROJECT_ROOT / "data" / "processed" / "pipeline_execution.log"

def setup_logging():
    """Configure logging for the pipeline execution."""
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return get_logger('main_pipeline')

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return file_path.stat().st_size

def verify_artifacts_exist(artifacts: List[Path]) -> Dict[str, bool]:
    """Verify that all required artifacts exist."""
    results = {}
    for artifact in artifacts:
        exists = artifact.exists()
        results[artifact.name] = exists
        if not exists:
            logging.warning(f"Artifact missing: {artifact}")
    return results

def generate_manifest(artifacts: List[Path], logger: logging.Logger) -> Dict[str, Any]:
    """Generate a manifest with SHA-256 hashes and metadata for all artifacts."""
    manifest = {
        "generated_at": datetime.utcnow().isoformat(),
        "project_id": "PROJ-1030-llmxive-follow-up-extending-scaling-mixt",
        "artifacts": {}
    }
    
    for artifact in artifacts:
        if artifact.exists():
            manifest["artifacts"][str(artifact.relative_to(PROJECT_ROOT))] = {
                "sha256": calculate_sha256(artifact),
                "size_bytes": calculate_file_size(artifact),
                "type": artifact.suffix
            }
        else:
            logger.warning(f"Skipping non-existent artifact: {artifact}")
    
    return manifest

def write_yaml_manifest(manifest: Dict[str, Any], logger: logging.Logger):
    """Write the manifest to a YAML file."""
    # Simple YAML serialization for the manifest structure
    yaml_content = f"# Generated at: {manifest['generated_at']}\n"
    yaml_content += f"project_id: {manifest['project_id']}\n"
    yaml_content += "artifacts:\n"
    
    for path, info in manifest['artifacts'].items():
        yaml_content += f"  {path}:\n"
        yaml_content += f"    sha256: {info['sha256']}\n"
        yaml_content += f"    size_bytes: {info['size_bytes']}\n"
        yaml_content += f"    type: {info['type']}\n"
    
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, 'w') as f:
        f.write(yaml_content)
    
    logger.info(f"Manifest written to {MANIFEST_FILE}")

def load_yaml_config(file_path: Path) -> Dict[str, Any]:
    """Load a YAML configuration file (simple parser)."""
    config = {}
    if not file_path.exists():
        return config
    
    with open(file_path, 'r') as f:
        current_section = None
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.endswith(':') and not line.startswith(' '):
                current_section = line[:-1]
                config[current_section] = {}
            elif ':' in line and current_section:
                key, value = line.split(':', 1)
                config[current_section][key.strip()] = value.strip()
    return config

def save_yaml_config(file_path: Path, config: Dict[str, Any]):
    """Save configuration to a YAML file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        for section, values in config.items():
            f.write(f"{section}:\n")
            for key, value in values.items():
                f.write(f"  {key}: {value}\n")

def update_project_timestamp():
    """Update the project state file with the current timestamp."""
    if PROJECT_STATE_FILE.exists():
        config = load_yaml_config(PROJECT_STATE_FILE)
        config.setdefault('state', {})
        config['state']['updated_at'] = datetime.utcnow().isoformat()
        save_yaml_config(PROJECT_STATE_FILE, config)
    else:
        # Create new project state file if it doesn't exist
        config = {
            'project_id': 'PROJ-1030-llmxive-follow-up-extending-scaling-mixt',
            'state': {
                'updated_at': datetime.utcnow().isoformat(),
                'status': 'running'
            }
        }
        save_yaml_config(PROJECT_STATE_FILE, config)

def run_pipeline_orchestration(logger: logging.Logger) -> Dict[str, Any]:
    """Run the full pipeline stages and collect results."""
    results = {
        "phases": {},
        "status": "success",
        "errors": []
    }
    
    # Define pipeline stages
    stages = [
        ("feature_extraction", extract_features_main, "T013"),
        ("label_generation", generate_labels_main, "T025"),
        ("classifier_training", train_classifier_main, "T031"),
        ("metrics_computation", compute_metrics_main, "T032"),
        ("feature_importance", feature_importance_main, "T033"),
        ("visualization", visualize_importance_main, "T035"),
        ("baseline_computation", compute_baseline_main, "T032.0"),
        ("prior_audit", run_prior_audit_main, "T036.3.1")
    ]
    
    for stage_name, stage_func, task_id in stages:
        logger.info(f"Starting phase: {stage_name} (Task {task_id})")
        start_time = time.time()
        try:
            # Run the stage function
            stage_func()
            end_time = time.time()
            results["phases"][stage_name] = {
                "status": "success",
                "duration_seconds": end_time - start_time,
                "task_id": task_id
            }
            logger.info(f"Completed phase: {stage_name}")
        except Exception as e:
            end_time = time.time()
            results["phases"][stage_name] = {
                "status": "failed",
                "duration_seconds": end_time - start_time,
                "task_id": task_id,
                "error": str(e)
            }
            results["errors"].append(f"Phase {stage_name} failed: {str(e)}")
            logger.error(f"Phase {stage_name} failed: {str(e)}")
            # Continue with other phases instead of stopping
    
    if results["errors"]:
        results["status"] = "partial_success"
    
    return results

def write_pipeline_time_log(timings: Dict[str, float]):
    """Write pipeline timing information to a JSON file."""
    with open(PIPELINE_TIMING_FILE, 'w') as f:
        json.dump(timings, f, indent=2)
    logging.info(f"Pipeline timing written to {PIPELINE_TIMING_FILE}")

def main():
    """Main entry point for the pipeline orchestrator."""
    logger = setup_logging()
    logger.info("Starting llmXive pipeline orchestration")
    
    # Ensure directories exist
    (PROJECT_ROOT / "state" / "projects").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    
    try:
        # Update project timestamp
        update_project_timestamp()
        logger.info("Project state updated")
        
        # Run pipeline stages
        pipeline_results = run_pipeline_orchestration(logger)
        
        # Collect artifacts for manifest
        artifact_paths = [
            PROJECT_ROOT / "data" / "processed" / "features.npy",
            PROJECT_ROOT / "data" / "processed" / "labels.csv",
            PROJECT_ROOT / "data" / "processed" / "classifier.pkl",
            PROJECT_ROOT / "data" / "processed" / "evaluation_metrics.json",
            PROJECT_ROOT / "data" / "processed" / "feature_importance.json",
            PROJECT_ROOT / "data" / "processed" / "shap_interpretation.md",
            PROJECT_ROOT / "data" / "processed" / "latent_audit_report.json",
            PROJECT_ROOT / "data" / "processed" / "prior_audit_report.json",
            PROJECT_ROOT / "data" / "processed" / "baseline_f1.json",
            PROJECT_ROOT / "docs" / "results_report.md"
        ]
        
        # Generate and write manifest
        manifest = generate_manifest(artifact_paths, logger)
        write_yaml_manifest(manifest, logger)
        
        # Calculate total timing
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Prepare timing data
        timing_data = {
            "total_pipeline_seconds": total_duration,
            "start_time": datetime.utcfromtimestamp(start_time).isoformat(),
            "end_time": datetime.utcfromtimestamp(end_time).isoformat(),
            "stages": {}
        }
        
        # Add stage timings
        for stage_name, stage_info in pipeline_results["phases"].items():
            timing_data["stages"][stage_name] = stage_info.get("duration_seconds", 0)
        
        write_pipeline_time_log(timing_data)
        
        # Write pipeline summary
        summary = {
            "project_id": "PROJ-1030-llmxive-follow-up-extending-scaling-mixt",
            "run_id": datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
            "status": pipeline_results["status"],
            "total_duration_seconds": total_duration,
            "phases": pipeline_results["phases"],
            "errors": pipeline_results.get("errors", []),
            "manifest_path": str(MANIFEST_FILE.relative_to(PROJECT_ROOT)),
            "timing_path": str(PIPELINE_TIMING_FILE.relative_to(PROJECT_ROOT))
        }
        
        with open(PIPELINE_SUMMARY_FILE, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Pipeline summary written to {PIPELINE_SUMMARY_FILE}")
        logger.info(f"Pipeline completed with status: {pipeline_results['status']}")
        
        return 0 if pipeline_results["status"] == "success" else 1
        
    except Exception as e:
        logger.error(f"Pipeline orchestration failed: {str(e)}")
        fail_loudly(f"Pipeline orchestration failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
