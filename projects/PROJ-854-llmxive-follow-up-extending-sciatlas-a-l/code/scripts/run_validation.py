import os
import sys
import json
import logging
import subprocess
import hashlib
from pathlib import Path
from src.lib import config

logger = logging.getLogger(__name__)

def compute_file_hash(filepath: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_pipeline_step(step_name: str) -> bool:
    """Run a specific pipeline step."""
    # Placeholder for running steps
    logger.info(f"Running step: {step_name}")
    return True

def validate_artifacts() -> dict:
    """Validate that all required artifacts exist."""
    artifacts = [
        "data/raw/openalex_stream.parquet",
        "data/processed/subgraph_with_clusters.parquet",
        "data/processed/final_analysis_dataset.parquet"
    ]
    
    results = {}
    for artifact in artifacts:
        path = Path(config.get_data_path()).parent / artifact
        # Adjust path relative to project root
        full_path = Path(config.get_config('data_path')) / artifact.replace("data/", "")
        if full_path.exists():
            results[artifact] = {"exists": True, "hash": compute_file_hash(str(full_path))}
        else:
            results[artifact] = {"exists": False, "hash": None}
    return results

def generate_validation_report(results: dict) -> str:
    """Generate a validation report string."""
    report = "# Validation Report\n\n"
    for artifact, info in results.items():
        status = "OK" if info["exists"] else "MISSING"
        report += f"- {artifact}: {status}\n"
        if info["hash"]:
            report += f"  Hash: {info['hash']}\n"
    return report

def main():
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Starting validation...")
    results = validate_artifacts()
    report = generate_validation_report(results)
    
    # Save report
    report_path = Path(config.get_artifacts_path()) / "validation_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    logger.info(f"Validation report saved to {report_path}")
    print(report)

if __name__ == "__main__":
    main()
