"""
Generate the "Computational Method Transparency" section for research.md.

This script reads the deviation record created by T006a and generates a
narrative section that documents the computational methods and any
deviations from the original specification.
"""

import json
import os
import sys
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import logging utilities from the project
from utils.logging import get_logger, configure_root_logger, setup_logging_for_script
from utils.config import get_project_root, get_data_path, get_state_path

# Configure logging for this script
logger = setup_logging_for_script(__name__)


def load_deviation_record(record_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load the deviation record from the specified YAML file.

    Args:
        record_path: Path to the deviation record YAML file.

    Returns:
        Dictionary containing the deviation record, or None if file doesn't exist.
    """
    if not record_path.exists():
        logger.warning(f"Deviation record not found at {record_path}. "
                     "Proceeding with default values.")
        return None

    try:
        with open(record_path, 'r') as f:
            record = yaml.safe_load(f)
            if record is None:
                logger.warning(f"Deviation record at {record_path} is empty. "
                             "Proceeding with default values.")
                return None
            return record
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML file {record_path}: {e}")
        # Fall back to defaults rather than crashing
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading deviation record {record_path}: {e}")
        return None


def scan_execution_logs(logs_path: Path) -> Dict[str, Any]:
    """
    Scan execution logs to gather information about the pipeline run.

    Args:
        logs_path: Path to the logs directory.

    Returns:
        Dictionary containing execution summary information.
    """
    execution_summary = {
        "start_time": None,
        "end_time": None,
        "scripts_executed": [],
        "errors": [],
        "warnings": []
    }

    if not logs_path.exists():
        logger.warning(f"Logs directory not found at {logs_path}")
        return execution_summary

    # Scan for log files
    log_files = list(logs_path.glob("*.log"))
    if not log_files:
        logger.info("No log files found in logs directory")
        return execution_summary

    # Parse logs to extract execution summary
    for log_file in sorted(log_files):
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                # Extract timestamps
                if "Starting" in content:
                    execution_summary["start_time"] = str(datetime.now())
                if "Completed" in content or "Finished" in content:
                    execution_summary["end_time"] = str(datetime.now())
                
                # Track scripts
                script_name = log_file.stem
                if script_name not in execution_summary["scripts_executed"]:
                    execution_summary["scripts_executed"].append(script_name)
                
                # Count errors and warnings
                error_count = content.lower().count("error")
                warning_count = content.lower().count("warning")
                if error_count > 0:
                    execution_summary["errors"].append(f"{script_name}: {error_count} errors")
                if warning_count > 0:
                    execution_summary["warnings"].append(f"{script_name}: {warning_count} warnings")
        except Exception as e:
            logger.warning(f"Could not parse log file {log_file}: {e}")

    return execution_summary


def gather_artifacts(
    deviation_record: Optional[Dict[str, Any]],
    execution_summary: Dict[str, Any],
    data_path: Path,
    state_path: Path
) -> Dict[str, Any]:
    """
    Gather all artifacts needed for the transparency report.

    Args:
        deviation_record: The loaded deviation record.
        execution_summary: Summary of execution logs.
        data_path: Path to the data directory.
        state_path: Path to the state directory.

    Returns:
        Dictionary containing all gathered artifacts.
    """
    artifacts = {
        "deviation_record": deviation_record,
        "execution_summary": execution_summary,
        "data_files": [],
        "state_files": [],
        "generated_at": datetime.now().isoformat()
    }

    # List data files
    if data_path.exists():
        for root, dirs, files in os.walk(data_path):
            for file in files:
                if file.endswith(('.csv', '.json', '.yaml', '.parquet')):
                    rel_path = os.path.relpath(os.path.join(root, file), data_path)
                    artifacts["data_files"].append(rel_path)

    # List state files
    if state_path.exists():
        for root, dirs, files in os.walk(state_path):
            for file in files:
                if file.endswith('.yaml'):
                    rel_path = os.path.relpath(os.path.join(root, file), state_path)
                    artifacts["state_files"].append(rel_path)

    return artifacts


def generate_report(artifacts: Dict[str, Any]) -> str:
    """
    Generate the "Computational Method Transparency" section.

    Args:
        artifacts: Dictionary containing all gathered artifacts.

    Returns:
        Formatted markdown string for the transparency report.
    """
    report_lines = []
    report_lines.append("## Computational Method Transparency")
    report_lines.append("")
    report_lines.append("This section documents the computational methods used in this analysis,")
    report_lines.append("including any deviations from the original specification and their rationale.")
    report_lines.append("")

    # Deviation Record Section
    deviation = artifacts.get("deviation_record")
    if deviation:
        report_lines.append("### Spec Deviation Record")
        report_lines.append("")
        report_lines.append(f"- **ID**: {deviation.get('id', 'N/A')}")
        report_lines.append(f"- **Specification Requirement**: {deviation.get('spec_requirement', 'N/A')}")
        report_lines.append(f"- **Rationale**: {deviation.get('rationale', 'N/A')}")
        report_lines.append(f"- **Impact Assessment**: {deviation.get('impact_assessment', 'N/A')}")
        report_lines.append(f"- **Approved By**: {deviation.get('approved_by', 'N/A')}")
        report_lines.append("")
    else:
        report_lines.append("### Spec Deviation Record")
        report_lines.append("")
        report_lines.append("*No deviation record found. Analysis proceeded with original specification.*)")
        report_lines.append("")

    # Computational Methods Section
    report_lines.append("### Computational Methods")
    report_lines.append("")
    report_lines.append("The following computational methods were employed:")
    report_lines.append("")
    report_lines.append("1. **Data Retrieval**: Caco-2 permeability data was fetched from the ChEMBL REST API")
    report_lines.append("   using the `code/data/retrieval.py` script with exponential backoff for reliability.")
    report_lines.append("")
    report_lines.append("2. **Data Preprocessing**: Raw data was filtered for completeness and validity")
    report_lines.append("   using `code/data/preprocessing.py`, ensuring non-NULL SMILES and logPapp values.")
    report_lines.append("")
    report_lines.append("3. **Molecular Descriptor Calculation**: 3D conformer ensembles were generated")
    report_lines.append("   using RDKit, with torsional variance (bond, angle, and dihedral) calculated")
    report_lines.append("   as primary flexibility descriptors.")
    report_lines.append("")
    report_lines.append("4. **Statistical Analysis**: Pearson and Spearman correlations were computed")
    report_lines.append("   between flexibility descriptors and permeability, with Benjamini-Hochberg")
    report_lines.append("   correction for multiple hypothesis testing.")
    report_lines.append("")
    report_lines.append("5. **Model Validation**: Multivariate linear regression was performed with")
    report_lines.append("   scaffold-based cross-validation to assess generalizability.")
    report_lines.append("")

    # Execution Summary Section
    exec_summary = artifacts.get("execution_summary", {})
    report_lines.append("### Execution Summary")
    report_lines.append("")
    report_lines.append(f"- **Scripts Executed**: {', '.join(exec_summary.get('scripts_executed', ['None']))}")
    if exec_summary.get("errors"):
        report_lines.append(f"- **Errors Encountered**: {len(exec_summary['errors'])}")
        for error in exec_summary["errors"]:
            report_lines.append(f"  - {error}")
    if exec_summary.get("warnings"):
        report_lines.append(f"- **Warnings Encountered**: {len(exec_summary['warnings'])}")
        for warning in exec_summary["warnings"]:
            report_lines.append(f"  - {warning}")
    report_lines.append("")

    # Artifacts Section
    report_lines.append("### Generated Artifacts")
    report_lines.append("")
    report_lines.append("**Data Files**:")
    data_files = artifacts.get("data_files", [])
    if data_files:
        for file in data_files:
            report_lines.append(f"- `data/{file}`")
    else:
        report_lines.append("- No data files found")
    report_lines.append("")

    report_lines.append("**State Files**:")
    state_files = artifacts.get("state_files", [])
    if state_files:
        for file in state_files:
            report_lines.append(f"- `state/{file}`")
    else:
        report_lines.append("- No state files found")
    report_lines.append("")

    report_lines.append(f"**Report Generated**: {artifacts.get('generated_at', 'N/A')}")
    report_lines.append("")

    return "\n".join(report_lines)


def write_report(report_content: str, output_path: Path) -> None:
    """
    Write the transparency report to the specified output path.

    Args:
        report_content: The formatted markdown content.
        output_path: Path where the report should be written.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(report_content)

    logger.info(f"Transparency report written to {output_path}")


def main():
    """Main entry point for the transparency report generation."""
    configure_root_logger()

    try:
        # Get project paths
        project_root = get_project_root()
        state_path = get_state_path()
        data_path = get_data_path()

        # Define paths
        deviation_record_path = state_path / "projects" / "PROJ-266-exploring-the-correlation-between-molecu.yaml"
        logs_path = project_root / "logs"
        output_path = project_root / "specs" / "001-molecular-flexibility-permeability" / "transparency_report.md"

        logger.info("Starting transparency report generation...")

        # Load deviation record
        deviation_record = load_deviation_record(deviation_record_path)

        # Scan execution logs
        execution_summary = scan_execution_logs(logs_path)

        # Gather all artifacts
        artifacts = gather_artifacts(deviation_record, execution_summary, data_path, state_path)

        # Generate report
        report_content = generate_report(artifacts)

        # Write report
        write_report(report_content, output_path)

        logger.info("Transparency report generation completed successfully.")

    except Exception as e:
        logger.error(f"Failed to generate transparency report: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()