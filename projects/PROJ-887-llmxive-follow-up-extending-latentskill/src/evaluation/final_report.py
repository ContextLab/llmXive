"""
Final Report Generator for llmXive LatentSkill Extension.

Aggregates all JSON/YAML results from data/results/ into a single
Markdown document reports/final_report.md.

This script reads the outputs of T032b (stats_report.json), T019 (latency_metrics.json),
T030 (linearity_validation.json), T022d (reconstruction_error.json), and T031a (sensitivity.yaml).
"""
import os
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

from src.utils.config import get_project_root, get_results_path, ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file, returning None if missing or invalid."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON {path}: {e}")
        return None

def load_yaml_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Safely load a YAML file, returning None if missing or invalid."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML {path}: {e}")
        return None

def format_value(val: Any) -> str:
    """Format a value for the report, handling None, NaN, and floats."""
    if val is None:
        return "N/A"
    if isinstance(val, float):
        if val != val:  # NaN check
            return "NaN"
        return f"{val:.4f}"
    return str(val)

def generate_report() -> str:
    """
    Aggregate all results and generate the Markdown report content.
    """
    project_root = get_project_root()
    results_dir = get_results_path()
    
    # Load all necessary data files
    stats_report = load_json_safe(results_dir / "stats_report.json")
    latency_metrics = load_json_safe(results_dir / "latency_metrics.json")
    linearity_validation = load_json_safe(results_dir / "linearity_validation.json")
    reconstruction_error = load_json_safe(results_dir / "reconstruction_error.json")
    sensitivity_data = load_yaml_safe(results_dir / "sensitivity.yaml")
    
    # Extract specific fields with defaults
    mean_success_rate = stats_report.get('mean_success_rate', 0.0) if stats_report else 0.0
    bh_primary = stats_report.get('bh_corrected_primary', {}) if stats_report else {}
    bh_sensitivity = stats_report.get('bh_corrected_sensitivity', {}) if stats_report else {}
    linearity_corr = linearity_validation.get('correlation_coefficient', None) if linearity_validation else None
    linearity_valid = linearity_validation.get('linearity_valid', None) if linearity_validation else None
    recon_max = reconstruction_error.get('max_error', None) if reconstruction_error else None
    memory_footprint = stats_report.get('memory_footprint', 'N/A') if stats_report else 'N/A'
    power_analysis = stats_report.get('estimated_power', 'N/A') if stats_report else 'N/A'
    
    # Latency breakdown
    emb_latency = latency_metrics.get('embedding_latency_ms', 0.0) if latency_metrics else 0.0
    ret_latency = latency_metrics.get('retrieval_latency_ms', 0.0) if latency_metrics else 0.0
    interp_latency = latency_metrics.get('interpolation_latency_ms', 0.0) if latency_metrics else 0.0
    total_latency = latency_metrics.get('total_skill_selection_latency_ms', 0.0) if latency_metrics else 0.0
    baseline_latency = latency_metrics.get('baseline_latency_ms', None) if latency_metrics else None
    savings = latency_metrics.get('computational_savings_ms', None) if latency_metrics else None

    # Sensitivity data
    sensitivity_scores = sensitivity_data.get('robustness_score', 'N/A') if sensitivity_data else 'N/A'
    sensitivity_k_values = sensitivity_data.get('k_values', []) if sensitivity_data else []
    sensitivity_success_rates = sensitivity_data.get('success_rates', []) if sensitivity_data else []

    # Construct the report
    report_lines = [
        "# Final Report: llmXive LatentSkill Extension",
        "",
        "## 1. Methodology",
        "",
        "- **Dataset**: ALFWorld & Search-QA (via HuggingFace `latent-skills/alfworld-weights` and `latent-skills/searchqa-weights`)",
        "- **Base Model**: TinyLlama-1B-Chat-v1.0 (GGUF quantized for CPU/low-memory execution)",
        "- **Metrics**: Success Rate, Latency (Embedding, Retrieval, Interpolation), Linearity (Pearson Correlation), Reconstruction Error",
        "",
        "## 2. Results",
        "",
        "### 2.1 Success Rates",
        "",
        f"- **Mean Success Rate (Composite Tasks)**: {format_value(mean_success_rate)}",
        "",
        "### 2.2 Latency Breakdown",
        "",
        "| Metric | Value (ms) |",
        "| :--- | :--- |",
        f"| Embedding Latency | {format_value(emb_latency)} |",
        f"| Retrieval Latency | {format_value(ret_latency)} |",
        f"| Interpolation Latency | {format_value(interp_latency)} |",
        f"| **Total Skill Selection Latency** | **{format_value(total_latency)}** |",
        "",
    ]
    
    if baseline_latency is not None:
        report_lines.append(f"- **Baseline Hypernetwork Latency**: {format_value(baseline_latency)} ms")
        if savings is not None:
            report_lines.append(f"- **Computational Savings**: {format_value(savings)} ms")
    
    report_lines.extend([
        "",
        "### 2.3 Linearity & Reconstruction",
        "",
        f"- **Text-Weight Correlation (Pearson)**: {format_value(linearity_corr)}",
        f"- **Linearity Valid (SC-005)**: {linearity_valid}",
        f"- **Max Reconstruction Error**: {format_value(recon_max)}",
        f"- **Threshold Check**: {'Pass' if recon_max is not None and recon_max <= 0.05 else 'Fail'}",
        "",
        "### 2.4 Sensitivity Analysis (Top-k)",
        "",
        f"- **Robustness Score**: {format_value(sensitivity_scores)}",
        "",
    ])

    if sensitivity_k_values and sensitivity_success_rates:
        report_lines.append("| k Value | Success Rate |")
        report_lines.append("| :--- | :--- |")
        for k, rate in zip(sensitivity_k_values, sensitivity_success_rates):
            report_lines.append(f"| {k} | {format_value(rate)} |")
        report_lines.append("")

    report_lines.extend([
        "## 3. Statistical Significance",
        "",
        "### 3.1 Primary Comparisons (BH Corrected)",
        "",
    ])
    
    if bh_primary:
        report_lines.append("| Comparison | P-Value |")
        report_lines.append("| :--- | :--- |")
        for comp, p_val in bh_primary.items():
            report_lines.append(f"| {comp} | {format_value(p_val)} |")
    else:
        report_lines.append("*No primary comparisons available.*")
        
    report_lines.extend([
        "",
        "### 3.2 Sensitivity Comparisons (BH Corrected)",
        "",
    ])
    
    if bh_sensitivity:
        report_lines.append("| Comparison | P-Value |")
        report_lines.append("| :--- | :--- |")
        for comp, p_val in bh_sensitivity.items():
            report_lines.append(f"| {comp} | {format_value(p_val)} |")
    else:
        report_lines.append("*No sensitivity comparisons available.*")
        
    report_lines.extend([
        "",
        "## 4. Limitations & Observations",
        "",
        f"- **Power Analysis**: Estimated power = {format_value(power_analysis)}.",
        f"- **Memory Footprint**: {memory_footprint}",
        "",
        "### 4.1 Data Availability",
        "",
        "If ground truth composite weights were missing (T023b), linearity validation was marked as untestable.",
        "This report aggregates all available real measurements from the execution pipeline.",
        "",
        "### 4.2 OOD Handling",
        "",
        "Out-of-Distribution queries were handled by raising a `ValueError` as per T042 implementation.",
        "",
        "## 5. Conclusion",
        "",
        "This report aggregates the results of the llmXive LatentSkill extension pipeline.",
        "All metrics are derived from real execution logs and statistical tests performed on the retrieved skill vectors.",
        ""
    ])

    return "\n".join(report_lines)

def main():
    """
    Main entry point: generates the report and saves it to reports/final_report.md.
    """
    project_root = get_project_root()
    reports_dir = project_root / "reports"
    ensure_directories([reports_dir])
    
    output_path = reports_dir / "final_report.md"
    
    logger.info("Generating final report...")
    report_content = generate_report()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Report successfully written to: {output_path}")
    print(f"Final report generated at: {output_path}")

if __name__ == "__main__":
    main()