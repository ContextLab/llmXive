"""
Validation Report Generator for llmXive Pipeline.

Aggregates metrics from multiple sources (metrics.json, holdout_metrics.json,
external_metrics.json, biomarker_summary.json) into a single comprehensive
Markdown report: artifacts/reports/final_validation_report.md.

Includes a clear "Simulation Mode" header if the data source is synthetic.
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Import config for path resolution
from config import get_artifacts_path, get_reports_path, get_data_path

# Import manifest loader to check data source
from data.manifest import load_manifest, get_source_type

# Setup logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Define relative paths for input artifacts
ARTIFACTS_DIR = "artifacts"
REPORTS_DIR = "reports"
DATA_DIR = "data"

FILE_METRICS = "metrics.json"
FILE_HOLDOUT = "holdout_metrics.json"
FILE_EXTERNAL = "external_metrics.json"
FILE_BIOMARKER_SUMMARY = "biomarker_summary.json"
FILE_MANIFEST = "data_manifest.yaml"

OUTPUT_REPORT = "final_validation_report.md"


def load_json_file(filename: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file from the artifacts/reports directory."""
    path = get_artifacts_path() / REPORTS_DIR / filename
    if not path.exists():
        logger.warning(f"File not found: {path}. Skipping.")
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON in {path}: {e}")
        return None


def load_manifest_file() -> Optional[Dict[str, Any]]:
    """Load the data manifest to determine source type."""
    path = get_data_path() / FILE_MANIFEST
    if not path.exists():
        logger.warning(f"Manifest not found: {path}. Assuming unknown source.")
        return None
    try:
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading manifest {path}: {e}")
        return None


def determine_mode(manifest_data: Optional[Dict[str, Any]]) -> str:
    """Determine if the report should be marked as Simulation Mode."""
    if not manifest_data:
        return "UNKNOWN_MODE"
    
    source = manifest_data.get('source', '').upper()
    # Check for explicit SIMULATED flag
    if 'SIMULATED' in source:
        return "SIMULATION_MODE"
    
    # Check for real data indicators
    if 'REAL' in source or 'NCBI' in source or 'METABOLIGHTS' in source:
        return "REAL_DATA_MODE"
    
    return "UNKNOWN_MODE"


def format_section(title: str, content: Dict[str, Any]) -> str:
    """Format a section of the report."""
    lines = [f"## {title}", ""]
    for key, value in content.items():
        if isinstance(value, dict):
            lines.append(f"### {key.replace('_', ' ').title()}")
            for k, v in value.items():
                lines.append(f"- **{k}**: {v}")
        elif isinstance(value, list):
            lines.append(f"### {key.replace('_', ' ').title()}")
            for item in value:
                if isinstance(item, dict):
                    item_str = ", ".join([f"{k}: {v}" for k, v in item.items()])
                    lines.append(f"- {item_str}")
                else:
                    lines.append(f"- {item}")
        else:
            lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
    lines.append("")
    return "\n".join(lines)


def generate_markdown_report(
    metrics: Optional[Dict[str, Any]],
    holdout: Optional[Dict[str, Any]],
    external: Optional[Dict[str, Any]],
    biomarker_summary: Optional[Dict[str, Any]],
    mode: str
) -> str:
    """Construct the full Markdown report string."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Header
    header = [
        "# Final Validation Report",
        f"**Generated:** {timestamp}",
        ""
    ]
    
    # Mode Warning
    if mode == "SIMULATION_MODE":
        header.append("## ⚠️ SIMULATION MODE")
        header.append("")
        header.append("> **IMPORTANT:** This report was generated using **synthetic data** for pipeline validation purposes.")
        header.append("> The results reflect the performance of the pipeline on simulated signals and **do not represent biological findings**.")
        header.append("> Real-world validation requires ingestion of actual omics data from NCBI SRA or MetaboLights.")
        header.append("")
    elif mode == "REAL_DATA_MODE":
        header.append("## ✅ REAL DATA MODE")
        header.append("")
        header.append("This report was generated using **real biological data**.")
        header.append("")
    else:
        header.append("## ⚠️ UNKNOWN DATA SOURCE")
        header.append("")
        header.append("The data source could not be determined from the manifest.")
        header.append("")

    report_lines = header + ["---", ""]

    # 1. Model Metrics (Cross-Validation)
    if metrics:
        report_lines.append("## 1. Model Performance (Cross-Validation)")
        report_lines.append("")
        # Flatten nested metrics if necessary
        if 'cv_metrics' in metrics:
            cv = metrics['cv_metrics']
            report_lines.append(f"- **Accuracy**: {cv.get('accuracy', 'N/A')}")
            report_lines.append(f"- **AUC/R²**: {cv.get('auc_r2', 'N/A')}")
            report_lines.append(f"- **F1 Score**: {cv.get('f1', 'N/A')}")
        else:
            for k, v in metrics.items():
                report_lines.append(f"- **{k}**: {v}")
        report_lines.append("")

    # 2. Null Model Comparison
    if metrics and 'null_metrics' in metrics:
        report_lines.append("## 2. Null Model Baseline Comparison")
        report_lines.append("")
        null_metrics = metrics['null_metrics']
        if isinstance(null_metrics, list) and len(null_metrics) > 0:
            # Average null metrics
            avg_null = sum(m.get('metric', 0) for m in null_metrics) / len(null_metrics)
            report_lines.append(f"- **Average Null Metric**: {avg_null:.4f}")
        report_lines.append("")

    # 3. Hold-out Validation (Permutation Test)
    if holdout:
        report_lines.append("## 3. Hold-out Set Validation (Permutation Test)")
        report_lines.append("")
        report_lines.append(f"- **Observed Metric**: {holdout.get('observed_metric', 'N/A')}")
        report_lines.append(f"- **Permutation p-value**: {holdout.get('permutation_p_value', 'N/A')}")
        if holdout.get('permutation_p_value', 1.0) <= 0.05:
            report_lines.append("- **Status**: ✅ Statistically Significant (p ≤ 0.05)")
        else:
            report_lines.append("- **Status**: ❌ Not Statistically Significant (p > 0.05)")
        report_lines.append("")

    # 4. External Validation
    if external:
        report_lines.append("## 4. External Validation Metrics")
        report_lines.append("")
        for k, v in external.items():
            if k != 'null_metrics': # Already covered in main metrics if needed, or specific here
                report_lines.append(f"- **{k.replace('_', ' ').title()}**: {v}")
        if 'vif_diagnostics' in external:
            report_lines.append("### VIF Diagnostics")
            for vif_entry in external['vif_diagnostics']:
                report_lines.append(f"- Feature: {vif_entry.get('feature_id', 'N/A')}, VIF: {vif_entry.get('vif', 'N/A')}")
        report_lines.append("")

    # 5. Biomarker Summary
    if biomarker_summary:
        report_lines.append("## 5. Biomarker Discovery Summary")
        report_lines.append("")
        report_lines.append(f"- **Significant SNPs**: {biomarker_summary.get('snps_count', 'N/A')}")
        report_lines.append(f"- **Significant Metabolites**: {biomarker_summary.get('metabolites_count', 'N/A')}")
        report_lines.append(f"- **Thresholds Tested**: {biomarker_summary.get('thresholds_tested', 'N/A')}")
        
        # Check success criteria
        snps = biomarker_summary.get('snps_count', 0)
        mets = biomarker_summary.get('metabolites_count', 0)
        if snps >= 10 and mets >= 10:
            report_lines.append("- **Success Criteria**: ✅ Met (≥10 SNPs and ≥10 Metabolites)")
        else:
            report_lines.append("- **Success Criteria**: ❌ Not Met (Need ≥10 SNPs and ≥10 Metabolites)")
        report_lines.append("")

    # Footer
    report_lines.append("---")
    report_lines.append("*End of Report*")
    
    return "\n".join(report_lines)


def save_report(content: str, output_path: Path) -> None:
    """Save the report to disk."""
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Report saved to: {output_path}")


def main():
    """Main entry point to generate the final validation report."""
    logger.info("Starting Final Validation Report Generation...")
    
    # Load inputs
    metrics = load_json_file(FILE_METRICS)
    holdout = load_json_file(FILE_HOLDOUT)
    external = load_json_file(FILE_EXTERNAL)
    biomarker_summary = load_json_file(FILE_BIOMARKER_SUMMARY)
    manifest = load_manifest_file()
    
    # Determine mode
    mode = determine_mode(manifest)
    logger.info(f"Detected data mode: {mode}")
    
    # Generate report
    report_content = generate_markdown_report(
        metrics=metrics,
        holdout=holdout,
        external=external,
        biomarker_summary=biomarker_summary,
        mode=mode
    )
    
    # Save output
    output_path = get_artifacts_path() / REPORTS_DIR / OUTPUT_REPORT
    save_report(report_content, output_path)
    
    logger.info("Final Validation Report Generation Complete.")
    return 0


if __name__ == "__main__":
    main()
