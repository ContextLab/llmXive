import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from config import get_processed_dir, get_figures_dir, get_project_root
from utils.logging import get_logger

logger = get_logger(__name__)


def load_processed_data(data_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load processed participant response data from JSON.
    
    Args:
        data_path: Optional path to the processed data file. If None, uses default.
        
    Returns:
        List of dictionaries containing response data.
    """
    if data_path is None:
        data_path = get_processed_dir() / "participant_responses.json"
        
    if not data_path.exists():
        logger.error(f"Processed data file not found: {data_path}")
        raise FileNotFoundError(f"Processed data file not found: {data_path}")
        
    with open(data_path, 'r') as f:
        return json.load(f)


def calculate_false_memory_rates(
    data: List[Dict[str, Any]], 
    condition_col: str = "condition",
    response_col: str = "response",
    question_type_col: str = "question_type"
) -> Dict[str, Dict[str, float]]:
    """
    Calculate mean false memory rates and confidence intervals by condition.
    
    Args:
        data: List of response dictionaries.
        condition_col: Key for the experimental condition.
        response_col: Key for the binary response (1=affirm, 0=reject).
        question_type_col: Key for question type ('true' or 'false' details).
        
    Returns:
        Dictionary mapping conditions to {'mean': float, 'ci_lower': float, 'ci_upper': float, 'n': int}.
    """
    results = {}
    
    # Group by condition and false-detail questions
    condition_data = {}
    for record in data:
        if record.get(question_type_col) == "false":
            cond = record.get(condition_col, "unknown")
            if cond not in condition_data:
                condition_data[cond] = []
            condition_data[cond].append(record.get(response_col, 0))
    
    # Calculate statistics for each condition
    for cond, responses in condition_data.items():
        if not responses:
            logger.warning(f"No false-detail responses found for condition: {cond}")
            continue
            
        arr = np.array(responses)
        n = len(arr)
        mean = np.mean(arr)
        std = np.std(arr, ddof=1) if n > 1 else 0.0
        
        # 95% Confidence Interval using t-distribution
        if n > 1:
            from scipy import stats as scipy_stats
            conf = 0.95
            dof = n - 1
            t_val = scipy_stats.t.ppf((1 + conf) / 2.0, dof)
            margin = t_val * (std / np.sqrt(n))
            ci_lower = max(0.0, mean - margin)
            ci_upper = min(1.0, mean + margin)
        else:
            ci_lower = mean
            ci_upper = mean
            
        results[cond] = {
            "mean": float(mean),
            "ci_lower": float(ci_lower),
            "ci_upper": float(ci_upper),
            "n": int(n)
        }
        
    return results


def plot_false_memory_rates(
    stats_data: Dict[str, Dict[str, float]],
    output_path: Optional[Path] = None,
    title: str = "False Memory Rates by Visual Detail Condition",
    xlabel: str = "Condition",
    ylabel: str = "Mean False Memory Rate (95% CI)"
) -> Path:
    """
    Generate a bar plot with error bars showing false memory rates.
    
    Args:
        stats_data: Dictionary of statistics from calculate_false_memory_rates.
        output_path: Path to save the figure. If None, uses default.
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        
    Returns:
        Path to the saved figure file.
    """
    if output_path is None:
        output_path = get_figures_dir() / "false_memory_rates.png"
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data for plotting
    conditions = list(stats_data.keys())
    if not conditions:
        raise ValueError("No conditions found in stats_data. Cannot generate plot.")
        
    means = [stats_data[c]["mean"] for c in conditions]
    ci_lower = [stats_data[c]["ci_lower"] for c in conditions]
    ci_upper = [stats_data[c]["ci_upper"] for c in conditions]
    
    # Calculate error bars (asymmetric)
    errors_lower = [m - l for m, l in zip(means, ci_lower)]
    errors_upper = [u - m for u, m in zip(ci_upper, means)]
    errors = [errors_lower, errors_upper]
    
    # Create plot
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid", context="talk")
    
    x_pos = np.arange(len(conditions))
    bars = plt.bar(x_pos, means, yerr=errors, capsize=8, 
                   color=sns.color_palette("muted", len(conditions)),
                   edgecolor='black', alpha=0.8)
    
    plt.xticks(x_pos, conditions, rotation=45, ha='right')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.ylim(0, 1.05)
    
    # Add sample size annotations
    for i, cond in enumerate(conditions):
        n = stats_data[cond]["n"]
        plt.text(i, 0.02, f"n={n}", ha='center', va='bottom', fontsize=10)
        
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Visualization saved to: {output_path}")
    return output_path


def generate_visualization(
    data_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    condition_col: str = "condition",
    response_col: str = "response",
    question_type_col: str = "question_type"
) -> Path:
    """
    Main entry point to generate the false memory visualization.
    
    Args:
        data_path: Path to processed data JSON.
        output_path: Path to save the figure.
        condition_col: Key for condition in data.
        response_col: Key for response in data.
        question_type_col: Key for question type in data.
        
    Returns:
        Path to the generated figure.
    """
    logger.info("Starting false memory visualization generation...")
    
    # Load data
    data = load_processed_data(data_path)
    logger.info(f"Loaded {len(data)} records from {data_path}")
    
    # Calculate statistics
    stats_data = calculate_false_memory_rates(
        data, 
        condition_col=condition_col,
        response_col=response_col,
        question_type_col=question_type_col
    )
    
    if not stats_data:
        raise ValueError("No valid data found to plot. Check input data format.")
        
    logger.info(f"Calculated statistics for {len(stats_data)} conditions: {list(stats_data.keys())}")
    
    # Generate plot
    fig_path = plot_false_memory_rates(stats_data, output_path)
    
    return fig_path


def main():
    """CLI entry point for visualization generation."""
    logger.info("Running visualization generation script...")
    
    try:
        # Use default paths from config
        data_path = get_processed_dir() / "participant_responses.json"
        output_path = get_figures_dir() / "false_memory_rates.png"
        
        fig_path = generate_visualization(data_path=data_path, output_path=output_path)
        
        print(f"SUCCESS: Visualization generated at {fig_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        logger.exception("An error occurred during visualization generation")
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())