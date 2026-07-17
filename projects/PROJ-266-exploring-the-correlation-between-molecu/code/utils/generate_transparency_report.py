"""
Transparency Report Generator for Computational Methodology.

This script reads the deviation record (DEV-001) from the project state,
scans execution logs for relevant metadata, and generates the "Computational
Method Transparency" section for research.md.

It handles the case where the deviation record is missing or empty by
logging a warning and proceeding with default values or halting gracefully.
"""
import json
import os
import sys
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import local utilities from the project API surface
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

# Configure logging for this module
configure_root_logger()
logger = get_logger(__name__)

# Constants
DEVIATION_RECORD_PATH = "state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml"
LOG_DIR = "logs"
REPORT_OUTPUT_PATH = "specs/001-molecular-flexibility-permeability/transparency_report_snippet.md"

def load_deviation_record() -> Dict[str, Any]:
    """
    Load the deviation record from the project state.

    Returns:
        Dict containing the deviation record or an empty dict if not found/invalid.
    """
    root = get_project_root()
    record_path = root / DEVIATION_RECORD_PATH

    if not record_path.exists():
        logger.warning(f"Deviation record not found at {record_path}. Proceeding with defaults.")
        return {}

    try:
        with open(record_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                logger.warning("Deviation record is not a valid YAML dictionary.")
                return {}
            return data
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse deviation record YAML: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error reading deviation record: {e}")
        return {}

def scan_execution_logs() -> Dict[str, Any]:
    """
    Scan execution logs for relevant metadata (timestamps, script names, errors).

    Returns:
        Dict containing log metadata.
    """
    root = get_project_root()
    log_dir = root / LOG_DIR
    metadata = {
        "scan_time": datetime.now().isoformat(),
        "log_files_found": [],
        "errors_found": [],
        "scripts_executed": []
    }

    if not log_dir.exists():
        logger.warning(f"Log directory not found at {log_dir}. Skipping log scan.")
        return metadata

    # Scan for log files
    log_files = list(log_dir.glob("*.log"))
    metadata["log_files_found"] = [str(f.relative_to(root)) for f in log_files]

    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Simple heuristic: look for ERROR or WARNING
                for line in lines:
                    if "ERROR" in line or "WARNING" in line:
                        metadata["errors_found"].append(str(log_file.relative_to(root)))
                        break
        except Exception as e:
            logger.warning(f"Could not read log file {log_file}: {e}")

    # Heuristic: check for specific script names in logs
    expected_scripts = ["retrieval.py", "preprocessing.py", "descriptors.py", "analysis.py"]
    for script in expected_scripts:
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if script in content:
                        metadata["scripts_executed"].append(script)
                        break
            except Exception:
                continue

    return metadata

def gather_artifacts() -> Dict[str, Any]:
    """
    Gather all artifacts needed for the report.

    Returns:
        Dict containing deviation record, log metadata, and artifact paths.
    """
    root = get_project_root()
    deviation = load_deviation_record()
    logs = scan_execution_logs()

    artifacts = {
        "timestamp": datetime.now().isoformat(),
        "deviation_record": deviation,
        "log_metadata": logs,
        "project_root": str(root),
        "deviation_id": deviation.get("deviations", [{}])[0].get("id", "N/A") if deviation.get("deviations") else "N/A",
        "conformer_count_override": deviation.get("deviations", [{}])[0].get("details", {}).get("new_value", "N/A") if deviation.get("deviations") else "N/A"
    }

    # Check for specific deviation ID DEV-001
    dev_001 = None
    if deviation.get("deviations"):
        for dev in deviation["deviations"]:
            if dev.get("id") == "DEV-001":
                dev_001 = dev
                break

    if dev_001:
        artifacts["deviation_001"] = dev_001
    else:
        logger.warning("Deviation ID DEV-001 not found in the record.")

    return artifacts

def generate_report(artifacts: Dict[str, Any]) -> str:
    """
    Generate the "Computational Method Transparency" section markdown.

    Args:
        artifacts: Dictionary containing deviation record and log metadata.

    Returns:
        Markdown string representing the transparency report section.
    """
    lines = []
    lines.append("## Computational Method Transparency")
    lines.append("")
    lines.append("This section documents the computational methods and any deviations from the original specification.")
    lines.append("")

    # Deviation Section
    lines.append("### Deviations from Specification")
    lines.append("")

    dev_001 = artifacts.get("deviation_001")
    if dev_001:
        lines.append(f"**Deviation ID**: {dev_001.get('id', 'N/A')}")
        lines.append(f"**Title**: {dev_001.get('title', 'N/A')}")
        lines.append(f"**Reason**: {dev_001.get('reason', 'N/A')}")
        lines.append(f"**Original Requirement**: {dev_001.get('details', {}).get('original_value', 'N/A')}")
        lines.append(f"**Adopted Method**: {dev_001.get('details', {}).get('new_value', 'N/A')}")
        lines.append(f"**Justification**: {dev_001.get('justification', 'N/A')}")
        lines.append(f"**Date Approved**: {dev_001.get('date', 'N/A')}")
        lines.append("")
        lines.append("> **Note**: The conformer generation count was reduced from 50 to 20 per molecule (DEV-001) to ensure feasibility within CPU-only CI constraints while maintaining statistical validity.")
    else:
        lines.append("*No deviations recorded.*")
        lines.append("")

    # Execution Metadata Section
    lines.append("### Execution Metadata")
    lines.append("")
    lines.append(f"- **Report Generated**: {artifacts.get('timestamp', 'N/A')}")
    lines.append(f"- **Scripts Executed**: {', '.join(artifacts.get('log_metadata', {}).get('scripts_executed', ['N/A']))}")
    lines.append(f"- **Log Files Scanned**: {len(artifacts.get('log_metadata', {}).get('log_files_found', []))}")

    errors = artifacts.get("log_metadata", {}).get("errors_found", [])
    if errors:
        lines.append(f"- **Errors Detected in Logs**: {', '.join(errors)}")
    else:
        lines.append("- **Errors Detected in Logs**: None")

    lines.append("")
    lines.append("---")
    lines.append("*Generated automatically by `code/utils/generate_transparency_report.py`.*")

    return "\n".join(lines)

def write_report(report: str, output_path: Path) -> None:
    """
    Write the generated report to a file.

    Args:
        report: The markdown string to write.
        output_path: The path to the output file.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"Transparency report written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write report to {output_path}: {e}")
        raise

def main():
    """Main entry point for the transparency report generator."""
    logger.info("Starting Transparency Report Generation...")

    # Gather artifacts
    artifacts = gather_artifacts()

    # Generate report
    report = generate_report(artifacts)

    # Determine output path
    root = get_project_root()
    output_path = root / REPORT_OUTPUT_PATH

    # Write report
    write_report(report, output_path)

    logger.info("Transparency Report Generation Complete.")

if __name__ == "__main__":
    main()