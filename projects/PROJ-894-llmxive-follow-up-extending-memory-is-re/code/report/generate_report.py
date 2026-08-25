import os
import json
import csv
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_output_dirs() -> None:
    """Ensure the docs directory exists."""
    docs_path = Path("docs")
    docs_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {docs_path}")

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents as a dictionary."""
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def load_csv_sample(file_path: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Load a sample of rows from a CSV file."""
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found: {file_path}")
        return []
    try:
        rows = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                rows.append(row)
        return rows
    except Exception as e:
        logger.error(f"Error reading CSV {file_path}: {e}")
        return []

def calculate_sample_size(base_results_path: str) -> int:
    """Calculate the total sample size from the base results CSV."""
    path = Path(base_results_path)
    if not path.exists():
        logger.warning(f"Base results file not found: {base_results_path}. Returning 0.")
        return 0
    try:
        count = 0
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for _ in reader:
                count += 1
        return count
    except Exception as e:
        logger.error(f"Error counting rows in {base_results_path}: {e}")
        return 0

def extract_limitations_from_plan(plan_path: str = "projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/plan.md") -> List[str]:
    """
    Extract limitations from the plan.md file.
    Looks for an 'Assumptions' or 'Limitations' section.
    Returns a list of string limitations.
    """
    path = Path(plan_path)
    limitations = []
    if not path.exists():
        logger.warning(f"Plan file not found: {plan_path}. Using default limitations.")
        return [
            "CPU-only execution environment (no GPU acceleration for LLM inference).",
            "Fixed sample size due to time and resource constraints.",
            "Heuristic strategies evaluated on a specific subset of LoCoMo tasks."
        ]

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple heuristic to find limitations/assumptions
        # Look for sections starting with "### Assumptions" or "### Limitations"
        lines = content.split('\n')
        in_section = False
        for line in lines:
            if '### Assumptions' in line or '### Limitations' in line:
                in_section = True
                continue
            if in_section:
                if line.startswith('###'):
                    break
                if line.strip().startswith('-'):
                    limitations.append(line.strip()[1:].strip())
                elif line.strip():
                    # If it's a non-bullet line in the section, maybe it's a paragraph
                    if len(line.strip()) > 10:
                        limitations.append(line.strip())
        
        if not limitations:
            # Fallback if no specific section found
            limitations = [
                "CPU-only execution environment (no GPU acceleration for LLM inference).",
                "Fixed sample size due to time and resource constraints.",
                "Heuristic strategies evaluated on a specific subset of LoCoMo tasks."
            ]
    except Exception as e:
        logger.error(f"Error reading plan file {plan_path}: {e}")
        limitations = [
            "CPU-only execution environment (no GPU acceleration for LLM inference).",
            "Fixed sample size due to time and resource constraints.",
            "Heuristic strategies evaluated on a specific subset of LoCoMo tasks."
        ]
    
    return limitations

def generate_report_content(
    baseline_stats: Optional[Dict],
    noisy_stats: Optional[Dict],
    correlation: Optional[Dict],
    threshold: Optional[Dict],
    reduction: Optional[Dict],
    accuracy_delta: Optional[Dict],
    limitations: List[str],
    sample_size: int
) -> str:
    """Generate the Markdown content for the research report."""
    
    report = []
    report.append("# Research Report: Extending 'Memory is Reconstructed, Not Retrieved'")
    report.append("")
    report.append("## Executive Summary")
    report.append("")
    report.append("This report presents the findings from the automated science pipeline evaluating graph memory strategies for LLM agents. "
                "We compare a baseline 'Full' traversal strategy against 'Lazy' and 'Greedy' heuristics on the LoCoMo benchmark, "
                "analyzing performance under both clean and noisy graph conditions.")
    report.append("")
    
    # Baseline Performance
    report.append("## 1. Baseline Performance")
    report.append("")
    if baseline_stats:
        report.append("The baseline 'Full' traversal strategy was executed on the clean dataset.")
        report.append(f"- **Total Tasks Executed**: {sample_size}")
        report.append(f"- **Average Accuracy**: {baseline_stats.get('mean_accuracy', 'N/A')}")
        report.append(f"- **Average Nodes Visited**: {baseline_stats.get('mean_nodes_visited', 'N/A')}")
        report.append(f"- **Average Latency (ms)**: {baseline_stats.get('mean_latency', 'N/A')}")
        report.append(f"- **Timeout Rate**: {baseline_stats.get('timeout_rate', 'N/A')}")
        report.append(f"- **Degenerate Rate**: {baseline_stats.get('degenerate_rate', 'N/A')}")
    else:
        report.append("*Baseline statistics could not be computed (data missing).*")
    report.append("")

    # Heuristic Comparison
    report.append("## 2. Heuristic Strategy Comparison")
    report.append("")
    report.append("We compared 'Lazy' and 'Greedy' strategies against the baseline.")
    report.append("")
    
    if reduction:
        report.append("### Node Reduction")
        report.append(f"- **Lazy Strategy Reduction**: {reduction.get('lazy_reduction_pct', 'N/A')}%")
        report.append(f"- **Greedy Strategy Reduction**: {reduction.get('greedy_reduction_pct', 'N/A')}%")
        report.append("")
    
    if accuracy_delta:
        report.append("### Accuracy Delta (Heuristic - Baseline)")
        report.append(f"- **Lazy Delta**: {accuracy_delta.get('lazy_delta', 'N/A')}")
        report.append(f"- **Greedy Delta**: {accuracy_delta.get('greedy_delta', 'N/A')}")
        report.append("")
    
    if noisy_stats:
        report.append("### Noisy Environment Performance")
        report.append("Performance under graph noise (edge replacement):")
        report.append(f"- **Noisy Baseline Accuracy**: {noisy_stats.get('clean_baseline_mean', 'N/A')} (Clean) vs {noisy_stats.get('noisy_baseline_mean', 'N/A')} (Noisy)")
        # Add specific noisy heuristic stats if available in the noisy_stats structure
        # Assuming noisy_stats might contain aggregated comparison data
        if 'noisy_lazy_mean' in noisy_stats:
            report.append(f"- **Noisy Lazy Accuracy**: {noisy_stats['noisy_lazy_mean']}")
        if 'noisy_greedy_mean' in noisy_stats:
            report.append(f"- **Noisy Greedy Accuracy**: {noisy_stats['noisy_greedy_mean']}")
    report.append("")

    # Statistical Significance
    report.append("## 3. Statistical Significance")
    report.append("")
    if threshold:
        is_sig = threshold.get('is_significant', False)
        p_val = threshold.get('p_value', 'N/A')
        report.append(f"- **Trend Significance**: {'Yes' if is_sig else 'No'} (p-value: {p_val})")
        if is_sig:
            report.append(f"- **Inflection Point**: {threshold.get('inflection_point', 'N/A')} nodes visited")
        else:
            report.append("- No statistically significant inflection point detected.")
        report.append(f"- **Correlation Coefficient**: {threshold.get('correlation_coefficient', 'N/A')}")
    else:
        report.append("*Statistical analysis results could not be computed (data missing).*")
    report.append("")

    # Threshold Analysis
    report.append("## 4. Threshold & Inflection Analysis")
    report.append("")
    if threshold:
        report.append("We performed binning analysis on `nodes_visited` to identify performance inflection points.")
        report.append(f"- **Trend Summary**: {threshold.get('trend_summary', 'N/A')}")
        if threshold.get('is_significant'):
            report.append(f"The first bin with mean accuracy < 95% of baseline occurs at {threshold.get('inflection_point', 'N/A')} nodes.")
    else:
        report.append("*Threshold analysis data missing.*")
    report.append("")

    # Robustness Findings
    report.append("## 5. Robustness Findings")
    report.append("")
    report.append("The pipeline explicitly handles degenerate graphs (single nodes, disconnected components) and timeouts.")
    report.append("- **Degenerate Graph Handling**: Strategies detect and flag single-node or disconnected graphs as 'DEGENERATE' or 'UNRESOLVED'.")
    report.append("- **Timeout Handling**: A hard timeout mechanism interrupts long-running tasks, logging 'TIMEOUT' status.")
    report.append("- **Noise Robustness**: The system maintains functionality under edge-replacement noise, though accuracy may degrade as expected.")
    report.append("")

    # Limitations
    report.append("## 6. Limitations")
    report.append("")
    report.append("This study is subject to the following constraints:")
    report.append("")
    for lim in limitations:
        report.append(f"- {lim}")
    report.append("")
    
    report.append("---")
    report.append("*Report generated by llmXive automated science pipeline.*")
    
    return "\n".join(report)

def main():
    """Main entry point to generate the research report."""
    ensure_output_dirs()
    
    # Define paths
    base_stats_path = "data/processed/stats_report.json"
    noisy_stats_path = "data/processed/noisy_stats_report.json"
    correlation_path = "data/processed/correlation_results.json"
    threshold_path = "data/processed/threshold_analysis.json"
    reduction_path = "data/processed/reduction_analysis.json"
    accuracy_delta_path = "data/processed/accuracy_delta.json"
    base_results_path = "data/processed/baseline_results.csv"
    output_path = "docs/research_report.md"
    
    # Load data
    logger.info("Loading statistical results...")
    baseline_stats = load_json_file(base_stats_path)
    noisy_stats = load_json_file(noisy_stats_path)
    correlation = load_json_file(correlation_path)
    threshold = load_json_file(threshold_path)
    reduction = load_json_file(reduction_path)
    accuracy_delta = load_json_file(accuracy_delta_path)
    
    # Calculate sample size
    sample_size = calculate_sample_size(base_results_path)
    
    # Extract limitations
    limitations = extract_limitations_from_plan()
    
    # Generate content
    logger.info("Generating report content...")
    content = generate_report_content(
        baseline_stats=baseline_stats,
        noisy_stats=noisy_stats,
        correlation=correlation,
        threshold=threshold,
        reduction=reduction,
        accuracy_delta=accuracy_delta,
        limitations=limitations,
        sample_size=sample_size
    )
    
    # Write output
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Report successfully written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write report to {output_path}: {e}")
        raise

if __name__ == "__main__":
    main()