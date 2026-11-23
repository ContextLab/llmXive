import os
import sys
import subprocess
import hashlib
import json
import logging
import argparse
from pathlib import Path
import yaml
from datetime import datetime

from utils.logger import get_logger, configure_root_logger
from data.config import get_config, reset_config

# Configure logging for this script
logger = get_logger("reproducibility")

def run_pipeline_with_seed(seed: int, output_dir: str) -> dict:
    """
    Runs the full pipeline with a specific seed and returns a summary of artifacts.
    Returns a dictionary containing the SHA-256 hashes of all output artifacts.
    """
    logger.info(f"Running pipeline with seed {seed}...")
    
    # Reset configuration to ensure clean state
    reset_config()
    config = get_config()
    config.seed = seed
    
    # Set environment variable for seed
    os.environ["PYTHONHASHSEED"] = str(seed)
    os.environ["PROJECT_SEED"] = str(seed)
    
    # Run the main pipeline
    # We assume the main.py script handles the full pipeline execution
    # We need to run it in a way that captures the artifacts
    
    try:
        # Run the main pipeline script
        # We use subprocess to ensure a clean environment for each run
        result = subprocess.run(
            [sys.executable, "code/main.py", "--action", "full"],
            capture_output=True,
            text=True,
            env={**os.environ, "PROJECT_SEED": str(seed)}
        )
        
        if result.returncode != 0:
            logger.error(f"Pipeline run with seed {seed} failed: {result.stderr}")
            return {"success": False, "error": result.stderr, "hashes": {}}
        
        logger.info(f"Pipeline run with seed {seed} completed successfully.")
        
    except Exception as e:
        logger.error(f"Error running pipeline with seed {seed}: {str(e)}")
        return {"success": False, "error": str(e), "hashes": {}}
    
    # Collect hashes of all output artifacts
    artifacts = {
        "data/processed/imputed_data.csv": "imputed_data_hash",
        "data/processed/regression_coefficients.csv": "regression_coefficients_hash",
        "data/processed/model_diagnostics.json": "model_diagnostics_hash",
        "data/processed/sensitivity_sweep_results.csv": "sensitivity_results_hash",
        "data/processed/final_report.json": "final_report_hash",
        "state/projects/PROJ-490-the-effect-of-simulated-social-compariso.yaml": "state_hash"
    }
    
    hashes = {}
    for artifact_path, hash_key in artifacts.items():
        full_path = Path(artifact_path)
        if full_path.exists():
            with open(full_path, "rb") as f:
                content = f.read()
                hashes[hash_key] = hashlib.sha256(content).hexdigest()
                logger.info(f"Hashed {artifact_path}: {hashes[hash_key][:16]}...")
        else:
            logger.warning(f"Artifact {artifact_path} not found for seed {seed}")
            hashes[hash_key] = None
    
    return {"success": True, "hashes": hashes}

def compare_runs(run1: dict, run2: dict) -> dict:
    """
    Compares the hashes from two pipeline runs and returns a comparison result.
    """
    if not run1["success"] or not run2["success"]:
        return {
            "reproducible": False,
            "reason": "One or both runs failed",
            "run1_success": run1["success"],
            "run2_success": run2["success"]
        }
    
    hashes1 = run1["hashes"]
    hashes2 = run2["hashes"]
    
    differences = []
    for key in hashes1:
        if hashes1[key] != hashes2[key]:
            differences.append({
                "artifact": key,
                "run1_hash": hashes1[key],
                "run2_hash": hashes2[key],
                "match": False
            })
        else:
            differences.append({
                "artifact": key,
                "run1_hash": hashes1[key],
                "run2_hash": hashes2[key],
                "match": True
            })
    
    all_match = all(d["match"] for d in differences)
    
    return {
        "reproducible": all_match,
        "differences": differences,
        "summary": f"Reproducibility check: {'PASSED' if all_match else 'FAILED'}"
    }

def write_reproducibility_report(comparison: dict, seed1: int, seed2: int, output_path: str):
    """
    Writes the reproducibility check results to a YAML file.
    """
    report = {
        "task_id": "T034",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "seeds_used": [seed1, seed2],
        "reproducible": comparison["reproducible"],
        "summary": comparison["summary"],
        "details": {
            "run1_success": comparison.get("run1_success", True),
            "run2_success": comparison.get("run2_success", True),
            "differences": comparison["differences"] if "differences" in comparison else []
        }
    }
    
    if not comparison["reproducible"]:
        report["failure_reason"] = comparison.get("reason", "Hash mismatch detected")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w") as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Reproducibility report written to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Verify reproducibility of the pipeline")
    parser.add_argument("--seed1", type=int, default=42, help="First seed value")
    parser.add_argument("--seed2", type=int, default=42, help="Second seed value (should be same for reproducibility check)")
    parser.add_argument("--output", type=str, default="state/reproducibility_check.yaml", help="Output file path")
    args = parser.parse_args()
    
    configure_root_logger()
    
    logger.info("Starting reproducibility check...")
    logger.info(f"Using seeds: {args.seed1} and {args.seed2}")
    
    # Run the pipeline twice with the same seed
    run1 = run_pipeline_with_seed(args.seed1, "run1")
    run2 = run_pipeline_with_seed(args.seed2, "run2")
    
    # Compare the results
    comparison = compare_runs(run1, run2)
    
    # Write the report
    write_reproducibility_report(comparison, args.seed1, args.seed2, args.output)
    
    if comparison["reproducible"]:
        logger.info("Reproducibility check PASSED")
        sys.exit(0)
    else:
        logger.error("Reproducibility check FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
