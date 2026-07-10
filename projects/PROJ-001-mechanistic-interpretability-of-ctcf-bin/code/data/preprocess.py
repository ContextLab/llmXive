import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

import pandas as pd
import numpy as np

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.extract_features import load_manifest
from setup_env import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'preprocess.log')
    ]
)
logger = logging.getLogger(__name__)

MIN_CELL_TYPES_REQUIRED = 5

def load_processed_dataset(dataset_path: Path) -> pd.DataFrame:
    """Load the dataset produced by extract_features (Parquet)."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {dataset_path}")
    logger.info(f"Loading dataset from {dataset_path}")
    return pd.read_parquet(dataset_path)

def identify_missing_atac_cells(df: pd.DataFrame, cell_type_col: str = 'cell_type') -> Set[str]:
    """
    Identify cell types where ATAC-seq data is missing.
    
    Based on the spec edge case: "exclude that cell type... or impute".
    We choose exclusion. We assume missing ATAC signal is represented by NaN
    in the 'atac_signal' column or a flag in the metadata.
    """
    logger.info("Identifying cell types with missing ATAC-seq data...")
    
    # Group by cell_type and check for NaN in atac_signal
    # Assuming the dataset has columns: sequence, cell_type, atac_signal, h3k27ac_signal, is_peak
    if 'atac_signal' not in df.columns:
        logger.warning("Column 'atac_signal' not found. Checking for 'atac' or similar.")
        # Fallback check if column name varies
        atac_col = next((c for c in df.columns if 'atac' in c.lower()), None)
        if not atac_col:
            logger.error("No ATAC-seq related column found. Cannot filter.")
            return set()
    else:
        atac_col = 'atac_signal'

    # Check for NaN values per cell type
    missing_cells = set()
    cell_groups = df.groupby(cell_type_col)
    
    for cell_type, group in cell_groups:
        if group[atac_col].isna().all():
            missing_cells.add(cell_type)
            logger.warning(f"Cell type '{cell_type}' has 100% missing ATAC-seq data. Marking for exclusion.")
        elif group[atac_col].isna().any():
            # If partial missing, we might still exclude or impute. 
            # Per spec: "exclude that cell type". We will exclude if >50% missing to be safe,
            # or strictly if any missing if the spec implies strict exclusion.
            # Let's implement strict exclusion for any missing data to ensure integrity as per "exclude... to ensure data integrity".
            missing_cells.add(cell_type)
            logger.warning(f"Cell type '{cell_type}' has some missing ATAC-seq data. Marking for exclusion.")

    return missing_cells

def filter_by_cell_types(df: pd.DataFrame, exclude_cells: Set[str], cell_type_col: str = 'cell_type') -> pd.DataFrame:
    """Filter the dataframe to remove rows belonging to excluded cell types."""
    if not exclude_cells:
        logger.info("No cell types to exclude.")
        return df
    
    initial_count = len(df)
    initial_types = df[cell_type_col].unique().tolist()
    
    filtered_df = df[~df[cell_type_col].isin(exclude_cells)]
    
    final_count = len(filtered_df)
    final_types = filtered_df[cell_type_col].unique().tolist()
    
    logger.info(f"Filtered {initial_count} rows to {final_count} rows.")
    logger.info(f"Excluded cell types: {exclude_cells}")
    logger.info(f"Remaining cell types: {final_types}")
    
    return filtered_df

def check_minimum_cell_types(df: pd.DataFrame, min_count: int = MIN_CELL_TYPES_REQUIRED, cell_type_col: str = 'cell_type') -> bool:
    """Check if the remaining dataset has enough cell types."""
    remaining_types = df[cell_type_col].nunique()
    logger.info(f"Remaining unique cell types: {remaining_types} (Required: {min_count})")
    return remaining_types >= min_count

def generate_scope_revision_trigger(output_path: Path, missing_cells: Set[str], remaining_cells: Set[str]):
    """Generate a trigger file if the dataset falls below the minimum cell type threshold."""
    content = {
        "trigger": "SCOPE_REVISION_REQUIRED",
        "reason": f"Exclusion of cell types with missing ATAC-seq data resulted in fewer than {MIN_CELL_TYPES_REQUIRED} cell types.",
        "excluded_cell_types": list(missing_cells),
        "remaining_cell_types": list(remaining_cells),
        "action_required": "Re-run T003 (search_sources) to find additional cell types with ATAC-seq data.",
        "timestamp": str(pd.Timestamp.now())
    }
    
    with open(output_path, 'w') as f:
        json.dump(content, f, indent=2)
    
    logger.error(f"Scope revision trigger generated at {output_path}")
    raise RuntimeError(f"Scope revision required: {output_path}")

def main():
    logger.info("Starting T014: Preprocess - Exclude cell types with missing ATAC-seq data")
    
    # Paths
    manifest_path = project_root / 'data' / 'manifest.json'
    dataset_path = project_root / 'data' / 'processed' / 'unified_ctcf_dataset.parquet'
    output_path = project_root / 'data' / 'processed' / 'unified_ctcf_dataset_preprocessed.parquet'
    trigger_path = project_root / 'docs' / 'scope_revision_trigger.md'
    
    # Ensure output directory exists
    ensure_directories([output_path.parent, trigger_path.parent])
    
    # 1. Load the dataset produced by extract_features (T013)
    try:
        df = load_processed_dataset(dataset_path)
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed: {e}")
        sys.exit(1)
    
    if df.empty:
        logger.error("Dataset is empty. Cannot proceed.")
        sys.exit(1)

    # 2. Identify cell types with missing ATAC-seq data
    missing_cells = identify_missing_atac_cells(df)
    
    if not missing_cells:
        logger.info("No cell types found with missing ATAC-seq data. Skipping exclusion.")
        # Still save the dataset as preprocessed (no change) to maintain pipeline flow
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved preprocessed dataset to {output_path}")
        return

    # 3. Filter the dataset
    filtered_df = filter_by_cell_types(df, missing_cells)
    
    # 4. Check if we still have enough cell types
    if not check_minimum_cell_types(filtered_df):
        remaining_cells = set(filtered_df['cell_type'].unique())
        logger.error("Exclusion resulted in insufficient cell types.")
        # Generate trigger file
        generate_scope_revision_trigger(trigger_path, missing_cells, remaining_cells)
        # The pipeline should halt here as per spec
        sys.exit(1)
    
    # 5. Save the final preprocessed dataset
    filtered_df.to_parquet(output_path, index=False)
    logger.info(f"Successfully saved preprocessed dataset to {output_path}")
    logger.info(f"Final dataset shape: {filtered_df.shape}")
    
    # Log summary
    logger.info("Preprocessing complete. Dataset ready for model training.")

if __name__ == "__main__":
    main()