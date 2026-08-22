"""
Reproducibility Check Script (T031)

Runs the full pipeline three times, computes SHA-256 hashes for all generated
artifacts, updates the artifact_hashes.yaml state file, and verifies metric
variance across runs is within acceptable bounds (ROC-AUC std < 0.02).

Satisfies Constitution V (Reproducibility).
"""
import argparse
import hashlib
import json
import logging
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
import pandas as pd
import numpy as np

# Project root relative to script location
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = PROJECT_ROOT / "state" / "projects" / "PROJ-544-predicting-the-glass-forming-region-of-m"
ARTIFACT_HASHES_FILE = STATE_DIR / "artifact_hashes.yaml"
LOG_DIR = PROJECT_ROOT / "logs"
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
MODELS_DIR = PROJECT_ROOT / "models"

# Scripts to run in the pipeline
PIPELINE_SCRIPTS = [
    "scripts/validate_descriptors.py",
    "scripts/sample_dataset.py",
    "scripts/filter_labels.py",
    "code/descriptors/check_imbalance.py",
    "code/descriptors/vif_report.py",
    "code/descriptors/vif_filter.py",
    "code/models/train.py",
    "code/models/evaluate.py",
    "code/models/importance.py",
    "scripts/sensitivity_analysis.py",
]

# Artifacts to hash (relative paths from PROJECT_ROOT)
ARTIFACT_PATTERNS = [
    "data/derived/descriptor_vector.csv",
    "data/derived/descriptor_vector_vif_filtered.csv",
    "data/derived/filtered_alloys.csv",
    "data/derived/imbalance_report.json",
    "data/derived/vif_report.json",
    "data/derived/pca_components.csv",
    "models/trained_models.pkl",
    "results/performance_metrics.json",
    "results/permutation_importance.csv",
    "results/sensitivity_report.json",
    "results/descriptor_benchmark_report.json",
    "results/shap_plots/shap_summary_RandomForest.png",
    "results/shap_plots/shap_summary_GradientBoosting.png",
]

def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "reproducibility_check.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def compute_file_hash(file_path: Path) -> Optional[str]:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        logging.warning(f"File not found for hashing: {file_path}")
        return None
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logging.error(f"Error computing hash for {file_path}: {e}")
        return None

def run_script(script_path: str, logger: logging.Logger) -> bool:
    """Run a pipeline script."""
    full_path = PROJECT_ROOT / script_path
    if not full_path.exists():
        logger.error(f"Script not found: {full_path}")
        return False
    
    logger.info(f"Running {script_path}...")
    try:
        # Run with python from project root
        result = subprocess.run(
            [sys.executable, str(full_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per script
        )
        
        if result.returncode != 0:
            logger.error(f"Script {script_path} failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
        
        logger.info(f"Successfully completed {script_path}")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Script {script_path} timed out")
        return False
    except Exception as e:
        logger.error(f"Error running {script_path}: {e}")
        return False

def collect_artifact_hashes(logger: logging.Logger) -> Dict[str, str]:
    """Collect SHA-256 hashes for all defined artifacts."""
    hashes = {}
    for pattern in ARTIFACT_PATTERNS:
        file_path = PROJECT_ROOT / pattern
        if file_path.exists():
            hash_val = compute_file_hash(file_path)
            if hash_val:
                hashes[pattern] = hash_val
        else:
            logger.warning(f"Artifact not found: {pattern}")
    return hashes

def load_existing_hashes() -> Dict[str, Any]:
    """Load existing artifact_hashes.yaml if it exists."""
    if ARTIFACT_HASHES_FILE.exists():
        try:
            with open(ARTIFACT_HASHES_FILE, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logging.warning(f"Could not load existing hashes: {e}")
    return {}

def save_hashes(hashes_data: Dict[str, Any]):
    """Save updated artifact_hashes.yaml."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_HASHES_FILE, 'w') as f:
        yaml.dump(hashes_data, f, default_flow_style=False, sort_keys=False)

def extract_roc_auc_from_metrics(logger: logging.Logger) -> Optional[float]:
    """Extract ROC-AUC from performance_metrics.json."""
    metrics_file = RESULTS_DIR / "performance_metrics.json"
    if not metrics_file.exists():
        logger.warning(f"Metrics file not found: {metrics_file}")
        return None
    
    try:
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        # Try to find ROC-AUC in various locations
        if isinstance(metrics, dict):
            if 'roc_auc' in metrics:
                return float(metrics['roc_auc'])
            if 'mean_roc_auc' in metrics:
                return float(metrics['mean_roc_auc'])
            if 'metrics' in metrics and isinstance(metrics['metrics'], dict):
                if 'roc_auc' in metrics['metrics']:
                    return float(metrics['metrics']['roc_auc'])
        
        logger.warning(f"Could not find ROC-AUC in metrics file: {metrics_file}")
        return None
    except Exception as e:
        logger.error(f"Error extracting ROC-AUC: {e}")
        return None

def check_reproducibility(hashes_list: List[Dict[str, str]], roc_auc_values: List[Optional[float]], logger: logging.Logger) -> Dict[str, Any]:
    """Check reproducibility and generate report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "num_runs": len(hashes_list),
        "run_hashes": hashes_list,
        "roc_auc_values": roc_auc_values,
        "artifacts_changed": [],
        "reproducible": True,
        "variance_check": {
            "metric": "ROC-AUC",
            "threshold": 0.02,
            "passed": True,
            "details": {}
        }
    }
    
    # Check if artifacts changed across runs
    if len(hashes_list) > 1:
        first_run_hashes = hashes_list[0]
        for i, run_hashes in enumerate(hashes_list[1:], 1):
            changed = []
            for artifact, hash_val in run_hashes.items():
                if artifact in first_run_hashes and first_run_hashes[artifact] != hash_val:
                    changed.append(artifact)
            if changed:
                report["artifacts_changed"].append({
                    "run": i + 1,
                    "changed_artifacts": changed
                })
                if changed:  # Any change means not reproducible
                    report["reproducible"] = False
    
    # Check ROC-AUC variance
    valid_roc_auc = [v for v in roc_auc_values if v is not None]
    if len(valid_roc_auc) >= 2:
        std_dev = np.std(valid_roc_auc)
        report["variance_check"]["details"]["std_dev"] = float(std_dev)
        report["variance_check"]["details"]["values"] = [float(v) for v in valid_roc_auc]
        report["variance_check"]["details"]["mean"] = float(np.mean(valid_roc_auc))
        
        if std_dev >= 0.02:
            report["variance_check"]["passed"] = False
            report["reproducible"] = False
    elif len(valid_roc_auc) == 1:
        report["variance_check"]["details"]["values"] = [float(valid_roc_auc[0])]
        report["variance_check"]["details"]["note"] = "Only one valid ROC-AUC value found"
    else:
        report["variance_check"]["passed"] = False
        report["variance_check"]["details"]["error"] = "No valid ROC-AUC values found"
        report["reproducible"] = False
    
    return report

def main():
    parser = argparse.ArgumentParser(description="Run reproducibility check for the glass-forming alloy pipeline")
    parser.add_argument("--runs", type=int, default=3, help="Number of pipeline runs to perform")
    parser.add_argument("--output", type=str, default=None, help="Output file for reproducibility report")
    args = parser.parse_args()
    
    logger = setup_logging()
    logger.info("=" * 80)
    logger.info("Starting Reproducibility Check (T031)")
    logger.info(f"Pipeline runs: {args.runs}")
    logger.info("=" * 80)
    
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load existing hashes
    existing_hashes = load_existing_hashes()
    
    all_run_hashes = []
    all_roc_auc_values = []
    
    for run_num in range(1, args.runs + 1):
        logger.info(f"\n{'='*40}")
        logger.info(f"Run {run_num}/{args.runs}")
        logger.info(f"{'='*40}")
        
        # Run pipeline scripts
        pipeline_success = True
        for script in PIPELINE_SCRIPTS:
            if not run_script(script, logger):
                pipeline_success = False
                logger.error(f"Pipeline failed at {script} during run {run_num}")
                break
        
        if not pipeline_success:
            logger.error(f"Skipping hash collection for run {run_num} due to pipeline failure")
            continue
        
        # Collect artifact hashes
        run_hashes = collect_artifact_hashes(logger)
        all_run_hashes.append(run_hashes)
        
        # Extract ROC-AUC
        roc_auc = extract_roc_auc_from_metrics(logger)
        all_roc_auc_values.append(roc_auc)
        
        logger.info(f"Run {run_num} completed. Collected {len(run_hashes)} artifact hashes.")
    
    # Generate reproducibility report
    report = check_reproducibility(all_run_hashes, all_roc_auc_values, logger)
    
    # Update artifact_hashes.yaml with latest run
    if all_run_hashes:
        latest_hashes = all_run_hashes[-1]
        updated_hashes = {
            "updated_at": datetime.now().isoformat(),
            "run_number": args.runs,
            "artifacts": latest_hashes
        }
        
        # Merge with existing structure if needed
        if "history" not in existing_hashes:
            existing_hashes["history"] = []
        
        existing_hashes["history"].append(updated_hashes)
        existing_hashes["latest"] = updated_hashes
        
        save_hashes(existing_hashes)
        logger.info(f"Updated {ARTIFACT_HASHES_FILE} with latest hashes")
    
    # Save report
    report_file = PROJECT_ROOT / "results" / "reproducibility_report.json"
    if args.output:
        report_file = Path(args.output)
    
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"\nReproducibility report saved to: {report_file}")
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("REPRODUCIBILITY CHECK SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total runs: {report['num_runs']}")
    logger.info(f"Reproducible: {report['reproducible']}")
    logger.info(f"Artifacts changed: {len(report['artifacts_changed'])} runs had changes")
    logger.info(f"ROC-AUC variance check: {'PASSED' if report['variance_check']['passed'] else 'FAILED'}")
    
    if report['variance_check']['passed']:
        logger.info(f"  Std dev: {report['variance_check']['details'].get('std_dev', 'N/A')}")
        logger.info(f"  Mean: {report['variance_check']['details'].get('mean', 'N/A')}")
    else:
        logger.warning(f"  Variance exceeded threshold of 0.02")
    
    if not report['reproducible']:
        logger.warning("Pipeline is NOT reproducible across runs!")
        return 1
    else:
        logger.info("Pipeline is REPRODUCIBLE across runs!")
        return 0

if __name__ == "__main__":
    sys.exit(main())