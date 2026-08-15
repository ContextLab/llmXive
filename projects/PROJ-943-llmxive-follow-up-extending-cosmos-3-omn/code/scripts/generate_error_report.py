import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger, log_script_start, log_script_end, get_memory_usage_mb

# Configuration paths
MISCLASSIFIED_PATH = PROJECT_ROOT / "data" / "processed" / "misclassified_samples.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "data" / "results" / "error_analysis_report.md"
VISUALIZATION_PATH = PROJECT_ROOT / "data" / "results" / "error_visualizations.png"

def load_misclassified_samples(path: Path) -> List[Dict[str, Any]]:
    """Load misclassified samples from JSONL file."""
    if not path.exists():
        raise FileNotFoundError(f"Misclassified samples file not found: {path}")
    
    samples = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                samples.append(json.loads(line))
            except json.JSONDecodeError as e:
                logging.warning(f"Skipping invalid JSON on line {line_num}: {e}")
    return samples

def count_error_categories(samples: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count occurrences of each error category."""
    counts = {"visual ambiguity": 0, "logical complexity": 0, "context mismatch": 0, "unknown": 0}
    for sample in samples:
        category = sample.get("error_category", "unknown")
        if category in counts:
            counts[category] += 1
        else:
            counts["unknown"] += 1
    return counts

def calculate_statistics(samples: List[Dict[str, Any]], counts: Dict[str, int]) -> Dict[str, Any]:
    """Calculate quantitative statistics for the report."""
    total = len(samples)
    if total == 0:
        return {"total_samples": 0, "percentages": {}}
    
    percentages = {
        cat: (count / total * 100) for cat, count in counts.items()
    }
    
    # Calculate average confidence for misclassified samples if available
    confidences = [s.get("prediction_confidence", 0.0) for s in samples if "prediction_confidence" in s]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    return {
        "total_samples": total,
        "percentages": percentages,
        "avg_confidence": avg_confidence
    }

def generate_qualitative_insights(samples: List[Dict[str, Any]], counts: Dict[str, int]) -> List[str]:
    """Generate qualitative descriptions based on data patterns."""
    insights = []
    
    if not samples:
        return ["No misclassified samples found to analyze."]
    
    total = len(samples)
    counts_sorted = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    
    # Identify dominant failure mode
    dominant_mode, dominant_count = counts_sorted[0]
    if dominant_count > 0:
        insights.append(
            f"The dominant failure mode is '{dominant_mode}' with {dominant_count} cases "
            f"({dominant_count/total*100:.1f}% of errors)."
        )
    
    # Analyze specific patterns if data allows
    if "visual ambiguity" in counts and counts["visual ambiguity"] > 0:
        insights.append(
            "Visual ambiguity errors suggest the model struggles with low-contrast or "
            "occluded objects in the input frames."
        )
    
    if "logical complexity" in counts and counts["logical complexity"] > 0:
        insights.append(
            "Logical complexity errors indicate difficulty in multi-step reasoning "
            "or handling nested constraints in the action space."
        )
    
    if "context mismatch" in counts and counts["context mismatch"] > 0:
        insights.append(
            "Context mismatch errors reveal a gap between the model's learned "
            "contextual priors and the actual scene dynamics."
        )
    
    # Check for confidence patterns
    confidences = [s.get("prediction_confidence", 0.0) for s in samples]
    if confidences:
        high_conf_errors = sum(1 for c in confidences if c > 0.8)
        if high_conf_errors > 0:
            insights.append(
                f"Found {high_conf_errors} cases where the model was highly confident (>80%) "
                "yet incorrect, suggesting potential overconfidence in specific failure modes."
            )
    
    return insights

def generate_report(samples: List[Dict[str, Any]], output_path: Path) -> None:
    """Generate the markdown error analysis report."""
    counts = count_error_categories(samples)
    stats = calculate_statistics(samples, counts)
    insights = generate_qualitative_insights(samples, counts)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_lines = [
        "# Error Analysis Report",
        "",
        f"**Generated:** {timestamp}",
        f"**Source:** {MISCLASSIFIED_PATH}",
        "",
        "## Executive Summary",
        "",
        f"This report analyzes {stats['total_samples']} misclassified samples from the proxy model evaluation.",
        f"The average prediction confidence for these errors is {stats['avg_confidence']:.3f}.",
        "",
        "## Quantitative Summary",
        "",
        "### Error Category Distribution",
        "",
        "| Category | Count | Percentage |",
        "|----------|-------|------------|",
    ]
    
    for category, count in counts.items():
        pct = stats['percentages'].get(category, 0.0)
        report_lines.append(f"| {category} | {count} | {pct:.2f}% |")
    
    report_lines.extend([
        "",
        "## Qualitative Insights",
        "",
    ])
    
    for i, insight in enumerate(insights, 1):
        report_lines.append(f"{i}. {insight}")
    
    report_lines.extend([
        "",
        "## Detailed Findings",
        "",
        "### Failure Mode Analysis",
        "",
        "The following patterns were observed in the misclassified samples:",
        "",
    ])
    
    # Add specific examples for each category if available
    for category in counts.keys():
        category_samples = [s for s in samples if s.get("error_category") == category]
        if category_samples:
            report_lines.append(f"**{category.replace('_', ' ').title()}** ({len(category_samples)} cases):")
            report_lines.append("")
            # Show up to 3 examples
            for idx, sample in enumerate(category_samples[:3], 1):
                desc = sample.get("text_description", "N/A")[:100]
                actions = sample.get("actions", [])
                actions_preview = f"[{', '.join(map(str, actions[:3]))}...]" if actions else "N/A"
                report_lines.append(f"- Example {idx}: Context: '{desc}...', Actions: {actions_preview}")
            report_lines.append("")
    
    report_lines.extend([
        "## Recommendations",
        "",
        "Based on the analysis:",
        "",
        "1. **Data Augmentation**: Increase diversity in visual inputs to address 'visual ambiguity'.",
        "2. **Model Architecture**: Consider adding attention mechanisms for better context handling.",
        "3. **Loss Function**: Implement focal loss to reduce impact of easy negatives and focus on hard examples.",
        "",
        "---",
        f"*Report generated by llmXive pipeline (Task T023)*",
    ])
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    logging.info(f"Error analysis report saved to {output_path}")

def main():
    """Main entry point for the error report generation."""
    logger = get_logger(__name__)
    log_script_start(logger, "generate_error_report")
    
    try:
        # Load data
        logger.info(f"Loading misclassified samples from {MISCLASSIFIED_PATH}")
        samples = load_misclassified_samples(MISCLASSIFIED_PATH)
        logger.info(f"Loaded {len(samples)} misclassified samples")
        
        if not samples:
            logger.warning("No misclassified samples found. Generating empty report.")
        
        # Generate report
        logger.info("Generating error analysis report")
        generate_report(samples, OUTPUT_PATH)
        
        # Log memory usage
        mem_mb = get_memory_usage_mb()
        logger.info(f"Peak memory usage: {mem_mb:.2f} MB")
        
        logger.info("Error report generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error during report generation: {e}", exc_info=True)
        raise
    finally:
        log_script_end(logger)

if __name__ == "__main__":
    main()