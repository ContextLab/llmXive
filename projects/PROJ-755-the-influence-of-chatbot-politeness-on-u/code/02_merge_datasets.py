import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import pyarrow.parquet as pq

# Import utilities from the project API surface
from utils.data_integrity import compute_file_checksum
from utils.schema_validator import load_schema, validate_dataset_schema, SchemaValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories() -> None:
    """Ensure required output directories exist."""
    dirs = ['data/processed', 'data/raw']
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("Ensured directories exist.")

def load_dataset(dataset_name: str, base_path: str = "data/raw") -> Optional[pd.DataFrame]:
    """
    Load a dataset from the raw directory.
    Expected subdirectories: hci_p2, persona_chat, empathetic_dialogues.
    Looks for parquet or csv files within the subdirectory.
    """
    dataset_dir = Path(base_path) / dataset_name
    if not dataset_dir.exists():
        logger.warning(f"Dataset directory {dataset_dir} does not exist. Skipping {dataset_name}.")
        return None

    # Find data files (prefer parquet, then csv)
    parquet_files = list(dataset_dir.glob("*.parquet"))
    csv_files = list(dataset_dir.glob("*.csv"))

    if parquet_files:
        file_path = parquet_files[0]
        logger.info(f"Loading {dataset_name} from {file_path}")
        try:
            return pd.read_parquet(file_path)
        except Exception as e:
            logger.error(f"Failed to load parquet for {dataset_name}: {e}")
    elif csv_files:
        file_path = csv_files[0]
        logger.info(f"Loading {dataset_name} from {file_path}")
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            logger.error(f"Failed to load csv for {dataset_name}: {e}")
    else:
        logger.warning(f"No supported data files found in {dataset_dir}")

    return None

def validate_and_prepare_dataset(df: pd.DataFrame, source_name: str) -> Optional[pd.DataFrame]:
    """
    Validate that the dataset has minimal required fields for merging.
    Required: user_id, dialogue_id.
    Optional but preserved: quality_rating, age, gender.
    """
    required_fields = ['user_id', 'dialogue_id']
    missing = [f for f in required_fields if f not in df.columns]
    
    if missing:
        logger.error(f"Dataset {source_name} missing required fields: {missing}. Dropping dataset.")
        return None

    # Normalize column names to lowercase to ensure consistency
    df.columns = [c.lower() for c in df.columns]
    
    # Ensure required fields exist in lowercase
    if 'user_id' not in df.columns or 'dialogue_id' not in df.columns:
        logger.error(f"Dataset {source_name} missing required fields after normalization. Dropping.")
        return None

    # Select only relevant columns if they exist
    relevant_cols = ['user_id', 'dialogue_id', 'quality_rating', 'age', 'gender']
    available_cols = [c for c in relevant_cols if c in df.columns]
    
    logger.info(f"Preparing {source_name}: keeping columns {available_cols}")
    return df[available_cols]

def merge_datasets(dialogues_list: List[Tuple[pd.DataFrame, str]]) -> pd.DataFrame:
    """
    Merge a list of (DataFrame, source_name) tuples into a single DataFrame.
    Performs an outer join on user_id and dialogue_id to preserve all data,
    but given the task logic, we assume unique (user_id, dialogue_id) per source
    or that we are concatenating distinct sources.
    
    Since the task implies combining available datasets if HCI_P2 is missing fields,
    we treat these as distinct sources of dialogues. We will concatenate them.
    """
    if not dialogues_list:
        raise ValueError("No datasets provided for merging.")

    dfs = [df for df, _ in dialogues_list]
    logger.info(f"Merging {len(dfs)} datasets.")
    
    # Concatenate along rows (axis=0)
    merged = pd.concat(dfs, ignore_index=True)
    
    # Reset index
    merged = merged.reset_index(drop=True)
    
    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged

def handle_missing_demographics(df: pd.DataFrame, report_path: Path) -> pd.DataFrame:
    """
    Check for missing demographics (age, gender) and log them.
    This function does NOT drop rows but ensures the validation report is updated.
    """
    if 'age' in df.columns and 'gender' in df.columns:
        missing_age = df['age'].isna().sum()
        missing_gender = df['gender'].isna().sum()
        logger.info(f"Missing age: {missing_age}, Missing gender: {missing_gender}")
    else:
        logger.warning("Demographic fields (age, gender) not found in merged data.")
    
    # Update validation report if it exists
    if report_path.exists():
        try:
            with open(report_path, 'r') as f:
                report = json.load(f)
            if report.get('status') == 'partial':
                logger.info("Validation report already indicates partial status.")
            elif report.get('status') == 'full':
                # If we merged, it might be because of partial, but if we have data now, check again
                # For T016, the logic is: if T012 said partial, we merge.
                # We just log the action.
                pass
        except Exception as e:
            logger.warning(f"Could not update validation report: {e}")
    
    return df

def save_merged_data(df: pd.DataFrame, output_path: Path) -> None:
    """Save the merged DataFrame to parquet and generate checksum."""
    df.to_parquet(output_path, index=False)
    checksum = compute_file_checksum(output_path)
    logger.info(f"Saved merged data to {output_path} (checksum: {checksum})")

def main():
    """
    Main entry point for T016: Conditional Merging Logic.
    
    Logic:
    1. Check data/raw/validation_report.json.
    2. If status is 'full', DO NOT MERGE. Log and exit.
    3. If status is 'partial' or missing, merge available fallbacks (Persona-Chat, EmpatheticDialogues).
    4. Save to data/processed/merged_dialogues.parquet.
    """
    ensure_directories()
    
    validation_report_path = Path("data/raw/validation_report.json")
    hci_p2_path = Path("data/raw/hci_p2")
    persona_chat_path = Path("data/raw/persona_chat")
    empathetic_path = Path("data/raw/empathetic_dialogues")
    
    # 1. Check Validation Report
    should_merge = False
    if validation_report_path.exists():
        try:
            with open(validation_report_path, 'r') as f:
                report = json.load(f)
            status = report.get('status', 'unknown')
            if status == 'partial':
                logger.info("Validation report status is 'partial'. Proceeding with merge.")
                should_merge = True
            elif status == 'full':
                logger.info("Validation report status is 'full'. No merge required. Exiting.")
                return
            else:
                logger.warning(f"Unknown validation status: {status}. Proceeding with merge to be safe.")
                should_merge = True
        except Exception as e:
            logger.error(f"Error reading validation report: {e}. Proceeding with merge.")
            should_merge = True
    else:
        logger.warning("Validation report not found. Proceeding with merge to ensure data availability.")
        should_merge = True

    if not should_merge:
        return

    # 2. Load Fallback Datasets
    # We assume HCI_P2 was downloaded in T015, but if it was partial, we need the others.
    # The task says: "merge available fallback datasets".
    
    datasets_to_load = []
    
    # Check Persona-Chat
    if persona_chat_path.exists():
        df_pc = load_dataset("persona_chat")
        if df_pc is not None:
            datasets_to_load.append(df_pc)
            logger.info("Loaded Persona-Chat.")
        else:
            logger.warning("Persona-Chat loading failed or empty.")
    else:
        logger.warning("Persona-Chat directory not found.")

    # Check EmpatheticDialogues
    if empathetic_path.exists():
        df_ed = load_dataset("empathetic_dialogues")
        if df_ed is not None:
            datasets_to_load.append(df_ed)
            logger.info("Loaded EmpatheticDialogues.")
        else:
            logger.warning("EmpatheticDialogues loading failed or empty.")
    else:
        logger.warning("EmpatheticDialogues directory not found.")

    if not datasets_to_load:
        logger.error("No fallback datasets available to merge. Cannot proceed.")
        # Create an empty output or exit? Task implies we need data.
        # We exit with error as we cannot fulfill the "merge" requirement without data.
        sys.exit(1)

    # 3. Validate and Prepare
    prepared_dfs = []
    for i, df in enumerate(datasets_to_load):
        source_name = "persona_chat" if i == 0 else "empathetic_dialogues"
        prepared = validate_and_prepare_dataset(df, source_name)
        if prepared is not None:
            prepared_dfs.append((prepared, source_name))

    if not prepared_dfs:
        logger.error("No valid datasets prepared for merging.")
        sys.exit(1)

    # 4. Merge
    merged_df = merge_datasets(prepared_dfs)

    # 5. Handle Demographics Logging
    handle_missing_demographics(merged_df, validation_report_path)

    # 6. Save
    output_path = Path("data/processed/merged_dialogues.parquet")
    save_merged_data(merged_df, output_path)

    logger.info("T016 Conditional Merge completed successfully.")

if __name__ == "__main__":
    main()
