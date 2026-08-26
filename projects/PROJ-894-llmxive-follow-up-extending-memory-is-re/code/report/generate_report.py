import os
import json
import csv
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_output_dirs(output_path: Path) -> None:
    """Ensure the directory for the output file exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_path.parent}")

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_limitations(file_path: Path) -> str:
    """Load the limitations text from a markdown file."""
    if not file_path.exists():
        logger.warning(f"Limitations file not found: {file_path}. Using default text.")
        return "No specific limitations were provided in the plan."
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def calculate_sample_size(report_data: Dict[str, Any]) -> int:
    """Calculate the total sample size from the report data."""
    total_tasks = 0
    strategies = report_data.get('strategies', {})
    for strategy_name, strategy_results in strategies.items():
        if 'results' in strategy_results and isinstance(strategy_results['results'], list):
            total_tasks += len(strategy_results['results'])
    # If we have a single source of truth for task count, prefer that
    if 'task_count' in report_data:
        return report_data['task_count']
    return total_tasks

def extract_limitations_from_plan(plan_path: Path) -> str:
    """Extract limitations from plan.md if available, otherwise use default."""
    if not plan_path.exists():
        return "No plan.md found to extract limitations from."
    with open(plan_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple heuristic to find assumptions/limitations section
    lines = content.split('\n')
    limitations = []
    in_section = False
    
    for line in lines:
        if 'Assumptions' in line or 'Limitations' in line:
            in_section = True
            continue
        if in_section:
            if line.startswith('###') or line.startswith('##'):
                break
            limitations.append(line)
    
    if limitations:
        return '\n'.join(limitations).strip()
    return "No specific limitations section found in plan.md."

def format_statistical_results(stats_data: Dict[str, Any]) -> str:
    """Format statistical test results for the report."""
    lines = []
    lines.append("### Statistical Significance Analysis")
    lines.append("")
    
    clean_tests = stats_data.get('clean_tests', {})
    noisy_tests = stats_data.get('noisy_tests', {})
    
    if clean_tests:
        lines.append("**Clean Data Results:**")
        for test_name, result in clean_tests.items():
            p_val = result.get('p_value', 'N/A')
            stat = result.get('statistic', 'N/A')
            significant = "Significant" if p_val != 'N/A' and float(p_val) < 0.05 else "Not Significant"
            lines.append(f"- {test_name}: p-value = {p_val}, statistic = {stat} ({significant})")
        lines.append("")
    
    if noisy_tests:
        lines.append("**Noisy Data Results:**")
        for test_name, result in noisy_tests.items():
            p_val = result.get('p_value', 'N/A')
            stat = result.get('statistic', 'N/A')
            significant = "Significant" if p_val != 'N/A' and float(p_val) < 0.05 else "Not Significant"
            lines.append(f"- {test_name}: p-value = {p_val}, statistic = {stat} ({significant})")
        lines.append("")
    
    return '\n'.join(lines)

def format_threshold_analysis(threshold_data: Dict[str, Any]) -> str:
    """Format threshold analysis results for the report."""
    lines = []
    lines.append("### Threshold and Inflection Analysis")
    lines.append("")
    
    inflection = threshold_data.get('inflection_point')
    if inflection is not None:
        lines.append(f"**Inflection Point:** {inflection} nodes")
    else:
        lines.append("**Inflection Point:** Not detected (no significant trend change)")
    
    corr = threshold_data.get('correlation_coefficient')
    if corr is not None:
        lines.append(f"**Correlation Coefficient:** {corr:.4f}")
    
    lines.append(f"**Trend Summary:** {threshold_data.get('trend_summary', 'N/A')}")
    lines.append(f"**Significant:** {threshold_data.get('is_significant', False)}")
    lines.append(f"**P-value:** {threshold_data.get('p_value', 'N/A')}")
    lines.append("")
    
    return '\n'.join(lines)

def format_reductions(report_data: Dict[str, Any]) -> str:
    """Format efficiency reduction metrics."""
    lines = []
    lines.append("### Efficiency Metrics")
    lines.append("")
    
    strategies = report_data.get('strategies', {})
    baseline = strategies.get('Full', {}).get('summary', {})
    
    if baseline.get('avg_nodes_visited'):
        lines.append(f"**Baseline (Full) Avg Nodes Visited:** {baseline['avg_nodes_visited']:.2f}")
    
    for strategy_name in ['Lazy', 'Greedy']:
        if strategy_name in strategies:
            summary = strategies[strategy_name].get('summary', {})
            if summary.get('avg_nodes_visited'):
                baseline_nodes = baseline.get('avg_nodes_visited', 0)
                current_nodes = summary.get('avg_nodes_visited', 0)
                if baseline_nodes > 0:
                    reduction = ((baseline_nodes - current_nodes) / baseline_nodes) * 100
                    lines.append(f"**{strategy_name} Avg Nodes Visited:** {current_nodes:.2f} ({reduction:.1f}% reduction)")
                else:
                    lines.append(f"**{strategy_name} Avg Nodes Visited:** {current_nodes:.2f}")
    lines.append("")
    
    return '\n'.join(lines)

def format_accuracy_deltas(report_data: Dict[str, Any]) -> str:
    """Format accuracy comparisons."""
    lines = []
    lines.append("### Accuracy Analysis")
    lines.append("")
    
    strategies = report_data.get('strategies', {})
    baseline = strategies.get('Full', {}).get('summary', {})
    baseline_acc = baseline.get('avg_accuracy', 0)
    
    lines.append(f"**Baseline (Full) Accuracy:** {baseline_acc:.2%}")
    
    for strategy_name in ['Lazy', 'Greedy']:
        if strategy_name in strategies:
            summary = strategies[strategy_name].get('summary', {})
            current_acc = summary.get('avg_accuracy', 0)
            delta = current_acc - baseline_acc
            lines.append(f"**{strategy_name} Accuracy:** {current_acc:.2%} (Δ {delta:+.2%})")
    
    lines.append("")
    return '\n'.join(lines)

def format_status_counts(status_data: Dict[str, Any]) -> str:
    """Format status counts for the report."""
    lines = []
    lines.append("### Execution Status Summary")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|--------|-------|")
    
    counts = status_data.get('counts', {})
    for status, count in sorted(counts.items()):
        lines.append(f"| {status} | {count} |")
    
    lines.append("")
    return '\n'.join(lines)

def generate_report_content(
    report_data: Dict[str, Any],
    limitations_text: str,
    statistical_data: Dict[str, Any],
    threshold_data: Dict[str, Any],
    status_data: Dict[str, Any]
) -> str:
    """Generate the full Markdown report content."""
    lines = []
    
    # Title and Introduction
    lines.append("# Research Report: Graph Memory for LLM Agents")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("This report presents the results of the active reconstruction strategies evaluated on the LoCoMo benchmark.")
    lines.append("The study compares Full, Lazy, and Greedy traversal strategies in terms of accuracy, efficiency, and robustness to noise.")
    lines.append("")
    
    # Sample Size
    sample_size = calculate_sample_size(report_data)
    lines.append(f"**Total Tasks Evaluated:** {sample_size}")
    lines.append("")
    
    # Accuracy Analysis
    lines.append(format_accuracy_deltas(report_data))
    
    # Efficiency Metrics
    lines.append(format_reductions(report_data))
    
    # Statistical Analysis
    lines.append(format_statistical_results(statistical_data))
    
    # Threshold Analysis
    lines.append(format_threshold_analysis(threshold_data))
    
    # Status Summary
    lines.append(format_status_counts(status_data))
    
    # Limitations
    lines.append("## Limitations")
    lines.append("")
    lines.append(limitations_text)
    lines.append("")
    
    # Conclusion
    lines.append("## Conclusion")
    lines.append("")
    lines.append("The analysis provides insights into the trade-offs between reconstruction fidelity and computational efficiency.")
    lines.append("Statistical significance testing confirms whether observed differences are robust.")
    lines.append("")
    
    return '\n'.join(lines)

def main():
    """Main entry point for report generation."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    report_data_path = project_root / 'data' / 'processed' / 'report_data.json'
    limitations_path = project_root / 'data' / 'processed' / 'limitation_text.md'
    stats_data_path = project_root / 'data' / 'processed' / 'statistical_results.json'
    threshold_data_path = project_root / 'data' / 'processed' / 'threshold_analysis.json'
    status_counts_path = project_root / 'data' / 'processed' / 'status_counts.json'
    output_path = project_root / 'docs' / 'research_report.md'
    
    logger.info(f"Generating report from: {report_data_path}")
    
    try:
        # Load all required input data
        report_data = load_json_file(report_data_path)
        limitations_text = load_limitations(limitations_path)
        statistical_data = load_json_file(stats_data_path)
        threshold_data = load_json_file(threshold_data_path)
        status_data = load_json_file(status_counts_path)
        
        # Generate report content
        report_content = generate_report_content(
            report_data,
            limitations_text,
            statistical_data,
            threshold_data,
            status_data
        )
        
        # Ensure output directory exists
        ensure_output_dirs(output_path)
        
        # Write report to disk
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Report successfully generated at: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        raise

if __name__ == "__main__":
    main()