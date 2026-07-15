"""
Transparency Report Generator for llmXive Project PROJ-266

This script generates the "Computational Method Transparency" section for research.md
at execution time (Phase N, T026). It reads the deviation record and execution logs
to output version-controlled computational artifacts as mandated by Constitution
Principle VI.

The script itself is the deliverable; its execution occurs in Phase N.
"""

import json
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

logger = get_logger(__name__)


def load_deviation_record() -> Dict[str, Any]:
    """
    Load the deviation record from the state directory.

    Returns:
        Dict containing deviation records.
    
    Raises:
        FileNotFoundError: If the deviation record file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    state_dir = get_project_root() / "state" / "projects"
    # Handle the specific project ID with potential truncation
    project_id = "PROJ-266-exploring-the-correlation-between-molecu"
    deviation_file = state_dir / f"{project_id}.yaml"
    
    if not deviation_file.exists():
        # Fallback to looking for any yaml file in the projects directory if exact match fails
        # This handles cases where the filename might be slightly different due to truncation
        files = list(state_dir.glob("PROJ-266*.yaml"))
        if files:
            deviation_file = files[0]
            logger.warning(f"Exact file {deviation_file.name} not found, using {deviation_file.name} instead.")
        else:
            raise FileNotFoundError(
                f"Deviation record not found at {state_dir}. "
                "Ensure T001 (project structure) and state management are complete."
            )

    logger.info(f"Loading deviation record from: {deviation_file}")
    with open(deviation_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def scan_execution_logs() -> List[Dict[str, Any]]:
    """
    Scan execution logs from the logs directory to gather metadata about
    script runs, parameters, and outcomes.

    Returns:
        List of log entries.
    """
    logs_dir = get_project_root() / "logs"
    if not logs_dir.exists():
        logger.warning(f"Logs directory {logs_dir} does not exist. Returning empty log list.")
        return []

    log_files = list(logs_dir.glob("*.log"))
    if not log_files:
        logger.warning("No log files found in logs directory.")
        return []

    log_entries = []
    for log_file in sorted(log_files):
        logger.info(f"Processing log file: {log_file.name}")
        try:
            # Attempt to parse as JSON if it looks like structured logging, otherwise parse lines
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip().startswith('[') or content.strip().startswith('{'):
                    # Try JSON
                    try:
                        data = json.loads(content)
                        if isinstance(data, list):
                            log_entries.extend(data)
                        else:
                            log_entries.append(data)
                    except json.JSONDecodeError:
                        # Fall back to line processing
                        pass
                else:
                    # Simple line-based parsing for standard log files
                    for line in content.splitlines():
                        if line.strip():
                            log_entries.append({
                                "source_file": log_file.name,
                                "raw_line": line,
                                "timestamp": datetime.now().isoformat()
                            })
        except Exception as e:
            logger.error(f"Error parsing {log_file.name}: {e}")
            continue

    return log_entries


def gather_artifacts() -> Dict[str, Any]:
    """
    Gather version-controlled computational artifacts (scripts and raw values)
    from data/ and code/ directories.

    Returns:
        Dictionary containing paths and metadata of artifacts.
    """
    project_root = get_project_root()
    artifacts = {
        "scripts": [],
        "data_files": [],
        "configs": []
    }

    # Scan code/ for Python scripts
    code_dir = project_root / "code"
    if code_dir.exists():
        for py_file in code_dir.rglob("*.py"):
            rel_path = py_file.relative_to(project_root)
            # Skip __init__.py and test files
            if py_file.name.startswith('__') or py_file.name.startswith('test_'):
                continue
            artifacts["scripts"].append({
                "path": str(rel_path),
                "size_bytes": py_file.stat().st_size,
                "modified": datetime.fromtimestamp(py_file.stat().st_mtime).isoformat()
            })

    # Scan data/ for processed data files
    data_dir = project_root / "data"
    if data_dir.exists():
        for data_file in data_dir.rglob("*"):
            if data_file.is_file():
                rel_path = data_file.relative_to(project_root)
                artifacts["data_files"].append({
                    "path": str(rel_path),
                    "size_bytes": data_file.stat().st_size,
                    "modified": datetime.fromtimestamp(data_file.stat().st_mtime).isoformat()
                })

    # Scan for config files
    for config_file in project_root.rglob("*.yaml"):
        if config_file.is_file():
            rel_path = config_file.relative_to(project_root)
            artifacts["configs"].append({
                "path": str(rel_path),
                "size_bytes": config_file.stat().st_size,
                "modified": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
            })

    return artifacts


def generate_report(deviation_record: Dict[str, Any], logs: List[Dict[str, Any]], artifacts: Dict[str, Any]) -> str:
    """
    Generate the Computational Method Transparency section for research.md.

    Args:
        deviation_record: The loaded deviation record.
        logs: List of execution log entries.
        artifacts: Dictionary of gathered artifacts.

    Returns:
        Markdown string representing the transparency report.
    """
    report_lines = [
        "## Computational Method Transparency",
        "",
        "This section documents the computational methods, deviations from specifications, "
        "and version-controlled artifacts used in this study, as mandated by Constitution Principle VI.",
        "",
        "### Deviation Record Summary",
        ""
    ]

    if deviation_record:
        deviations = deviation_record.get("deviations", [])
        if deviations:
            report_lines.append("The following deviations from the original specification were recorded:")
            report_lines.append("")
            for dev in deviations:
                dev_id = dev.get("id", "Unknown")
                description = dev.get("description", "No description provided.")
                justification = dev.get("justification", "No justification provided.")
                report_lines.append(f"- **{dev_id}**: {description}")
                report_lines.append(f"  - *Justification*: {justification}")
                report_lines.append("")
        else:
            report_lines.append("No deviations from the specification were recorded.")
            report_lines.append("")
    else:
        report_lines.append("No deviation record found.")
        report_lines.append("")

    report_lines.extend([
        "### Execution Log Summary",
        ""
    ])

    if logs:
        report_lines.append(f"Total log entries processed: {len(logs)}")
        report_lines.append("")
        # Summarize unique scripts run
        scripts_run = set()
        for log in logs:
            if "source_file" in log:
                scripts_run.add(log["source_file"])
            elif "script" in log:
                scripts_run.add(log["script"])
        
        if scripts_run:
            report_lines.append("Scripts executed during this pipeline run:")
            for script in sorted(scripts_run):
                report_lines.append(f"- `{script}`")
            report_lines.append("")
    else:
        report_lines.append("No execution logs found.")
        report_lines.append("")

    report_lines.extend([
        "### Version-Controlled Artifacts",
        "",
        "The following computational artifacts (scripts, data, and configurations) were generated "
        "and stored in the project repository:",
        "",
        "#### Scripts",
        ""
    ])

    if artifacts["scripts"]:
        report_lines.append("| Path | Size (bytes) | Modified |")
        report_lines.append("|------|--------------|----------|")
        for script in artifacts["scripts"]:
            report_lines.append(
                f"| `{script['path']}` | {script['size_bytes']} | {script['modified']} |"
            )
        report_lines.append("")
    else:
        report_lines.append("No scripts found.")
        report_lines.append("")

    report_lines.extend([
        "#### Data Files",
        ""
    ])

    if artifacts["data_files"]:
        report_lines.append("| Path | Size (bytes) | Modified |")
        report_lines.append("|------|--------------|----------|")
        for data_file in artifacts["data_files"]:
            report_lines.append(
                f"| `{data_file['path']}` | {data_file['size_bytes']} | {data_file['modified']} |"
            )
        report_lines.append("")
    else:
        report_lines.append("No data files found.")
        report_lines.append("")

    report_lines.extend([
        "#### Configuration Files",
        ""
    ])

    if artifacts["configs"]:
        report_lines.append("| Path | Size (bytes) | Modified |")
        report_lines.append("|------|--------------|----------|")
        for config in artifacts["configs"]:
            report_lines.append(
                f"| `{config['path']}` | {config['size_bytes']} | {config['modified']} |"
            )
        report_lines.append("")
    else:
        report_lines.append("No configuration files found.")
        report_lines.append("")

    report_lines.extend([
        "---",
        f"*Generated on: {datetime.now().isoformat()}*",
        ""
    ])

    return "\n".join(report_lines)


def write_report(report_content: str, output_path: Path) -> None:
    """
    Write the generated report to a file.

    Args:
        report_content: The markdown content to write.
        output_path: The path to write the file to.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    logger.info(f"Transparency report written to: {output_path}")


def main() -> int:
    """
    Main entry point for the transparency report generator.

    Returns:
        0 on success, 1 on failure.
    """
    configure_root_logger()
    logger.info("Starting transparency report generation...")

    try:
        # 1. Load deviation record
        deviation_record = load_deviation_record()
        logger.info("Deviation record loaded successfully.")

        # 2. Scan execution logs
        logs = scan_execution_logs()
        logger.info(f"Processed {len(logs)} log entries.")

        # 3. Gather artifacts
        artifacts = gather_artifacts()
        logger.info(f"Gathered {len(artifacts['scripts'])} scripts, "
                    f"{len(artifacts['data_files'])} data files, "
                    f"{len(artifacts['configs'])} configs.")

        # 4. Generate report
        report_content = generate_report(deviation_record, logs, artifacts)
        logger.info("Report content generated.")

        # 5. Write report to data/ directory
        project_root = get_project_root()
        output_path = project_root / "data" / "transparency_report.md"
        write_report(report_content, output_path)

        # Also write a JSON summary for programmatic access
        summary_path = project_root / "data" / "transparency_summary.json"
        summary_data = {
            "generated_at": datetime.now().isoformat(),
            "deviation_count": len(deviation_record.get("deviations", [])) if deviation_record else 0,
            "log_entries": len(logs),
            "artifacts_count": {
                "scripts": len(artifacts["scripts"]),
                "data_files": len(artifacts["data_files"]),
                "configs": len(artifacts["configs"])
            }
        }
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)
        logger.info(f"Transparency summary written to: {summary_path}")

        logger.info("Transparency report generation completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        return 1
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML deviation record: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during report generation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
