"""
Main entry point for the reproducibility assessment pipeline.
Handles environment logging (FR-012), orchestration of ingestion,
model execution, and aggregation of results into a final report (FR-005, FR-009).
"""
import json
import logging
import os
import platform
import subprocess
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

# Import from existing API surface
from ingest import ingest_pipeline, load_manifest, validate_manifest
from metrics import calculate_all_metrics, calculate_deviation_index
from model_runner import run_reproducibility_assessment

# Configure logging
LOG_DIR = Path("artifacts/logs")
REPORTS_DIR = Path("artifacts/reports")
LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "pipeline.log"),
    ],
)
logger = logging.getLogger(__name__)

def get_docker_hash() -> Optional[str]:
    """
    Attempt to retrieve the Docker image hash if running in a container.
    Returns None if not running in Docker or if the command fails.
    """
    try:
        if os.path.exists("/.dockerenv"):
            image_id_path = "/etc/image-id"
            if os.path.exists(image_id_path):
                with open(image_id_path, "r") as f:
                    return f.read().strip()
            
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.Id}}", "current"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
            
            with open("/proc/1/cgroup", "r") as f:
                content = f.read()
                return hashlib.sha256(content.encode()).hexdigest()[:12]
    except Exception as e:
        logger.debug(f"Could not retrieve Docker hash: {e}")
    
    return None

def log_environment() -> Dict[str, Any]:
    """
    Capture and log environment details as per FR-012.
    Writes the snapshot to artifacts/logs/env.log.
    """
    env_info = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "python_version": sys.version,
        "platform": {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "docker_hash": get_docker_hash(),
        "libraries": {}
    }

    critical_libs = [
        "torch", "scikit-learn", "rdkit", "statsmodels", 
        "pandas", "numpy", "matplotlib", "pyyaml", "requests", 
        "scipy", "jsonschema"
    ]

    for lib_name in critical_libs:
        try:
            lib = __import__(lib_name)
            version = getattr(lib, "__version__", "unknown")
            env_info["libraries"][lib_name] = version
        except ImportError:
            env_info["libraries"][lib_name] = "not_installed"
        except Exception as e:
            env_info["libraries"][lib_name] = f"error: {e}"

    log_path = LOG_DIR / "env.log"
    with open(log_path, "w") as f:
        json.dump(env_info, f, indent=2)
    
    logger.info(f"Environment logged to {log_path}")
    return env_info

def aggregate_results(results: List[Dict[str, Any]], manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate individual ReproResult objects into a final report.
    Calculates deviations and the reproducibility score S (FR-009) against
    the reported metrics in the manifest.
    
    Args:
        results: List of ReproResult dictionaries from model_runner.
        manifest: The loaded manifest containing reported reference metrics.
    
    Returns:
        A dictionary containing the aggregated report.
    """
    if not results:
        logger.warning("No results to aggregate.")
        return {"results": [], "summary": {"total_papers": 0}}

    aggregated_results = []
    summary_stats = {
        "total_papers": len(results),
        "successful_reproductions": 0,
        "failed_reproductions": 0,
        "mae_deviations": [],
        "r2_deviations": [],
        "rho_deviations": []
    }

    # Extract reference metrics from manifest (assuming single target for now or first entry)
    # In a multi-paper scenario, this would map DOI to ref metrics.
    # For this implementation, we assume the manifest contains 'reported_metrics' 
    # relevant to the processed data, or we iterate if manifest has a list.
    # Based on T009, manifest has DOI, repo, dataset, reported_metrics.
    
    ref_metrics = manifest.get("reported_metrics", {})
    if not ref_metrics:
        logger.warning("Manifest does not contain 'reported_metrics'. Cannot calculate deviations.")
    
    for res in results:
        # Determine success based on model substitution or data availability flags
        is_success = True
        if res.get("status") == "Model Substitution/Unavailable" or res.get("status") == "Data Unavailable":
            is_success = False
            summary_stats["failed_reproductions"] += 1
        else:
            summary_stats["successful_reproductions"] += 1

        # Calculate Deviations and Score S (FR-009)
        dev_mae = 0.0
        dev_r2 = 0.0
        dev_rho = 0.0
        score_s = 0.0

        if ref_metrics:
            eps = 1e-6
            ref_mae = ref_metrics.get("mae", 0.0)
            ref_r2 = ref_metrics.get("r2", 0.0)
            ref_rho = ref_metrics.get("spearman_rho", 0.0)
            
            curr_mae = res.get("mae", 0.0)
            curr_r2 = res.get("r2", 0.0)
            curr_rho = res.get("spearman_rho", 0.0)

            dev_mae = abs(curr_mae - ref_mae) / (abs(ref_mae) + eps)
            dev_r2 = abs(curr_r2 - ref_r2) / (abs(ref_r2) + eps)
            dev_rho = abs(curr_rho - ref_rho) / (abs(ref_rho) + eps)

            # S = 1 – (|ΔMAE|/(|MAE_ref|+ε) + |ΔR2|/(|R2_ref|+ε) + |Δρ|/(|ρ_ref|+ε))/3
            score_s = 1.0 - (dev_mae + dev_r2 + dev_rho) / 3.0
            
            summary_stats["mae_deviations"].append(dev_mae)
            summary_stats["r2_deviations"].append(dev_r2)
            summary_stats["rho_deviations"].append(dev_rho)

        # Construct the final ReproResult object for the report
        final_result = {
            "doi": res.get("doi", "unknown"),
            "status": res.get("status", "Success"),
            "reproduced_metrics": {
                "mae": res.get("mae"),
                "r2": res.get("r2"),
                "spearman_rho": res.get("spearman_rho"),
                "max_metric_std": res.get("max_metric_std", 0.0)
            },
            "reference_metrics": {
                "mae": ref_metrics.get("mae"),
                "r2": ref_metrics.get("r2"),
                "spearman_rho": ref_metrics.get("spearman_rho")
            },
            "deviations": {
                "mae": dev_mae,
                "r2": dev_r2,
                "rho": dev_rho
            },
            "reproducibility_score_s": score_s,
            "notes": res.get("notes", "")
        }
        aggregated_results.append(final_result)

    # Compute summary averages
    if summary_stats["mae_deviations"]:
        summary_stats["avg_mae_deviation"] = sum(summary_stats["mae_deviations"]) / len(summary_stats["mae_deviations"])
    if summary_stats["r2_deviations"]:
        summary_stats["avg_r2_deviation"] = sum(summary_stats["r2_deviations"]) / len(summary_stats["r2_deviations"])
    if summary_stats["rho_deviations"]:
        summary_stats["avg_rho_deviation"] = sum(summary_stats["rho_deviations"]) / len(summary_stats["rho_deviations"])

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "results": aggregated_results,
        "summary": summary_stats
    }

def main():
    """
    Orchestrate the full pipeline:
    1. Log environment (FR-012)
    2. Load and validate manifest
    3. Ingest data
    4. Run reproducibility assessment (model training/eval)
    5. Aggregate results and calculate deviations/score S
    6. Write final report to artifacts/reports/repro_results.json
    """
    logger.info("Starting reproducibility assessment pipeline...")
    
    # Step 1: Environment Logging (FR-012)
    env_snapshot = log_environment()
    logger.info(f"Python: {env_snapshot['python_version']}")
    if env_snapshot['docker_hash']:
        logger.info(f"Docker Hash: {env_snapshot['docker_hash']}")
    
    # Step 2: Load Manifest
    manifest_path = Path("data/manifest.yaml")
    if not manifest_path.exists():
        logger.error(f"Manifest not found at {manifest_path}. Aborting.")
        return
    
    logger.info(f"Loading manifest from {manifest_path}")
    manifest = load_manifest(manifest_path)
    validate_manifest(manifest)
    
    # Step 3: Ingest Data
    logger.info("Starting data ingestion pipeline...")
    # ingest_pipeline handles fetching and processing based on manifest
    # It returns the path to processed data or metadata needed for the next step
    processed_data_info = ingest_pipeline(manifest)
    
    # Step 4: Run Reproducibility Assessment
    logger.info("Running reproducibility assessment (model training and evaluation)...")
    # run_reproducibility_assessment expects manifest and processed data info
    # It returns a list of ReproResult dictionaries
    results = run_reproducibility_assessment(manifest, processed_data_info)
    
    # Step 5: Aggregate Results
    logger.info("Aggregating results and calculating deviations...")
    report = aggregate_results(results, manifest)
    
    # Step 6: Write Report
    output_path = REPORTS_DIR / "repro_results.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Final report written to {output_path}")
    logger.info(f"Summary: {report['summary']['successful_reproductions']} successful, "
                f"{report['summary']['failed_reproductions']} failed out of {report['summary']['total_papers']} papers.")
    
    return report

if __name__ == "__main__":
    main()