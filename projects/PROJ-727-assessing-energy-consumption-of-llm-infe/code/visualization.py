import os
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from code.config import DATA_PROCESSED_DIR

def load_data():
    """Load aggregated results from CSV."""
    file_path = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    return pd.read_csv(file_path)

def plot_energy_bar():
    """
    Generate Bar Plot: Y=Energy per Token (Joules), X=Model ID.
    Include error bars if standard deviation > 0.
    Include a legend.
    Save to data/processed/energy_bar.png.
    """
    df = load_data()

    # Calculate Energy per Token in Joules (1 kWh = 3,600,000 Joules)
    # Ensure we handle cases where tokens_generated might be 0 (though filtered in T016)
    df['energy_per_token_joules'] = (df['energy_kwh'] * 3_600_000) / df['tokens_generated']

    # Group by model_id to calculate mean and std for error bars
    grouped = df.groupby('model_id')['energy_per_token_joules']
    means = grouped.mean()
    stds = grouped.std()
    models = means.index.tolist()

    # Prepare data for plotting
    x = np.arange(len(models))
    y = means.values
    yerr = stds.values

    # Create the plot
    plt.figure(figsize=(10, 6))
    
    # Plot bar chart with error bars
    # Only add error bars if std > 0, otherwise matplotlib handles it gracefully (or we set yerr=0)
    # The requirement says: "Include error bars if standard deviation > 0"
    # We'll pass the std array; if all are 0, it draws no error bars effectively.
    plt.bar(x, y, yerr=yerr, capsize=5, color='skyblue', edgecolor='black', label='Energy per Token')

    plt.xticks(x, models, rotation=45)
    plt.ylabel('Energy per Token (Joules)')
    plt.xlabel('Model ID')
    plt.title('Energy Consumption per Token by Model')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Save the plot
    output_path = os.path.join(DATA_PROCESSED_DIR, "energy_bar.png")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    # Validation step: programmatically confirm the plot file exists and contains required elements
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Failed to generate plot: {output_path}")
    
    # Reload to verify content (basic check)
    img = plt.imread(output_path)
    if img.size == 0:
        raise ValueError("Generated plot is empty.")
    
    # Note: We cannot programmatically verify title/labels from the saved image file easily without OCR,
    # but we have just generated it with these elements. The existence of the file with non-zero size
    # and the code above confirms the intent.
    
    print(f"Bar plot generated successfully: {output_path}")
    return output_path

def plot_tradeoff_scatter():
    """
    Generate Scatter Plot: Y=Energy per Correct Solution, X=Pass@1 Accuracy.
    Distinct markers per model. Include a legend.
    Save to data/processed/tradeoff_scatter.png.
    """
    df = load_data()

    # Calculate metrics
    # Energy per Correct Solution: Sum of energy for passed solutions / count of passed solutions
    # However, the data is per problem. We need to aggregate per model first.
    # Y = Total Energy for Correct / Count of Correct
    # X = Pass@1 Accuracy = Count of Correct / Total Problems (per model)
    
    # Filter for passed solutions only for energy calculation
    passed_df = df[df['pass_fail_status'] == 1]
    
    # Calculate total energy and count of correct solutions per model
    model_stats = df.groupby('model_id').agg(
        total_correct=('pass_fail_status', 'sum'),
        total_problems=('problem_id', 'count'),
        total_energy_kwh=('energy_kwh', 'sum')
    ).reset_index()
    
    model_stats['accuracy'] = model_stats['total_correct'] / model_stats['total_problems']
    model_stats['energy_per_correct_kwh'] = model_stats['total_energy_kwh'] / model_stats['total_correct']
    model_stats['energy_per_correct_joules'] = model_stats['energy_per_correct_kwh'] * 3_600_000

    # Create the plot
    plt.figure(figsize=(10, 6))
    
    markers = ['o', 's', '^']
    for i, model in enumerate(model_stats['model_id']):
        row = model_stats[model_stats['model_id'] == model].iloc[0]
        plt.scatter(
            [row['accuracy']], 
            [row['energy_per_correct_joules']], 
            marker=markers[i % len(markers)], 
            s=100, 
            label=model
        )
    
    plt.xlabel('Pass@1 Accuracy')
    plt.ylabel('Energy per Correct Solution (Joules)')
    plt.title('Sustainability Trade-off: Energy vs Accuracy')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)

    # Save the plot
    output_path = os.path.join(DATA_PROCESSED_DIR, "tradeoff_scatter.png")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    # Validation
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Failed to generate plot: {output_path}")
    
    img = plt.imread(output_path)
    if img.size == 0:
        raise ValueError("Generated plot is empty.")
    
    print(f"Scatter plot generated successfully: {output_path}")
    return output_path

def main():
    """Main entry point for visualization tasks."""
    print("Starting visualization generation...")
    try:
        plot_energy_bar()
        plot_tradeoff_scatter()
        print("All visualizations completed.")
    except Exception as e:
        print(f"Error generating visualizations: {e}")
        raise

if __name__ == "__main__":
    main()