"""
Report generation module for reproducibility and results.
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

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.logging_config import get_logger, log_operation

logger = get_logger("report")

# Configuration
GATE_STATUS_PATH = PROJECT_ROOT / "data" / "gate_status.json"
STAT_GATE_STATUS_PATH = PROJECT_ROOT / "data" / "stat_gate_status.json"
ANALYSIS_RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "analysis_results.json"
MERGED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "merged_drugs.csv"
REPRODUCIBILITY_LOG_PATH = PROJECT_ROOT / "data" / "reproducibility_log.json"
RESULTS_REPORT_PATH = PROJECT_ROOT / "results_report.md"
INSUFFICIENCY_REPORT_PATH = PROJECT_ROOT / "data" / "data_insufficiency_report.md"

def get_data_path() -> Path:
    """Return the path to the analysis results."""
    return ANALYSIS_RESULTS_PATH

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    if not file_path.exists():
        return "FILE_NOT_FOUND"
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_package_version(package_name: str) -> str:
    """Get version of a package."""
    try:
        return pkg_resources.get_distribution(package_name).version
    except Exception:
        return "unknown"

def load_gate_status() -> Dict[str, Any]:
    """Load the main gate status."""
    if not GATE_STATUS_PATH.exists():
        return {"status": "FAIL", "reason": "Gate status file missing"}
    with open(GATE_STATUS_PATH, "r") as f:
        return json.load(f)

def load_stat_gate_status() -> Dict[str, Any]:
    """Load the statistical gate status."""
    if not STAT_GATE_STATUS_PATH.exists():
        return {"status": "FAIL", "reason": "Stat gate status file missing"}
    with open(STAT_GATE_STATUS_PATH, "r") as f:
        return json.load(f)

def collect_reproducibility_metadata() -> Dict[str, Any]:
    """Collect metadata for reproducibility log."""
    metadata = {
        "code_version": get_package_version("llmXive-project") if "llmXive-project" in [d.project_name for d in pkg_resources.working_set] else "local",
        "rdkit_version": get_package_version("rdkit"),
        "scikit_learn_version": get_package_version("scikit-learn"),
        "pandas_version": get_package_version("pandas"),
        "scipy_version": get_package_version("scipy"),
        "timestamp": datetime.utcnow().isoformat(),
        "artifacts": []
    }

    # Add file hashes
    files_to_hash = [
        (MERGED_DATA_PATH, "merged_drugs.csv", "raw_fda_structures.parquet", "ingestion"),
        (ANALYSIS_RESULTS_PATH, "analysis_results.json", MERGED_DATA_PATH, "analysis"),
        (GATE_STATUS_PATH, "gate_status.json", None, "gate_check"),
        (STAT_GATE_STATUS_PATH, "stat_gate_status.json", GATE_STATUS_PATH, "stat_gate_check")
    ]

    for path, name, source, transformation in files_to_hash:
        if path.exists():
          artifact = {
              "path": str(path.relative_to(PROJECT_ROOT)),
              "hash": calculate_file_hash(path),
              "lineage": {
                  "source_path": str(source.relative_to(PROJECT_ROOT)) if source and source.exists() else None,
                  "transformation": transformation
              }
          }
          metadata["artifacts"].append(artifact)

    return metadata

def save_reproducibility_report(metadata: Dict[str, Any]) -> None:
    """Save reproducibility log to JSON."""
    with open(REPRODUCIBILITY_LOG_PATH, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    logger.log("Reproducibility report saved", {"path": str(REPRODUCIBILITY_LOG_PATH)})

def verify_artifact_integrity() -> bool:
    """Verify that all required artifacts exist and are non-empty."""
    required_files = [
        ANALYSIS_RESULTS_PATH,
        REPRODUCIBILITY_LOG_PATH
    ]

    for file_path in required_files:
        if not file_path.exists():
            logger.log("Artifact missing", {"path": str(file_path)})
            return False
        if file_path.stat().st_size == 0:
            logger.log("Artifact empty", {"path": str(file_path)})
            return False

    return True

def generate_results_report(analysis_results: Dict[str, Any]) -> None:
    """Generate the results report in Markdown."""
    report_lines = [
        "# Molecular Complexity and Degradation Rates Analysis Report",
        "",
        "## Summary",
        f"- **Status**: {analysis_results.get('status', 'UNKNOWN')}",
        f"- **Sample Size (N)**: {analysis_results.get('N', 0)}",
        f"- **R² Score**: {analysis_results.get('R2', 'N/A')}",
        f"- **Methodology**: {analysis_results.get('methodology', 'N/A')}",
        "",
        "## Regression Coefficients (LASSO)",
        ""
    ]

    coeffs = analysis_results.get("coefficients", {})
    if coeffs:
        for feat, coef in coeffs.items():
            report_lines.append(f"- **{feat}**: {coef:.6f}")
    else:
        report_lines.append("No coefficients available.")

    report_lines.extend([
        "",
        "## Statistical Diagnostics",
        ""
    ])

    diagnostics = analysis_results.get("diagnostics", {})
    if diagnostics:
        sw = diagnostics.get("shapiro_wilk", {})
        bp = diagnostics.get("breusch_pagan", {})
        report_lines.append(f"- **Shapiro-Wilk Test**: Stat={sw.get('stat', 'N/A')}, p={sw.get('p', 'N/A')}")
        report_lines.append(f"- **Breusch-Pagan Test**: Stat={bp.get('stat', 'N/A')}, p={bp.get('p', 'N/A')}")
    else:
        report_lines.append("Diagnostics not available.")

    report_lines.extend([
        "",
        "## Reproducibility",
        "",
        f"- **Report Generated**: {datetime.utcnow().isoformat()}",
        "",
        "See `reproducibility_log.json` for full artifact hashes and lineage."
    ])

    with open(RESULTS_REPORT_PATH, "w") as f:
        f.write("\n".join(report_lines))

    logger.log("Results report generated", {"path": str(RESULTS_REPORT_PATH)})

def generate_data_insufficiency_report(gate_status: Dict[str, Any], stat_gate_status: Dict[str, Any]) -> None:
    """Generate the data insufficiency report."""
    report_lines = [
        "# Data Insufficiency Report",
        "",
        "## Data Availability Gate",
        f"- **Status**: {gate_status.get('status', 'UNKNOWN')}",
        f"- **Reason**: {gate_status.get('reason', 'N/A')}",
        f"- **N**: {gate_status.get('N', 0)}",
        "",
        "## Statistical Gate",
        f"- **Status**: {stat_gate_status.get('status', 'UNKNOWN')}",
        f"- **Reason**: {stat_gate_status.get('reason', 'N/A')}",
        f"- **N**: {stat_gate_status.get('N', 0)}",
        "",
        "## Conclusion",
        "",
        "The pipeline was halted due to insufficient data. The required minimum sample size (N >= 30) for the standard condition subset was not met, or no valid degradation data was found.",
        "",
        "Please verify data sources and retry."
    ]

    with open(INSUFFICIENCY_REPORT_PATH, "w") as f:
        f.write("\n".join(report_lines))

    logger.log("Data insufficiency report generated", {"path": str(INSUFFICIENCY_REPORT_PATH)})

@log_operation("Generate_Report")
def main() -> None:
    """Main entry point for report generation."""
    logger.log("Report generation started")

    gate_status = load_gate_status()
    stat_gate_status = load_stat_gate_status()

    # Check for gate failures
    if gate_status.get("status") == "FAIL" or stat_gate_status.get("status") == "FAIL":
        logger.log("Gate failed, generating insufficiency report")
        generate_data_insufficiency_report(gate_status, stat_gate_status)
        logger.log("Report generation completed (insufficiency)")
        return

    # Load analysis results
    if not ANALYSIS_RESULTS_PATH.exists():
        logger.log("Analysis results not found")
        # Generate a minimal report indicating no analysis was run
        report_lines = [
            "# Report Generation Failed",
            "",
            "Analysis results not found. Please run the analysis pipeline first."
        ]
        with open(RESULTS_REPORT_PATH, "w") as f:
            f.write("\n".join(report_lines))
        return

    with open(ANALYSIS_RESULTS_PATH, "r") as f:
        analysis_results = json.load(f)

    if analysis_results.get("status") == "SKIPPED":
        logger.log("Analysis skipped, generating insufficiency report")
        generate_data_insufficiency_report(gate_status, stat_gate_status)
        return

    # Generate results report
    generate_results_report(analysis_results)

    # Collect and save reproducibility metadata
    metadata = collect_reproducibility_metadata()
    save_reproducibility_report(metadata)

    # Verify artifacts
    if not verify_artifact_integrity():
        logger.log("Artifact verification failed")
        # Note: We don't raise here, as the report was generated
    else:
        logger.log("Artifact verification passed")

    logger.log("Report generation completed successfully")

if __name__ == "__main__":
    main()
