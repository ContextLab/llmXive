"""
Checksum Generation and Recording for Data Artifacts (T039).

This module implements Constitution Principle III by generating SHA-256 checksums
for all critical data artifacts and recording them in a state file alongside
a derivation.json file documenting the transformation path.
"""
import os
import sys
import json
import hashlib
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path if running as script
if __name__ == "__main__" and str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import setup_logger, log_error, safe_execute

# Configure logger
logger = setup_logger("checksum_recorder")

# Define the artifacts to checksum based on T039 requirements
ARTIFACT_RELATIVE_PATHS = [
    "data/results.csv",
    "data/intermediate/baseline_run.jsonl",
    "data/intermediate/hf_run_1b.jsonl",
    "data/intermediate/hf_run_7b.jsonl",
    "data/filtered_swe_bench_v1.parquet", # The filtered dataset
]

# Output paths
CHECKSUM_STATE_FILE = "state/projects/PROJ-904-llmxive-follow-up-extending-claw-sen.yaml"
DERIVATION_FILE = "state/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/derivation.json"

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"Artifact not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to calculate hash for {file_path}: {e}")

def record_checksums(artifacts: List[str], project_root: Path) -> Dict[str, Any]:
    """
    Calculate checksums for all artifacts and return a dictionary of results.
    
    Args:
        artifacts: List of relative file paths to checksum.
        project_root: Path to the project root directory.
        
    Returns:
        Dictionary containing checksums and metadata.
    """
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "artifacts": {},
        "missing_artifacts": [],
        "status": "success"
    }

    for rel_path in artifacts:
        full_path = project_root / rel_path
        logger.info(f"Processing artifact: {rel_path}")
        
        if not full_path.exists():
            logger.warning(f"Artifact missing, skipping: {rel_path}")
            results["missing_artifacts"].append(rel_path)
            continue
        
        try:
            file_hash = calculate_sha256(full_path)
            file_size = full_path.stat().st_size
            
            results["artifacts"][rel_path] = {
                "sha256": file_hash,
                "size_bytes": file_size,
                "exists": True
            }
            logger.info(f"  -> Hash: {file_hash} (Size: {file_size} bytes)")
        except Exception as e:
            logger.error(f"Error processing {rel_path}: {e}")
            results["artifacts"][rel_path] = {
                "error": str(e),
                "exists": False
            }
            results["status"] = "partial_failure"

    if results["missing_artifacts"]:
        logger.warning(f"Missing {len(results['missing_artifacts'])} artifacts.")
        
    return results

def write_yaml_state(checksum_data: Dict[str, Any], output_path: Path) -> None:
    """
    Write the checksum data to a YAML file.
    Since PyYAML might not be in strict dependencies, we use a simple manual writer
    or json if yaml is unavailable, but the spec asks for YAML.
    We will implement a basic YAML writer for this specific structure.
    """
    try:
        import yaml
        with open(output_path, 'w') as f:
            yaml.dump(checksum_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Wrote YAML state to: {output_path}")
    except ImportError:
        # Fallback to manual YAML writing for simple structure if yaml not installed
        logger.warning("PyYAML not found, writing manual YAML representation.")
        with open(output_path, 'w') as f:
            f.write(f"timestamp: {checksum_data['timestamp']}\n")
            f.write(f"status: {checksum_data['status']}\n")
            f.write("artifacts:\n")
            for path, info in checksum_data['artifacts'].items():
                f.write(f"  {path}:\n")
                for key, val in info.items():
                    if isinstance(val, str):
                        f.write(f"    {key}: '{val}'\n")
                    else:
                        f.write(f"    {key}: {val}\n")
            if checksum_data['missing_artifacts']:
                f.write("missing_artifacts:\n")
                for m in checksum_data['missing_artifacts']:
                    f.write(f"  - {m}\n")
            else:
                f.write("missing_artifacts: []\n")
        logger.info(f"Wrote manual YAML state to: {output_path}")

def write_derivation_json(derivation_data: Dict[str, Any], output_path: Path) -> None:
    """Write the derivation path documentation to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(derivation_data, f, indent=2)
    logger.info(f"Wrote derivation log to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate checksums for data artifacts (T039)")
    parser.add_argument("--project-root", type=str, default=".", help="Path to project root")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    logger.info(f"Project root: {project_root}")

    # 1. Calculate Checksums
    checksum_results = record_checksums(ARTIFACT_RELATIVE_PATHS, project_root)

    # 2. Prepare Derivation Data
    # This documents the transformation path for every artifact
    derivation_data = {
        "project_id": "PROJ-904-llmxive-follow-up-extending-claw-swe-ben",
        "task_id": "T039",
        "description": "Checksum generation and recording for data artifacts",
        "timestamp": datetime.utcnow().isoformat(),
        "artifacts": []
    }

    for rel_path, info in checksum_results["artifacts"].items():
        if info.get("exists"):
            # Infer derivation based on filename patterns
            derivation_info = {
                "path": rel_path,
                "hash": info["sha256"],
                "size": info["size_bytes"],
                "source_tasks": []
            }
            
            if "baseline_run.jsonl" in rel_path:
                derivation_info["source_tasks"] = ["T016"]
                derivation_info["description"] = "Baseline execution results"
            elif "hf_run_1b.jsonl" in rel_path:
                derivation_info["source_tasks"] = ["T023"]
                derivation_info["description"] = "High-fidelity 1B model results"
            elif "hf_run_7b.jsonl" in rel_path:
                derivation_info["source_tasks"] = ["T027"]
                derivation_info["description"] = "High-fidelity 7B model results"
            elif "results.csv" in rel_path:
                derivation_info["source_tasks"] = ["T028"]
                derivation_info["description"] = "Aggregated results (Single Source of Truth)"
            elif "filtered_swe_bench_v1.parquet" in rel_path:
                derivation_info["source_tasks"] = ["T012c"]
                derivation_info["description"] = "Filtered dataset (>500 lines)"
            else:
                derivation_info["source_tasks"] = ["Unknown"]
                derivation_info["description"] = "Data artifact"
            
            derivation_data["artifacts"].append(derivation_info)

    # 3. Write Outputs
    state_file = project_root / CHECKSUM_STATE_FILE
    derivation_file = project_root / DERIVATION_FILE

    write_yaml_state(checksum_results, state_file)
    write_derivation_json(derivation_data, derivation_file)

    # 4. Final Status
    if checksum_results["missing_artifacts"]:
        logger.error(f"Task T039 completed with missing artifacts: {checksum_results['missing_artifacts']}")
        sys.exit(1)
    else:
        logger.info("Task T039 completed successfully. All artifacts checksummed.")
        sys.exit(0)

if __name__ == "__main__":
    main()