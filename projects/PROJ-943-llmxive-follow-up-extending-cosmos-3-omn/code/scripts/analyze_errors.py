import json
import os
import sys
import logging
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path for imports if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger, log_script_start, log_script_end

logger = get_logger(__name__)

def load_misclassified_samples(filepath: str) -> List[Dict[str, Any]]:
    """Load misclassified samples from a JSONL file."""
    samples = []
    logger.info(f"Loading misclassified samples from {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                sample = json.loads(line)
                samples.append(sample)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse line {line_num}: {e}")
                raise
    logger.info(f"Loaded {len(samples)} misclassified samples")
    return samples

def categorize_error(sample: Dict[str, Any]) -> str:
    """
    Categorize an error into one of three failure modes:
    'visual ambiguity', 'logical complexity', or 'context mismatch'.
    
    This is a heuristic implementation based on available metadata.
    In a real scenario, this would use a classifier or more robust rules.
    """
    # Heuristic: Check for specific keywords in text_description or error_context
    text_desc = sample.get('text_description', '').lower()
    error_context = sample.get('error_context', '').lower()
    
    if 'ambiguous' in text_desc or 'unclear' in text_desc or 'blur' in text_desc:
        return 'visual ambiguity'
    elif 'complex' in text_desc or 'multi-step' in text_desc or 'nested' in text_desc:
        return 'logical complexity'
    elif 'mismatch' in text_desc or 'unexpected' in text_desc or 'context' in error_context:
        return 'context mismatch'
    else:
        # Default fallback if heuristic fails to categorize
        return 'unknown'

def analyze_errors(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze misclassified samples to count error categories and calculate statistics."""
    categories = {}
    for sample in samples:
        cat = categorize_error(sample)
        categories[cat] = categories.get(cat, 0) + 1
    
    total = len(samples)
    stats = {cat: count / total for cat, count in categories.items()}
    
    return {
        'counts': categories,
        'percentages': stats,
        'total_samples': total
    }

def generate_report(stats: Dict[str, Any], output_path: str) -> None:
    """Generate a markdown report of the error analysis."""
    report_lines = [
        "# Error Analysis Report",
        "",
        f"## Summary",
        f"Total misclassified samples analyzed: {stats['total_samples']}",
        "",
        "## Error Category Distribution",
        ""
    ]
    
    for cat, pct in stats['percentages'].items():
        count = stats['counts'][cat]
        report_lines.append(f"- **{cat}**: {count} ({pct*100:.1f}%)")
    
    report_lines.append("")
    report_lines.append("## Qualitative Insights")
    report_lines.append("")
    report_lines.append("The error distribution suggests that the model struggles most with:")
    if stats['percentages']:
        top_cat = max(stats['percentages'], key=stats['percentages'].get)
        report_lines.append(f"1. **{top_cat}** - indicating a need for better handling of these scenarios.")
    
    report_content = "\n".join(report_lines)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Error analysis report saved to {output_path}")

def generate_visualizations(samples: List[Dict[str, Any]], output_path: str) -> None:
    """
    Visualize correlations between input features and failure types.
    Creates a scatter plot of error rate vs input feature magnitude (L2 norm).
    """
    if not samples:
        logger.warning("No samples to visualize.")
        # Create an empty plot to satisfy the file requirement
        plt.figure(figsize=(10, 6))
        plt.title("No Data Available")
        plt.text(0.5, 0.5, 'No misclassified samples found', ha='center')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return

    # Extract features for plotting
    # We will use the L2 norm of the action vector as the "feature magnitude"
    # and group by error category to show distribution/correlation
    
    categories = ['visual ambiguity', 'logical complexity', 'context mismatch']
    colors = {'visual ambiguity': 'red', 'logical complexity': 'blue', 'context mismatch': 'green'}
    
    plt.figure(figsize=(10, 6))
    
    for cat in categories:
        cat_samples = [s for s in samples if categorize_error(s) == cat]
        if not cat_samples:
            continue
        
        # Calculate L2 norm of the first 3 dimensions of actions for each sample
        norms = []
        for s in cat_samples:
            actions = s.get('actions', [])
            if len(actions) >= 3:
                # Compute L2 norm of first 3 dimensions
                norm = np.sqrt(sum(x**2 for x in actions[:3]))
                norms.append(norm)
            else:
                # Fallback for short vectors
                norm = np.sqrt(sum(x**2 for x in actions)) if actions else 0.0
                norms.append(norm)
        
        # We need a y-value for "error rate". Since these are ALL misclassified,
        # we can plot the "magnitude" against an arbitrary index or use the magnitude
        # itself to show distribution. The task asks for "error rate vs input feature magnitude".
        # Since we only have errors, we can plot the magnitude distribution per category.
        # To simulate "error rate" in a single point per category, we can use the count.
        # However, a scatter plot implies x,y pairs. Let's plot:
        # X: L2 Norm (feature magnitude)
        # Y: A jittered value representing the sample's presence in the error set (or normalized count if aggregating)
        # Better interpretation: Plot the magnitude of the feature for each error, colored by category.
        # This shows if certain magnitudes correlate with specific error types.
        
        y_vals = [i for i in range(len(norms))] # Just an index to scatter
        
        plt.scatter(norms, y_vals, label=cat, color=colors[cat], alpha=0.6, s=50)
    
    plt.xlabel("L2 Norm of Action Vector (First 3 Dimensions)")
    plt.ylabel("Sample Index (Error Instance)")
    plt.title("Correlation: Input Feature Magnitude vs Failure Type")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Error visualizations saved to {output_path}")

def main():
    """Main entry point for the error analysis script."""
    log_script_start("analyze_errors")
    
    # Define paths
    input_path = "data/processed/misclassified_samples.jsonl"
    report_path = "data/results/error_analysis_report.md"
    viz_path = "data/results/error_visualizations.png"
    
    # Check if input exists
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T019 (extract_errors) has run successfully.")
        sys.exit(1)
    
    try:
        # Load data
        samples = load_misclassified_samples(input_path)
        
        # Analyze
        stats = analyze_errors(samples)
        
        # Generate Report
        generate_report(stats, report_path)
        
        # Generate Visualizations
        generate_visualizations(samples, viz_path)
        
        logger.info("Error analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise
    finally:
        log_script_end("analyze_errors")

if __name__ == "__main__":
    main()