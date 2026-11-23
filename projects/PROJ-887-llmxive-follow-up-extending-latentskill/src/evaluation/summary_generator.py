"""
Task T085: Generate a summary report of the llmXive LatentSkill follow-up study.

This script aggregates key findings, statistical significance, and limitations
from the final pipeline run into a concise Markdown summary.

Dependencies:
- data/results/stats_report.json (from T032c)
- data/results/linearity_validation.json (from T030b)
- data/results/latency_metrics.json (from T019/T059c)
- data/processed/citation_verification.json (from T006b)
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(project_root / "code"))

from src.utils.config import get_project_root, ensure_directories

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if not found or invalid."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {path}: {e}")
        return None

def load_yaml_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Load a YAML file safely (minimal parser for simple dicts)."""
    try:
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not installed; skipping YAML load.")
        return None
    except FileNotFoundError:
        logger.warning(f"File not found: {path}")
        return None
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
        return None

def generate_summary(stats_report: Dict, linearity: Dict, latency: Dict, citations: Dict) -> str:
    """Generate the Markdown summary content."""
    lines = []
    lines.append("# llmXive LatentSkill Follow-up: Summary Report")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    
    # Key Findings
    lines.append("### Key Findings")
    if stats_report:
        success_rate = stats_report.get("mean_success_rate", "N/A")
        linearity_valid = stats_report.get("status_linearity", "N/A")
        power = stats_report.get("power_estimate", "N/A")
        
        lines.append(f"- **Mean Success Rate**: {success_rate}")
        lines.append(f"- **Linearity Validation (SC-005)**: {linearity_valid}")
        lines.append(f"- **Statistical Power**: {power}")
        
        # Significance
        bh_primary = stats_report.get("bh_corrected_primary", {})
        if bh_primary:
            significant = [k for k, v in bh_primary.items() if v is not None and v < 0.05]
            lines.append(f"- **Significant Strategies (BH-corrected p < 0.05)**: {', '.join(significant) if significant else 'None'}")
        else:
            lines.append("- **Significant Strategies**: Data unavailable.")
    else:
        lines.append("- *Stats report not found. Pipeline may have failed.*")
    
    lines.append("")
    
    # Statistical Significance
    lines.append("## Statistical Significance")
    lines.append("")
    if stats_report:
        bh_primary = stats_report.get("bh_corrected_primary", {})
        bh_sensitivity = stats_report.get("bh_corrected_sensitivity", {})
        
        lines.append("### Primary Hypothesis Tests")
        lines.append("| Strategy | BH-Corrected p-value |")
        lines.append("| :--- | :--- |")
        for strat, p_val in bh_primary.items():
            p_str = f"{p_val:.4f}" if isinstance(p_val, (int, float)) else str(p_val)
            lines.append(f"| {strat} | {p_str} |")
        
        lines.append("")
        lines.append("### Sensitivity Analysis (Top-k)")
        lines.append("| k Value | BH-Corrected p-value |")
        lines.append("| :--- | :--- |")
        for k_val, p_val in bh_sensitivity.items():
            p_str = f"{p_val:.4f}" if isinstance(p_val, (int, float)) else str(p_val)
            lines.append(f"| {k_val} | {p_str} |")
    else:
        lines.append("*Statistical data unavailable.*")
    
    lines.append("")
    
    # Limitations & Warnings
    lines.append("## Limitations & Warnings")
    lines.append("")
    if stats_report:
        warnings = stats_report.get("warnings", [])
        if warnings:
            lines.append("### Warnings Encountered")
            for w in warnings:
                lines.append(f"- {w}")
        else:
            lines.append("- No critical warnings recorded.")
        
        lines.append("")
        lines.append("### Study Limitations")
        if stats_report.get("power_estimate", 0) < 0.8:
            lines.append("- **Low Statistical Power**: The estimated power ({:.2f}) is below the 0.8 threshold. Results should be interpreted with caution.".format(stats_report.get("power_estimate", 0)))
        else:
            lines.append("- **Statistical Power**: Adequate (>{:.2f}).".format(stats_report.get("power_estimate", 0)))
        
        # Data Integrity
        lines.append("")
        lines.append("### Data Integrity")
        if citations and citations.get("status") == "verified":
            lines.append("- All data sources verified as real and reachable.")
        else:
            lines.append("- **Warning**: Data source verification status unknown or failed.")
    else:
        lines.append("- Unable to compile limitations due to missing stats report.")
    
    lines.append("")
    lines.append("---")
    lines.append("*Generated by T085 Summary Generator*")
    return "\n".join(lines)

def main():
    """Main entry point for T085."""
    logger.info("Starting T085: Summary Generation")
    
    project_root = get_project_root()
    output_path = project_root / "reports" / "summary.md"
    ensure_directories([output_path.parent])
    
    # Paths to source files
    stats_path = project_root / "data" / "results" / "stats_report.json"
    linearity_path = project_root / "data" / "results" / "linearity_validation.json"
    latency_path = project_root / "data" / "results" / "latency_metrics.json"
    citations_path = project_root / "data" / "processed" / "citation_verification.json"
    
    # Load data
    stats_report = load_json_safe(stats_path)
    linearity = load_json_safe(linearity_path)
    latency = load_json_safe(latency_path)
    citations = load_json_safe(citations_path)
    
    if not stats_report:
        logger.error("Critical: stats_report.json not found. Cannot generate summary.")
        # Generate a minimal failure summary
        summary_content = "# Summary Generation Failed\n\nThe required `stats_report.json` was not found. The pipeline did not complete successfully."
    else:
        summary_content = generate_summary(stats_report, linearity, latency, citations)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    logger.info(f"Summary written to: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
