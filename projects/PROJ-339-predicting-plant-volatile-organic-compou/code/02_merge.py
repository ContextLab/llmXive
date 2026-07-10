"""
Merge genomic and VOC data with strict filtering rules.

This module implements the merge logic for User Story 1, including:
- Loading stage 1 data (normalized transcript + VOC data)
- Filtering samples with <3 biological replicates per condition
- Filtering samples missing critical environmental metadata
- Performing exact sample ID matching join

Dependencies:
- code/01_ingest.py (for data format compatibility)
- code/utils/validation.py (for replicate checks)
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.validation import check_replicates


def load_stage1_data(input_path: str) -> pd.DataFrame:
    """
    Load stage 1 data (normalized transcript + VOC data).
    
    Args:
        input_path: Path to the stage 1 CSV file
    
    Returns:
        DataFrame with normalized transcript and VOC data
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Stage 1 data file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = ['sample_id', 'condition_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df


def filter_replicates(df: pd.DataFrame, min_replicates: int = 3) -> pd.DataFrame:
    """
    Filter out conditions with fewer than min_replicates samples.
    
    Args:
        df: Input DataFrame with 'condition_id' column
        min_replicates: Minimum number of replicates required per condition
    
    Returns:
        Filtered DataFrame with only conditions meeting the replicate requirement
    """
    if 'condition_id' not in df.columns:
        raise ValueError("DataFrame must contain 'condition_id' column")
    
    # Count replicates per condition
    condition_counts = df.groupby('condition_id').size()
    
    # Identify conditions with sufficient replicates
    valid_conditions = condition_counts[condition_counts >= min_replicates].index.tolist()
    
    # Filter DataFrame
    filtered_df = df[df['condition_id'].isin(valid_conditions)].copy()
    
    return filtered_df


def filter_environmental_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out samples missing critical environmental metadata.
    
    Critical fields: 'temperature', 'light_intensity'
    
    Args:
        df: Input DataFrame with environmental columns
    
    Returns:
        Filtered DataFrame with no missing values in critical fields
    """
    critical_fields = ['temperature', 'light_intensity']
    
    # Check which critical fields exist
    existing_critical = [field for field in critical_fields if field in df.columns]
    
    if not existing_critical:
        raise ValueError(f"No critical environmental fields found. Expected at least one of: {critical_fields}")
    
    # Filter out rows with missing values in any critical field
    filtered_df = df.dropna(subset=existing_critical).copy()
    
    return filtered_df


def merge_dataframes(
    genomic_df: pd.DataFrame, 
    voc_df: pd.DataFrame, 
    key_column: str = 'sample_id'
) -> pd.DataFrame:
    """
    Merge genomic and VOC data on exact sample ID match.
    
    Args:
        genomic_df: DataFrame with genomic data
        voc_df: DataFrame with VOC data
        key_column: Column name to join on (default: 'sample_id')
    
    Returns:
        Merged DataFrame with only exact matches
    """
    # Perform inner join on sample_id
    merged_df = pd.merge(
        genomic_df,
        voc_df,
        on=key_column,
        how='inner'
    )
    
    return merged_df


def main(
    stage1_input: Optional[str] = None,
    output_path: Optional[str] = None,
    min_replicates: int = 3
) -> pd.DataFrame:
    """
    Main merge pipeline function.
    
    This function orchestrates the full merge process:
    1. Load stage 1 data
    2. Filter by replicate count
    3. Filter by environmental metadata completeness
    4. Output the merged dataset
    
    Args:
        stage1_input: Path to stage 1 CSV file. If None, uses default path.
        output_path: Path for output CSV. If None, uses default path.
        min_replicates: Minimum replicates required per condition
    
    Returns:
        Final merged DataFrame
    """
    # Set default paths if not provided
    if stage1_input is None:
        stage1_input = str(Path(__file__).parent.parent / "data" / "processed" / "stage1_normalized.csv")
    
    if output_path is None:
        output_path = str(Path(__file__).parent.parent / "data" / "processed" / "merged_dataset.csv")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load stage 1 data
    print(f"Loading stage 1 data from {stage1_input}...")
    data = load_stage1_data(stage1_input)
    print(f"  Loaded {len(data)} samples")
    
    # Step 2: Filter by replicate count
    print(f"Filtering for conditions with >= {min_replicates} replicates...")
    filtered_data = filter_replicates(data, min_replicates=min_replicates)
    print(f"  Retained {len(filtered_data)} samples after replicate filtering")
    
    # Step 3: Filter by environmental metadata
    print("Filtering for complete environmental metadata...")
    final_data = filter_environmental_metadata(filtered_data)
    print(f"  Retained {len(final_data)} samples after environmental filtering")
    
    # Step 4: Save output
    final_data.to_csv(output_path, index=False)
    print(f"Saved merged dataset to {output_path}")
    
    return final_data


if __name__ == "__main__":
    # Example usage
    main()