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

def ensure_directories(output_path: Path):
    """Ensure the output directory exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

def load_marginal_frequencies(input_path: Path) -> pd.DataFrame:
    """
    Load marginal frequencies from normalized ingredients.
    Expected columns: ingredient_id, canonical_name, frequency.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Marginal frequencies file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    required_cols = ['ingredient_id', 'frequency']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Input file missing required columns: {required_cols}. Found: {df.columns.tolist()}")
    
    return df[['ingredient_id', 'frequency']]

def load_positional_ranks(input_path: Path) -> pd.DataFrame:
    """
    Load positional ranks. This data might come from the processed recipe list
    where ingredients are ordered.
    Expected columns: ingredient_id, avg_position or similar.
    For this task, if positional data is missing, we default to frequency-based logic only,
    but we check for the file existence if it's a strict requirement.
    """
    if input_path.exists():
        df = pd.read_csv(input_path)
        # Normalize column names if necessary
        if 'avg_position' not in df.columns and 'position' in df.columns:
            df['avg_position'] = df['position']
        return df
    else:
        logger.warning(f"Positional ranks file not found: {input_path}. Proceeding with frequency-based role derivation only.")
        return pd.DataFrame()

def load_co_occurrence_matrix(input_path: Path) -> pd.DataFrame:
    """
    Load co-occurrence matrix if it exists.
    IMPORTANT: Per FR-005, we must EXCLUDE co-occurrence data from role derivation
    to ensure independence. This function is provided for potential future validation
    or if the logic changes, but the derivation logic below will NOT use it.
    """
    if input_path.exists():
        return pd.read_parquet(input_path)
    return pd.DataFrame()

def load_reference_ingredients(input_path: Path) -> pd.DataFrame:
    """
    Load reference ingredients if a specific canonical list is needed.
    """
    if input_path.exists():
        return pd.read_csv(input_path)
    return pd.DataFrame()

def verify_exclusion_of_co_occurrence(co_occurrence_data: pd.DataFrame):
    """
    Verify that co-occurrence data is not used in the calculation logic.
    This is a sanity check for the implementation.
    """
    if not co_occurrence_data.empty:
        logger.warning("Co-occurrence data loaded but must be excluded from role derivation per FR-005.")
        # We do not raise here to allow the script to run, but we log a warning.
        # The actual derivation function below does not accept co_occurrence as an argument.

def calculate_functional_role(marginal_freq_df: pd.DataFrame, positional_df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive functional role (primary, secondary, garnish) based on position and frequency.
    
    Logic:
    1. Calculate marginal frequency from raw recipe list ONLY (already done in input).
    2. If positional data exists, use it. Otherwise, assume position is correlated with frequency
       (high frequency ingredients are often primary, but we rely on the explicit rank if available).
    
    Heuristics (adjustable):
    - Primary: High frequency AND (low average position if available).
    - Secondary: Medium frequency.
    - Garnish: Low frequency OR high average position.
    
    Since we must exclude co-occurrence, we rely solely on:
    - Frequency (marginal count)
    - Position (if available)
    
    We will use quantiles on frequency to define thresholds.
    """
    if marginal_freq_df.empty:
        raise ValueError("Marginal frequency DataFrame is empty.")
    
    result_df = marginal_freq_df.copy()
    
    # Define thresholds based on frequency distribution
    # Primary: Top 20% by frequency
    # Secondary: Next 50%
    # Garnish: Bottom 30%
    # This is a heuristic; real world might need more complex NLP or position logic.
    
    freq_quantiles = result_df['frequency'].quantile([0.3, 0.8])
    threshold_garnish = freq_quantiles[0.3]
    threshold_primary = freq_quantiles[0.8]
    
    def assign_role(freq, pos=None):
        # If positional data is available and significant, we could adjust,
        # but per task description, we rely on marginal frequency primarily if pos is missing.
        # If pos is available, we might lower the threshold for 'primary' if pos is very low (1st ingredient).
        
        if pos is not None and pd.notna(pos):
            # If it's in the top 3 positions, it's likely primary regardless of frequency (if freq > 0)
            if pos <= 3 and freq > 0:
                return 'primary'
        
        if freq >= threshold_primary:
            return 'primary'
        elif freq >= threshold_garnish:
            return 'secondary'
        else:
            return 'garnish'
    
    if not positional_df.empty and 'avg_position' in positional_df.columns:
        # Merge to get positions
        merged = result_df.merge(positional_df[['ingredient_id', 'avg_position']], on='ingredient_id', how='left')
        merged['functional_role'] = merged.apply(
            lambda row: assign_role(row['frequency'], row['avg_position']), axis=1
        )
        return merged[['ingredient_id', 'canonical_name', 'frequency', 'functional_role']]
    else:
        # No positional data, use frequency only
        result_df['functional_role'] = result_df['frequency'].apply(assign_role)
        return result_df[['ingredient_id', 'canonical_name', 'frequency', 'functional_role']]

def save_output(df: pd.DataFrame, output_path: Path):
    """Save the derived functional roles to CSV."""
    ensure_directories(output_path)
    df.to_csv(output_path, index=False)
    logger.info(f"Functional roles saved to {output_path}")

def main():
    # Paths relative to project root
    # Assuming project root is the parent of 'code'
    project_root = Path(__file__).resolve().parent.parent
    
    input_freq_path = project_root / "data" / "processed" / "normalized_ingredients.csv"
    input_pos_path = project_root / "data" / "processed" / "positional_ranks.csv" # Optional
    input_co_path = project_root / "data" / "processed" / "co_occurrence_matrix.parquet" # For verification only
    output_path = project_root / "data" / "processed" / "functional_roles.csv"
    
    logger.info(f"Starting functional role derivation. Input: {input_freq_path}")
    
    try:
        # Load data
        marginal_freq_df = load_marginal_frequencies(input_freq_path)
        positional_df = load_positional_ranks(input_pos_path)
        co_occurrence_df = load_co_occurrence_matrix(input_co_path)
        
        # Verify exclusion constraint
        verify_exclusion_of_co_occurrence(co_occurrence_df)
        
        # Calculate roles
        result_df = calculate_functional_role(marginal_freq_df, positional_df)
        
        # Save
        save_output(result_df, output_path)
        
        logger.info("Task T014b completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during derivation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
