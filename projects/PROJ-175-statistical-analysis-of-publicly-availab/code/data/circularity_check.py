import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_marginal_frequencies(input_path: str) -> pd.DataFrame:
    """
    Load marginal frequencies from the functional roles CSV.
    Expected columns: ingredient_id, functional_role, marginal_frequency (or similar).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Marginal frequencies file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    # Normalize column names for safety
    df.columns = df.columns.str.strip().str.lower()
    
    # Identify the frequency column (could be 'frequency', 'marginal_frequency', etc.)
    freq_col = None
    possible_names = ['marginal_frequency', 'frequency', 'freq', 'count']
    for name in possible_names:
        if name in df.columns:
            freq_col = name
            break
    
    if freq_col is None:
        raise ValueError("Could not identify frequency column in marginal frequencies file.")
    
    return df[['ingredient_id', freq_col]].rename(columns={freq_col: 'marginal_frequency'})

def load_co_occurrence_matrix(input_path: str) -> pd.DataFrame:
    """
    Load co-occurrence matrix and convert to long format (ingredient_pair, co_occurrence).
    Expected: A square matrix or a long-format CSV with pairs.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Co-occurrence matrix file not found: {input_path}")
    
    # Try to detect format: if it's a square matrix, pivot; if long, just load
    df = pd.read_parquet(input_path) if input_path.endswith('.parquet') else pd.read_csv(input_path)
    
    df.columns = df.columns.str.strip().str.lower()
    
    # Check if it's already in long format (has 'ingredient_1', 'ingredient_2', 'co_occurrence')
    if 'ingredient_1' in df.columns and 'ingredient_2' in df.columns and 'co_occurrence' in df.columns:
        return df[['ingredient_1', 'ingredient_2', 'co_occurrence']]
    
    # If it's a square matrix (index=ingredients, columns=ingredients)
    if df.shape[0] == df.shape[1] and df.shape[0] > 1:
        # Reset index to make ingredients a column
        df_reset = df.reset_index()
        if 'index' in df_reset.columns:
            df_reset = df_reset.rename(columns={'index': 'ingredient_1'})
        else:
            # Assume first column is ingredient_1
            first_col = df_reset.columns[0]
            df_reset = df_reset.rename(columns={first_col: 'ingredient_1'})
        
        # Melt to long format
        long_df = df_reset.melt(
            id_vars=['ingredient_1'],
            var_name='ingredient_2',
            value_name='co_occurrence'
        )
        return long_df
    
    # Fallback: try to find columns that look like pairs
    raise ValueError("Could not determine format of co-occurrence matrix. Expected square matrix or long format with pair columns.")

def calculate_circularity(marginal_freq_df: pd.DataFrame, co_occurrence_df: pd.DataFrame) -> dict:
    """
    Calculate Pearson correlation between marginal frequency and co-occurrence.
    Returns a dictionary with the correlation coefficient and a warning flag.
    """
    # Merge on ingredient_id (assuming co_occurrence_df has ingredient_1 or similar as the key)
    # We need to match the 'ingredient_id' from marginal_freq_df to 'ingredient_1' or 'ingredient_2' in co_occurrence_df
    # For simplicity, we'll match to 'ingredient_1' and assume symmetry or use the first match.
    
    # Normalize column names
    marginal_freq_df.columns = marginal_freq_df.columns.str.strip().str.lower()
    co_occurrence_df.columns = co_occurrence_df.columns.str.strip().str.lower()
    
    # Ensure we have the right columns
    if 'ingredient_id' not in marginal_freq_df.columns:
        raise ValueError("marginal_freq_df must have 'ingredient_id' column.")
    
    # We need to aggregate co-occurrence per ingredient. 
    # If co_occurrence_df has (i, j, value), we can sum or average over j for each i.
    # Let's compute the mean co-occurrence for each ingredient (averaging over all partners).
    
    # Merge to get marginal frequency for ingredient_1
    merged = co_occurrence_df.merge(
        marginal_freq_df,
        left_on='ingredient_1',
        right_on='ingredient_id',
        how='inner'
    )
    
    if merged.empty:
        logger.warning("No matching ingredients found between marginal frequencies and co-occurrence matrix.")
        return {
            "correlation": None,
            "warning": True,
            "message": "No matching ingredients found.",
            "threshold": 0.1
        }
    
    # Aggregate: average co-occurrence per ingredient (ingredient_1)
    agg_df = merged.groupby('ingredient_id')['co_occurrence'].mean().reset_index()
    agg_df.columns = ['ingredient_id', 'mean_co_occurrence']
    
    # Merge with marginal frequency again to get both metrics
    final_df = marginal_freq_df.merge(
        agg_df,
        on='ingredient_id',
        how='inner'
    )
    
    if final_df.empty or len(final_df) < 2:
        logger.warning("Not enough data points to compute correlation.")
        return {
            "correlation": None,
            "warning": True,
            "message": "Insufficient data points for correlation.",
            "threshold": 0.1
        }
    
    # Calculate Pearson correlation
    # Drop NaNs
    clean_df = final_df.dropna(subset=['marginal_frequency', 'mean_co_occurrence'])
    
    if len(clean_df) < 2:
        logger.warning("Not enough non-NaN data points to compute correlation.")
        return {
            "correlation": None,
            "warning": True,
            "message": "Insufficient non-NaN data points.",
            "threshold": 0.1
        }
    
    corr, _ = pd.Series(clean_df['marginal_frequency']).corr(clean_df['mean_co_occurrence'], method='pearson')
    
    warning_flag = abs(corr) > 0.1 if corr is not None else False
    
    return {
        "correlation": float(corr) if corr is not None else None,
        "warning": warning_flag,
        "message": "Circularity detected" if warning_flag else "No significant circularity detected",
        "threshold": 0.1,
        "sample_size": len(clean_df)
    }

def save_output(result: dict, output_path: str):
    """
    Save the circularity check result to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Circularity check result saved to {output_path}")

def main():
    # Paths
    amendment_log_path = "data/amendment_log.json"
    marginal_freq_path = "data/processed/functional_roles.csv"
    co_occurrence_path = "data/processed/co_occurrence_matrix.parquet"
    output_path = "data/logs/circularity_warning.json"
    
    # Check if amendment log exists and is ratified
    if not os.path.exists(amendment_log_path):
        logger.warning("Amendment log not found. Skipping circularity check.")
        # Create a default warning if amendment log is missing
        result = {
            "correlation": None,
            "warning": True,
            "message": "Amendment log not found. Cannot proceed with circularity check.",
            "threshold": 0.1
        }
        save_output(result, output_path)
        return
    
    with open(amendment_log_path, 'r') as f:
        amendment_log = json.load(f)
    
    if amendment_log.get('status') != 'RATIFIED':
        logger.warning("Amendment log status is not RATIFIED. Skipping circularity check.")
        result = {
            "correlation": None,
            "warning": True,
            "message": "Amendment log status is not RATIFIED.",
            "threshold": 0.1
        }
        save_output(result, output_path)
        return
    
    # Check if co-occurrence matrix exists (it might not if T015 hasn't run yet)
    if not os.path.exists(co_occurrence_path):
        logger.warning("Co-occurrence matrix not found. Skipping circularity check.")
        result = {
            "correlation": None,
            "warning": True,
            "message": "Co-occurrence matrix not found.",
            "threshold": 0.1
        }
        save_output(result, output_path)
        return
    
    try:
        marginal_freq_df = load_marginal_frequencies(marginal_freq_path)
        co_occurrence_df = load_co_occurrence_matrix(co_occurrence_path)
        result = calculate_circularity(marginal_freq_df, co_occurrence_df)
        save_output(result, output_path)
        
        if result['warning']:
            logger.warning(f"Circularity warning: Correlation {result['correlation']:.4f} exceeds threshold {result['threshold']}.")
        else:
            logger.info(f"Circularity check passed: Correlation {result['correlation']:.4f} is within threshold.")
            
    except Exception as e:
        logger.error(f"Error during circularity check: {e}")
        result = {
            "correlation": None,
            "warning": True,
            "message": f"Error during check: {str(e)}",
            "threshold": 0.1
        }
        save_output(result, output_path)
        raise

if __name__ == "__main__":
    main()
