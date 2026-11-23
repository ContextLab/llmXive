"""
T030b: Calculate and record the slope of the curve connecting the models
on the scatter plot (Energy per Correct Solution vs Pass@1 Accuracy).

This script reads aggregated data from data/processed/energy_results_aggregated.csv,
computes centroids (mean Accuracy, mean Energy/Correct) per model,
and calculates the slope between the centroids of the three models.

Output: data/processed/scatter_slope.txt
"""
import os
import pandas as pd
import numpy as np
from code.config import DATA_PROCESSED_DIR

def calculate_scatter_slope():
    """
    Calculate the slope of the line connecting model centroids on the 
    Energy/Correct vs Accuracy scatter plot.
    
    Returns:
        float: The calculated slope, or None if calculation fails.
    """
    input_file = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(
            f"Required input file not found: {input_file}. "
            "Run T016 (aggregation) first."
        )
    
    df = pd.read_csv(input_file)
    
    # Validate required columns
    required_cols = ['model_id', 'pass_fail_status', 'energy_kwh', 'tokens_generated']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_file}: {missing}")
    
    # Filter out rows with nulls or zeros that might skew the mean
    # (Though T016 should have already cleaned this, we double-check)
    df_clean = df.dropna(subset=['energy_kwh', 'tokens_generated', 'pass_fail_status'])
    
    if df_clean.empty:
        raise ValueError("No valid data rows found after cleaning.")
    
    # Calculate Energy per Correct Solution (Joules)
    # Energy in kWh -> Joules (1 kWh = 3.6e6 J)
    # Only count energy for correct solutions (pass_fail_status == 1)
    # We need to aggregate energy by problem and success status first?
    # Actually, the spec implies "Energy per Correct Solution". 
    # Since energy_kwh is per problem inference, we sum energy for problems where pass_fail_status == 1.
    # Then divide by the count of correct solutions.
    
    # Group by model_id
    # For each model:
    # 1. Sum energy_kwh for rows where pass_fail_status == 1
    # 2. Count rows where pass_fail_status == 1
    # 3. Energy per Correct = (Sum Energy * 3.6e6) / Count
    
    # Also need Pass@1 Accuracy: Count(pass_fail_status==1) / Total_Count
    
    results = []
    for model_id, group in df_clean.groupby('model_id'):
        total_problems = len(group)
        correct_problems = group[group['pass_fail_status'] == 1]
        
        if len(correct_problems) == 0:
            # Avoid division by zero; accuracy is 0, energy/correct is undefined
            # We'll mark as NaN or 0 depending on interpretation. 
            # For slope calculation, we might need to skip or handle carefully.
            accuracy = 0.0
            energy_per_correct = np.nan
        else:
            accuracy = len(correct_problems) / total_problems
            total_energy_kwh = correct_problems['energy_kwh'].sum()
            energy_per_correct_joules = (total_energy_kwh * 3_600_000) / len(correct_problems)
            energy_per_correct = energy_per_correct_joules
        
        results.append({
            'model_id': model_id,
            'accuracy': accuracy,
            'energy_per_correct': energy_per_correct
        })
    
    results_df = pd.DataFrame(results)
    
    # Drop models where energy_per_correct is NaN (0 correct solutions)
    # We cannot calculate a meaningful slope if a point is undefined.
    results_df = results_df.dropna(subset=['energy_per_correct'])
    
    if len(results_df) < 2:
        raise ValueError(
            f"Insufficient valid models to calculate slope. "
            f"Found {len(results_df)} valid models (need at least 2)."
        )
    
    # Sort by accuracy to ensure consistent ordering for "curve" or "line"
    # The slope is typically calculated between the min and max points 
    # or via linear regression if we consider all points.
    # The task says "slope of the curve connecting the models". 
    # With 3 points, a simple linear regression (best fit line) is the standard interpretation.
    
    X = results_df['accuracy'].values
    y = results_df['energy_per_correct'].values
    
    # Linear regression: y = mx + c
    # We want the slope (m)
    slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
    
    return slope, results_df

def main():
    try:
        slope, results_df = calculate_scatter_slope()
        
        output_file = os.path.join(DATA_PROCESSED_DIR, "scatter_slope.txt")
        
        with open(output_file, 'w') as f:
            f.write(f"Slope of Energy/Correct vs Accuracy: {slope:.6f}\n")
            f.write(f"R-squared: {results_df['accuracy'].corr(results_df['energy_per_correct'])**2 if len(results_df) > 1 else 0:.6f}\n")
            f.write("\nModel Centroids (Accuracy, Energy/Correct J):\n")
            for _, row in results_df.iterrows():
                f.write(f"  {row['model_id']}: ({row['accuracy']:.4f}, {row['energy_per_correct']:.2f})\n")
        
        print(f"Slope calculation complete. Results written to {output_file}")
        print(f"Calculated Slope: {slope}")
        
    except Exception as e:
        print(f"Error calculating scatter slope: {e}")
        raise

if __name__ == "__main__":
    main()
