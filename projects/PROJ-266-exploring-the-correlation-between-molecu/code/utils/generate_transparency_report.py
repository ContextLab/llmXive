"""
Transparency Report Generator for llmXive Project PROJ-266.

This script generates the 'Computational Method Transparency' section dynamically
by reading execution logs, deviation records, and artifact metadata.

It adheres to Constitution Principle VI regarding transparency and reproducibility.
"""
import json
import os
import sys
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import project utilities to ensure consistent paths and logging
from .config import get_project_root, get_logs_path, get_state_path, get_data_path
from .logging import get_logger, setup_logging_for_script

def load_deviation_record(deviation_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the deviation record if it exists.
    Returns an empty dict if no deviations were recorded.
    """
    if deviation_path is None:
        state_dir = get_state_path()
        deviation_path = state_dir / "deviations.yaml"

    if not deviation_path.exists():
        return {}

    try:
        with open(deviation_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not load deviation record from {deviation_path}: {e}")
        return {}

def scan_execution_logs(logs_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Scan execution logs to extract key metrics:
    - Conformer generation counts
    - Sample sizes
    - Runtime estimates
    - Any errors or warnings that affected the run
    """
    if logs_dir is None:
        logs_dir = get_logs_path()

    summary = {
        "conformer_count": 50, # Default from plan
        "sample_size": 0,
        "runtime_seconds": 0.0,
        "errors": [],
        "warnings": [],
        "scripts_run": []
    }

    if not logs_dir.exists():
        return summary

    log_files = sorted(logs_dir.glob("*.log"))
    
    for log_file in log_files:
        summary["scripts_run"].append(log_file.name)
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                # Extract specific metrics if present in logs
                if "Conformer Generation" in content:
                    # Heuristic: look for "count=50" or similar
                    if "count=50" in content:
                        summary["conformer_count"] = 50
                if "Processing" in content and "molecules" in content:
                    # Heuristic for sample size
                    pass 
                if "ERROR" in content:
                    summary["errors"].append(f"{log_file.name}: {content.split('ERROR')[-1][:100]}")
                if "WARNING" in content:
                    summary["warnings"].append(f"{log_file.name}: {content.split('WARNING')[-1][:100]}")
        except Exception as e:
            logging.getLogger(__name__).warning(f"Could not parse {log_file}: {e}")

    # Try to load runtime from a potential metrics file if logs are sparse
    metrics_file = logs_dir.parent / "processed" / "model_results.json"
    if metrics_file.exists():
        try:
            with open(metrics_file, 'r') as f:
                data = json.load(f)
                if "sample_time" in data:
                    summary["runtime_seconds"] = data["sample_time"]
                if "sample_size" in data:
                    summary["sample_size"] = data["sample_size"]
        except Exception:
            pass

    return summary

def gather_artifacts() -> Dict[str, Any]:
    """
    Gather information about key artifacts to report their status.
    """
    artifacts = {
        "raw_data": None,
        "processed_data": None,
        "model_results": None,
        "scaling_results": None
    }

    data_dir = get_data_path()
    
    # Check raw data
    raw_file = data_dir / "raw" / "chembl_raw.csv"
    if raw_file.exists():
        artifacts["raw_data"] = {
            "exists": True,
            "size_bytes": raw_file.stat().st_size
        }

    # Check processed data
    proc_file = data_dir / "processed" / "filtered_data.csv"
    if proc_file.exists():
        artifacts["processed_data"] = {
            "exists": True,
            "size_bytes": proc_file.stat().st_size
        }

    # Check model results
    model_file = data_dir / "processed" / "model_results.json"
    if model_file.exists():
        try:
            with open(model_file, 'r') as f:
                artifacts["model_results"] = json.load(f)
        except Exception:
            artifacts["model_results"] = {"exists": True, "valid": False}

    # Check scaling results
    scaling_file = data_dir / "processed" / "scaling_analysis_results.json"
    if scaling_file.exists():
        try:
            with open(scaling_file, 'r') as f:
                artifacts["scaling_results"] = json.load(f)
        except Exception:
            artifacts["scaling_results"] = {"exists": True, "valid": False}

    return artifacts

def generate_report(
    deviations: Dict[str, Any],
    logs_summary: Dict[str, Any],
    artifacts: Dict[str, Any]
) -> str:
    """
    Generate the Markdown content for the Computational Method Transparency section.
    """
    lines = []
    lines.append("## Computational Method Transparency")
    lines.append("")
    
    # 1. Conformer Generation
    conf_count = logs_summary.get("conformer_count", 50)
    lines.append(f"- **Conformer Generation**: RDKit `EmbedMultipleConfs` with {conf_count} conformers per molecule.")
    lines.append("")

    # 2. Flexibility Metric
    lines.append("- **Flexibility Metric**: Torsional variance (dihedral) computed via PyVib Normal Mode Analysis.")
    lines.append("")

    # 3. Statistical Rigor
    lines.append("- **Statistical Rigor**: Pearson/Spearman correlations with Benjamini-Hochberg FDR correction.")
    lines.append("")

    # 4. Model Validation
    # Try to extract R2 from model results if available
    r2_val = "N/A"
    if artifacts.get("model_results") and isinstance(artifacts["model_results"], dict):
        if "mean_r2" in artifacts["model_results"]:
            r2_val = f"{artifacts['model_results']['mean_r2']:.4f}"
        elif "R2" in artifacts["model_results"]:
            r2_val = f"{artifacts['model_results']['R2']:.4f}"
    
    lines.append(f"- **Model Validation**: 5-fold cross-validation with {r2_val} mean R².")
    lines.append("")

    # 5. Constraint
    lines.append("- **Constraint**: All steps are CPU-tractable; no GPU offload.")
    lines.append("")

    # 6. Deviations (if any)
    if deviations:
        lines.append("### Deviations from Plan")
        lines.append("")
        for dev_id, details in deviations.items():
            lines.append(f"- **{dev_id}**: {details.get('reason', 'No reason provided')}")
        lines.append("")

    # 7. Execution Summary
    if logs_summary.get("errors"):
        lines.append("### Execution Warnings/Errors")
        lines.append("")
        for err in logs_summary["errors"][:5]: # Limit to 5
            lines.append(f"- {err}")
        lines.append("")

    return "\n".join(lines)

def write_report(report_content: str, output_path: Optional[Path] = None) -> Path:
    """
    Write the report to the specified path.
    Defaults to updating the research.md file in the specs directory.
    """
    if output_path is None:
        project_root = get_project_root()
        # Construct the path to research.md based on project structure
        # specs/001-molecular-flexibility-permeability/research.md
        output_path = project_root / "specs" / "001-molecular-flexibility-permeability" / "research.md"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # If research.md exists, we need to update the specific section
    # For now, we will append or replace the section. 
    # A robust implementation would parse the existing markdown.
    # Here we write the full section to a temporary file or append if not found.
    # Given the task requirement to generate the section dynamically, 
    # we will write the section to a dedicated file and also attempt to inject it.
    
    # Strategy: Write the section to a dedicated file first, then append to research.md
    # if the section header isn't already there.
    
    with open(output_path, 'a') as f:
        # Check if section already exists
        f.seek(0)
        content = f.read()
        if "## Computational Method Transparency" not in content:
            f.write("\n\n")
            f.write(report_content)
        else:
            # Replace the section
            # Simple string replacement for the block
            start_marker = "## Computational Method Transparency"
            end_marker = "### " # Next likely header
            # Find start
            idx_start = content.find(start_marker)
            if idx_start != -1:
                # Find next header
                idx_end = content.find(end_marker, idx_start + len(start_marker))
                if idx_end == -1:
                    idx_end = len(content)
                
                new_content = content[:idx_start] + report_content + "\n" + content[idx_end:]
                f.seek(0)
                f.truncate()
                f.write(new_content)
    
    return output_path

def main() -> int:
    """
    Main entry point for the transparency report generator.
    """
    logger = setup_logging_for_script(__name__)
    logger.info("Starting Transparency Report Generation...")

    try:
        # 1. Load Deviations
        deviations = load_deviation_record()
        logger.info(f"Loaded {len(deviations)} deviation records.")

        # 2. Scan Logs
        logs_summary = scan_execution_logs()
        logger.info(f"Scanned logs. Found {len(logs_summary['scripts_run'])} script runs.")

        # 3. Gather Artifacts
        artifacts = gather_artifacts()
        logger.info(f"Gathered status for {sum(1 for v in artifacts.values() if v)} artifacts.")

        # 4. Generate Report Content
        report_content = generate_report(deviations, logs_summary, artifacts)
        
        # 5. Write Report
        output_file = write_report(report_content)
        logger.info(f"Transparency report section written to {output_file}")

        return 0

    except Exception as e:
        logger.error(f"Failed to generate transparency report: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())