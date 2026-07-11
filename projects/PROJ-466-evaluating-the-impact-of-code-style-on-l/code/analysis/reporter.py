import csv
import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Constants
HUMAN_EVAL_TASK_COUNT = 164
MIN_SAMPLE_SIZE_FOR_ROBUSTNESS = 300  # Heuristic threshold for robust statistical power
SMALL_EFFECT_SIZE_THRESHOLD = 0.2     # Cohen's d or similar threshold for "small" effect

logger = logging.getLogger(__name__)

def load_collinearity_status(metrics_path: Path) -> Dict[str, Any]:
    """Load collinearity status from metrics analysis."""
    if not metrics_path.exists():
        logger.warning(f"Collinearity status file not found: {metrics_path}")
        return {"flag": None, "suggestion": None}
    
    try:
        with open(metrics_path, 'r') as f:
            data = json.load(f)
        return {
            "flag": data.get("collinearity_flag"),
            "suggestion": data.get("collinearity_suggestion")
        }
    except Exception as e:
        logger.error(f"Error loading collinearity status: {e}")
        return {"flag": None, "suggestion": None}

def load_bias_flag(samples_path: Path) -> Optional[str]:
    """Load bias flag from samples CSV if present."""
    if not samples_path.exists():
        logger.warning(f"Samples file not found: {samples_path}")
        return None
    
    try:
        with open(samples_path, 'r') as f:
            reader = csv.DictReader(f)
            # Check header for bias flag column
            if "bias_flag" in reader.fieldnames:
                for row in reader:
                    if row.get("bias_flag"):
                        return row["bias_flag"]
    except Exception as e:
        logger.error(f"Error loading bias flag: {e}")
    
    return None

def calculate_effect_size_stats(stats_results: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate summary statistics for effect sizes.
    Returns mean, max, and min effect sizes from post-hoc comparisons.
    """
    effect_sizes = []
    
    if "posthoc_results" in stats_results:
        for result in stats_results["posthoc_results"]:
            if "effect_size" in result:
                effect_sizes.append(result["effect_size"])
    
    if not effect_sizes:
        return {"mean": 0.0, "max": 0.0, "min": 0.0, "count": 0}
    
    return {
        "mean": sum(effect_sizes) / len(effect_sizes),
        "max": max(effect_sizes),
        "min": min(effect_sizes),
        "count": len(effect_sizes)
    }

def check_power_limitations(stats_results: Dict[str, Any], 
                             effect_size_stats: Dict[str, float],
                             task_count: int = HUMAN_EVAL_TASK_COUNT) -> Dict[str, Any]:
    """
    Check for power limitations based on sample size and effect sizes.
    
    Returns a dictionary with:
    - warning_flag: True if power is insufficient
    - reason: Explanation of the limitation
    - recommendation: Suggested action
    """
    warnings = []
    is_power_limited = False
    
    # Check 1: Sample size (task count)
    if task_count < MIN_SAMPLE_SIZE_FOR_ROBUSTNESS:
        warnings.append(
            f"Sample size (N={task_count}) is below recommended threshold "
            f"({MIN_SAMPLE_SIZE_FOR_ROBUSTNESS}) for robust statistical conclusions."
        )
        is_power_limited = True
    
    # Check 2: Effect sizes
    if effect_size_stats["count"] > 0:
        mean_effect = effect_size_stats["mean"]
        if mean_effect < SMALL_EFFECT_SIZE_THRESHOLD:
            warnings.append(
                f"Mean effect size ({mean_effect:.3f}) is small (< {SMALL_EFFECT_SIZE_THRESHOLD}). "
                "Results may lack practical significance even if statistically significant."
            )
            is_power_limited = True
    
    # Check 3: High variance in effect sizes (indicates instability)
    if effect_size_stats["count"] > 1:
        effect_range = effect_size_stats["max"] - effect_size_stats["min"]
        if effect_range > 1.0:  # Large variance in effect sizes
            warnings.append(
                f"High variance in effect sizes (range: {effect_range:.3f}) suggests "
                "inconsistent results across comparisons, reducing confidence in conclusions."
            )
    
    if is_power_limited:
        return {
            "warning_flag": True,
            "reasons": warnings,
            "recommendation": (
                "Consider increasing sample size, aggregating results across more tasks, "
                "or interpreting findings with caution due to limited statistical power."
            )
        }
    else:
        return {
            "warning_flag": False,
            "reasons": [],
            "recommendation": "Statistical power appears sufficient for the analysis."
        }

def generate_report(stats_results: Dict[str, Any], 
                    collinearity_status: Dict[str, Any],
                    bias_flag: Optional[str],
                    output_path: Path) -> None:
    """
    Generate a text summary report with power limitation warnings.
    """
    effect_size_stats = calculate_effect_size_stats(stats_results)
    power_check = check_power_limitations(stats_results, effect_size_stats)
    
    report_lines = [
        "=== Code Style Diversity Analysis Report ===",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "--- Statistical Results ---",
        f"Kruskal-Wallis H-statistic: {stats_results.get('h_statistic', 'N/A')}",
        f"p-value: {stats_results.get('p_value', 'N/A')}",
        f"Significant: {stats_results.get('is_significant', 'N/A')}",
        "",
        "--- Post-hoc Analysis ---",
        f"Number of comparisons: {effect_size_stats['count']}",
        f"Mean effect size: {effect_size_stats['mean']:.4f}",
        f"Max effect size: {effect_size_stats['max']:.4f}",
        f"Min effect size: {effect_size_stats['min']:.4f}",
        "",
        "--- Bias Detection ---"
    ]
    
    if bias_flag:
        report_lines.append(f"Bias Flag: {bias_flag}")
    else:
        report_lines.append("Bias Flag: Not detected")
    
    report_lines.append("")
    report_lines.append("--- Collinearity Check ---")
    if collinearity_status.get("flag"):
        report_lines.append(f"Collinearity Detected: {collinearity_status['flag']}")
        if collinearity_status.get("suggestion"):
            report_lines.append(f"Suggestion: {collinearity_status['suggestion']}")
    else:
        report_lines.append("No significant collinearity detected.")
    
    report_lines.append("")
    report_lines.append("--- Power Limitation Warning ---")
    if power_check["warning_flag"]:
        report_lines.append("⚠️  POWER LIMITATION WARNING ⚠️")
        report_lines.append("")
        for reason in power_check["reasons"]:
            report_lines.append(f"• {reason}")
        report_lines.append("")
        report_lines.append(f"Recommendation: {power_check['recommendation']}")
    else:
        report_lines.append("✓ Statistical power is sufficient for robust conclusions.")
    
    report_lines.append("")
    report_lines.append("=== End of Report ===")
    
    report_text = "\n".join(report_lines)
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    logger.info(f"Report written to {output_path}")

def generate_html_report(stats_results: Dict[str, Any],
                         collinearity_status: Dict[str, Any],
                         bias_flag: Optional[str],
                         output_path: Path) -> None:
    """
    Generate an HTML report with power limitation warnings.
    """
    effect_size_stats = calculate_effect_size_stats(stats_results)
    power_check = check_power_limitations(stats_results, effect_size_stats)
    
    warning_class = "power-warning" if power_check["warning_flag"] else "power-ok"
    warning_icon = "⚠️" if power_check["warning_flag"] else "✓"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Code Style Diversity Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
            .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; }}
            .power-warning {{ background-color: #fff3cd; border-left-color: #ffc107; padding: 15px; }}
            .power-ok {{ background-color: #d4edda; border-left-color: #28a745; padding: 15px; }}
            .warning-text {{ color: #856404; font-weight: bold; }}
            .success-text {{ color: #155724; font-weight: bold; }}
            table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Code Style Diversity Analysis Report</h1>
            <p>Generated: {datetime.now().isoformat()}</p>
        </div>
        
        <div class="section">
            <h2>Statistical Results</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Kruskal-Wallis H-statistic</td><td>{stats_results.get('h_statistic', 'N/A')}</td></tr>
                <tr><td>p-value</td><td>{stats_results.get('p_value', 'N/A')}</td></tr>
                <tr><td>Significant</td><td>{stats_results.get('is_significant', 'N/A')}</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>Post-hoc Analysis</h2>
            <p>Number of comparisons: {effect_size_stats['count']}</p>
            <p>Mean effect size: {effect_size_stats['mean']:.4f}</p>
            <p>Max effect size: {effect_size_stats['max']:.4f}</p>
            <p>Min effect size: {effect_size_stats['min']:.4f}</p>
        </div>
        
        <div class="section">
            <h2>Bias Detection</h2>
            <p>Bias Flag: <strong>{bias_flag if bias_flag else 'Not detected'}</strong></p>
        </div>
        
        <div class="section">
            <h2>Collinearity Check</h2>
            <p>{'Collinearity Detected: ' + collinearity_status.get('flag', 'No') if collinearity_status.get('flag') else 'No significant collinearity detected.'}</p>
            {f"<p>Suggestion: {collinearity_status.get('suggestion', '')}</p>" if collinearity_status.get('suggestion') else ''}
        </div>
        
        <div class="section {warning_class}">
            <h2>Power Limitation Warning</h2>
            <p class="{warning_icon}">{warning_icon} {'⚠️  POWER LIMITATION WARNING ⚠️' if power_check['warning_flag'] else '✓ Statistical power is sufficient.'}</p>
            {f"<ul>{''.join([f'<li>{r}</li>' for r in power_check['reasons']])}</ul>" if power_check['reasons'] else ''}
            <p><strong>Recommendation:</strong> {power_check['recommendation']}</p>
        </div>
        
        <hr>
        <p><em>Report generated by llmXive pipeline</em></p>
    </body>
    </html>
    """
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    logger.info(f"HTML report written to {output_path}")

def run_reporter_pipeline(stats_results_path: Path,
                          metrics_path: Path,
                          samples_path: Path,
                          output_dir: Path,
                          report_format: str = "both") -> Dict[str, Path]:
    """
    Run the full reporting pipeline:
    1. Load collinearity status
    2. Load bias flag
    3. Load stats results
    4. Generate reports with power limitation warnings
    
    Args:
        stats_results_path: Path to JSON file with stats results
        metrics_path: Path to metrics JSON file
        samples_path: Path to samples CSV file
        output_dir: Directory to write reports
        report_format: "text", "html", or "both"
    
    Returns:
        Dictionary with paths to generated reports
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load dependencies
    collinearity_status = load_collinearity_status(metrics_path)
    bias_flag = load_bias_flag(samples_path)
    
    # Load stats results
    if not stats_results_path.exists():
        raise FileNotFoundError(f"Stats results file not found: {stats_results_path}")
    
    with open(stats_results_path, 'r') as f:
        stats_results = json.load(f)
    
    # Generate reports
    report_paths = {}
    
    if report_format in ["text", "both"]:
        text_report_path = output_dir / "report.txt"
        generate_report(stats_results, collinearity_status, bias_flag, text_report_path)
        report_paths["text"] = text_report_path
    
    if report_format in ["html", "both"]:
        html_report_path = output_dir / "report.html"
        generate_html_report(stats_results, collinearity_status, bias_flag, html_report_path)
        report_paths["html"] = html_report_path
    
    logger.info(f"Report generation complete. Outputs: {report_paths}")
    return report_paths