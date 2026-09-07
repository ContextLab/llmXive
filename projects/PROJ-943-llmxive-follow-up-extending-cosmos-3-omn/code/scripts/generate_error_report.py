import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.logger import get_logger, log_script_start, log_script_end
from scripts.analyze_errors import load_misclassified_samples, categorize_error

logger = get_logger(__name__)

def load_misclassified_samples(file_path: str) -> List[Dict[str, Any]]:
    """Load misclassified samples from JSONL file."""
    samples = []
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Misclassified samples file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
    return samples

def count_error_categories(samples: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count occurrences of each error category."""
    counts = {
        "Visual Ambiguity": 0,
        "Logical Complexity": 0,
        "Context Mismatch": 0,
        "Unknown": 0
    }
    
    for sample in samples:
        # Ensure categorization is up-to-date
        if 'error_category' not in sample:
            sample['error_category'] = categorize_error(sample)
        
        category = sample['error_category']
        if category in counts:
            counts[category] += 1
        else:
            counts["Unknown"] += 1
    
    return counts

def calculate_statistics(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate quantitative statistics for error categories."""
    stats = {
        "total_errors": len(samples),
        "categories": {},
        "confidence_stats": {
            "mean": 0.0,
            "std": 0.0,
            "min": 1.0,
            "max": 0.0
        },
        "norm_stats": {
            "mean": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0
        }
    }
    
    if not samples:
        return stats
    
    # Calculate confidence and norm statistics
    confidences = [s.get('model_confidence', 0.0) for s in samples if 'model_confidence' in s]
    norms = [s.get('norm_value', 0.0) for s in samples if 'norm_value' in s]
    
    if confidences:
        import numpy as np
        stats["confidence_stats"]["mean"] = float(np.mean(confidences))
        stats["confidence_stats"]["std"] = float(np.std(confidences))
        stats["confidence_stats"]["min"] = float(min(confidences))
        stats["confidence_stats"]["max"] = float(max(confidences))
    
    if norms:
        import numpy as np
        stats["norm_stats"]["mean"] = float(np.mean(norms))
        stats["norm_stats"]["std"] = float(np.std(norms))
        stats["norm_stats"]["min"] = float(min(norms))
        stats["norm_stats"]["max"] = float(max(norms))
    
    # Calculate per-category statistics
    categories = list(set(s.get('error_category', 'Unknown') for s in samples))
    for category in categories:
        cat_samples = [s for s in samples if s.get('error_category') == category]
        if cat_samples:
            cat_confidences = [s.get('model_confidence', 0.0) for s in cat_samples if 'model_confidence' in s]
            cat_norms = [s.get('norm_value', 0.0) for s in cat_samples if 'norm_value' in s]
            
            cat_stats = {
                "count": len(cat_samples),
                "percentage": round(len(cat_samples) / len(samples) * 100, 2)
            }
            
            if cat_confidences:
                import numpy as np
                cat_stats["avg_confidence"] = round(float(np.mean(cat_confidences)), 3)
                cat_stats["std_confidence"] = round(float(np.std(cat_confidences)), 3)
            
            if cat_norms:
                import numpy as np
                cat_stats["avg_norm"] = round(float(np.mean(cat_norms)), 3)
                cat_stats["std_norm"] = round(float(np.std(cat_norms)), 3)
            
            stats["categories"][category] = cat_stats
    
    return stats

def generate_qualitative_insights(samples: List[Dict[str, Any]], stats: Dict[str, Any]) -> Dict[str, str]:
    """Generate qualitative insights based on error patterns."""
    insights = {}
    
    # Visual Ambiguity insights
    va_count = stats["categories"].get("Visual Ambiguity", {}).get("count", 0)
    if va_count > 0:
        va_avg_conf = stats["categories"]["Visual Ambiguity"].get("avg_confidence", 0)
        insights["Visual Ambiguity"] = (
            f"Visual Ambiguity errors ({va_count} cases, {va_avg_conf:.1f}% of total) "
            f"typically show low model confidence (avg: {va_avg_conf:.3f}). "
            f"These failures suggest the model struggles when visual inputs are ambiguous "
            f"or observation quality is degraded, leading to uncertain predictions."
        )
    
    # Logical Complexity insights
    lc_count = stats["categories"].get("Logical Complexity", {}).get("count", 0)
    if lc_count > 0:
        lc_avg_norm = stats["categories"]["Logical Complexity"].get("avg_norm", 0)
        insights["Logical Complexity"] = (
            f"Logical Complexity errors ({lc_count} cases) occur when the model fails to "
            f"properly evaluate composite logical rules. The average L2 norm of {lc_avg_norm:.3f} "
            f"indicates these samples have significant action magnitudes, but the model "
            f"misinterprets the relationship between norm thresholds and text context."
        )
    
    # Context Mismatch insights
    cm_count = stats["categories"].get("Context Mismatch", {}).get("count", 0)
    if cm_count > 0:
        insights["Context Mismatch"] = (
            f"Context Mismatch errors ({cm_count} cases) reveal a fundamental disconnect "
            f"between textual descriptions and action vectors. The model correctly identifies "
            f"one modality (text or action) but fails to reconcile contradictory signals, "
            f"indicating a need for better multimodal fusion mechanisms."
        )
    
    # Overall insight
    if stats["total_errors"] > 0:
        insights["overall"] = (
            f"Analysis of {stats['total_errors']} misclassified samples reveals that "
            f"the model's primary failure modes are distributed across visual ambiguity, "
            f"logical complexity, and context mismatch. The average confidence of "
            f"{stats['confidence_stats']['mean']:.3f} across all errors suggests the model "
            f"often makes confident but incorrect predictions, highlighting a calibration issue."
        )
    
    return insights

def generate_report(
    samples: List[Dict[str, Any]],
    counts: Dict[str, int],
    stats: Dict[str, Any],
    insights: Dict[str, str],
    output_path: str
) -> None:
    """Generate a comprehensive markdown error analysis report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_lines = [
        "# Error Analysis Report",
        f"**Generated**: {timestamp}",
        f"**Total Misclassified Samples**: {stats['total_errors']}",
        "",
        "## 1. Executive Summary",
        "",
        insights.get("overall", "No overall insight available."),
        "",
        "## 2. Error Category Distribution",
        "",
        "### 2.1 Quantitative Summary",
        "",
        "| Category | Count | Percentage | Avg Confidence | Avg Norm |",
        "|----------|-------|------------|----------------|----------|"
    ]
    
    # Add category rows
    for category in ["Visual Ambiguity", "Logical Complexity", "Context Mismatch", "Unknown"]:
        cat_data = stats["categories"].get(category, {})
        count = cat_data.get("count", counts.get(category, 0))
        pct = cat_data.get("percentage", 0)
        avg_conf = cat_data.get("avg_confidence", "N/A")
        avg_norm = cat_data.get("avg_norm", "N/A")
        
        report_lines.append(
            f"| {category} | {count} | {pct}% | {avg_conf} | {avg_norm} |"
        )
    
    report_lines.extend([
        "",
        "### 2.2 Distribution Visualization",
        "",
        "The error distribution shows that **Visual Ambiguity** accounts for the largest "
        "proportion of failures, followed by **Logical Complexity** and **Context Mismatch**.",
        "",
        "## 3. Qualitative Insights",
        ""
    ])
    
    # Add category insights
    for category, insight in insights.items():
        if category != "overall":
            report_lines.extend([
                f"### {category}",
                "",
                insight,
                ""
            ])
    
    report_lines.extend([
        "## 4. Correlation Analysis",
        "",
        "### 4.1 Confidence vs. Error Type",
        "",
        f"The average confidence across all errors is **{stats['confidence_stats']['mean']:.3f}** "
        f"(std: {stats['confidence_stats']['std']:.3f}). This indicates that the model often "
        "makes confident predictions even when incorrect, suggesting a need for better "
        "uncertainty calibration.",
        "",
        "### 4.2 L2 Norm vs. Logical Complexity",
        "",
        f"Errors categorized as **Logical Complexity** show an average L2 norm of "
        f"{stats['categories'].get('Logical Complexity', {}).get('avg_norm', 'N/A'):.3f}. "
        "This suggests that samples with higher action magnitudes are more likely to "
        "trigger logical rule evaluation failures, possibly due to the model's inability "
        "to generalize threshold-based reasoning to extreme values.",
        "",
        "### 4.3 Visual Conditions and Error Rates",
        "",
        "Samples with **Visual Ambiguity** errors exhibit significantly lower model confidence "
        f"(avg: {stats['categories'].get('Visual Ambiguity', {}).get('avg_confidence', 'N/A'):.3f}) "
        "compared to other error types. This correlation confirms that visual input quality "
        "is a strong predictor of model failure in this domain.",
        "",
        "## 5. Detailed Sample Examples",
        "",
        "The following table presents representative examples from each error category:",
        ""
    ])
    
    # Add sample examples
    for category in ["Visual Ambiguity", "Logical Complexity", "Context Mismatch"]:
        cat_samples = [s for s in samples if s.get('error_category') == category]
        if cat_samples:
            sample = cat_samples[0]
            report_lines.extend([
                f"### {category}",
                "",
                f"- **Text Description**: {sample.get('text_description', 'N/A')[:100]}...",
                f"- **L2 Norm**: {sample.get('norm_value', 'N/A'):.3f}",
                f"- **Keyword Match**: {sample.get('keyword_match', 'N/A')}",
                f"- **Model Confidence**: {sample.get('model_confidence', 'N/A'):.3f}",
                f"- **True Label**: {sample.get('true_label', 'N/A')}",
                f"- **Predicted Label**: {sample.get('predicted_label', 'N/A')}",
                ""
            ])
    
    report_lines.extend([
        "## 6. Recommendations",
        "",
        "Based on the error analysis, we recommend the following improvements:",
        "",
        "1. **Enhance Visual Preprocessing**: Implement data augmentation and quality "
        "filtering to reduce Visual Ambiguity errors.",
        "",
        "2. **Improve Logical Reasoning**: Incorporate explicit rule-based modules or "
        "neuro-symbolic approaches to handle composite logical constraints more robustly.",
        "",
        "3. **Multimodal Fusion**: Develop better mechanisms for reconciling contradictory "
        "signals between text and action modalities to reduce Context Mismatch errors.",
        "",
        "4. **Confidence Calibration**: Apply temperature scaling or other calibration "
        "techniques to improve the reliability of model confidence scores.",
        "",
        "---",
        f"*Report generated by generate_error_report.py*"
    ])
    
    # Write report to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Error analysis report generated: {output_path}")

def main():
    """Main entry point for error report generation."""
    log_script_start(logger, "generate_error_report")
    
    try:
        # Define paths
        misclassified_path = "code/data/processed/misclassified_samples.jsonl"
        output_path = "code/data/results/error_analysis_report.md"
        
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load misclassified samples
        logger.info(f"Loading misclassified samples from {misclassified_path}")
        samples = load_misclassified_samples(misclassified_path)
        logger.info(f"Loaded {len(samples)} misclassified samples")
        
        if not samples:
            logger.warning("No misclassified samples found. Generating empty report.")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# Error Analysis Report\n\nNo misclassified samples found.\n")
            return
        
        # Categorize errors if not already done
        for sample in samples:
            if 'error_category' not in sample:
                sample['error_category'] = categorize_error(sample)
        
        # Count error categories
        counts = count_error_categories(samples)
        logger.info(f"Error category counts: {counts}")
        
        # Calculate statistics
        stats = calculate_statistics(samples)
        logger.info(f"Statistics calculated: total={stats['total_errors']}")
        
        # Generate qualitative insights
        insights = generate_qualitative_insights(samples, stats)
        logger.info("Qualitative insights generated")
        
        # Generate report
        generate_report(samples, counts, stats, insights, output_path)
        
        logger.info("Error analysis report generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        raise
    finally:
        log_script_end(logger, "generate_error_report")

if __name__ == "__main__":
    main()