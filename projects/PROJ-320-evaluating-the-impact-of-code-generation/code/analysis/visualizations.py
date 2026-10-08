"""
Visualization and Correlation Analysis Module.

Implements correlation analysis between code complexity and review metrics
to control for confounding variables (SC-003, FR-005).

Output: data/processed/correlation_results.json
"""
import os
import sys
import json
import csv
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Attempt to import matplotlib and seaborn for plotting
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for CI
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOT_LIBS = True
except ImportError:
    HAS_PLOT_LIBS = False
    print("Warning: matplotlib/seaborn not installed. Visualization features disabled.")

# Attempt to import scipy for statistical correlation
try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("Warning: scipy not installed. Correlation analysis will fail.")


# --- Utility Functions ---

def apply_publication_style():
    """Apply consistent styling for research-quality plots."""
    if not HAS_PLOT_LIBS:
        return
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.1)
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
    plt.rcParams['axes.linewidth'] = 1.2
    plt.rcParams['xtick.major.width'] = 1.2
    plt.rcParams['ytick.major.width'] = 1.2
    plt.rcParams['pdf.fonttype'] = 42  # Ensure text is editable in PDF
    plt.rcParams['svg.fonttype'] = 'none'


def load_metrics_for_viz(metrics_path: str) -> List[Dict[str, Any]]:
    """
    Load metrics from CSV file.
    
    Args:
        metrics_path: Path to data/processed/prs_metrics.csv
        
    Returns:
        List of dictionaries containing PR metrics.
        
    Raises:
        FileNotFoundError: If the metrics file does not exist.
    """
    if not os.path.exists(metrics_path):
        # Normalize path relative to project root if absolute path logic is needed elsewhere
        # but here we assume the caller passes the correct path.
        # The error message in the execution log showed a missing file.
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    data = []
    with open(metrics_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats/ints
            cleaned_row = {}
            for k, v in row.items():
                if v is None or v == '':
                    cleaned_row[k] = None
                    continue
                try:
                    if k in ['pr_id', 'comment_count', 'review_cycles']:
                        cleaned_row[k] = int(v)
                    elif k in ['time_to_merge_minutes', 'complexity_score']:
                        cleaned_row[k] = float(v)
                    else:
                        cleaned_row[k] = v
                except ValueError:
                    cleaned_row[k] = v
            data.append(cleaned_row)
    
    if not data:
        raise ValueError(f"Metrics file {metrics_path} is empty or has no valid rows.")
        
    return data


def generate_correlation_plot(
    data: List[Dict[str, Any]],
    output_path: str
) -> Dict[str, float]:
    """
    Generate a correlation matrix plot and calculate correlation coefficients.
    
    This function specifically measures the relationship between complexity
    and review metrics to control for confounding variables as required by SC-003.
    
    Args:
        data: List of PR metric dictionaries.
        output_path: Path to save the correlation plot (PNG/PDF).
        
    Returns:
        Dictionary containing correlation coefficients and p-values.
    """
    if not HAS_PLOT_LIBS or not HAS_SCIPY:
        print("Error: Cannot generate correlation plot without matplotlib, seaborn, and scipy.")
        return {}

    # Extract relevant columns
    # We expect 'complexity_score', 'comment_count', 'time_to_merge_minutes', 'source_type'
    complexity = []
    comment_count = []
    time_to_merge = []
    labels = [] # For source type tracking if needed for coloring, but correlation is numeric

    for row in data:
        c_score = row.get('complexity_score')
        c_count = row.get('comment_count')
        t_merge = row.get('time_to_merge_minutes')
        
        if c_score is not None and c_count is not None and t_merge is not None:
            # Filter out extreme outliers if they are NaN or Inf
            if math.isfinite(c_score) and math.isfinite(c_count) and math.isfinite(t_merge):
                complexity.append(c_score)
                comment_count.append(c_count)
                time_to_merge.append(t_merge)
    
    if len(complexity) < 3:
        print("Warning: Insufficient data points for correlation analysis.")
        return {}

    # Calculate Pearson correlations
    # 1. Complexity vs Comment Count
    corr_comments, p_val_comments = stats.pearsonr(complexity, comment_count)
    # 2. Complexity vs Time to Merge
    corr_time, p_val_time = stats.pearsonr(complexity, time_to_merge)
    
    # 3. Comment Count vs Time to Merge (control check)
    corr_ct, p_val_ct = stats.pearsonr(comment_count, time_to_merge)

    results = {
        "complexity_vs_comments": {
            "r": round(corr_comments, 4),
            "p_value": round(p_val_comments, 4)
        },
        "complexity_vs_time_to_merge": {
            "r": round(corr_time, 4),
            "p_value": round(p_val_time, 4)
        },
        "comments_vs_time_to_merge": {
            "r": round(corr_ct, 4),
            "p_value": round(p_val_ct, 4)
        }
    }

    # Generate Plot
    plt.figure(figsize=(10, 8))
    # Prepare dataframe for seaborn
    import pandas as pd
    df = pd.DataFrame({
        'Complexity': complexity,
        'Comment Count': comment_count,
        'Time to Merge (min)': time_to_merge
    })
    
    # Use pairplot or heatmap. Heatmap is cleaner for correlation matrix.
    corr_matrix = df.corr()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, 
                square=True, linewidths=1, cbar_kws={"shrink": 0.8})
    plt.title("Correlation Matrix: Complexity vs Review Metrics")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Correlation plot saved to: {output_path}")
    return results


def run_visualization_pipeline(
    metrics_path: str = "data/processed/prs_metrics.csv",
    output_dir: str = "reports/figures"
) -> Dict[str, Any]:
    """
    Run the full visualization pipeline including boxplots, histograms, and correlation analysis.
    
    Args:
        metrics_path: Path to the metrics CSV.
        output_dir: Directory to save figures.
        
    Returns:
        Dictionary containing all analysis results.
    """
    results = {
        "boxplots": None,
        "histograms": None,
        "correlation": None
    }
    
    # Load data
    data = load_metrics_for_viz(metrics_path)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Correlation Analysis (Primary Task for T035)
    corr_plot_path = os.path.join(output_dir, "correlation_matrix.png")
    corr_results = generate_correlation_plot(data, corr_plot_path)
    results["correlation"] = corr_results
    
    # 2. Boxplots (T031 requirement)
    # Note: This is a simplified implementation for the boxplot requirement.
    # In a full implementation, this would separate by source_type.
    if HAS_PLOT_LIBS:
        apply_publication_style()
        plt.figure(figsize=(12, 6))
        
        # Prepare data for boxplot
        # We need to filter by source_type if available, otherwise just plot distribution
        # Assuming 'source_type' is in the data if it came from labeled dataset
        # But extract_metrics might not have carried it if not joined correctly.
        # Let's assume the data has 'source_type' or we just plot the distribution.
        
        # If source_type exists:
        if 'source_type' in data[0]:
            llm_data = [r['comment_count'] for r in data if r.get('source_type') == 'llm' and r.get('comment_count') is not None]
            human_data = [r['comment_count'] for r in data if r.get('source_type') == 'human' and r.get('comment_count') is not None]
            
            if llm_data and human_data:
                plt.boxplot([llm_data, human_data], labels=['LLM', 'Human'])
                plt.title('Comment Count by Source Type')
                plt.ylabel('Count')
            else:
                # Fallback if no source type separation
                all_counts = [r['comment_count'] for r in data if r.get('comment_count') is not None]
                plt.boxplot([all_counts], labels=['All'])
                plt.title('Comment Count Distribution')
        else:
            # Fallback if no source type
            all_counts = [r['comment_count'] for r in data if r.get('comment_count') is not None]
            plt.boxplot([all_counts], labels=['All'])
            plt.title('Comment Count Distribution')
        
        boxplot_path = os.path.join(output_dir, "boxplots.pdf")
        plt.savefig(boxplot_path, format='pdf', bbox_inches='tight')
        plt.close()
        results["boxplots"] = boxplot_path
        
        # 3. Histograms
        plt.figure(figsize=(12, 6))
        all_times = [r['time_to_merge_minutes'] for r in data if r.get('time_to_merge_minutes') is not None]
        if all_times:
            plt.hist(all_times, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            plt.title('Distribution of Time to Merge')
            plt.xlabel('Minutes')
            plt.ylabel('Frequency')
            hist_path = os.path.join(output_dir, "histograms.pdf")
            plt.savefig(hist_path, format='pdf', bbox_inches='tight')
            plt.close()
            results["histograms"] = hist_path
    
    return results


def main():
    """CLI entry point for visualization and correlation analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate visualizations and correlation analysis.")
    parser.add_argument("--input", type=str, default="data/processed/prs_metrics.csv",
                        help="Path to input metrics CSV (default: data/processed/prs_metrics.csv)")
    parser.add_argument("--output", type=str, default="reports/figures",
                        help="Output directory for figures (default: reports/figures)")
    
    args = parser.parse_args()
    
    print(f"Starting visualization pipeline with input: {args.input}")
    
    try:
        results = run_visualization_pipeline(
            metrics_path=args.input,
            output_dir=args.output
        )
        
        # Save correlation results to JSON as required by T035
        # The task requires output: data/processed/correlation_results.json
        json_output_path = "data/processed/correlation_results.json"
        os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
        
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(results.get('correlation', {}), f, indent=2)
        
        print(f"Correlation results saved to: {json_output_path}")
        print(f"Boxplots saved to: {results.get('boxplots', 'N/A')}")
        print(f"Histograms saved to: {results.get('histograms', 'N/A')}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during visualization pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()