"""
Report Generation Module for PROJ-071.
Generates results_report.md or data_insufficiency_report.md based on gate status.
Implements reproducibility checks and artifact integrity verification.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import shared utilities from logging_config
from logging_config import get_logger, log_operation

# Import analysis results loader
from analysis import load_gate_status, load_stat_gate_status, save_analysis_results

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = DATA_DIR / "outputs"
GATE_STATUS_FILE = DATA_DIR / "gate_status.json"
STAT_GATE_STATUS_FILE = DATA_DIR / "stat_gate_status.json"
ANALYSIS_RESULTS_FILE = PROCESSED_DIR / "analysis_results.json"
RESULTS_REPORT_FILE = PROJECT_ROOT / "results_report.md"
INSUFFICIENCY_REPORT_FILE = PROJECT_ROOT / "data_insufficiency_report.md"
REPRODUCIBILITY_LOG_FILE = PROJECT_ROOT / "reproducibility_log.json"

# Ensure directories exist
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger("report_generation")


class ReportGenerationError(Exception):
    """Raised when report generation fails due to missing data or validation errors."""
    pass


def get_data_path() -> Path:
    """Return the project root data path."""
    return DATA_DIR


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    if not file_path.exists():
        return "FILE_NOT_FOUND"
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.log("hash_error", error=str(e))
        return f"ERROR:{str(e)}"


def load_gate_status() -> Dict[str, Any]:
    """Load gate status from JSON file."""
    if not GATE_STATUS_FILE.exists():
        return {"status": "UNKNOWN", "reason": "File not found"}
    with open(GATE_STATUS_FILE, "r") as f:
        return json.load(f)


def load_stat_gate_status() -> Dict[str, Any]:
    """Load statistical gate status from JSON file."""
    if not STAT_GATE_STATUS_FILE.exists():
        return {"status": "UNKNOWN", "reason": "File not found"}
    with open(STAT_GATE_STATUS_FILE, "r") as f:
        return json.load(f)


def verify_artifact_integrity() -> bool:
    """
    Verify that critical artifacts exist and are non-empty.
    Returns True if all checks pass, False otherwise.
    """
    checks = [
        (GATE_STATUS_FILE, "Gate status file"),
        (ANALYSIS_RESULTS_FILE if load_gate_status().get("status") == "PASS" else None, "Analysis results"),
        (PROCESSED_DIR / "standard_subset.csv", "Standard subset data"),
    ]

    for path, desc in checks:
        if path is None:
            continue
        if not path.exists():
            logger.log("integrity_fail", artifact=desc, reason="File missing")
            return False
        if path.stat().st_size == 0:
            logger.log("integrity_fail", artifact=desc, reason="File empty")
            return False

    return True


def collect_reproducibility_metadata() -> Dict[str, Any]:
    """
    Collect reproducibility metadata: versions, hashes, URLs, dates.
    """
    metadata = {
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "packages": {},
        "dataset_info": {},
        "file_hashes": {}
    }

    # Collect package versions
    packages_to_check = ["rdkit", "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn", "statsmodels", "scipy"]
    for pkg in packages_to_check:
        try:
            mod = __import__(pkg)
            version = getattr(mod, "__version__", "unknown")
            metadata["packages"][pkg] = version
        except ImportError:
            metadata["packages"][pkg] = "not_installed"
        except Exception as e:
            metadata["packages"][pkg] = f"error:{str(e)}"

    # Collect file hashes
    critical_files = [
        DATA_DIR / "config.yaml",
        GATE_STATUS_FILE,
        STAT_GATE_STATUS_FILE,
        PROCESSED_DIR / "merged_drugs.csv",
        PROCESSED_DIR / "standard_subset.csv",
        ANALYSIS_RESULTS_FILE,
        PROCESSED_DIR / "excluded_molecules.csv",
    ]

    for file_path in critical_files:
        if file_path.exists():
          rel_path = str(file_path.relative_to(PROJECT_ROOT))
          metadata["file_hashes"][rel_path] = calculate_file_hash(file_path)
        else:
          rel_path = str(file_path.relative_to(PROJECT_ROOT))
          metadata["file_hashes"][rel_path] = "MISSING"

    # Dataset info from config if available
    config_file = DATA_DIR / "config.yaml"
    if config_file.exists():
        try:
            import yaml
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
            metadata["dataset_info"] = {
                "dataset_id": config.get("dataset_id", "unknown"),
                "dataset_version": config.get("dataset_version", "unknown"),
                "temp_range": [config.get("temp_min"), config.get("temp_max")],
                "ph_range": [config.get("ph_min"), config.get("ph_max")]
            }
        except Exception as e:
            metadata["dataset_info"]["error"] = str(e)

    return metadata


def generate_reproducibility_log(metadata: Dict[str, Any]) -> None:
    """Save reproducibility metadata to JSON file."""
    log_entry = {
        "generated_at": metadata["timestamp"],
        "environment": {
            "python": metadata["python_version"],
            "platform": metadata["platform"],
            "packages": metadata["packages"]
        },
        "dataset_info": metadata["dataset_info"],
        "file_hashes": metadata["file_hashes"],
        "lineage": {
            "analysis_results": {
                "source": "standard_subset.csv",
                "transformation": "MLR+LASSO regression",
                "hash": metadata["file_hashes"].get("data/processed/analysis_results.json", "MISSING")
            },
            "standard_subset": {
                "source": "merged_drugs.csv",
                "transformation": "Standard condition filtering",
                "hash": metadata["file_hashes"].get("data/processed/standard_subset.csv", "MISSING")
            },
            "merged_drugs": {
                "source": "fda_structures.parquet + degradation_data",
                "transformation": "Ingestion and merging",
                "hash": metadata["file_hashes"].get("data/processed/merged_drugs.csv", "MISSING")
            },
            "excluded_molecules": {
                "source": "merged_drugs.csv",
                "transformation": "Descriptor calculation error logging",
                "hash": metadata["file_hashes"].get("data/processed/excluded_molecules.csv", "MISSING")
            }
        }
    }

    with open(REPRODUCIBILITY_LOG_FILE, "w") as f:
        json.dump(log_entry, f, indent=2, default=str)


def generate_results_report(metadata: Dict[str, Any]) -> None:
    """Generate the main results report in Markdown format."""
    if not verify_artifact_integrity():
        raise ReportGenerationError("Artifact integrity check failed")

    # Load analysis results
    if not ANALYSIS_RESULTS_FILE.exists():
        raise ReportGenerationError("Analysis results file not found")

    with open(ANALYSIS_RESULTS_FILE, "r") as f:
        results = json.load(f)

    # Build report content
    report_lines = [
        "# Molecular Complexity and Degradation Rates Analysis Report",
        "",
        f"**Generated**: {datetime.utcnow().isoformat()}",
        "",
        "## 1. Methodology",
        "",
        "This study explores the correlation between molecular complexity metrics and degradation rates in FDA-approved pharmaceuticals.",
        "Molecular descriptors (TPSA, Rotatable Bonds, MW, Aromatic Rings, Wiener Index, Zagreb Index) were calculated using RDKit.",
        "Degradation data was filtered for standard conditions (Temp: 20-30°C, pH: 7.35-7.45).",
        "Multiple Linear Regression (MLR) and LASSO regression with K-fold cross-validation were performed.",
        "",
        "## 2. Data Summary",
        "",
        f"- **Dataset ID**: {metadata['dataset_info'].get('dataset_id', 'N/A')}",
        f"- **Dataset Version**: {metadata['dataset_info'].get('dataset_version', 'N/A')}",
        f"- **Standard Condition Range**: Temp {metadata['dataset_info'].get('temp_range', [None, None])}, pH {metadata['dataset_info'].get('ph_range', [None, None])}",
        "",
        "## 3. Results",
        "",
        f"- **Status**: {results.get('status', 'UNKNOWN')}",
        f"- **Sample Size (N)**: {results.get('N', 0)}",
        f"- **R² Score**: {results.get('R2', 'N/A')}",
        "",
        "### 3.1 Model Coefficients",
        "",
    ]

    coeffs = results.get("coefficients", {})
    if coeffs:
        report_lines.append("| Feature | Coefficient |")
        report_lines.append("|---------|-------------|")
        for feature, coef in coeffs.items():
            report_lines.append(f"| {feature} | {coef:.6f} |")
    else:
        report_lines.append("No coefficients available (model may have been skipped).")

    report_lines.extend([
        "",
        "### 3.2 P-Values",
        "",
    ])

    p_values = results.get("p_values", {})
    if p_values:
        report_lines.append("| Feature | P-Value |")
        report_lines.append("|---------|---------|")
        for feature, p in p_values.items():
            report_lines.append(f"| {feature} | {p:.6f} |")
    else:
        report_lines.append("No p-values available.")

    report_lines.extend([
        "",
        "### 3.3 Diagnostic Tests",
        "",
    ])

    diagnostics = results.get("diagnostics", {})
    if diagnostics:
        shapiro = diagnostics.get("shapiro_wilk", {})
        bp = diagnostics.get("breusch_pagan", {})
        report_lines.append(f"- **Shapiro-Wilk (Normality)**: Stat={shapiro.get('stat', 'N/A')}, p={shapiro.get('p', 'N/A')}")
        report_lines.append(f"- **Breusch-Pagan (Homoscedasticity)**: Stat={bp.get('stat', 'N/A')}, p={bp.get('p', 'N/A')}")
    else:
        report_lines.append("Diagnostics not performed.")

    report_lines.extend([
        "",
        "## 4. Reproducibility",
        "",
        "### 4.1 Environment",
        "",
        f"- **Python Version**: {metadata['python_version']}",
        f"- **Platform**: {metadata['platform']}",
        "",
        "### 4.2 Package Versions",
        "",
        "| Package | Version |",
        "|---------|---------|",
    ])

    for pkg, ver in metadata["packages"].items():
        report_lines.append(f"| {pkg} | {ver} |")

    report_lines.extend([
        "",
        "### 4.3 File Hashes (SHA256)",
        "",
        "| File | Hash |",
        "|------|------|",
    ])

    for file_path, file_hash in metadata["file_hashes"].items():
        report_lines.append(f"| {file_path} | {file_hash} |")

    report_lines.extend([
        "",
        "## 5. Conclusion",
        "",
        "The analysis provides quantitative evidence regarding the relationship between molecular complexity and degradation rates.",
        "Results should be interpreted in the context of the sample size and the specific standard conditions applied.",
        "",
        "---",
        f"*Report generated by llmXive pipeline (Task T035)*"
    ])

    report_content = "\n".join(report_lines)

    with open(RESULTS_REPORT_FILE, "w") as f:
        f.write(report_content)

    logger.log("report_generated", path=str(RESULTS_REPORT_FILE), status="SUCCESS")


def generate_data_insufficiency_report() -> None:
    """Generate a report when data gates fail."""
    gate_status = load_gate_status()
    stat_gate_status = load_stat_gate_status()

    report_lines = [
        "# Data Insufficiency Report",
        "",
        f"**Generated**: {datetime.utcnow().isoformat()}",
        "",
        "## Data Availability Status",
        "",
        f"- **Primary Gate Status**: {gate_status.get('status', 'UNKNOWN')}",
    ]

    if "reason" in gate_status:
        report_lines.append(f"- **Reason**: {gate_status['reason']}")
    if "N" in gate_status:
        report_lines.append(f"- **Available Records (N)**: {gate_status['N']}")

    report_lines.extend([
        "",
        "## Statistical Gate Status",
        "",
        f"- **Secondary Gate Status**: {stat_gate_status.get('status', 'UNKNOWN')}",
    ])

    if "reason" in stat_gate_status:
        report_lines.append(f"- **Reason**: {stat_gate_status['reason']}")
    if "N_std" in stat_gate_status:
        report_lines.append(f"- **Standard Condition Records (N_std)**: {stat_gate_status['N_std']}")

    report_lines.extend([
        "",
        "## Conclusion",
        "",
        "The dataset did not meet the minimum requirements for statistical analysis.",
        "No further analysis or modeling was performed.",
        "",
        "## Recommendations",
        "",
        "1. Verify the data source configuration in `data/config.yaml`.",
        "2. Check if the degradation data columns are correctly named.",
        "3. Consider expanding the dataset or relaxing condition filters if scientifically justified.",
        "",
        "---",
        f"*Report generated by llmXive pipeline (Task T035)*"
    ])

    report_content = "\n".join(report_lines)

    with open(INSUFFICIENCY_REPORT_FILE, "w") as f:
        f.write(report_content)

    logger.log("insufficiency_report_generated", path=str(INSUFFICIENCY_REPORT_FILE), status="SUCCESS")


def main():
    """Main entry point for report generation."""
    try:
        # Collect metadata first
        logger.log("collecting_metadata")
        metadata = collect_reproducibility_metadata()

        # Save reproducibility log
        logger.log("saving_reproducibility_log")
        generate_reproducibility_log(metadata)

        # Determine which report to generate
        gate_status = load_gate_status()

        if gate_status.get("status") == "PASS":
            logger.log("generating_results_report")
            generate_results_report(metadata)
        else:
            logger.log("generating_insufficiency_report")
            generate_data_insufficiency_report()

        logger.log("report_generation_complete", status="SUCCESS")
        return 0

    except Exception as e:
        logger.log("report_generation_failed", error=str(e))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())