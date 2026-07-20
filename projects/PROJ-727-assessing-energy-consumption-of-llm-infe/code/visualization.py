import os
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import logging
import sys
from pathlib import Path
from code.config import DATA_PROCESSED_DIR, MODEL_IDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def load_data(filepath):
    """
    Load data from a CSV file.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded data from {filepath}: {len(df)} rows")
    return df

def calculate_energy_per_token_joules(df):
    """
    Calculate Energy per Token in Joules.
    Formula: energy_kwh * 3,600,000 / tokens_generated
    """
    # Filter out rows with 0 tokens or null energy to avoid division by zero or errors
    valid_df = df[(df['tokens_generated'] > 0) & (df['energy_kwh'].notna())]
    if valid_df.empty:
        logger.warning("No valid rows found for energy per token calculation.")
        return pd.DataFrame()
    
    valid_df = valid_df.copy()
    valid_df['energy_per_token_joules'] = (valid_df['energy_kwh'] * 3_600_000) / valid_df['tokens_generated']
    return valid_df

def plot_energy_bar(df, output_path):
    """
    Generate Bar Plot: Y=Energy per Token (Joules), X=Model ID.
    Includes error bars (std dev), legend, title, and axis labels.
    """
    if df.empty:
        raise ValueError("Input dataframe is empty. Cannot generate plot.")
    
    # Calculate mean and std per model
    stats = df.groupby('model_id')['energy_per_token_joules'].agg(['mean', 'std']).reset_index()
    stats.columns = ['model_id', 'mean_energy', 'std_energy']
    
    # Ensure std is not None (replace with 0 if NaN)
    stats['std_energy'] = stats['std_energy'].fillna(0)
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(stats['model_id'], stats['mean_energy'], yerr=stats['std_energy'], 
                   capsize=5, color=['#1f77b4', '#ff7f0e', '#2ca02c'], 
                   edgecolor='black', alpha=0.8)
    
    plt.title('Energy Consumption per Token by Model', fontsize=14, fontweight='bold')
    plt.xlabel('Model ID', fontsize=12)
    plt.ylabel('Energy per Token (Joules)', fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add legend if multiple models or just to label the metric
    plt.legend(['Energy per Token (Mean ± Std Dev)'], loc='upper right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Bar plot saved to {output_path}")

def plot_tradeoff_scatter(df, output_path):
    """
    Generate Scatter Plot: Y=Energy per Correct Solution, X=Pass@1 Accuracy.
    
    Definitions:
    - Energy per Correct Solution = Total Energy for Model / Count of Passed Problems
    - Pass@1 Accuracy = Count of Passed Problems / Total Problems
    
    This plot will contain one point per model.
    """
    if df.empty:
        raise ValueError("Input dataframe is empty. Cannot generate plot.")
    
    # Ensure we have necessary columns
    required_cols = ['model_id', 'energy_kwh', 'pass_fail_status']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")
    
    # Group by model to calculate metrics
    model_stats = df.groupby('model_id').agg(
        total_energy=('energy_kwh', 'sum'),
        passed_count=('pass_fail_status', 'sum'),
        total_count=('pass_fail_status', 'count')
    ).reset_index()
    
    # Calculate metrics
    # Handle case where passed_count is 0 to avoid division by zero
    model_stats['energy_per_correct_solution'] = np.where(
        model_stats['passed_count'] > 0,
        model_stats['total_energy'] / model_stats['passed_count'],
        np.nan
    )
    
    model_stats['pass_accuracy'] = model_stats['passed_count'] / model_stats['total_count']
    
    # Filter out rows where energy_per_correct_solution is NaN (no correct solutions)
    plot_data = model_stats.dropna(subset=['energy_per_correct_solution'])
    
    if plot_data.empty:
        logger.warning("No models with correct solutions found. Cannot generate scatter plot.")
        # Create an empty plot to satisfy the requirement of producing a file
        plt.figure(figsize=(10, 6))
        plt.title('Energy per Correct Solution vs Pass@1 Accuracy', fontsize=14, fontweight='bold')
        plt.xlabel('Pass@1 Accuracy', fontsize=12)
        plt.ylabel('Energy per Correct Solution (kWh)', fontsize=12)
        plt.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=14)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        logger.info(f"Empty scatter plot saved to {output_path}")
        return

    plt.figure(figsize=(10, 6))
    
    # Plot points
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    for i, (_, row) in enumerate(plot_data.iterrows()):
        color = colors[i % len(colors)]
        plt.scatter(row['pass_accuracy'], row['energy_per_correct_solution'], 
                    s=100, c=color, edgecolors='black', label=row['model_id'], zorder=3)
        
        # Annotate points with model ID
        plt.annotate(row['model_id'], (row['pass_accuracy'], row['energy_per_correct_solution']), 
                     textcoords="offset points", xytext=(0,10), ha='center', fontsize=10)
    
    plt.title('Energy per Correct Solution vs Pass@1 Accuracy', fontsize=14, fontweight='bold')
    plt.xlabel('Pass@1 Accuracy', fontsize=12)
    plt.ylabel('Energy per Correct Solution (kWh)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(title='Model')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Scatter plot saved to {output_path}")

def validate_plot(filepath, expected_points=None):
    """
    Validate that a plot file exists and optionally check for content.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Plot file not found: {filepath}")
    
    file_size = os.path.getsize(filepath)
    if file_size == 0:
        raise ValueError(f"Plot file is empty: {filepath}")
    
    logger.info(f"Validated plot: {filepath} (size: {file_size} bytes)")
    return True

def create_mock_data():
    """
    Create a mock dataset for testing the visualization logic without real inference data.
    """
    data = {
        'model_id': ['gpt2-small'] * 5 + ['codebert-base'] * 5 + ['starcoder-1b'] * 5,
        'problem_id': list(range(5)) * 3,
        'tokens_generated': [10, 15, 20, 25, 30] * 3,
        'energy_kwh': [0.001, 0.0012, 0.0015, 0.0018, 0.002] * 3,
        'runtime_seconds': [1.0, 1.2, 1.5, 1.8, 2.0] * 3,
        'pass_fail_status': [1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0]
    }
    return pd.DataFrame(data)

def main():
    parser = argparse.ArgumentParser(description="Generate energy consumption visualizations.")
    parser.add_argument('--mock', action='store_true', help="Use mock data for testing.")
    parser.add_argument('--input', type=str, default=None, help="Path to input CSV file.")
    args = parser.parse_args()

    # Determine input data
    if args.mock:
        logger.info("Running in mock mode.")
        df = create_mock_data()
        input_source = "mock"
    elif args.input:
        if not os.path.exists(args.input):
            logger.error(f"Input file not found: {args.input}")
            sys.exit(1)
        df = load_data(args.input)
        input_source = args.input
    else:
        # Default path from config
        input_path = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")
        if not os.path.exists(input_path):
            logger.error(f"Default input file not found: {input_path}")
            logger.info("Run with --mock to test with synthetic data, or provide --input.")
            sys.exit(1)
        df = load_data(input_path)
        input_source = input_path

    # Calculate Energy per Token for Bar Plot
    df_with_metric = calculate_energy_per_token_joules(df)
    
    # Output paths
    bar_plot_path = os.path.join(DATA_PROCESSED_DIR, "energy_bar.png")
    scatter_plot_path = os.path.join(DATA_PROCESSED_DIR, "tradeoff_scatter.png")

    # Generate Bar Plot
    logger.info("Generating Bar Plot...")
    try:
        plot_energy_bar(df_with_metric, bar_plot_path)
        validate_plot(bar_plot_path)
    except Exception as e:
        logger.error(f"Failed to generate bar plot: {e}")
        sys.exit(1)

    # Generate Scatter Plot
    logger.info("Generating Scatter Plot...")
    try:
        plot_tradeoff_scatter(df, scatter_plot_path)
        validate_plot(scatter_plot_path)
    except Exception as e:
        logger.error(f"Failed to generate scatter plot: {e}")
        sys.exit(1)

    logger.info("All visualizations generated successfully.")

if __name__ == "__main__":
    main()