"""
Final Report Generator for LLM Code Review Impact Study.

This module compiles all findings, limitations, and visualizations into a
research summary. It enforces the audit gate before proceeding.
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import get_logger, setup_logging
from utils.config import get_config_summary

logger = None

def setup_logging_and_config():
    """Initialize logging and load configuration."""
    global logger
    logger = setup_logging("generate_final_report", "data/logs/final_report.log")
    logger.info("Starting final report generation")
    return get_config_summary()

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        logger.error(f"Required file not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def load_gate_status() -> Dict[str, Any]:
    """
    Load the gate status from data/processed/gate_status.json.
    Aborts execution if status is 'blocked'.
    """
    gate_path = PROJECT_ROOT / "data" / "processed" / "gate_status.json"
    logger.info(f"Loading gate status from {gate_path}")
    
    if not gate_path.exists():
        logger.error("Gate status file missing. Cannot proceed with final report.")
        sys.exit(1)

    data = load_json_file(gate_path)
    if data is None:
        logger.error("Failed to load gate status data.")
        sys.exit(1)

    status = data.get("status", "unknown")
    if status == "blocked":
        reason = data.get("reason", "Unknown reason")
        error_msg = f"GATE BLOCKED: {reason}. Aborting final report generation."
        logger.error(error_msg)
        sys.exit(1)
    
    logger.info(f"Gate status is '{status}'. Proceeding with report generation.")
    return data

def load_results() -> Optional[Dict[str, Any]]:
    """Load statistical results from data/processed/results.json."""
    results_path = PROJECT_ROOT / "data" / "processed" / "results.json"
    return load_json_file(results_path)

def load_visualization_summary() -> Optional[Dict[str, Any]]:
    """Load visualization metadata from reports/figures/summary.json."""
    viz_path = PROJECT_ROOT / "reports" / "figures" / "summary.json"
    return load_json_file(viz_path)

def compile_limitations(results: Dict[str, Any], gate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Compile a list of study limitations based on data and audit results."""
    limitations = []
    
    # Check sample size
    if results and "summary" in results:
        total_prs = results["summary"].get("total_prs", 0)
        if total_prs < 100:
            limitations.append(f"Small sample size (N={total_prs}) may limit statistical power.")
    
    # Check audit error rate
    error_rate = gate_data.get("error_rate", 0.0)
    if error_rate > 0.02:
        limitations.append(f"Labeling error rate ({error_rate:.2%}) exceeds ideal threshold, potentially introducing noise.")
    
    # Check data sources
    limitations.append("Analysis limited to three specific GitHub repositories; generalizability to other domains unverified.")
    limitations.append("Code complexity metrics are simplified approximations of cognitive load.")
    
    return {
        "identified_limitations": limitations,
        "count": len(limitations)
    }

def generate_report_content(results: Dict[str, Any], viz_summary: Dict[str, Any], limitations: Dict[str, Any]) -> str:
    """Generate the text content of the research summary."""
    content_lines = []
    content_lines.append("# Research Summary: Impact of Code Generation on Code Review Quality")
    content_lines.append("")
    content_lines.append("## 1. Executive Summary")
    content_lines.append("")
    
    if results:
        summary = results.get("summary", {})
        content_lines.append(f"This study analyzed {summary.get('total_prs', 'N/A')} Pull Requests to compare review metrics between LLM-generated and human-written code.")
        content_lines.append("")
        
        # Primary Findings
        content_lines.append("### Primary Findings")
        if "t_tests" in results:
            t_tests = results["t_tests"]
            for metric, data in t_tests.items():
                p_val = data.get("p_value", 0)
                stat = data.get("statistic", 0)
                effect = data.get("effect_size", 0)
                sig = "significant" if p_val < 0.05 else "not significant"
                content_lines.append(f"- **{metric.replace('_', ' ').title()}**: t-statistic={stat:.4f}, p-value={p_val:.4f} ({sig}), Cohen's d={effect:.4f}")
        content_lines.append("")
        
        # Sensitivity Analysis
        if "sensitivity_analysis" in results:
            content_lines.append("### Sensitivity Analysis (Secondary Detector Cohort)")
            sens = results["sensitivity_analysis"]
            if "mann_whitney" in sens:
                mw = sens["mann_whitney"]
                for metric, data in mw.items():
                    p_val = data.get("p_value", 0)
                    stat = data.get("statistic", 0)
                    sig = "consistent" if p_val < 0.05 else "divergent"
                    content_lines.append(f"- **{metric.replace('_', ' ').title()}**: U-statistic={stat:.4f}, p-value={p_val:.4f} ({sig})")
            content_lines.append("")

    content_lines.append("## 2. Limitations")
    content_lines.append("")
    for lim in limitations.get("identified_limitations", []):
        content_lines.append(f"- {lim}")
    content_lines.append("")
    
    content_lines.append("## 3. Visualizations")
    content_lines.append("")
    if viz_summary:
        plots = viz_summary.get("plots_generated", [])
        for plot in plots:
            content_lines.append(f"- {plot.get('type', 'Unknown')}: {plot.get('path', 'N/A')}")
    else:
        content_lines.append("- No visualization metadata found.")
    content_lines.append("")
    
    content_lines.append("## 4. Conclusion")
    content_lines.append("")
    content_lines.append("The final report PDF (see `reports/figures/final_report.pdf`) contains detailed visualizations and statistical tables.")
    
    return "\n".join(content_lines)

def save_report(content: str, output_path: Path):
    """Save the generated report content to a Markdown file."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Report saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        raise

def generate_final_report():
    """Main orchestration function for generating the final report."""
    config = setup_logging_and_config()
    
    # 1. Check Gate
    gate_data = load_gate_status()
    
    # 2. Load Data
    results = load_results()
    viz_summary = load_visualization_summary()
    
    if not results:
        logger.warning("Results file missing or empty. Generating report with partial data.")
        results = {"summary": {"total_prs": 0}, "t_tests": {}, "sensitivity_analysis": {}}
    
    # 3. Compile Limitations
    limitations = compile_limitations(results, gate_data)
    
    # 4. Generate Content
    report_content = generate_report_content(results, viz_summary, limitations)
    
    # 5. Save Report
    output_path = PROJECT_ROOT / "reports" / "final_report.md"
    save_report(report_content, output_path)
    
    # 6. Trigger PDF Generation (if the helper exists in this module or imported)
    # Note: The task description implies compiling findings into a summary. 
    # The PDF generation is often a separate step or handled by generate_final_report_pdf.py.
    # We will attempt to call the PDF generator if it's available in the same package.
    try:
        from analysis.generate_final_report_pdf import generate_final_report_pdf
        logger.info("Triggering PDF generation...")
        generate_final_report_pdf()
    except ImportError:
        logger.warning("PDF generator module not found or not imported. Text report only.")
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        # Do not fail the whole task if PDF fails, as the text report is the primary deliverable here

    logger.info("Final report generation complete.")
    return output_path

def main():
    """Entry point for the script."""
    try:
        generate_final_report()
    except SystemExit:
        # Re-raise system exits (like gate blocks)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()