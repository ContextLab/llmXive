import os
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from code.config import DATA_PROCESSED_DIR, FIGURES_DIR

def load_data():
    """
    Load the aggregated energy results from the processed CSV file.
    Returns a pandas DataFrame.
    """
    filepath = os.path.join(DATA_PROCESSED_DIR, 'energy_results_aggregated.csv')
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Aggregated data file not found at {filepath}")
    df = pd.read_csv(filepath)
    return df

def plot_energy_bar(df):
    """
    Generate a bar plot of Energy per Token (Joules) vs Model ID.
    Includes title, axis labels with units, error bars, and legend.
    Saves the plot to data/processed/energy_bar.png.
    """
    # Calculate mean and std of energy per token for each model
    # Ensure 'energy_per_token_joules' exists or calculate it
    # Assuming the aggregated CSV has 'energy_kwh' and 'tokens_generated'
    # We need to convert kWh to Joules: 1 kWh = 3,600,000 Joules
    if 'energy_per_token_joules' not in df.columns:
        # Calculate if not present, assuming energy_kwh and tokens_generated exist
        # Handle division by zero or nulls
        df['energy_kwh_clean'] = pd.to_numeric(df['energy_kwh'], errors='coerce')
        df['tokens_generated_clean'] = pd.to_numeric(df['tokens_generated'], errors='coerce')
        
        # Filter out rows where calculation is invalid
        valid_df = df[(df['energy_kwh_clean'].notna()) & (df['tokens_generated_clean'] > 0)]
        if valid_df.empty:
            raise ValueError("No valid data points to calculate energy per token.")
        
        # Calculate Joules per token
        valid_df['energy_per_token_joules'] = (valid_df['energy_kwh_clean'] * 3_600_000) / valid_df['tokens_generated_clean']
    else:
        valid_df = df.dropna(subset=['energy_per_token_joules'])

    # Group by model_id to get mean and std
    grouped = valid_df.groupby('model_id')['energy_per_token_joules'].agg(['mean', 'std', 'count']).reset_index()
    grouped.columns = ['model_id', 'mean_energy', 'std_energy', 'count']

    # Prepare data for plotting
    models = grouped['model_id'].tolist()
    means = grouped['mean_energy'].tolist()
    stds = grouped['std_energy'].tolist()

    # Create the plot
    plt.figure(figsize=(10, 6))
    x_pos = np.arange(len(models))
    bars = plt.bar(x_pos, means, yerr=stds, capsize=5, color=['skyblue', 'lightgreen', 'salmon'], edgecolor='black')

    # Title and Labels
    plt.title('Energy Consumption per Token by Model (CPU Inference)', fontsize=14, fontweight='bold')
    plt.xlabel('Model ID', fontsize=12)
    plt.ylabel('Energy per Token (Joules)', fontsize=12)
    plt.xticks(x_pos, models, rotation=45)
    
    # Legend (if multiple bars per group, but here we have single bars per model)
    # Adding a legend to explain the error bars or colors if needed
    plt.legend(['Mean Energy (±1 Std Dev)'], loc='upper right')
    
    plt.tight_layout()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(FIGURES_DIR), exist_ok=True)
    output_path = os.path.join(DATA_PROCESSED_DIR, 'energy_bar.png')
    plt.savefig(output_path)
    plt.close()
    print(f"Bar plot saved to {output_path}")
    return output_path

def plot_tradeoff_scatter(df):
    """
    Generate a scatter plot: Y=Energy per Correct Solution, X=Pass@1 Accuracy.
    Includes title, axis labels with units, distinct markers per model, and legend.
    Saves the plot to data/processed/tradeoff_scatter.png.
    """
    # Calculate metrics per model
    # 1. Accuracy: pass_fail_status mean (0/1) per model
    # 2. Energy per Correct Solution: Total Energy / Total Correct Solutions? 
    #    Or Mean Energy / Accuracy? 
    #    Definition: Energy per Correct Solution = (Total Energy for Model) / (Number of Passed Solutions)
    #    Or per problem? The prompt says "Energy per Correct Solution".
    #    Let's aggregate per model: Sum(Energy) / Sum(Pass)
    
    # Convert necessary columns to numeric
    df['energy_kwh_clean'] = pd.to_numeric(df['energy_kwh'], errors='coerce')
    df['pass_fail_status'] = pd.to_numeric(df['pass_fail_status'], errors='coerce')
    
    # Filter valid rows
    valid_df = df[(df['energy_kwh_clean'].notna()) & (df['pass_fail_status'].notna())]
    
    if valid_df.empty:
        raise ValueError("No valid data for scatter plot.")

    # Aggregate per model
    agg = valid_df.groupby('model_id').agg(
        total_energy_kwh=('energy_kwh_clean', 'sum'),
        total_correct=('pass_fail_status', 'sum'),
        count=('problem_id', 'count')
    ).reset_index()

    # Calculate Accuracy (Pass@1 approximated as pass rate here)
    agg['accuracy'] = agg['total_correct'] / agg['count']
    
    # Calculate Energy per Correct Solution (Joules)
    # Total Energy (Joules) / Total Correct Solutions
    agg['total_energy_joules'] = agg['total_energy_kwh'] * 3_600_000
    agg['energy_per_correct'] = agg['total_energy_joules'] / agg['total_correct']

    # Prepare plot data
    models = agg['model_id'].tolist()
    accuracies = agg['accuracy'].tolist()
    energy_per_correct = agg['energy_per_correct'].tolist()

    plt.figure(figsize=(10, 6))
    
    # Distinct markers and colors
    markers = ['o', 's', '^']
    colors = ['blue', 'green', 'red']
    
    for i, model in enumerate(models):
        plt.scatter(accuracies[i], energy_per_correct[i], 
                    marker=markers[i], s=100, color=colors[i], 
                    label=f'{model}', zorder=5)
        
        # Annotate points
        plt.annotate(model, (accuracies[i], energy_per_correct[i]), 
                     textcoords="offset points", xytext=(5,5), fontsize=10)

    # Title and Labels
    plt.title('Sustainability Trade-off: Accuracy vs. Energy per Correct Solution', fontsize=14, fontweight='bold')
    plt.xlabel('Pass@1 Accuracy (Fraction)', fontsize=12)
    plt.ylabel('Energy per Correct Solution (Joules)', fontsize=12)
    
    plt.legend(title='Model')
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(FIGURES_DIR), exist_ok=True)
    output_path = os.path.join(DATA_PROCESSED_DIR, 'tradeoff_scatter.png')
    plt.savefig(output_path)
    plt.close()
    print(f"Scatter plot saved to {output_path}")
    return output_path

def main():
    """
    Main entry point to generate all visualizations for User Story 3.
    """
    print("Loading aggregated data...")
    df = load_data()
    
    print("Generating Energy Bar Plot...")
    plot_energy_bar(df)
    
    print("Generating Trade-off Scatter Plot...")
    plot_tradeoff_scatter(df)
    
    print("All visualizations completed successfully.")

if __name__ == "__main__":
    main()
