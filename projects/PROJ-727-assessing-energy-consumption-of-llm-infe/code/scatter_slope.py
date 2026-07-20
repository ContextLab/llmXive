import os
import pandas as pd
import numpy as np
from code.config import DATA_PROCESSED_DIR

def calculate_scatter_slope(input_file: str, output_file: str) -> None:
    """
    Calculate the slope of the curve connecting the models on the scatter plot
    (Energy per Correct Solution vs Accuracy) and write it to a text file.

    The scatter plot (T029) uses:
      Y = Energy per Correct Solution (kWh)
      X = Pass@1 Accuracy (0.0 to 1.0)

    This function computes the slope between the two extreme points (min and max accuracy)
    to satisfy SC-004: "Calculate and record the slope of the curve connecting the models".
    
    Args:
        input_file: Path to the aggregated CSV file.
        output_file: Path to write the slope result.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}. Run T016 first.")

    df = pd.read_csv(input_file)

    # Calculate metrics per model
    # We need: Energy per Correct Solution = Energy / (Tokens * PassRate) ? 
    # Actually, the spec for T029 says: "Y=Energy per Correct Solution"
    # Usually this is total_energy / number_of_correct_solutions.
    # Since we have per-problem data, we aggregate by model_id.
    
    # Group by model to get aggregate accuracy and total energy
    # We assume 'pass_fail_status' is 1 for pass, 0 for fail.
    # We need to calculate:
    # 1. Total Energy consumed by the model (sum of energy_kwh)
    # 2. Total Correct Solutions (sum of pass_fail_status)
    # 3. Accuracy = Correct / Total_Problems (if we had total problems, but here we just have the subset run)
    # However, the scatter plot in T029 likely plots the aggregate metric per model.
    
    # Let's derive the points from the aggregated data.
    # We need to map each model to (Accuracy, Energy_per_Correct).
    
    # Filter out nulls
    df_clean = df.dropna(subset=['energy_kwh', 'tokens_generated', 'pass_fail_status'])
    
    if df_clean.empty:
        raise ValueError("No valid data found in input file to calculate slope.")

    # Aggregate by model
    model_stats = df_clean.groupby('model_id').agg(
        total_energy=('energy_kwh', 'sum'),
        total_correct=('pass_fail_status', 'sum'),
        total_problems=('problem_id', 'count')
    ).reset_index()

    # Calculate Accuracy (Pass@1 proxy: correct / total_problems run)
    # Note: If the dataset is a sample, this is the empirical accuracy on that sample.
    model_stats['accuracy'] = model_stats['total_correct'] / model_stats['total_problems']

    # Calculate Energy per Correct Solution (kWh per correct solution)
    # Avoid division by zero
    model_stats['energy_per_correct'] = model_stats.apply(
        lambda row: row['total_energy'] / row['total_correct'] if row['total_correct'] > 0 else np.nan,
        axis=1
    )

    # Drop models with no correct solutions for the slope calculation
    model_stats = model_stats.dropna(subset=['energy_per_correct', 'accuracy'])

    if len(model_stats) < 2:
        raise ValueError("Need at least 2 models with valid accuracy and energy data to calculate slope.")

    # Sort by accuracy to find the curve endpoints
    model_stats = model_stats.sort_values('accuracy')

    # The "curve connecting the models" is approximated by the line connecting the min and max accuracy points
    # as per the requirement to "record the slope of the curve connecting the models".
    # We take the first and last point in the sorted list.
    p_low = model_stats.iloc[0]
    p_high = model_stats.iloc[-1]

    x_low, y_low = p_low['accuracy'], p_low['energy_per_correct']
    x_high, y_high = p_high['accuracy'], p_high['energy_per_correct']

    # Calculate slope
    if x_high == x_low:
        slope = float('inf')
    else:
        slope = (y_high - y_low) / (x_high - x_low)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Write the result
    with open(output_file, 'w') as f:
        f.write(f"Slope of Energy per Correct Solution vs Accuracy curve: {slope:.6f} kWh/accuracy_unit\n")
        f.write(f"Calculation: (Energy_high - Energy_low) / (Acc_high - Acc_low)\n")
        f.write(f"Points: ({x_low:.5f}, {y_low:.6f}) -> ({x_high:.5f}, {y_high:.6f})\n")
        f.write(f"Models used for slope: {p_low['model_id']} (low acc) to {p_high['model_id']} (high acc)\n")

def main():
    input_file = os.path.join(DATA_PROCESSED_DIR, 'energy_results_aggregated.csv')
    output_file = os.path.join(DATA_PROCESSED_DIR, 'scatter_slope.txt')
    
    print(f"Calculating scatter slope from {input_file}...")
    try:
        calculate_scatter_slope(input_file, output_file)
        print(f"Slope calculation complete. Results written to {output_file}")
    except Exception as e:
        print(f"Error calculating slope: {e}")
        raise

if __name__ == "__main__":
    main()