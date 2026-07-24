"""
Report generation module for the LLM Test Generation Pipeline.
Generates final Markdown/JSON reports with statistical results.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import get_output_dir, get_data_dir

logger = logging.getLogger(__name__)

def generate_final_report(
    execution_results: List[Dict[str, Any]],
    analysis_results: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Generates a final Markdown and JSON report of the pipeline execution.
    
    Args:
        execution_results: List of execution result dictionaries.
        analysis_results: Dictionary containing statistical analysis results.
        
    Returns:
        Path to the generated report file.
    """
    output_dir = Path(get_output_dir())
    report_path = output_dir / "final_report.json"
    md_path = output_dir / "final_report.md"

    # Prepare JSON data
    report_data = {
        "summary": {
            "total_samples": len(execution_results),
            "successful_executions": len([r for r in execution_results if r.get("status") == "success"]),
            "failed_executions": len([r for r in execution_results if r.get("status") != "success"]),
        },
        "execution_details": execution_results,
        "statistical_analysis": analysis_results or {}
    }

    # Write JSON
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    logger.info(f"JSON report written to {report_path}")

    # Write Markdown
    md_content = generate_markdown_report(report_data)
    with open(md_path, 'w') as f:
        f.write(md_content)
    logger.info(f"Markdown report written to {md_path}")

    return report_path

def generate_markdown_report(data: Dict[str, Any]) -> str:
    """
    Generates a Markdown string from the report data.
    """
    lines = [
        "# LLM Test Generation Pipeline Report",
        "",
        "## Summary",
        f"- Total Samples: {data['summary']['total_samples']}",
        f"- Successful: {data['summary']['successful_executions']}",
        f"- Failed: {data['summary']['failed_executions']}",
        ""
    ]

    if data.get('statistical_analysis'):
        stats = data['statistical_analysis']
        lines.extend([
            "## Statistical Analysis",
            f"- Test Type: {stats.get('test_type', 'N/A')}",
            f"- P-Value: {stats.get('p_value', 'N/A')}",
            f"- Effect Size: {stats.get('effect_size', 'N/A')}",
            f"- Conclusion: {stats.get('conclusion', 'N/A')}",
            ""
        ])

    lines.append("## Execution Details")
    lines.append("| Project ID | Coverage | Status |")
    lines.append("|---|---|---|")
    for r in data.get('execution_details', []):
        proj_id = r.get('project_id', 'Unknown')
        cov = r.get('coverage', 'N/A')
        status = r.get('status', 'Unknown')
        lines.append(f"| {proj_id} | {cov} | {status} |")

    return "\n".join(lines)
