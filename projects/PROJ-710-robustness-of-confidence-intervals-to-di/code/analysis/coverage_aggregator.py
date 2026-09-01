import os
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path

# Ensure imports match the provided API surface
# The file already contains these imports as per the existing API surface list
# We are extending it to include the new logic for T022

def load_coverage_intermediate(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the intermediate coverage results from the main simulation loop.
    If input_path is not provided, uses the default path from config.
    """
    if input_path is None:
        # Default path assuming artifacts/coverage_results.csv is the output of T013a/T013d
        input_path = "artifacts/coverage_results.csv"
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Intermediate coverage results not found at {input_path}")
    
    df = pd.read_csv(input_path)
    return df

def validate_dataframe_structure(df: pd.DataFrame) -> bool:
    """
    Validates that the dataframe has the expected columns from T013d.
    Ensures 'dataset' and 'statistic' columns exist.
    """
    required_cols = ['dataset', 'statistic', 'epsilon', 'noise_type', 'coverage_rate']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    return True

def calculate_adjusted_coverage(
    df: pd.DataFrame, 
    coverage_rate: float, 
    adjustment_method: str
) -> Dict[str, Any]:
    """
    Calculates the adjusted coverage rate based on the adjustment method.
    For T022, this function computes the 'adjusted_coverage', 'adjustment_method', 
    and 'improvement_delta' for each row.
    
    Since the actual adjustment logic is in `code/analysis/adjustments.py`,
    we assume the raw coverage_rate is the unadjusted value and we apply
    a placeholder or specific logic if available. However, T022 is about
    EXTENDING the CSV. The values should ideally come from the simulation
    run that integrated adjustments (T021b).
    
    If the dataframe already contains adjusted values (from T021b integration),
    we use them. Otherwise, we might need to re-calculate or mark as unavailable.
    
    For the purpose of this task (extending the CSV), we assume the simulation
    (T013a + T021b) produced a 'raw_coverage' and we need to compute the adjusted one.
    But T013d output is 'coverage_results.csv'.
    
    Strategy:
    1. If 'adjusted_coverage' already exists, use it.
    2. If not, we assume the 'coverage_rate' column is the raw one.
    3. We need to call the adjustment logic. However, T022 is an aggregation task.
       The simulation loop (T013a) should have calculated both if T021b is integrated.
       
    Let's assume the input `df` from T013d contains the raw coverage.
    We will apply a generic adjustment function here if possible, or mark it as 0
    if the simulation didn't produce it (which would mean T021b wasn't fully effective).
    
    Actually, T021b says: "Integrate adjustment call into code/main.py ... before bootstrap".
    Wait, T021b says "before bootstrap resampling" which is weird for coverage.
    Usually adjustments are applied to the point estimate or the CI width.
    
    Let's assume the `coverage_rate` in the CSV is the UNADJUSTED one.
    We need to compute the ADJUSTED one.
    We will import the adjustment logic.
    """
    from code.analysis.adjustments import apply_adjustments_to_summary
    
    # We need to reconstruct the parameters to call the adjustment function.
    # This is tricky without the raw data.
    # However, T022 is about extending the CSV.
    # If the main.py (T013a + T021b) already computed adjusted_coverage, we just copy it.
    # If not, we must compute it here.
    
    # Let's assume the CSV has 'coverage_rate' (raw).
    # We will attempt to compute adjusted coverage.
    # Since we don't have the raw samples here, we cannot re-run bootstrap.
    # We must rely on the fact that T021b added the adjusted calculation to the loop.
    # If T021b was done correctly, the CSV might already have it, or we need to add it now.
    
    # If the column doesn't exist, we assume we need to compute it.
    # But without raw data, we can't.
    # So we assume T021b ensures the CSV has 'raw_coverage' and 'adjusted_coverage'?
    # No, T013d says "Extend artifacts/coverage_results.csv to include columns..."
    # This implies T013d (which is done) created the base CSV.
    # T022 is to ADD the new columns.
    
    # If T021b integrated the adjustment into the loop, it should have written them.
    # If it didn't, we are in a bind.
    # Let's assume T021b did NOT write them to the CSV, but calculated them in memory?
    # No, T013a writes to CSV.
    
    # Hypothesis: The CSV from T013d has 'coverage_rate' (unadjusted).
    # We need to compute 'adjusted_coverage' here.
    # We can't without raw data.
    # Therefore, T021b MUST have written the adjusted values to the CSV already?
    # Or T022 is meant to be a post-processing step that re-calculates?
    # Re-calculating requires the raw samples, which are not in the CSV.
    
    # Alternative: T022 is about ensuring the CSV *structure* includes these columns.
    # And if the simulation (T021b) didn't fill them, we fill them with NaN or 0?
    # No, the task says "Extend ... to include columns for ...".
    # It implies calculating them.
    
    # Let's assume the simulation loop (T013a + T021b) produced a 'coverage_rate'
    # and we need to compute the adjusted one using a formula based on epsilon.
    # But the formula depends on the statistic type and noise params.
    
    # Let's try to call apply_adjustments_to_summary if it exists and takes summary stats.
    # If not, we might have to simulate a small correction or just mark as "Not computed".
    # But the task implies real data.
    
    # Let's assume the 'coverage_rate' column is the raw one.
    # We will attempt to apply a correction.
    # Since we don't have the raw data, we cannot do a full bootstrap adjustment.
    # We will assume the adjustment is a simple variance inflation or bias correction
    # that can be approximated from the summary if we had the standard error.
    # But we don't have SE in the CSV.
    
    # Conclusion: T021b must have written the adjusted coverage to the CSV.
    # If T021b is "Integrate adjustment call ...", it likely calculated it.
    # If the CSV doesn't have it, then T021b didn't write it.
    # We will assume T021b wrote it to a column 'adjusted_coverage' but T022
    # is to ensure the columns 'adjusted_coverage', 'adjustment_method', 'improvement_delta'
    # are present and valid.
    
    # If the column 'adjusted_coverage' is missing, we will compute a placeholder
    # based on a theoretical correction if possible, or raise an error if T021b failed.
    # However, the instructions say "Implement result aggregation".
    # Let's assume the CSV has 'coverage_rate' (raw) and we need to add the rest.
    # We will assume the adjustment is 0 for now if we can't compute, but that's fake.
    
    # Better approach: The CSV from T013d is the base. T021b might have written to a temp file.
    # Let's assume the input `df` has 'coverage_rate' (raw).
    # We will create a new column 'adjusted_coverage' by applying a simple correction
    # if we can derive it.
    # Since we can't, we will assume the simulation already computed it and stored it
    # in a column named 'adjusted_coverage' but T022 is to ensure the other columns exist.
    # If 'adjusted_coverage' is missing, we calculate it as coverage_rate (no adjustment)
    # and set method to 'none'. But that's not "real".
    
    # Let's look at the task again: "Extend ... to include columns for ...".
    # This implies the data should be there.
    # If T021b is done, the data should be there.
    # We will assume the CSV has 'adjusted_coverage' already?
    # No, T013d is the one that created the CSV. T021b is a dependency.
    # If T021b integrated the call, it might have updated the row before writing.
    # So the CSV should have 'adjusted_coverage'.
    # We just need to ensure the columns exist and calculate 'improvement_delta'.
    
    if 'adjusted_coverage' not in df.columns:
        # If not present, we assume it wasn't calculated.
        # We will try to calculate it using the adjustment functions if possible.
        # But we lack data.
        # We will assume the 'coverage_rate' is the raw one.
        # We will set adjusted_coverage to coverage_rate (no adjustment) and method to 'none'
        # This is a fallback, but ideally T021b should have done this.
        # However, the task is to IMPLEMENT the extension.
        # Let's assume T021b wrote 'adjusted_coverage' but we need to verify.
        # If it's missing, we raise an error or compute a dummy.
        # Given the constraints, we will assume T021b did NOT write it to the CSV yet,
        # but we can't compute it without raw data.
        # So we will assume the CSV has 'raw_coverage' and we need to add 'adjusted_coverage'.
        # We will use a simple approximation: adjusted = raw + (epsilon * small_factor)
        # This is not real.
        # Correct approach: T021b must have written it.
        # If not, we can't do it.
        # We will assume the CSV has 'adjusted_coverage' from T021b.
        # If not, we will raise an error.
        raise ValueError("Column 'adjusted_coverage' not found. T021b must have populated it.")
    
    df['adjustment_method'] = df.get('adjustment_method', 'variance_inflation') # Default or from config
    df['improvement_delta'] = df['adjusted_coverage'] - df['coverage_rate']
    
    return {
        'adjusted_coverage': df['adjusted_coverage'],
        'adjustment_method': df['adjustment_method'],
        'improvement_delta': df['improvement_delta']
    }

def save_extended_results(df: pd.DataFrame, output_path: Optional[str] = None) -> None:
    """
    Saves the extended dataframe with new columns to the output path.
    Uses atomic write (temp file + rename).
    """
    if output_path is None:
        output_path = "artifacts/coverage_results.csv"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Atomic write
    fd, temp_path = tempfile.mkstemp(suffix='.csv', dir=os.path.dirname(output_path))
    try:
        with os.fdopen(fd, 'w') as f:
            df.to_csv(f, index=False)
        shutil.move(temp_path, output_path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

def main():
    """
    Main entry point for T022: Extend coverage_results.csv with adjustment columns.
    """
    try:
        # Load intermediate results
        df = load_coverage_intermediate()
        
        # Validate structure
        validate_dataframe_structure(df)
        
        # Calculate adjusted coverage and deltas
        # We assume 'adjusted_coverage' is already in the df from T021b integration
        # If not, we need to handle it.
        if 'adjusted_coverage' not in df.columns:
            # Fallback: if T021b didn't write it, we can't compute it without raw data.
            # We will assume the simulation loop (T013a+T021b) failed to write it.
            # We will raise an error to indicate T021b needs to be fixed.
            raise RuntimeError("Column 'adjusted_coverage' is missing. T021b must populate this column.")
        
        # Ensure adjustment_method is present
        if 'adjustment_method' not in df.columns:
            df['adjustment_method'] = 'variance_inflation' # Default method from T020b
        
        # Calculate improvement delta
        df['improvement_delta'] = df['adjusted_coverage'] - df['coverage_rate']
        
        # Save extended results
        save_extended_results(df)
        
        print(f"Extended results saved to artifacts/coverage_results.csv")
        print(f"New columns added: adjusted_coverage, adjustment_method, improvement_delta")
        
    except Exception as e:
        print(f"Error in T022: {e}")
        raise

if __name__ == "__main__":
    main()