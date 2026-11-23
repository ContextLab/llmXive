"""
T021: Generate scatter plot of error rate vs input feature magnitude grouped by failure mode.

Dependencies:
- T018: analyze_errors.py (provides categorize_error and the misclassified_samples.jsonl)

Output:
- code/data/results/error_visualizations.png
"""
import json
import os
import sys
import logging
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.analyze_errors import load_misclassified_samples, categorize_error
from utils.logger import get_logger, log_script_start, log_script_end

logger = get_logger(__name__)

def load_and_categorize_data(input_path: Path) -> list:
    """Load misclassified samples and ensure each has a 'failure_mode' field."""
    samples = load_misclassified_samples(input_path)
    
    if not samples:
        logger.warning("No misclassified samples found. Generating an empty plot.")
        return []
    
    processed_samples = []
    for sample in samples:
        # Ensure the sample has the necessary fields for categorization if not already present
        # The analyze_errors script should have added 'failure_mode', but we re-categorize to be safe
        # or to ensure consistency if the input file is from a previous run without the field.
        if 'failure_mode' not in sample:
            # Re-run categorization logic locally or assume the file is correct.
            # Since T018 is a dependency, we assume the file is correct, but we add the field if missing.
            # To be robust, we call the categorize_error function if we have the raw data.
            # However, load_misclassified_samples returns the processed dict.
            # If the field is missing, we try to infer or default.
            # For safety, we'll re-categorize if the input format matches the raw output of extract_errors.
            # But T018 output is expected to have 'failure_mode'.
            # Let's assume if it's missing, we try to categorize based on available fields.
            try:
                mode = categorize_error(sample)
                sample['failure_mode'] = mode
            except Exception as e:
                logger.warning(f"Could not categorize sample: {e}")
                sample['failure_mode'] = "Unknown"
        
        processed_samples.append(sample)
    
    return processed_samples

def calculate_error_rates_by_mode(samples: list) -> dict:
    """
    Calculate error rate (1 - accuracy) per failure mode.
    Since these are ALL misclassified samples, the 'error' is 1.0 for each.
    However, the task asks for "error rate (1 - accuracy)" grouped by failure mode.
    If we interpret this as the density of errors in that category relative to the total errors,
    we might just plot the count or the proportion.
    
    Re-reading the task: "Y-axis = error rate (1 - accuracy), grouped by failure mode."
    If the dataset used for the plot is ONLY the misclassified samples (from T018),
    then the "error rate" for every single point is 1.0.
    This would result in a horizontal line at y=1.0, which is not a useful scatter plot.
    
    Alternative interpretation:
    The task might imply we need to calculate the error rate *of that category* 
    relative to the TOTAL samples in that category (denominator).
    But we only have misclassified samples here.
    
    Let's look at the dependency: T018 loads `misclassified_samples.jsonl`.
    If we strictly follow the dependency, we only have errors.
    
    However, to make a meaningful "scatter plot" of "error rate", we typically need
    the total count per bin or per mode.
    
    Perhaps the task implies:
    1. Bin the X-axis (norm_value) into intervals.
    2. For each bin, calculate the error rate (errors / total in bin).
    3. But we only have errors.
    
    Let's reconsider the standard interpretation in such research contexts:
    Often, "Error Rate vs Feature" plots show the proportion of errors in bins of the feature.
    If we only have the error samples, we cannot compute the rate (numerator known, denominator unknown).
    
    UNLESS: The task expects us to load the *unified dataset* (from T010) and the *predictions* (from T016b)
    to compute the true error rate per bin/mode.
    But the dependency says "DEPENDENCY: T018". T018 produces `misclassified_samples.jsonl`.
    
    If the task strictly requires using T018's output, and T018 only has errors,
    then "error rate" might be a misnomer for "density" or "count" in the plot,
    OR the task implies we should compute the error rate of the *categories* themselves
    (which is 100% for misclassified samples).
    
    Let's assume the user wants to visualize the *distribution* of errors (which are all rate=1)
    across the X-axis, perhaps jittered or as a count-based heatmap, OR
    the task expects us to load the full dataset to compute the actual rate.
    
    Given the strict dependency on T018, I will assume the "error rate" for the plot
    is effectively the density of errors, or simply 1.0 for all points (which is trivial).
    However, to make a "scatter plot" that looks like a research artifact:
    I will bin the `norm_value` (X-axis).
    For each bin, I will calculate the count of errors.
    But the Y-axis is "error rate".
    
    Let's try a different approach that is common in such papers:
    We plot the *average* error rate for samples in that norm bin.
    To do this, we NEED the full dataset (or at least the predictions for the full dataset).
    The task description says "DEPENDENCY: T018".
    Maybe T018's output is used to *filter* or *annotate*, but we need the full context?
    
    Actually, looking at T016b: "Output `code/data/results/raw_predictions.jsonl`".
    This file contains `true_label` and `predicted_label` for EVERY sample.
    T018 loads `misclassified_samples.jsonl` which is a subset.
    
    If I strictly follow "DEPENDENCY: T018", I only have the errors.
    If I only have errors, I cannot calculate a rate (0 < rate <= 1) unless I assume the denominator.
    
    Let's assume the task implies: "Plot the error rate (calculated from the full predictions) 
    but group/annotate by the failure modes identified in T018".
    This requires loading `raw_predictions.jsonl` (from T016b) and `misclassified_samples.jsonl` (from T018).
    
    I will implement it this way:
    1. Load `code/data/results/raw_predictions.jsonl` (T016b output).
    2. Load `code/data/results/misclassified_samples.jsonl` (T018 output) to get failure modes.
    3. Merge them (or map failure modes to the full dataset where applicable).
    4. Bin by `norm_value`.
    5. Calculate error rate per bin.
    6. Plot.
    
    If `raw_predictions.jsonl` is missing, we fallback to plotting the density of errors (count) 
    and label the Y-axis "Error Density (Count)" or similar, but the prompt says "error rate".
    I will try to load the raw predictions. If missing, I will raise an error or plot 1.0.
    Given the strict "fail loudly" rule, I will check for the existence of the raw predictions.
    """
    
    raw_predictions_path = Path("code/data/results/raw_predictions.jsonl")
    if not raw_predictions_path.exists():
        logger.error(f"Required file {raw_predictions_path} not found. Cannot calculate error rate.")
        # Fallback: If we can't calculate rate, we plot the distribution of errors (count)
        # and label it appropriately, or fail.
        # Let's try to proceed with the assumption that the user might have run T016b.
        # If not, we can't compute rate. I will raise a clear error.
        raise FileNotFoundError(f"Cannot compute error rate without {raw_predictions_path}. "
                                f"Please ensure T016b has been executed.")

    with open(raw_predictions_path, 'r') as f:
        all_predictions = [json.loads(line) for line in f]
    
    # Create a mapping of sample_id (or index) to failure_mode if it's a misclassified sample
    # We need a unique key. The raw_predictions might have 'sample_id' or we use index.
    # Let's assume 'sample_id' exists or we use the index.
    # T016b output: `predicted_label`, `true_label`, `norm_value`, ...
    # T018 output: `misclassified_samples.jsonl` with same fields + `failure_mode`.
    
    # Build a map of (norm_value, text_description?) -> failure_mode?
    # Better: If the samples have a unique ID, use that. If not, we might have to match by features.
    # Let's assume they have a 'sample_id' or we can match by (norm_value, text_description, predicted_label).
    # To be safe, let's assume the `misclassified_samples` are a subset of `raw_predictions`.
    # We can iterate through raw_predictions and check if they are in the misclassified list.
    # But matching by all fields is risky.
    # Let's assume the `misclassified_samples` file has the same structure as the raw predictions
    # plus the `failure_mode`.
    
    # Strategy:
    # 1. Create a set of "error keys" from misclassified_samples.
    #    Key = (norm_value, text_description) - assuming these are unique enough or combined with ID.
    #    If no ID, we might have duplicates.
    #    Let's try to use `sample_id` if available, else (norm_value, text_description).
    
    error_map = {} # key -> failure_mode
    
    for sample in samples:
        # Try to find a unique key
        if 'sample_id' in sample:
            key = sample['sample_id']
        else:
            # Fallback to a tuple of features
            key = (sample.get('norm_value'), sample.get('text_description', ''))
        
        error_map[key] = sample['failure_mode']
    
    # Now process all predictions
    binned_data = {} # bin_start -> { 'errors': count, 'total': count, 'modes': {mode: count} }
    
    # Define bins for norm_value
    all_norms = [p.get('norm_value', 0) for p in all_predictions]
    if not all_norms:
        logger.warning("No norm values found in predictions.")
        return {}
    
    min_norm = min(all_norms)
    max_norm = max(all_norms)
    
    # Create bins
    num_bins = 20
    if max_norm == min_norm:
        bins = [min_norm - 0.1, min_norm + 0.1]
    else:
        bins = np.linspace(min_norm, max_norm, num_bins + 1)
    
    for i in range(len(bins) - 1):
        bin_start = bins[i]
        bin_end = bins[i+1]
        binned_data[bin_start] = {'errors': 0, 'total': 0, 'mode_counts': {}}
    
    for p in all_predictions:
        norm = p.get('norm_value', 0)
        # Find bin
        # np.digitize returns index starting at 1
        idx = np.digitize(norm, bins) - 1
        if idx < 0: idx = 0
        if idx >= len(bins) - 1: idx = len(bins) - 2
        
        bin_start = bins[idx]
        binned_data[bin_start]['total'] += 1
        
        # Check if error
        is_error = (p.get('predicted_label') != p.get('true_label'))
        if is_error:
            binned_data[bin_start]['errors'] += 1
            
            # Determine failure mode
            # Construct key
            if 'sample_id' in p:
                key = p['sample_id']
            else:
                key = (p.get('norm_value'), p.get('text_description', ''))
            
            if key in error_map:
                mode = error_map[key]
            else:
                # Should not happen if logic is correct, but fallback
                mode = categorize_error(p) # Re-categorize if needed
            
            binned_data[bin_start]['mode_counts'][mode] = binned_data[bin_start]['mode_counts'].get(mode, 0) + 1
    
    # Calculate error rates and prepare for plotting
    plot_data = []
    for bin_start in sorted(binned_data.keys()):
        data = binned_data[bin_start]
        if data['total'] > 0:
            error_rate = data['errors'] / data['total']
        else:
            error_rate = 0.0
        
        plot_data.append({
            'bin_start': bin_start,
            'bin_end': bins[sorted(binned_data.keys()).index(bin_start) + 1],
            'error_rate': error_rate,
            'mode_counts': data['mode_counts'],
            'total': data['total'],
            'errors': data['errors']
        })
    
    return plot_data

def generate_scatter_plot(plot_data: list, output_path: Path):
    """Generate the scatter plot grouped by failure mode."""
    if not plot_data:
        logger.warning("No data to plot. Creating an empty plot with a message.")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No data available for plotting", ha='center', va='center', transform=ax.transAxes)
        ax.set_xlabel("Input Feature Magnitude (norm_value)")
        ax.set_ylabel("Error Rate (1 - Accuracy)")
        ax.set_title("Error Analysis: Error Rate vs Feature Magnitude")
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return

    # Prepare data for scatter plot
    # We will plot a point for each bin.
    # X = bin center
    # Y = error rate
    # Color/Marker = dominant failure mode or size = count?
    # The task says "grouped by failure mode".
    # We can use different colors for different modes.
    # But we have multiple modes per bin.
    # Let's plot the overall error rate as a line, and overlay markers for the dominant mode?
    # Or, plot separate series for each mode?
    # "Scatter plot... grouped by failure mode" usually means:
    # X = norm, Y = error_rate, Color = mode.
    # But error_rate is per bin.
    # Maybe we plot the error rate of samples *in that mode*?
    # But we don't have the total count per mode per bin easily without more complex logic.
    
    # Let's interpret "grouped by failure mode" as:
    # Calculate error rate for each mode separately in each bin?
    # We have `mode_counts` (errors per mode) and `total` (total samples).
    # We don't have `total per mode` in the bin.
    # So we can't calculate "error rate for mode X" without knowing "total samples of mode X".
    # We only know "total samples" and "errors of mode X".
    
    # Alternative: Plot the error rate (total errors / total samples) as a line.
    # And use markers to indicate the dominant failure mode in that bin.
    # Or, plot the proportion of errors that are of a certain mode.
    
    # Let's try:
    # X = bin center
    # Y = overall error rate
    # Color = Dominant failure mode in that bin (if errors > 0)
    # Size = number of errors (log scale)
    
    modes = set()
    for item in plot_data:
        for mode in item['mode_counts'].keys():
            modes.add(mode)
    
    # Map modes to colors
    mode_colors = plt.cm.tab10(np.linspace(0, 1, len(modes)))
    mode_color_map = {mode: color for mode, color in zip(modes, mode_colors)}
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    x_vals = []
    y_vals = []
    c_vals = []
    s_vals = []
    mode_labels = []
    
    for item in plot_data:
        if item['total'] == 0:
            continue
        
        center = (item['bin_start'] + item['bin_end']) / 2
        error_rate = item['error_rate']
        
        x_vals.append(center)
        y_vals.append(error_rate)
        
        # Determine dominant mode
        if item['errors'] > 0:
            dominant_mode = max(item['mode_counts'], key=item['mode_counts'].get)
            color = mode_color_map.get(dominant_mode, 'gray')
            mode_labels.append(dominant_mode)
            s_vals.append(np.log1p(item['errors']) * 50 + 50) # Scale size
        else:
            color = 'lightgray'
            mode_labels.append('No Error')
            s_vals.append(50)
        
        c_vals.append(color)
    
    # Plot
    scatter = ax.scatter(x_vals, y_vals, c=c_vals, s=s_vals, alpha=0.7, edgecolors='w', linewidth=0.5)
    
    # Create custom legend
    from matplotlib.lines import Line2D
    legend_elements = [Line2D([0], [0], marker='o', color='w', label=mode,
                              markerfacecolor=mode_color_map[mode], markersize=10)
                       for mode in modes]
    legend_elements.append(Line2D([0], [0], marker='o', color='w', label='No Error',
                                  markerfacecolor='lightgray', markersize=10))
    
    ax.set_xlabel("Input Feature Magnitude (norm_value)", fontsize=12)
    ax.set_ylabel("Error Rate (1 - Accuracy)", fontsize=12)
    ax.set_title("Error Rate vs Feature Magnitude (Grouped by Dominant Failure Mode)", fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Add colorbar or legend?
    # Since we have categorical colors, a legend is better.
    # But if there are many modes, it gets crowded.
    # Let's use a legend for the modes.
    ax.legend(handles=legend_elements, title="Dominant Failure Mode", loc='best')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Scatter plot saved to {output_path}")

def main():
    log_script_start(logger, "T021: Generate Error Visualizations")
    
    input_path = Path("code/data/processed/misclassified_samples.jsonl")
    output_path = Path("code/data/results/error_visualizations.png")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        logger.error(f"Input file {input_path} not found. T018 must be completed first.")
        sys.exit(1)
    
    try:
        samples = load_and_categorize_data(input_path)
        plot_data = calculate_error_rates_by_mode(samples)
        generate_scatter_plot(plot_data, output_path)
        logger.info("T021 completed successfully.")
    except Exception as e:
        logger.error(f"Error during T021 execution: {e}", exc_info=True)
        sys.exit(1)
    finally:
        log_script_end(logger)

if __name__ == "__main__":
    main()