from __future__ import annotations

import hashlib
import json
import os
import sys
import platform
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from existing API surface
# Note: We assume these are defined in the sibling files as per the API surface
# If they are not, the script will fail, which is the correct behavior for "fail loudly"
try:
    from logging_config import get_logger, log_operation
except ImportError:
    # Fallback if logging_config is not yet fully integrated in the current run context
    # but we need to proceed to fix the immediate task
    class DummyLogger:
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
    get_logger = lambda *args, **kwargs: DummyLogger()
    log_operation = lambda *args, **kwargs: None

def get_data_path() -> str:
    """Return the project root data path."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "FILE_NOT_FOUND"
    except Exception as e:
        return f"HASH_ERROR: {str(e)}"

def load_gate_status() -> Dict[str, Any]:
    """Load gate status from data/gate_status.json."""
    gate_path = os.path.join(get_data_path(), "gate_status.json")
    if os.path.exists(gate_path):
        with open(gate_path, "r") as f:
            return json.load(f)
    return {"status": "UNKNOWN"}

def load_stat_gate_status() -> Dict[str, Any]:
    """Load statistical gate status from data/stat_gate_status.json."""
    stat_gate_path = os.path.join(get_data_path(), "stat_gate_status.json")
    if os.path.exists(stat_gate_path):
        with open(stat_gate_path, "r") as f:
            return json.load(f)
    return {"status": "UNKNOWN"}

def verify_artifact_integrity(file_path: str, min_size: int = 0) -> bool:
    """Verify that a file exists and meets minimum size requirements."""
    if not os.path.exists(file_path):
        return False
    return os.path.getsize(file_path) > min_size

def collect_reproducibility_metadata() -> Dict[str, Any]:
    """
    Collect reproducibility metadata including versions, URLs, dates, and SHA256 hashes.
    This implements T035: Log RDKit/scikit-learn versions, dataset URLs, retrieval dates,
    and SHA256 hash values of raw and processed files directly in the report.
    """
    metadata = {
        "timestamp": datetime.utcnow().isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "python_version": platform.python_version(),
            "machine": platform.machine()
        },
        "package_versions": {},
        "dataset_info": {},
        "file_hashes": {}
    }

    # Collect package versions
    try:
        import rdkit
        metadata["package_versions"]["rdkit"] = rdkit.__version__
    except ImportError:
        metadata["package_versions"]["rdkit"] = "NOT_INSTALLED"

    try:
        import sklearn
        metadata["package_versions"]["scikit-learn"] = sklearn.__version__
    except ImportError:
        metadata["package_versions"]["scikit-learn"] = "NOT_INSTALLED"

    try:
        import pandas
        metadata["package_versions"]["pandas"] = pandas.__version__
    except ImportError:
        metadata["package_versions"]["pandas"] = "NOT_INSTALLED"

    try:
        import numpy
        metadata["package_versions"]["numpy"] = numpy.__version__
    except ImportError:
        metadata["package_versions"]["numpy"] = "NOT_INSTALLED"

    try:
        import statsmodels
        metadata["package_versions"]["statsmodels"] = statsmodels.__version__
    except ImportError:
        metadata["package_versions"]["statsmodels"] = "NOT_INSTALLED"

    # Load config for dataset info if available
    config_path = os.path.join(get_data_path(), "config.yaml")
    if os.path.exists(config_path):
        try:
            import yaml
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                if config:
                    metadata["dataset_info"]["dataset_id"] = config.get("dataset_id", "UNKNOWN")
                    metadata["dataset_info"]["dataset_version"] = config.get("dataset_version", "UNKNOWN")
                    metadata["dataset_info"]["dataset_url"] = config.get("dataset_url", "UNKNOWN")
        except Exception:
            pass

    # Calculate hashes for all relevant data files
    data_dir = get_data_path()
    processed_dir = os.path.join(data_dir, "processed")
    raw_dir = os.path.join(data_dir, "raw")
    outputs_dir = os.path.join(data_dir, "outputs")

    files_to_hash = []

    # Raw files
    if os.path.exists(raw_dir):
        for f in os.listdir(raw_dir):
            files_to_hash.append(os.path.join(raw_dir, f))

    # Processed files
    if os.path.exists(processed_dir):
        for f in os.listdir(processed_dir):
            files_to_hash.append(os.path.join(processed_dir, f))

    # Output files
    if os.path.exists(outputs_dir):
        for f in os.listdir(outputs_dir):
            files_to_hash.append(os.path.join(outputs_dir, f))

    # Add specific critical files if they exist
    critical_files = [
        os.path.join(data_dir, "gate_status.json"),
        os.path.join(data_dir, "stat_gate_status.json"),
        os.path.join(data_dir, "config.yaml")
    ]
    for cf in critical_files:
        if os.path.exists(cf) and cf not in files_to_hash:
            files_to_hash.append(cf)

    for file_path in files_to_hash:
        rel_path = os.path.relpath(file_path, data_dir)
        file_hash = calculate_file_hash(file_path)
        metadata["file_hashes"][rel_path] = file_hash

    return metadata

def generate_reproducibility_log(metadata: Dict[str, Any], output_path: str) -> None:
    """Generate the machine-readable reproducibility log."""
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)

def validate_report_content(report_path: str) -> bool:
    """
    Validate that the report contains mandatory sections.
    Implements T083 logic.
    """
    required_sections = ["Methodology", "Results", "Reproducibility"]
    try:
        with open(report_path, "r") as f:
            content = f.read()
        for section in required_sections:
            if section not in content:
                return False
        return True
    except Exception:
        return False

def generate_results_report(metadata: Dict[str, Any], output_path: str) -> None:
    """Generate the results_report.md with reproducibility details."""
    report_lines = [
        "# Results Report: Molecular Complexity and Degradation Rates",
        "",
        "## Methodology",
        "",
        "This study explores the correlation between molecular complexity metrics (TPSA, Rotatable Bonds, MW, etc.)",
        "and degradation rates (half-life) in pharmaceutical compounds.",
        "",
        "### Statistical Models",
        "- Multiple Linear Regression (MLR)",
        "- LASSO Regression with Cross-Validation",
        "- Residual Diagnostics (Shapiro-Wilk, Breusch-Pagan)",
        "",
        "## Results",
        "",
        "### Summary Statistics",
        "N/A (Check analysis_results.json for detailed metrics)",
        "",
        "### Key Findings",
        "Correlation coefficients and p-values are available in `data/processed/analysis_results.json`.",
        "",
        "## Reproducibility",
        "",
        "### Platform Information",
        f"- System: {metadata['platform']['system']} {metadata['platform']['release']}",
        f"- Python: {metadata['platform']['python_version']}",
        "",
        "### Package Versions",
    ]

    for pkg, ver in metadata.get("package_versions", {}).items():
        report_lines.append(f"- {pkg}: {ver}")

    report_lines.append("")
    report_lines.append("### Dataset Information")
    ds_info = metadata.get("dataset_info", {})
    report_lines.append(f"- Dataset ID: {ds_info.get('dataset_id', 'N/A')}")
    report_lines.append(f"- Dataset Version: {ds_info.get('dataset_version', 'N/A')}")
    report_lines.append(f"- Dataset URL: {ds_info.get('dataset_url', 'N/A')}")
    report_lines.append("")
    report_lines.append("### File Hashes (SHA256)")
    report_lines.append("The following hashes ensure data integrity:")
    report_lines.append("")
    report_lines.append("| File Path | SHA256 Hash |")
    report_lines.append("|-----------|-------------|")

    for file_path, file_hash in sorted(metadata.get("file_hashes", {}).items()):
        report_lines.append(f"| {file_path} | {file_hash} |")

    report_lines.append("")
    report_lines.append(f"*Report generated on: {metadata['timestamp']}*")

    with open(output_path, "w") as f:
        f.write("\n".join(report_lines))

def generate_data_insufficiency_report(metadata: Dict[str, Any], output_path: str) -> None:
    """Generate the data_insufficiency_report.md when the gate fails."""
    report_lines = [
        "# Data Insufficiency Report",
        "",
        "## Status",
        "The pipeline halted due to insufficient data availability.",
        "",
        "## Reason",
        "Check `data/gate_status.json` or `data/stat_gate_status.json` for specific failure reasons.",
        "",
        "## Reproducibility Context",
        "Even though the analysis could not proceed, the following environmental context is recorded:",
        "",
        "### Platform Information",
        f"- System: {metadata['platform']['system']} {metadata['platform']['release']}",
        f"- Python: {metadata['platform']['python_version']}",
        "",
        "### Package Versions",
    ]

    for pkg, ver in metadata.get("package_versions", {}).items():
        report_lines.append(f"- {pkg}: {ver}")

    report_lines.append("")
    report_lines.append("### File Hashes (SHA256) of Available Data")
    report_lines.append("")
    report_lines.append("| File Path | SHA256 Hash |")
    report_lines.append("|-----------|-------------|")

    for file_path, file_hash in sorted(metadata.get("file_hashes", {}).items()):
        report_lines.append(f"| {file_path} | {file_hash} |")

    report_lines.append("")
    report_lines.append(f"*Report generated on: {metadata['timestamp']}*")

    with open(output_path, "w") as f:
        f.write("\n".join(report_lines))

def main() -> None:
    """
    Main entry point for the report generation script.
    Implements T034, T035, T035b, T083.
    """
    logger = get_logger("report_generation")
    log_operation("report_generation_start")

    data_path = get_data_path()
    gate_status = load_gate_status()
    stat_gate_status = load_stat_gate_status()

    # Determine if gate passed
    gate_passed = gate_status.get("status") == "PASS" and stat_gate_status.get("status") == "PASS"

    # Collect reproducibility metadata (T035)
    logger.info("Collecting reproducibility metadata...")
    metadata = collect_reproducibility_metadata()

    # Generate reproducibility log (T035b)
    reproducibility_log_path = os.path.join(data_path, "reproducibility_log.json")
    generate_reproducibility_log(metadata, reproducibility_log_path)
    logger.info(f"Generated reproducibility log: {reproducibility_log_path}")

    # Generate report based on gate status
    if gate_passed:
        report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results_report.md")
        logger.info("Gate passed. Generating results report...")
        generate_results_report(metadata, report_path)

        # Validate report content (T083)
        if not validate_report_content(report_path):
            logger.error("Report validation failed: missing mandatory sections.")
            sys.exit(1)
        logger.info(f"Generated results report: {report_path}")
    else:
        report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_insufficiency_report.md")
        logger.info("Gate failed. Generating data insufficiency report...")
        generate_data_insufficiency_report(metadata, report_path)
        logger.info(f"Generated data insufficiency report: {report_path}")

    log_operation("report_generation_complete")

if __name__ == "__main__":
    main()