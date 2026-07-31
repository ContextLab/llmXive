import os
import sys
import logging
import pandas as pd
from pathlib import Path
from config.environment import ensure_directories

logger = logging.getLogger(__name__)

def load_model_results(input_path: Path) -> pd.DataFrame:
    """
    Load the model results CSV containing coefficients, p-values, and adjusted p-values.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Model results file not found at {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded model results with {len(df)} rows from {input_path}")
    return df

def extract_summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract summary statistics (coefficient, p-value, adjusted p-value) for the primary 
    relationship of interest (heteroplasmy burden vs age) from the model results.
    
    This function filters the results to the specific row representing the main effect 
    of burden on age and selects the relevant columns.
    """
    # Filter for the main effect row (assuming the model output includes a 'term' column)
    # The Rank-OLS model in T024 should have a term for 'rank(burden)' or similar
    main_effect_mask = df['term'].str.contains('burden', case=False, na=False)
    
    if not main_effect_mask.any():
        # Fallback: if term column doesn't exist or doesn't match, assume first row is main effect
        # This handles cases where the model output format might differ slightly
        logger.warning("Could not find 'burden' term in results. Using first row as main effect.")
        summary_df = df.iloc[[0]].copy()
    else:
        summary_df = df[main_effect_mask].copy()
    
    # Select only the required columns
    required_cols = ['term', 'coefficient', 'p_value', 'p_value_adj']
    available_cols = [c for c in required_cols if c in summary_df.columns]
    
    if len(available_cols) < 3:
        missing = set(required_cols) - set(available_cols)
        raise ValueError(f"Missing required columns in model results: {missing}")
    
    summary_df = summary_df[available_cols]
    
    # Add metadata columns
    summary_df['analysis_type'] = 'Rank-OLS'
    summary_df['dependent_variable'] = 'age'
    summary_df['independent_variable'] = 'mitochondrial_burden'
    
    logger.info(f"Extracted summary statistics: {summary_df.to_dict('records')}")
    return summary_df

def write_summary_statistics(df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the summary statistics to a CSV file.
    """
    ensure_directories([output_path.parent])
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote summary statistics to {output_path}")

def main():
    """
    Main entry point for generating summary statistics.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths based on project structure
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / "data" / "processed" / "model_results.csv"
    output_path = base_dir / "data" / "processed" / "analysis_results.csv"
    
    logger.info(f"Starting summary generation. Input: {input_path}, Output: {output_path}")
    
    try:
        # Load model results
        model_results = load_model_results(input_path)
        
        # Extract summary statistics
        summary = extract_summary_statistics(model_results)
        
        # Write output
        write_summary_statistics(summary, output_path)
        
        logger.info("Summary statistics generation completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to generate summary statistics: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
