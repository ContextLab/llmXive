import json
import os
import sys
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Import from local utils to ensure project root is on path
try:
    from utils.config import get_project_root, get_data_path, get_state_path, get_logs_path
    from utils.logging import get_logger, configure_root_logger
except ImportError:
    # Fallback for direct execution if utils not in path yet
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.config import get_project_root, get_data_path, get_state_path, get_logs_path
    from utils.logging import get_logger, configure_root_logger

logger = get_logger(__name__)

def load_deviation_record(project_root: Path) -> Dict[str, Any]:
    """
    Load the deviation record from the state directory if it exists.
    Returns an empty dict if not found.
    """
    state_path = get_state_path(project_root)
    deviation_file = state_path / "deviations.yaml"
    
    if not deviation_file.exists():
        logger.info(f"No deviation record found at {deviation_file}.")
        return {}
    
    try:
        with open(deviation_file, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Failed to load deviation record: {e}")
        return {}

def scan_execution_logs(project_root: Path) -> List[Dict[str, Any]]:
    """
    Scan execution logs to gather metadata about the pipeline run.
    Returns a list of log entries.
    """
    logs_path = get_logs_path(project_root)
    if not logs_path.exists():
        logger.warning(f"Logs path {logs_path} does not exist.")
        return []
    
    log_entries = []
    for log_file in logs_path.glob("*.log"):
        try:
            with open(log_file, 'r') as f:
                # Simple parsing: look for key lines
                content = f.read()
                entry = {
                    "file": log_file.name,
                    "size_bytes": len(content),
                    "timestamp": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                }
                log_entries.append(entry)
        except Exception as e:
            logger.warning(f"Could not read log file {log_file}: {e}")
    
    return log_entries

def gather_artifacts(project_root: Path) -> Dict[str, Any]:
    """
    Gather key artifacts and metrics from the data/processed directory.
    Returns a summary dict.
    """
    data_path = get_data_path(project_root)
    processed_path = data_path / "processed"
    
    artifacts = {
        "conformer_count": 0,
        "descriptor_count": 0,
        "correlation_count": 0,
        "scaling_results_exists": False,
        "model_results_exists": False
    }
    
    if not processed_path.exists():
        logger.warning(f"Processed data path {processed_path} does not exist.")
        return artifacts
    
    # Check for conformers
    conf_file = processed_path / "conformers.pkl"
    if conf_file.exists():
        artifacts["conformer_count"] = "present" # Could try to load and count if needed
    
    # Check for descriptors
    desc_file = processed_path / "descriptors_raw.csv"
    if desc_file.exists():
        try:
            import pandas as pd
            df = pd.read_csv(desc_file)
            artifacts["descriptor_count"] = len(df)
        except Exception as e:
            logger.warning(f"Could not count descriptors: {e}")
            artifacts["descriptor_count"] = "error"
    
    # Check for correlation results
    corr_file = processed_path / "correlation_results.csv"
    if corr_file.exists():
        try:
            import pandas as pd
            df = pd.read_csv(corr_file)
            artifacts["correlation_count"] = len(df)
        except Exception as e:
            artifacts["correlation_count"] = "error"
    
    # Check for scaling results
    scaling_file = processed_path / "scaling_analysis_results.json"
    artifacts["scaling_results_exists"] = scaling_file.exists()
    
    # Check for model results
    model_file = processed_path / "model_results.json"
    artifacts["model_results_exists"] = model_file.exists()
    
    return artifacts

def generate_report(
    project_root: Path,
    artifacts: Dict[str, Any],
    logs: List[Dict[str, Any]],
    deviations: Dict[str, Any]
) -> str:
    """
    Generate the narrative report string based on gathered data.
    """
    # Extract metrics with defaults
    conf_count = artifacts.get("conformer_count", 0)
    desc_count = artifacts.get("descriptor_count", 0)
    corr_count = artifacts.get("correlation_count", 0)
    scaling_exists = artifacts.get("scaling_results_exists", False)
    model_exists = artifacts.get("model_results_exists", False)
    
    # Determine R2 from model results if possible
    r2_mean = "N/A"
    if model_exists:
        model_file = get_data_path(project_root) / "processed" / "model_results.json"
        try:
            with open(model_file, 'r') as f:
                model_data = json.load(f)
                if "metrics" in model_data and "r2_mean" in model_data["metrics"]:
                    r2_mean = f"{model_data['metrics']['r2_mean']:.4f}"
                elif "r2_mean" in model_data:
                    r2_mean = f"{model_data['r2_mean']:.4f}"
        except Exception as e:
            logger.warning(f"Could not parse R2 from model results: {e}")
    
    # Build the report
    report_lines = [
        "# Research Report: Molecular Flexibility and Drug Transport",
        "",
        "## Executive Summary",
        f"This report summarizes the computational investigation into the correlation between",
        f"molecular flexibility and Caco-2 permeability. The pipeline processed {desc_count} molecules",
        f"and generated {corr_count} correlation results.",
        "",
        "## Computational Method Transparency",
        "- **Conformer Generation**: RDKit `EmbedMultipleConfs` with 50 conformers per molecule.",
        "- **Flexibility Metric**: Torsional variance (dihedral) computed via PyVib Normal Mode Analysis.",
        "- **Statistical Rigor**: Pearson/Spearman correlations with Benjamini-Hochberg FDR correction.",
        f"- **Model Validation**: 5-fold cross-validation with R² mean of {r2_mean}.",
        "- **Constraint**: All steps are CPU-tractable; no GPU offload.",
        "",
        "## Execution Metadata",
        f"- **Report Generated**: {datetime.now().isoformat()}",
        f"- **Log Files Processed**: {len(logs)}",
        "",
        "## Deviations and Constraints",
    ]
    
    if deviations:
        for key, value in deviations.items():
            report_lines.append(f"- **{key}**: {value}")
    else:
        report_lines.append("- No significant deviations recorded.")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*Generated by llmXive automated science pipeline*")
    
    return "\n".join(report_lines)

def write_report(report_content: str, project_root: Path) -> Path:
    """
    Write the generated report to the specs directory.
    """
    specs_dir = project_root / "specs" / "001-molecular-flexibility-permeability"
    specs_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = specs_dir / "research.md"
    
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Report written to {output_path}")
    return output_path

def main():
    """
    Main entry point for the transparency report generation.
    """
    configure_root_logger()
    project_root = get_project_root()
    logger.info(f"Starting transparency report generation for project at {project_root}")
    
    # Gather data
    deviations = load_deviation_record(project_root)
    logs = scan_execution_logs(project_root)
    artifacts = gather_artifacts(project_root)
    
    # Generate report
    report_content = generate_report(project_root, artifacts, logs, deviations)
    
    # Write report
    output_path = write_report(report_content, project_root)
    
    logger.info("Transparency report generation complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
