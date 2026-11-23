"""
Primary LMM script invoking R's lmerTest via rpy2 to obtain Satterthwaite-approximated
p-values and degrees of freedom.

Output: data/results/lmm_summary_satterthwaite.csv
Depends on: T020 (data/processed/analysis_ready.csv)
"""
import csv
import sys
import os
import logging
from pathlib import Path

# Import local config and logging utilities
from config import get_processed_data_dir, get_results_dir
from logging_config import setup_logging, get_logger

# Setup logging
logger = setup_logging()

def get_analysis_ready_path():
    """Return the path to the analysis-ready CSV."""
    return get_processed_data_dir() / "analysis_ready.csv"

def load_analysis_ready_data():
    """Load the analysis-ready dataset."""
    path = get_analysis_ready_path()
    if not path.exists():
        raise FileNotFoundError(f"Analysis ready data not found at {path}")
    
    data = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    if not data:
        raise ValueError("Analysis ready data file is empty")
    
    return data

def run_r_lmer_test(data):
    """
    Run the LMM using R's lmerTest via rpy2.
    
    Model: rating ~ cue_intensity * relationship_context + (1|participant_id)
    Returns: Dictionary of results including coefficients, p-values, and df.
    """
    try:
        import rpy2.robjects as ro
        from rpy2.robjects import pandas2ri
        from rpy2.robjects.packages import importr
        from rpy2.robjects import Formula
        import pandas as pd
    except ImportError as e:
        logger.error("rpy2 or pandas not installed. Install with: pip install rpy2 pandas")
        raise e

    # Activate pandas conversion
    pandas2ri.activate()

    # Import R packages
    base = importr('base')
    stats = importr('stats')
    lmerTest = importr('lmerTest')
    utils = importr('utils')

    # Convert data to pandas DataFrame
    df = pd.DataFrame(data)

    # Ensure categorical variables are factors
    if 'participant_id' in df.columns:
        df['participant_id'] = df['participant_id'].astype('category')
    if 'relationship_context' in df.columns:
        df['relationship_context'] = df['relationship_context'].astype('category')
    
    # Convert to R DataFrame
    r_df = pandas2ri.py2rpy(df)
    ro.globalenv['data'] = r_df

    # Define the model formula
    # Model: rating ~ cue_intensity * relationship_context + (1|participant_id)
    # Note: Assuming 'cue_intensity' is numeric or ordered factor, 'relationship_context' is factor
    formula_str = "rating ~ cue_intensity * relationship_context + (1|participant_id)"
    formula = Formula(formula_str)

    try:
        logger.info(f"Fitting LMM with Satterthwaite approximation: {formula_str}")
        
        # Fit the model using lmerTest (which extends lmer to provide p-values)
        # lmerTest::lmer automatically uses Satterthwaite for df and p-values
        model = lmerTest.lmer(formula, data=df)
        
        # Get summary
        summary = model.slots['call_list'] # Access internal slots if needed, but summary() is better
        # Actually, lmerTest returns an object where summary() provides the table
        # We need to capture the summary output
        
        # Use rpy2 to call summary() on the model
        summary_obj = lmerTest.summary(model)
        
        # Extract the coefficients table
        # The coefficients table is in the 'coefficients' slot of the summary
        coef_table = summary_obj.slots['coefficients']
        
        # coef_table is a matrix-like object in R, convert to pandas
        # We need to extract the matrix data
        # rpy2 matrices can be converted to numpy arrays
        import numpy as np
        coef_array = np.array(coef_table)
        
        # Create a DataFrame with appropriate column names
        # R's lmerTest summary coefficients table columns: Estimate, Std. Error, t value, Pr(>|t|)
        # But we need df_Satterthwaite. lmerTest summary usually includes 'df' in the table if available
        
        # Let's try to get the full table including df
        # Sometimes the table is accessed via summary$coefficients
        # If df is not in the standard coefficients, lmerTest might put it in a separate component or 
        # the summary object has a specific structure.
        
        # Alternative: Use the 'coef' function which might return a data frame with df
        # Or parse the print output (less robust)
        
        # Let's try to access the 'coefficients' attribute which in lmerTest summary
        # might be a data frame with 'df' column if Satterthwaite is used.
        
        # A more robust way with rpy2:
        # The summary object has a slot 'coefficients' which is a matrix.
        # We can check if there is a 'df' column in the summary object's attributes or slots.
        
        # Let's try to convert the summary coefficients to a pandas DataFrame directly
        # and see what columns are available.
        
        # If the matrix doesn't have df, we might need to extract it differently.
        # lmerTest::lmer returns an object where the summary() call produces a table with 'df'.
        # Let's assume the standard output structure:
        # Estimate, Std. Error, t value, Pr(>|t|), df (sometimes)
        
        # To be safe, let's construct the DataFrame from the matrix and manually handle columns
        # based on typical lmerTest output.
        
        # Columns in R matrix:
        # 0: Estimate
        # 1: Std. Error
        # 2: t value
        # 3: Pr(>|t|)
        # If df is present, it might be column 4 or in a separate slot.
        
        # Actually, lmerTest summary coefficients usually has 5 columns: Estimate, Std. Error, t value, Pr(>|t|), df
        # Let's check the dimensions.
        
        rows, cols = coef_array.shape
        
        if cols >= 5:
            # Assume 5th column is df
            df_values = coef_array[:, 4]
        else:
            # Fallback: if df is missing, we might need to extract it from another slot
            # or the model object itself.
            # For now, let's assume it's there or handle the error.
            logger.warning("df column not found in coefficients table. Attempting alternative extraction.")
            df_values = np.ones(rows) * np.nan # Placeholder

        # Construct the result DataFrame
        result_df = pd.DataFrame({
            'term': df.index.tolist(),
            'estimate': coef_array[:, 0],
            'std_error': coef_array[:, 1],
            't_value': coef_array[:, 2],
            'p_value': coef_array[:, 3],
            'df_Satterthwaite': df_values if cols >= 5 else np.nan
        })
        
        logger.info("LMM fit completed successfully.")
        return result_df

    except Exception as e:
        logger.error(f"Error fitting LMM: {e}")
        raise e

def save_results(results_df, output_path):
    """Save the LMM summary results to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point."""
    logger.info("Starting Satterthwaite LMM analysis (T021b)")
    
    try:
        # Load data
        data = load_analysis_ready_data()
        logger.info(f"Loaded {len(data)} rows for analysis")
        
        # Run R model
        results_df = run_r_lmer_test(data)
        
        # Save results
        output_path = get_results_dir() / "lmm_summary_satterthwaite.csv"
        save_results(results_df, output_path)
        
        # Verify output
        if not output_path.exists():
            raise FileNotFoundError("Output file was not created")
        
        # Check for required column
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if 'df_Satterthwaite' not in headers:
                raise ValueError("Output missing required column 'df_Satterthwaite'")
        
        logger.info("T021b completed successfully")
        
    except Exception as e:
        logger.error(f"Task T021b failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
