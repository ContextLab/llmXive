"""
Visualization module for LLM energy consumption analysis.
Generates bar plots and scatter plots based on aggregated energy data.
"""
import os
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from code.config import DATA_PROCESSED_DIR

# Ensure the processed directory exists
os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

def load_data():
    """
    Load the aggregated energy results from the CSV file.
    Returns a pandas DataFrame.
    """
    input_path = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Aggregated data file not found: {input_path}")
    df = pd.read_csv(input_path)
    return df

def calculate_energy_per_token_joules(row):
    """
    Calculate Energy per Token in Joules.
    Energy (kWh) -> Joules: * 3,600,000
    """
    if pd.isna(row['energy_kwh']) or pd.isna(row['tokens_generated']) or row['tokens_generated'] == 0:
        return np.nan
    energy_joules = row['energy_kwh'] * 3_600_000
    return energy_joules / row['tokens_generated']

def plot_energy_bar(df):
    """
    Generate Bar Plot: Y=Energy per Token (Joules), X=Model ID.
    Includes error bars if standard deviation > 0.
    Saves to data/processed/energy_bar.png.
    """
    # Calculate Energy per Token for each row
    df['energy_per_token_j'] = df.apply(calculate_energy_per_token_joules, axis=1)

    # Group by model to calculate mean and std
    model_stats = df.groupby('model_id')['energy_per_token_j'].agg(['mean', 'std']).reset_index()

    # Filter out NaNs for plotting
    model_stats = model_stats.dropna(subset=['mean'])

    plt.figure(figsize=(10, 6))
    
    # Prepare for plotting
    models = model_stats['model_id']
    means = model_stats['mean']
    stds = model_stats['std']
    
    # Handle NaN stds (replace with 0 for plotting purposes if needed, but bar width might be 0)
    stds = stds.fillna(0)

    # Plot bar chart with error bars
    plt.bar(models, means, yerr=stds, capsize=5, color='skyblue', edgecolor='black', alpha=0.7)

    plt.title('Energy Consumption per Token by Model', fontsize=14)
    plt.xlabel('Model ID', fontsize=12)
    plt.ylabel('Energy per Token (Joules)', fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add legend if multiple models or specific context needed
    # Since we plot per model, legend might be redundant but requested
    plt.legend(['Energy per Token (Mean ± Std)'], loc='upper right')

    output_path = os.path.join(DATA_PROCESSED_DIR, "energy_bar.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"Bar plot saved to: {output_path}")
    return output_path

def plot_tradeoff_scatter(df):
    """
    Generate Scatter Plot: Y=Energy per Correct Solution, X=Pass@1 Accuracy.
    
    Definitions:
    - Energy per Correct Solution = Total Energy for Model / Count of Passed Problems
    - Pass@1 Accuracy = Count of Passed Problems / Total Problems
    
    This results in one point per model.
    Saves to data/processed/tradeoff_scatter.png.
    """
    # Ensure we have the necessary columns
    required_cols = ['model_id', 'energy_kwh', 'pass_fail_status']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing required columns in data. Found: {df.columns.tolist()}")

    # Group by model to calculate metrics
    model_metrics = df.groupby('model_id').agg(
        total_energy=('energy_kwh', 'sum'),
        passed_problems=('pass_fail_status', 'sum'),
        total_problems=('pass_fail_status', 'count')
    ).reset_index()

    # Calculate derived metrics
    # Handle division by zero if no problems passed
    model_metrics['energy_per_correct'] = model_metrics.apply(
        lambda row: row['total_energy'] / row['passed_problems'] if row['passed_problems'] > 0 else np.nan, 
        axis=1
    )
    
    model_metrics['accuracy'] = model_metrics['passed_problems'] / model_metrics['total_problems']

    # Filter out rows where we couldn't calculate energy per correct (e.g., 0 passed)
    plot_data = model_metrics.dropna(subset=['energy_per_correct', 'accuracy'])

    if plot_data.empty:
        print("Warning: No data points to plot for scatter plot (likely 0 passed problems for all models).")
        # Create an empty plot with labels to satisfy artifact requirement
        plt.figure(figsize=(10, 6))
        plt.title('Energy vs Accuracy Trade-off (No Data)', fontsize=14)
        plt.xlabel('Pass@1 Accuracy', fontsize=12)
        plt.ylabel('Energy per Correct Solution (kWh)', fontsize=12)
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.grid(True, alpha=0.3)
        plt.legend(['Models'], loc='best')
        output_path = os.path.join(DATA_PROCESSED_DIR, "tradeoff_scatter.png")
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        print(f"Empty scatter plot saved to: {output_path}")
        return output_path

    plt.figure(figsize=(10, 6))
    
    # Scatter plot
    plt.scatter(
        plot_data['accuracy'], 
        plot_data['energy_per_correct'], 
        s=200, 
        c='darkgreen', 
        edgecolors='black', 
        linewidth=1.5,
        label='Models'
    )

    # Annotate points with model names
    for _, row in plot_data.iterrows():
        plt.annotate(
            row['model_id'], 
            (row['accuracy'], row['energy_per_correct']), 
            textcoords="offset points", 
            xytext=(0,10), 
            ha='center',
            fontsize=10,
            fontweight='bold'
        )

    plt.title('Energy vs Accuracy Trade-off', fontsize=14)
    plt.xlabel('Pass@1 Accuracy', fontsize=12)
    plt.ylabel('Energy per Correct Solution (kWh)', fontsize=12)
    plt.xlim(0, 1) # Accuracy is between 0 and 1
    plt.grid(True, alpha=0.3)
    
    plt.legend(loc='best')

    output_path = os.path.join(DATA_PROCESSED_DIR, "tradeoff_scatter.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"Scatter plot saved to: {output_path}")
    return output_path

def validate_plot(output_path):
    """
    Basic validation that the plot file exists and is not empty.
    """
    if not os.path.exists(output_path):
        return False
    if os.path.getsize(output_path) == 0:
        return False
    return True

def main(mock=False):
    """
    Main entry point to generate all visualizations.
    If mock=True, creates a synthetic dataset for testing logic.
    """
    if mock:
        print("Running in MOCK mode for verification...")
        # Create synthetic data for T029 verification
        synthetic_data = {
            'model_id': ['GPT2-small', 'CodeBERT', 'StarCoder-1B'],
            'problem_id': [f'prob_{i}' for i in range(3)],
            'tokens_generated': [10, 20, 30],
            'energy_kwh': [0.001, 0.002, 0.003],
            'runtime_seconds': [1.0, 2.0, 3.0],
            'pass_fail_status': [1, 0, 1] # 1 passed, 0 failed
        }
        # Repeat for multiple problems to simulate real data structure if needed, 
        # but for scatter plot we need aggregated per model. 
        # Let's make it slightly more realistic: 3 models, 2 problems each.
        # Model A: 2 passed, 0.001 kWh total
        # Model B: 1 passed, 0.002 kWh total
        # Model C: 0 passed -> skip or handle
        synthetic_rows = []
        models = ['GPT2-small', 'CodeBERT', 'StarCoder-1B']
        for i, model in enumerate(models):
            for j in range(2): # 2 problems per model
                synthetic_rows.append({
                    'model_id': model,
                    'problem_id': f'{model}_prob_{j}',
                    'tokens_generated': 10 + i,
                    'energy_kwh': (0.001 * (i+1)), # Total energy will be sum
                    'runtime_seconds': 1.0,
                    'pass_fail_status': 1 if j == 0 else (1 if model != 'StarCoder-1B' else 0)
                })
        
        df = pd.DataFrame(synthetic_rows)
        # Manually save to processed dir for the function to read if needed, 
        # but we can pass df directly if we modify the flow. 
        # However, the spec says load from file. So we write it.
        temp_path = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")
        df.to_csv(temp_path, index=False)
        print(f"Mock data written to {temp_path}")
    
    # Load data
    try:
        df = load_data()
    except FileNotFoundError as e:
        print(f"Error loading data: {e}")
        if not mock:
            raise
        return

    # Generate Bar Plot
    print("Generating Energy Bar Plot...")
    bar_path = plot_energy_bar(df)
    if not validate_plot(bar_path):
        print("Warning: Bar plot validation failed.")
    else:
        print(f"Bar plot validated successfully.")

    # Generate Scatter Plot
    print("Generating Trade-off Scatter Plot...")
    scatter_path = plot_tradeoff_scatter(df)
    if not validate_plot(scatter_path):
        print("Warning: Scatter plot validation failed.")
    else:
        print(f"Scatter plot validated successfully.")

    print("Visualization generation complete.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate energy consumption visualizations.")
    parser.add_argument("--mock", action="store_true", help="Run with synthetic data for testing.")
    args = parser.parse_args()
    main(mock=args.mock)