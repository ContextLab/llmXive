import os
import pandas as pd
import numpy as np
from code.config import DATA_PROCESSED_DIR

def calculate_scatter_slope():
    """
    Calculates the slope of the curve connecting the models on the scatter plot
    (Energy per Correct Solution vs Accuracy) and saves it to data/processed/scatter_slope.txt.
    This satisfies SC-004.
    """
    # Load the aggregated data
    filepath = os.path.join(DATA_PROCESSED_DIR, 'energy_results_aggregated.csv')
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Aggregated data file not found at {filepath}")
    
    df = pd.read_csv(filepath)

    # Prepare data similar to the scatter plot logic
    df['energy_kwh_clean'] = pd.to_numeric(df['energy_kwh'], errors='coerce')
    df['pass_fail_status'] = pd.to_numeric(df['pass_fail_status'], errors='coerce')
    
    valid_df = df[(df['energy_kwh_clean'].notna()) & (df['pass_fail_status'].notna())]
    
    if valid_df.empty:
        raise ValueError("No valid data for slope calculation.")

    # Aggregate per model
    agg = valid_df.groupby('model_id').agg(
        total_energy_kwh=('energy_kwh_clean', 'sum'),
        total_correct=('pass_fail_status', 'sum'),
        count=('problem_id', 'count')
    ).reset_index()

    # Calculate Accuracy and Energy per Correct Solution
    agg['accuracy'] = agg['total_correct'] / agg['count']
    agg['total_energy_joules'] = agg['total_energy_kwh'] * 3_600_000
    agg['energy_per_correct'] = agg['total_energy_joules'] / agg['total_correct']

    # Sort by accuracy to define a "curve" connecting points from low to high accuracy
    agg_sorted = agg.sort_values('accuracy')

    # Calculate slope between the first and last points (extremes)
    # Or perform a linear regression on the three points to get a global slope?
    # The prompt says "slope of the curve connecting the models". 
    # With 3 points, a simple linear regression slope is a reasonable interpretation of the trend.
    x = agg_sorted['accuracy'].values
    y = agg_sorted['energy_per_correct'].values

    # Linear regression: y = mx + c
    # Using numpy polyfit (degree 1)
    slope, intercept = np.polyfit(x, y, 1)

    # Format the result
    result_text = f"Slope of the trade-off curve (Energy per Correct Solution vs Accuracy):\n{slope:.6f} Joules per Accuracy Unit\n\nCalculated from {len(agg_sorted)} models.\nData source: {filepath}"

    # Write to file
    output_path = os.path.join(DATA_PROCESSED_DIR, 'scatter_slope.txt')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(result_text)
    
    print(f"Slope calculation saved to {output_path}")
    print(f"Calculated slope: {slope}")
    return output_path

if __name__ == "__main__":
    calculate_scatter_slope()