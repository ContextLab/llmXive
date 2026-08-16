import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import hashlib

# -----------------------------------------------------------------------------
# Logging Setup
# -----------------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    """Configure logging for the ingestion module."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    return logger

logger = setup_logging()

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def setup_directories() -> Tuple[Path, Path]:
    """Ensure required output directories exist."""
    project_root = Path(__file__).resolve().parent.parent
    data_processed = project_root / "data" / "processed"
    data_processed.mkdir(parents=True, exist_ok=True)
    return project_root, data_processed

def load_and_align_data(
    input_path: Path,
    use_mock: bool = False
) -> pd.DataFrame:
    """
    Load the raw dataset and align teacher/student scores.
    Handles missing student_scalar by marking exclusion.
    """
    logger.info(f"Loading dataset from {input_path} (mock={use_mock})")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        if input_path.suffix == '.parquet':
            df = pd.read_parquet(input_path)
        elif input_path.suffix == '.csv':
            df = pd.read_csv(input_path)
        else:
            raise ValueError(f"Unsupported file format: {input_path.suffix}")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    # Basic alignment: ensure required columns exist conceptually
    # The schema discovery (T038) ensures column names match logical fields.
    # We assume 'prompt', 'teacher_scores', 'student_scalar', 'human_annotations' exist
    # or are mapped correctly by the loader logic in T037/T038.
    
    required_cols = ['prompt', 'student_scalar']
    for col in required_cols:
        if col not in df.columns:
            # Attempt to handle if wrapped in object or json string
            if col == 'student_scalar' and 'student_scores' in df.columns:
                logger.warning("Column 'student_scalar' missing, checking 'student_scores'...")
                # This is a placeholder for complex JSON parsing if needed
                # For now, we assume T038 handled the mapping to 'student_scalar'
                raise ValueError(f"Required column '{col}' not found in dataset.")
    
    # Mark missing student_scalar
    if 'student_scalar' in df.columns:
        missing_mask = df['student_scalar'].isna()
        if missing_mask.any():
            logger.info(f"Marking {missing_mask.sum()} samples as excluded due to missing student_scalar.")
            # We add a column for exclusion reason, but don't drop yet (T024 handles final filtering)
            df['excluded_reason'] = ''
            df.loc[missing_mask, 'excluded_reason'] = 'missing_student_scalar'
    else:
        # If the column doesn't exist at all, mark all as excluded
        df['excluded_reason'] = 'missing_student_scalar'
        logger.warning("Column 'student_scalar' entirely missing. Marking all samples as excluded.")

    return df

def identify_primary_quality_dimension(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive the primary_dimension for each sample based on:
    1. Prompt metadata (if available and parseable).
    2. Existing 'primary_dimension' column (if present).
    3. Deterministic fallback to 'Alignment'.
    
    Returns the dataframe with the 'primary_dimension' column populated (no nulls).
    """
    logger.info("Identifying primary quality dimensions...")
    
    # Initialize with nulls to track where we need fallback
    if 'primary_dimension' in df.columns:
        df['primary_dimension'] = df['primary_dimension'].astype(str)
        # Clean existing values (strip whitespace, handle 'nan')
        df['primary_dimension'] = df['primary_dimension'].replace(['nan', 'NaN', 'None'], None)
    else:
        df['primary_dimension'] = None

    fallback_count = 0
    metadata_count = 0
    column_count = 0

    # Valid dimensions
    valid_dims = {'Alignment', 'Realism', 'Aesthetics', 'Plausibility'}

    # Check if we have a metadata column (often 'prompt_metadata' or similar)
    # We assume the schema discovery (T038) would have mapped a metadata field if it existed.
    # If not, we try to parse the prompt text for hints or use a hash.
    
    has_metadata_col = 'prompt_metadata' in df.columns
    has_existing_col = 'primary_dimension' in df.columns

    # 1. Try Metadata Rule
    if has_metadata_col:
        logger.info("Found 'prompt_metadata' column. Attempting to parse primary_dimension...")
        # Assume prompt_metadata is a JSON string or dict
        for idx, row in df.iterrows():
            if pd.notna(df.at[idx, 'primary_dimension']):
                continue # Already filled by previous logic or existing column
            
            meta = row.get('prompt_metadata')
            if isinstance(meta, str):
                try:
                    meta_dict = json.loads(meta)
                    if 'primary_dimension' in meta_dict:
                        val = meta_dict['primary_dimension']
                        if val in valid_dims:
                            df.at[idx, 'primary_dimension'] = val
                            metadata_count += 1
                            continue
                except json.JSONDecodeError:
                    pass
            elif isinstance(meta, dict):
                if 'primary_dimension' in meta:
                    val = meta['primary_dimension']
                    if val in valid_dims:
                        df.at[idx, 'primary_dimension'] = val
                        metadata_count += 1
                        continue

    # 2. Try Existing Column Rule (if not filled yet)
    if has_existing_col:
        # Re-check for nulls after metadata attempt
        null_mask = df['primary_dimension'].isna()
        if null_mask.any():
            # Use existing values if they are valid, else mark for fallback
            # (Logic: if we are here, the existing column had nulls or invalid data)
            # We treat the existing column as a source, but if it's null, we fall back.
            # The loop below handles the fallback for remaining nulls.
            pass

    # 3. Fallback Rule (Hash or Default)
    # For remaining nulls, we use a deterministic hash of the prompt text
    remaining_mask = df['primary_dimension'].isna()
    if remaining_mask.any():
        logger.info(f"Applying fallback rule for {remaining_mask.sum()} samples.")
        
        # Deterministic hash function mapping to dimensions
        def hash_to_dimension(prompt_text: str) -> str:
            if not isinstance(prompt_text, str) or not prompt_text:
                return 'Alignment'
            h = hashlib.md5(prompt_text.encode('utf-8')).hexdigest()
            # Use first char of hash
            val = int(h[0], 16) % 4
            dims = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
            return dims[val]

        df.loc[remaining_mask, 'primary_dimension'] = df.loc[remaining_mask, 'prompt'].apply(hash_to_dimension)
        fallback_count = remaining_mask.sum()

    # Ensure no nulls remain
    if df['primary_dimension'].isna().any():
        logger.warning("Some primary_dimension values are still null. Filling with default 'Alignment'.")
        df['primary_dimension'] = df['primary_dimension'].fillna('Alignment')
        fallback_count += df['primary_dimension'].isna().sum() # Should be 0 now

    logger.info(f"Primary dimension assignment complete: Metadata={metadata_count}, Existing={column_count}, Fallback={fallback_count}")
    
    return df

def print_summary(df: pd.DataFrame) -> None:
    """Print summary statistics of the ingested and aligned data."""
    logger.info("--- Ingestion Summary ---")
    logger.info(f"Total samples: {len(df)}")
    
    if 'excluded_reason' in df.columns:
        excluded = df[df['excluded_reason'].notna()]
        logger.info(f"Excluded samples: {len(excluded)}")
        if len(excluded) > 0:
            logger.info(f"Exclusion reasons:\n{excluded['excluded_reason'].value_counts()}")
    
    if 'primary_dimension' in df.columns:
        logger.info(f"Primary dimension distribution:\n{df['primary_dimension'].value_counts()}")
    
    # Check for nulls in critical columns
    for col in ['prompt', 'student_scalar', 'primary_dimension']:
        if col in df.columns:
            nulls = df[col].isna().sum()
            if nulls > 0:
                logger.warning(f"Column '{col}' has {nulls} null values.")
            else:
                logger.info(f"Column '{col}' has no null values.")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Ingest and align Z-Reward dataset.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/z_reward.parquet",
        help="Path to the input dataset file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/raw_data.parquet",
        help="Path to the output processed dataset file."
    )
    parser.add_argument(
        "--use-mock-data",
        action="store_true",
        help="Flag indicating if the input is mock data."
    )
    return parser.parse_args()

def main() -> None:
    """Main entry point for the ingestion task."""
    args = parse_args()
    project_root, data_processed = setup_directories()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # 1. Load and Align
    try:
        df = load_and_align_data(input_path, use_mock=args.use_mock_data)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during loading/alignment: {e}")
        sys.exit(1)

    # 2. Identify Primary Dimension (T014)
    try:
        df = identify_primary_quality_dimension(df)
    except Exception as e:
        logger.error(f"Error during primary dimension identification: {e}")
        sys.exit(1)

    # 3. Save Output
    try:
        if output_path.suffix == '.parquet':
            df.to_parquet(output_path, index=False)
        else:
            df.to_csv(output_path, index=False)
        logger.info(f"Saved aligned data to {output_path}")
    except Exception as e:
        logger.error(f"Error saving output: {e}")
        sys.exit(1)

    # 4. Print Summary
    print_summary(df)

    # 5. Log specific T014 details to a JSON log if needed for traceability
    # (Optional, but good practice for the "log entry for samples using fallback" requirement)
    # We already logged the counts in identify_primary_quality_dimension.

if __name__ == "__main__":
    main()