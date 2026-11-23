import json
import os
import sys
import logging
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import logging utilities from the project's utility module
try:
    from utils.logger import get_logger, log_script_start, log_script_end
except ImportError:
    # Fallback for direct execution or missing utils path setup
    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def log_script_start(name):
        logging.info(f"Starting script: {name}")

    def log_script_end(name):
        logging.info(f"Finished script: {name}")

def load_misclassified_samples(file_path: str) -> List[Dict[str, Any]]:
    """
    Load misclassified samples from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file containing misclassified samples.
        
    Returns:
        List of dictionaries representing the samples.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    logger = get_logger(__name__)
    logger.info(f"Loading misclassified samples from {file_path}")
    
    samples = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                sample = json.loads(line)
                samples.append(sample)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON at line {line_num}: {e}")
                raise
    
    logger.info(f"Loaded {len(samples)} misclassified samples")
    return samples

def categorize_error(sample: Dict[str, Any]) -> str:
    """
    Categorize a misclassified sample into one of three failure modes:
    1. Visual Ambiguity
    2. Logical Complexity
    3. Context Mismatch
    
    Heuristics:
    - Visual Ambiguity: model confidence < 0.6 OR observation data is missing/low quality.
    - Logical Complexity: (norm > 0.5 AND keyword_match == False) OR (norm <= 0.5 AND keyword_match == True).
    - Context Mismatch: text_description contains "Safety Constraint" AND (actions vector is zero OR contradicts text).
    
    Args:
        sample: A dictionary representing a misclassified sample.
        
    Returns:
        A string indicating the error category.
    """
    # Extract relevant fields with defaults
    model_confidence = sample.get('model confidence', 1.0)
    norm_value = sample.get('norm_value', 0.0)
    keyword_match = sample.get('keyword_match', False)
    text_description = sample.get('text_description', "")
    actions = sample.get('actions', [])
    
    # Heuristic 1: Visual Ambiguity
    # Check if confidence is low or observation data is missing/low quality
    # Assuming 'observation' field might exist; if missing, treat as low quality
    has_observation = 'observation' in sample and sample['observation'] is not None
    # Simple check for "low quality" could be checking if observation is empty or very small if it's a list
    observation_quality_ok = True
    if has_observation:
        obs = sample['observation']
        if isinstance(obs, list) and len(obs) == 0:
            observation_quality_ok = False
        # Add more specific quality checks if needed, e.g., variance, etc.
    
    if model_confidence < 0.6 or not observation_quality_ok:
        return "Visual Ambiguity"
    
    # Heuristic 2: Logical Complexity
    # (norm > 0.5 AND keyword_match == False) OR (norm <= 0.5 AND keyword_match == True)
    # This implies a contradiction between the vector norm and the text keyword presence
    logical_complexity = (norm_value > 0.5 and not keyword_match) or (norm_value <= 0.5 and keyword_match)
    if logical_complexity:
        return "Logical Complexity"
    
    # Heuristic 3: Context Mismatch
    # text_description contains "Safety Constraint" AND (actions vector is zero OR contradicts text)
    contains_safety_constraint = "Safety Constraint" in text_description
    is_actions_zero = False
    if actions:
        # Check if all elements in actions are effectively zero
        is_actions_zero = all(abs(float(x)) < 1e-6 for x in actions)
    
    # "Contradicts text" is harder to define programmatically without NLP.
    # For this implementation, we will consider it a mismatch if the safety constraint is mentioned
    # but the actions are zero (implying no action taken despite a constraint) or if the norm is very low
    # while the text suggests a constraint violation (which would imply high norm).
    # However, the prompt specifically says: "text_description contains 'Safety Constraint' AND actions vector is zero or contradicts the text".
    # We'll interpret "contradicts the text" loosely here as: if safety constraint is present,
    # but the norm (which drives the violation label) is low, it might be a mismatch in expectation.
    # But the strongest signal is "actions vector is zero".
    
    if contains_safety_constraint and (is_actions_zero or (len(actions) > 0 and all(abs(float(x)) < 1e-6 for x in actions))):
        return "Context Mismatch"
    
    # Default category if none of the above match (should be rare for misclassified)
    return "Unknown"

def analyze_errors(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the list of misclassified samples and categorize them.
    
    Args:
        samples: List of misclassified sample dictionaries.
        
    Returns:
        A dictionary containing the categorized errors and summary statistics.
    """
    logger = get_logger(__name__)
    
    categorized_samples = {
        "Visual Ambiguity": [],
        "Logical Complexity": [],
        "Context Mismatch": [],
        "Unknown": []
    }
    
    for sample in samples:
        category = categorize_error(sample)
        categorized_samples[category].append(sample)
    
    summary = {
        "total_samples": len(samples),
        "category_counts": {k: len(v) for k, v in categorized_samples.items()},
        "category_percentages": {
            k: (len(v) / len(samples) * 100) if len(samples) > 0 else 0
            for k, v in categorized_samples.items()
        }
    }
    
    logger.info(f"Analysis complete. Summary: {summary}")
    return {
        "categorized_samples": categorized_samples,
        "summary": summary
    }

def generate_report(analysis_results: Dict[str, Any], output_path: str) -> None:
    """
    Generate a markdown report from the analysis results.
    
    Args:
        analysis_results: The dictionary returned by analyze_errors.
        output_path: Path to save the markdown report.
    """
    logger = get_logger(__name__)
    logger.info(f"Generating report at {output_path}")
    
    summary = analysis_results['summary']
    categorized_samples = analysis_results['categorized_samples']
    
    report_lines = [
        "# Error Analysis Report",
        "",
        "## Summary",
        f"- Total Misclassified Samples: {summary['total_samples']}",
        ""
    ]
    
    report_lines.append("### Category Distribution")
    report_lines.append("| Category | Count | Percentage |")
    report_lines.append("|---|---|---|")
    for cat, count in summary['category_counts'].items():
        pct = summary['category_percentages'][cat]
        report_lines.append(f"| {cat} | {count} | {pct:.2f}% |")
    report_lines.append("")
    
    report_lines.append("## Detailed Analysis by Category")
    report_lines.append("")
    
    for category, samples in categorized_samples.items():
        if not samples:
            continue
        
        report_lines.append(f"### {category}")
        report_lines.append(f"**Count**: {len(samples)}")
        report_lines.append("")
        report_lines.append("#### Sample Details")
        report_lines.append("| ID | Confidence | Norm Value | Keyword Match | Text Description |")
        report_lines.append("|---|---|---|---|---|")
        
        for i, sample in enumerate(samples[:5]): # Limit to first 5 for brevity
            sample_id = sample.get('id', f"sample_{i}")
            conf = sample.get('model confidence', 'N/A')
            norm = sample.get('norm_value', 'N/A')
            kw = sample.get('keyword_match', 'N/A')
            text = sample.get('text_description', '')[:50] + "..." if len(sample.get('text_description', '')) > 50 else sample.get('text_description', '')
            report_lines.append(f"| {sample_id} | {conf} | {norm} | {kw} | {text} |")
        report_lines.append("")
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Report generated successfully at {output_path}")

def generate_visualizations(analysis_results: Dict[str, Any], output_path: str) -> None:
    """
    Generate a scatter plot of error rate vs input feature magnitude, grouped by failure mode.
    
    Args:
        analysis_results: The dictionary returned by analyze_errors.
        output_path: Path to save the visualization image.
    """
    logger = get_logger(__name__)
    logger.info(f"Generating visualization at {output_path}")
    
    categorized_samples = analysis_results['categorized_samples']
    total_samples = analysis_results['summary']['total_samples']
    
    # Prepare data for plotting
    categories = ["Visual Ambiguity", "Logical Complexity", "Context Mismatch"]
    colors = ['red', 'blue', 'green']
    x_data = []
    y_data = []
    labels = []
    
    # We need to calculate error rate per category.
    # Since these ARE misclassified samples, the "error rate" in this context
    # might be interpreted as the proportion of the total misclassified set that falls into this category,
    # or we could plot the norm_value (magnitude) against the count/proportion.
    # The task asks for: X-axis = input feature magnitude (norm_value), Y-axis = error rate (1 - accuracy).
    # Since we are looking at misclassified samples, "accuracy" for these is 0.
    # A more meaningful interpretation for this specific plot on misclassified data:
    # X-axis: Average Norm Value for the category.
    # Y-axis: Percentage of total misclassified samples in this category (representing the "error contribution").
    
    category_stats = []
    for cat in categories:
        samples = categorized_samples.get(cat, [])
        if samples:
            norms = [s.get('norm_value', 0) for s in samples]
            avg_norm = np.mean(norms)
            count = len(samples)
            error_contribution = (count / total_samples) if total_samples > 0 else 0
            category_stats.append((avg_norm, error_contribution, cat))
        else:
            category_stats.append((0, 0, cat))
    
    # Sort by norm value for better visualization
    category_stats.sort(key=lambda x: x[0])
    
    x_vals = [stat[0] for stat in category_stats]
    y_vals = [stat[1] for stat in category_stats]
    cat_labels = [stat[2] for stat in category_stats]
    
    plt.figure(figsize=(10, 6))
    plt.scatter(x_vals, y_vals, c=colors[:len(x_vals)], s=100, alpha=0.7, edgecolors='k')
    
    for i, txt in enumerate(cat_labels):
        plt.annotate(txt, (x_vals[i], y_vals[i]), xytext=(5, 5), textcoords='offset points')
    
    plt.xlabel('Average Input Feature Magnitude (L2 Norm)')
    plt.ylabel('Error Contribution (Proportion of Misclassified Samples)')
    plt.title('Error Analysis: Feature Magnitude vs Error Contribution by Category')
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Visualization saved to {output_path}")

def main():
    """
    Main entry point for the error analysis script.
    """
    logger = get_logger(__name__)
    log_script_start("analyze_errors")
    
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent
    input_file = base_dir / "data" / "processed" / "misclassified_samples.jsonl"
    report_output = base_dir / "data" / "results" / "error_analysis_report.md"
    viz_output = base_dir / "data" / "results" / "error_visualizations.png"
    
    # Ensure output directories exist
    report_output.parent.mkdir(parents=True, exist_ok=True)
    viz_output.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T016e (extract_errors.py) has been run successfully.")
        sys.exit(1)
    
    try:
        # Load data
        samples = load_misclassified_samples(str(input_file))
        
        if not samples:
            logger.warning("No misclassified samples found. Generating empty report.")
            # Still generate empty structures
            analysis_results = {
                "categorized_samples": {"Visual Ambiguity": [], "Logical Complexity": [], "Context Mismatch": [], "Unknown": []},
                "summary": {"total_samples": 0, "category_counts": {}, "category_percentages": {}}
            }
        else:
            # Analyze
            analysis_results = analyze_errors(samples)
        
        # Generate Report
        generate_report(analysis_results, str(report_output))
        
        # Generate Visualizations
        generate_visualizations(analysis_results, str(viz_output))
        
        logger.info("Error analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        sys.exit(1)
    finally:
        log_script_end("analyze_errors")

if __name__ == "__main__":
    main()