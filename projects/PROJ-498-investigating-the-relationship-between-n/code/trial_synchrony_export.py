"""
T036 Implementation: Generate per-trial synchrony CSV.

This script loads aggregated data (synchrony and behavioral metrics) and
computes a trial-level record containing subject_id, trial_id, condition,
synchrony, and rt. It excludes rows where synchrony is missing (NaN).

Output: data/trial_level/per_trial_synchrony.csv
"""
import os
import sys
import json
import pandas as pd
import numpy as np

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ensure_directories
from analysis import load_aggregated_data

def generate_trial_level_synchrony_csv():
    """
    Generates data/trial_level/per_trial_synchrony.csv with columns:
    subject_id, trial_id, condition, synchrony, rt.
    Excludes rows with missing synchrony.
    """
    # Ensure output directory exists
    ensure_directories()
    output_path = os.path.join("data", "trial_level", "per_trial_synchrony.csv")
    
    # Load aggregated data (which should contain trial-level info if T035 ran)
    # The load_aggregated_data function from analysis.py is expected to return
    # a DataFrame or dict containing the necessary trial-level data.
    # Based on T035, we expect trial-level data to be available.
    
    # Since load_aggregated_data might return aggregated (subject-level) data,
    # we need to check the structure. If it doesn't contain trial-level data,
    # we might need to reconstruct it from the raw epoch data.
    # However, T035 (run_trial_level_lme) implies trial-level data exists.
    
    # Let's assume the data is available in a format we can process.
    # If the previous tasks (T031-T035) produced trial-level data, we should access it.
    
    # Attempt to load the data. If the analysis module provides a function
    # specifically for trial-level data, we should use that.
    # For now, we'll try to load the aggregated data and see if it has trial info.
    # If not, we might need to load from the processed epochs directly.
    
    # Given the constraints, let's assume the 'load_aggregated_data' returns a dict
    # with keys like 'trial_data' or similar. If not, we'll need to adjust.
    # However, the task says "requires T004" (hashing) and implies the data is ready.
    
    # Let's try to load the data from the expected location or via the analysis module.
    # If the analysis module doesn't provide trial-level data directly, we might need
    # to construct it from the synchrony metrics and behavioral data.
    
    # Since T035 ran, we assume there is a way to get trial-level synchrony.
    # Let's try to load the data from the metrics directory if it exists.
    
    # Fallback: If we can't get trial-level data from load_aggregated_data,
    # we might need to load the synchrony metrics and behavioral data separately
    # and merge them.
    
    # Let's assume the data is in data/metrics/synchrony_metrics.csv and
    # we have trial-level behavioral data from the epochs.
    
    # However, the task description says "Generate ... with columns ...", implying
    # we need to create this file from existing data.
    
    # Let's try to load the data from the analysis module.
    # If it fails, we'll implement a fallback.
    
    try:
        # Try to load aggregated data which might contain trial-level info
        data = load_aggregated_data()
        
        # Check if data is a DataFrame or a dict
        if isinstance(data, dict):
            # Look for trial-level data in the dict
            if 'trial_data' in data:
                df = data['trial_data']
            elif 'trial_level' in data:
                df = data['trial_level']
            else:
                # If no trial-level data found, we might need to construct it
                # For now, let's assume the data is in a DataFrame format
                df = pd.DataFrame()
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            df = pd.DataFrame()
        
        # If the dataframe is empty or doesn't have the required columns,
        # we need to construct it from other sources.
        if df.empty or not all(col in df.columns for col in ['subject_id', 'trial_id', 'condition', 'synchrony', 'rt']):
            # Fallback: Try to load from files
            # This part assumes that the previous tasks have saved the necessary data
            # Let's try to load synchrony metrics and behavioral data
            
            # Load synchrony metrics (might be subject-level, but we need trial-level)
            # If trial-level synchrony is not available, we might need to compute it
            # from the epochs. However, T035 implies we have trial-level data.
            
            # For now, let's assume we can load the data from the analysis module
            # or from files. If not, we'll create a placeholder with the correct structure.
            
            # Since we cannot fabricate data, we must ensure the data exists.
            # If the data doesn't exist, we should raise an error.
            raise FileNotFoundError("Trial-level data not found. Ensure T035 has been run successfully.")
        
    except FileNotFoundError as e:
        print(f"Error loading data: {e}")
        # If we can't load the data, we should not create a fake file.
        # Instead, we should exit with an error.
        sys.exit(1)
    
    # Ensure the required columns are present
    required_columns = ['subject_id', 'trial_id', 'condition', 'synchrony', 'rt']
    if not all(col in df.columns for col in required_columns):
        # If columns are missing, we might need to rename or construct them
        # For now, let's assume the data is in the correct format
        print("Warning: Some required columns are missing. Checking data structure...")
        print(df.columns.tolist())
        # If the structure is different, we might need to adjust
        # But since we cannot fabricate, we must ensure the data is correct
        if not all(col in df.columns for col in required_columns):
            print("Error: Required columns not found in the data.")
            sys.exit(1)
    
    # Filter out rows with missing synchrony (NaN)
    df_clean = df.dropna(subset=['synchrony'])
    
    # Ensure the columns are in the correct order
    df_clean = df_clean[required_columns]
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    df_clean.to_csv(output_path, index=False)
    print(f"Successfully generated {output_path} with {len(df_clean)} rows.")
    
    return output_path

if __name__ == "__main__":
    generate_trial_level_synchrony_csv()
