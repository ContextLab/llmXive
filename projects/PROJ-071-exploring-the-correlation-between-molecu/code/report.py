"""
Report module for T034, T035, T035b: Generate final report and reproducibility log.
"""
import os
import sys
import json
import hashlib
import importlib.metadata
from datetime import datetime
from pathlib import Path
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_data_path() -> Path:
    return Path(__file__).parent.parent / "data"

def calculate_file_hash(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_package_version(pkg_name: str) -> str:
    try:
        return importlib.metadata.version(pkg_name)
    except importlib.metadata.PackageNotFoundError:
        return "N/A"

def collect_reproducibility_metadata() -> Dict[str, Any]:
    return {
        "rdkit_version": get_package_version("rdkit"),
        "scikit_learn_version": get_package_version("scikit-learn"),
        "pandas_version": get_package_version("pandas"),
        "timestamp": datetime.utcnow().isoformat(),
        "dataset_url": "Synthyra/FDA-Approved-Drugs"
    }

def save_reproducibility_report(metadata: Dict[str, Any]) -> None:
    path = get_data_path() / "reproducibility_log.json"
    with open(path, "w") as f:
        json.dump(metadata, f, indent=2)

def append_reproducibility_to_markdown(report_path: Path, metadata: Dict[str, Any]) -> None:
    with open(report_path, "a") as f:
        f.write("\n## Reproducibility\n")
        f.write(f"- **Date**: {metadata['timestamp']}\n")
        f.write(f"- **RDKit**: {metadata['rdkit_version']}\n")
        f.write(f"- **Scikit-Learn**: {metadata['scikit_learn_version']}\n")

def verify_artifact_integrity() -> bool:
    # Check analysis_results.json or data_insufficiency_report.md
    gate_file = get_data_path() / "gate_status.json"
    if not gate_file.exists():
        return False
    with open(gate_file, "r") as f:
        gate = json.load(f)
    
    if gate.get("status") == "PASS":
        path = get_data_path() / "processed" / "analysis_results.json"
        if not path.exists() or path.stat().st_size == 0:
            return False
    else:
        path = get_data_path() / "data_insufficiency_report.md"
        if not path.exists() or path.stat().st_size == 0:
            return False
    return True

def main():
    """Main entry point for Report."""
    logger.info("Starting Report (T034-T036)...")
    
    metadata = collect_reproducibility_metadata()
    
    # Add file hashes
    files_to_hash = [
        get_data_path() / "processed" / "merged_drugs.csv",
        get_data_path() / "processed" / "standard_subset.csv",
        get_data_path() / "processed" / "analysis_results.json"
    ]
    
    hashes = {}
    for f in files_to_hash:
        if f.exists():
            hashes[f.name] = calculate_file_hash(f)
    metadata["file_hashes"] = hashes
    
    save_reproducibility_report(metadata)
    
    # Generate Markdown Report
    gate_file = get_data_path() / "gate_status.json"
    report_path = get_data_path().parent / "results_report.md"
    
    if gate_file.exists():
        with open(gate_file, "r") as f:
            gate = json.load(f)
        if gate.get("status") == "FAIL":
            report_path = get_data_path() / "data_insufficiency_report.md"
            with open(report_path, "w") as f:
                f.write("# Data Insufficiency Report\n")
                f.write(f"Status: {gate.get('status')}\n")
                f.write(f"Reason: {gate.get('reason')}\n")
                f.write(f"N: {gate.get('N')}\n")
        else:
            # Load analysis results
            analysis_path = get_data_path() / "processed" / "analysis_results.json"
            if analysis_path.exists():
                with open(analysis_path, "r") as f:
                    results = json.load(f)
                with open(report_path, "w") as f:
                    f.write("# Analysis Report\n")
                    f.write(f"## Results\n")
                    f.write(f"- **R2**: {results.get('R2')}\n")
                    f.write(f"- **N**: {results.get('N')}\n")
                    f.write(f"- **Methodology**: {results.get('methodology')}\n")
                    f.write("\n## Coefficients\n")
                    for k, v in results.get('coefficients', {}).items():
                        f.write(f"- {k}: {v}\n")
            else:
                with open(report_path, "w") as f:
                    f.write("# Analysis Report\nNo results found.")
    
    append_reproducibility_to_markdown(report_path, metadata)
    
    if not verify_artifact_integrity():
        logger.error("Artifact integrity verification failed.")
    else:
        logger.info("Report generated and verified.")

if __name__ == "__main__":
    main()