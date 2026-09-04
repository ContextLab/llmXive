"""
Report generation module for T034, T035, T035b, T035c, T083.
Generates results_report.md, data_insufficiency_report.md, and reproducibility_log.json.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logging
logger = logging.getLogger(__name__)

def get_data_path() -> Path:
    return PROJECT_ROOT / "data"

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    if not file_path.exists():
        return ""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_gate_status() -> Dict[str, Any]:
    gate_file = get_data_path() / "gate_status.json"
    if not gate_file.exists():
        return {"status": "FAIL", "reason": "File missing"}
    with open(gate_file, 'r') as f:
        return json.load(f)

def load_stat_gate_status() -> Dict[str, Any]:
    stat_gate_file = get_data_path() / "stat_gate_status.json"
    if not stat_gate_file.exists():
        return {"status": "FAIL", "reason": "File missing"}
    with open(stat_gate_file, 'r') as f:
        return json.load(f)

def verify_artifact_integrity() -> bool:
    """Verify that required artifacts exist and are non-empty."""
    gate_status = load_gate_status()
    if gate_status.get("status") == "PASS":
        analysis_file = get_data_path() / "processed" / "analysis_results.json"
        if not analysis_file.exists() or analysis_file.stat().st_size == 0:
            logger.error("Analysis results file is missing or empty.")
            return False
        # Check content
        with open(analysis_file, 'r') as f:
            data = json.load(f)
            if data.get("N", 0) == 0 or data.get("R2") is None:
                logger.error("Analysis results contain null/zero metrics.")
                return False
    else:
        report_file = get_data_path() / "data_insufficiency_report.md"
        if not report_file.exists() or report_file.stat().st_size == 0:
            logger.error("Insufficiency report file is missing or empty.")
            return False
    return True

def collect_reproducibility_metadata() -> Dict[str, Any]:
    """Collect version info and environment metadata."""
    # Fix: Use 'dict' instead of 'Dict' for runtime type hint if Python < 3.9
    # But for type hints in comments/annotations, Dict is fine if imported.
    # The error was: NameError: name 'Dict' is not defined.
    # We need to import it or use 'dict'.
    import sys
    if sys.version_info >= (3, 9):
        from collections.abc import Mapping
    else:
        from typing import Dict as DictType, Mapping as MappingType

    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "timestamp": datetime.utcnow().isoformat(),
        "packages": {
            "rdkit": "2023.9.5", # Pinned version
            "pandas": "2.0.3",
            "scikit-learn": "1.3.0"
        }
    }

def generate_reproducibility_log() -> None:
    """Generate reproducibility_log.json with lineage tracking."""
    log = {
        "artifacts": [],
        "metadata": collect_reproducibility_metadata()
    }

    # List of files to track
    files_to_track = [
        ("data/raw/fda_structures.parquet", "raw", "Initial download"),
        ("data/processed/merged_drugs.csv", "processed", "Ingestion & Merge"),
        ("data/processed/standard_subset.csv", "processed", "Standardization"),
        ("data/processed/analysis_results.json", "processed", "Analysis"),
        ("data/processed/excluded_molecules.csv", "processed", "Descriptor Calculation"),
    ]

    for rel_path, lineage_type, transformation in files_to_track:
        full_path = PROJECT_ROOT / rel_path
        if full_path.exists():
            file_hash = calculate_file_hash(full_path)
            log["artifacts"].append({
                "path": rel_path,
                "hash": file_hash,
                "lineage": {
                    "source_path": "fda_structures.parquet" if lineage_type == "processed" and "merged" in rel_path else "unknown",
                    "transformation": transformation
                }
            })

    log_file = PROJECT_ROOT / "reproducibility_log.json"
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=2)
    logger.info(f"Reproducibility log saved to {log_file}")

def generate_results_report() -> None:
    """Generate results_report.md."""
    analysis_file = get_data_path() / "processed" / "analysis_results.json"
    if not analysis_file.exists():
        logger.error("Analysis results file not found.")
        return

    with open(analysis_file, 'r') as f:
        results = json.load(f)

    report_path = PROJECT_ROOT / "results_report.md"
    with open(report_path, 'w') as f:
        f.write("# Molecular Complexity vs Degradation Rates Analysis\n\n")
        f.write("## Methodology\n\n")
        f.write("This study analyzes the correlation between molecular complexity metrics (TPSA, MW, etc.) and degradation half-lives.\n")
        f.write("Data was sourced from FDA-approved drug structures and degradation databases.\n\n")
        f.write("## Results\n\n")
        f.write(f"- **N (Standard Conditions)**: {results.get('N', 0)}\n")
        f.write(f"- **R² Score**: {results.get('R2', 'N/A')}\n")
        f.write(f"- **Methodology**: {results.get('methodology', 'N/A')}\n\n")
        
        if results.get('coefficients'):
            f.write("### Coefficients\n\n")
            for feat, coef in results['coefficients'].items():
                f.write(f"- {feat}: {coef:.4f}\n")
            f.write("\n")

        f.write("## Reproducibility\n\n")
        f.write(f"- **Dataset Hash**: {calculate_file_hash(PROJECT_ROOT / 'data' / 'processed' / 'merged_drugs.csv')}\n")
        f.write(f"- **Code Version**: 1.0.0\n")
        f.write(f"- **Timestamp**: {results.get('timestamp', 'N/A')}\n")

    logger.info(f"Results report saved to {report_path}")

def generate_data_insufficiency_report() -> None:
    """Generate data_insufficiency_report.md."""
    report_path = get_data_path() / "data_insufficiency_report.md"
    with open(report_path, 'w') as f:
        f.write("# Data Insufficiency Report\n\n")
        f.write("## Reason\n\n")
        f.write("The pipeline halted due to insufficient data availability or quality.\n")
        f.write("Please check the gate status logs for details.\n")
    logger.info(f"Insufficiency report saved to {report_path}")

def main():
    """Main entry point for report generation."""
    logger.info("Starting Report Generation...")
    
    gate_status = load_gate_status()
    
    if gate_status.get("status") == "PASS":
        if not verify_artifact_integrity():
            logger.error("Artifact integrity check failed. Cannot generate report.")
            return
        generate_results_report()
    else:
        generate_data_insufficiency_report()

    generate_reproducibility_log()
    logger.info("Report generation complete.")

if __name__ == '__main__':
    main()
