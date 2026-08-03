"""
Report generation module for reproducibility and results summary.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pkg_resources

from code.logging_config import get_logger, log_operation

# Configure logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = get_logger("report")


def get_data_path() -> Path:
    """Return the project root path."""
    return Path(__file__).parent.parent


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_package_version(package_name: str) -> str:
    """Get version of a package."""
    try:
        return pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        return "unknown"


def collect_reproducibility_metadata() -> Dict[str, Any]:
    """Collect metadata for reproducibility."""
    metadata = {
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": sys.version,
        "packages": {
            "rdkit": get_package_version("rdkit"),
            "pandas": get_package_version("pandas"),
            "scikit-learn": get_package_version("scikit-learn"),
            "numpy": get_package_version("numpy"),
            "statsmodels": get_package_version("statsmodels"),
            "scipy": get_package_version("scipy"),
        },
        "code_version": "v1.0.0",  # Could be replaced with git hash
    }
    return metadata


def save_reproducibility_report(metadata: Dict[str, Any], artifacts: List[Dict[str, str]]) -> Path:
    """Save reproducibility report to JSON file."""
    report = {
        "metadata": metadata,
        "artifacts": artifacts,
    }

    output_path = get_data_path() / "reproducibility_log.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Reproducibility report saved to {output_path}")
    return output_path


def load_gate_status() -> Dict[str, Any]:
    """Load gate status from data/gate_status.json."""
    gate_path = get_data_path() / "data" / "gate_status.json"
    if not gate_path.exists():
        return {"status": "FAIL", "reason": "Gate status file not found"}
    with open(gate_path, "r") as f:
        return json.load(f)


def load_stat_gate_status() -> Dict[str, Any]:
    """Load statistical gate status from data/stat_gate_status.json."""
    stat_gate_path = get_data_path() / "data" / "stat_gate_status.json"
    if not stat_gate_path.exists():
        return {"status": "FAIL", "reason": "Stat gate status file not found"}
    with open(stat_gate_path, "r") as f:
        return json.load(f)


def verify_artifact_integrity(file_path: Path) -> bool:
    """Verify that a file exists and is non-empty."""
    if not file_path.exists():
        return False
    return file_path.stat().st_size > 0


def generate_results_report(
    results: Dict[str, Any],
    gate_status: Dict[str, Any],
    stat_gate_status: Dict[str, Any],
    metadata: Dict[str, Any],
    artifacts: List[Dict[str, str]],
) -> Path:
    """Generate a markdown results report."""
    report_path = get_data_path() / "results_report.md"

    with open(report_path, "w") as f:
        f.write("# Molecular Complexity and Degradation Rates Analysis Report\n\n")
        f.write(f"**Generated:** {metadata['timestamp']}\n\n")
        f.write("## Summary\n\n")

        if gate_status.get("status") != "PASS" or stat_gate_status.get("status") != "PASS":
            f.write("### Data Insufficiency\n\n")
            f.write(f"Data gate status: {gate_status.get('status', 'UNKNOWN')}\n")
            f.write(f"Statistical gate status: {stat_gate_status.get('status', 'UNKNOWN')}\n")
            f.write(f"Reason: {gate_status.get('reason', 'Unknown')}\n")
        else:
            f.write(f"### Analysis Results\n\n")
            f.write(f"- **N (sample size):** {results.get('N', 0)}\n")
            f.write(f"- **R² Score:** {results.get('R2', 'N/A')}\n")
            f.write(f"- **Methodology:** {results.get('methodology', 'N/A')}\n\n")

            if results.get('coefficients'):
                f.write("### Model Coefficients\n\n")
                f.write("| Feature | Coefficient |\n")
                f.write("|---------|-------------|\n")
                for feat, coef in results['coefficients'].items():
                    f.write(f"| {feat} | {coef:.6f} |\n")
                f.write("\n")

            if results.get('p_values'):
                f.write("### P-values\n\n")
                f.write("| Feature | P-value |\n")
                f.write("|---------|---------|\n")
                for feat, p_val in results['p_values'].items():
                    f.write(f"| {feat} | {p_val:.6f} |\n")
                f.write("\n")

            if results.get('diagnostics'):
                f.write("### Diagnostic Tests\n\n")
                diag = results['diagnostics']
                f.write(f"- **Shapiro-Wilk:** Stat={diag.get('shapiro_wilk', {}).get('stat', 'N/A'):.4f}, p={diag.get('shapiro_wilk', {}).get('p', 'N/A'):.4f}\n")
                f.write(f"- **Breusch-Pagan:** Stat={diag.get('breusch_pagan', {}).get('stat', 'N/A'):.4f}, p={diag.get('breusch_pagan', {}).get('p', 'N/A'):.4f}\n")

        f.write("\n## Reproducibility\n\n")
        f.write("### Package Versions\n\n")
        for pkg, ver in metadata['packages'].items():
            f.write(f"- {pkg}: {ver}\n")

        f.write("\n### Artifact Hashes\n\n")
        for artifact in artifacts:
            f.write(f"- `{artifact['path']}`: `{artifact['hash']}`\n")

    logger.info(f"Results report saved to {report_path}")
    return report_path


def generate_data_insufficiency_report(
    gate_status: Dict[str, Any],
    stat_gate_status: Dict[str, Any],
    metadata: Dict[str, Any],
) -> Path:
    """Generate a data insufficiency report."""
    report_path = get_data_path() / "data_insufficiency_report.md"

    with open(report_path, "w") as f:
        f.write("# Data Insufficiency Report\n\n")
        f.write(f"**Generated:** {metadata['timestamp']}\n\n")
        f.write("## Data Gate Status\n\n")
        f.write(f"- Status: {gate_status.get('status', 'UNKNOWN')}\n")
        f.write(f"- Reason: {gate_status.get('reason', 'Unknown')}\n")
        if 'N' in gate_status:
            f.write(f"- N (count): {gate_status['N']}\n")

        f.write("\n## Statistical Gate Status\n\n")
        f.write(f"- Status: {stat_gate_status.get('status', 'UNKNOWN')}\n")
        if 'N' in stat_gate_status:
            f.write(f"- N (count): {stat_gate_status['N']}\n")

        f.write("\n## Conclusion\n\n")
        f.write("The analysis could not be completed due to insufficient data. ")
        f.write("Please ensure that the data ingestion and standardization steps ")
        f.write("have successfully collected at least 30 samples with valid degradation data.\n")

    logger.info(f"Data insufficiency report saved to {report_path}")
    return report_path


@log_operation("main")
def main() -> int:
    """Main entry point for report generation."""
    logger.info("Starting report generation")

    try:
        # Load gate statuses
        gate_status = load_gate_status()
        stat_gate_status = load_stat_gate_status()

        # Collect metadata
        metadata = collect_reproducibility_metadata()

        # Define artifacts to hash
        artifacts_to_hash = [
            "data/raw/fda_structures.parquet",
            "data/processed/merged_drugs.csv",
            "data/processed/standard_subset.csv",
            "data/processed/full_dataset_with_covariates.csv",
            "data/processed/analysis_results.json",
            "data/processed/excluded_molecules.csv",
        ]

        artifacts = []
        for artifact_path in artifacts_to_hash:
            full_path = get_data_path() / artifact_path
            if full_path.exists():
                file_hash = calculate_file_hash(full_path)
                artifacts.append({"path": artifact_path, "hash": file_hash})
            else:
                logger.warning(f"Artifact not found: {artifact_path}")

        # Determine which report to generate
        if gate_status.get("status") != "PASS" or stat_gate_status.get("status") != "PASS":
            # Generate data insufficiency report
            generate_data_insufficiency_report(gate_status, stat_gate_status, metadata)

            # Verify the report was created
            report_path = get_data_path() / "data_insufficiency_report.md"
            if not verify_artifact_integrity(report_path):
                logger.error("Failed to create data insufficiency report")
                return 1
        else:
            # Load analysis results
            results_path = get_data_path() / "data" / "processed" / "analysis_results.json"
            if not results_path.exists():
                logger.error("Analysis results file not found")
                return 1

            with open(results_path, "r") as f:
                results = json.load(f)

            # Generate results report
            generate_results_report(results, gate_status, stat_gate_status, metadata, artifacts)

            # Verify the report was created
            report_path = get_data_path() / "results_report.md"
            if not verify_artifact_integrity(report_path):
                logger.error("Failed to create results report")
                return 1

        # Save reproducibility log
        save_reproducibility_report(metadata, artifacts)

        # Verify reproducibility log
        reproducibility_path = get_data_path() / "reproducibility_log.json"
        if not verify_artifact_integrity(reproducibility_path):
            logger.error("Failed to create reproducibility log")
            return 1

        logger.info("Report generation completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())