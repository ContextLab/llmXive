import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for file paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "features.csv"
LABELED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "labeled_classification_data.csv"
LIMITATIONS_NOTE_PATH = PROJECT_ROOT / "results" / "limitations_note.txt"
CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    import yaml
    if not CONFIG_PATH.exists():
        logger.warning(f"Config file not found at {CONFIG_PATH}. Using defaults.")
        return {"thresholds": {"search_time_median": 0.5}}
    
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_search_time_data() -> pd.DataFrame:
    """
    Load search time data from the processed features file.
    
    Returns:
        pd.DataFrame: DataFrame containing search_time column.
    
    Raises:
        FileNotFoundError: If the processed features file does not exist.
        ValueError: If 'search_time' column is missing or marked UNFULFILLABLE.
    """
    if not PROCESSED_FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"Processed features file not found at {PROCESSED_FEATURES_PATH}. "
            "Please ensure T015 (feature extraction) has completed successfully."
        )
    
    df = pd.read_csv(PROCESSED_FEATURES_PATH)
    
    # Check if 'search_time' column exists
    if 'search_time' not in df.columns:
        raise ValueError(
            f"'search_time' column not found in {PROCESSED_FEATURES_PATH}. "
            "Feature extraction (T015) may have failed or produced incomplete output."
        )
    
    # Check if all values are marked as UNFULFILLABLE
    if 'status' in df.columns:
        unfulfillable_count = (df['status'] == 'UNFULFILLABLE').sum()
        total_count = len(df)
        if unfulfillable_count == total_count:
            raise ValueError(
                f"All {total_count} rows in 'search_time' are marked as 'UNFULFILLABLE'. "
                "Cannot proceed with ground-truth labeling. The pipeline halted because "
                "neither metadata nor valid stimulus image data was available for salience computation, "
                "and search time could not be derived."
            )
        elif unfulfillable_count > 0:
            logger.warning(
                f"{unfulfillable_count} out of {total_count} rows have 'search_time' marked as 'UNFULFILLABLE'. "
                "These rows will be excluded from labeling."
            )
            # Filter out unfulfillable rows
            df = df[df['status'] != 'UNFULFILLABLE']
    
    # Check for NaN values in search_time
    if df['search_time'].isna().all():
        raise ValueError(
            f"All 'search_time' values are NaN. Cannot proceed with labeling."
        )
    
    return df

def label_by_median_split(df: pd.DataFrame, column: str = 'search_time') -> pd.DataFrame:
    """
    Create a binary classification label based on median split of the specified column.
    
    Args:
        df: Input DataFrame.
        column: Column name to use for median split (default: 'search_time').
    
    Returns:
        pd.DataFrame: DataFrame with new 'load_label' column (0 = Low Load, 1 = High Load).
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")
    
    median_val = df[column].median()
    logger.info(f"Median {column} value: {median_val:.4f}")
    
    # Create binary labels: 1 if above median (High Load), 0 otherwise (Low Load)
    df = df.copy()
    df['load_label'] = (df[column] > median_val).astype(int)
    
    label_counts = df['load_label'].value_counts().to_dict()
    logger.info(f"Label distribution - Low Load (0): {label_counts.get(0, 0)}, High Load (1): {label_counts.get(1, 0)}")
    
    return df

def save_labeled_data(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the labeled DataFrame to a CSV file.
    
    Args:
        df: DataFrame with labels.
        output_path: Optional path to save the file. Defaults to LABELED_DATA_PATH.
    
    Returns:
        Path: Path to the saved file.
    """
    if output_path is None:
        output_path = LABELED_DATA_PATH
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Labeled data saved to {output_path}")
    
    return output_path

def write_limitations_note(output_path: Optional[Path] = None) -> Path:
    """
    Write a limitations note to the results directory, explicitly labeling the output
    as 'Search-Time Estimation' due to the lack of independent ground-truth measures.
    
    Args:
        output_path: Optional path to save the note. Defaults to LIMITATIONS_NOTE_PATH.
    
    Returns:
        Path: Path to the saved note.
    """
    if output_path is None:
        output_path = LIMITATIONS_NOTE_PATH
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    note_content = """
================================================================================
LIMITATIONS NOTE: Ground-Truth Labeling Methodology
================================================================================

Task: T029 - Ground-Truth Labeling for Cognitive Load Classification

METHODOLOGY LIMITATION:
-----------------------
This pipeline does not have access to an independent, external measure of cognitive load
(e.g., subjective rating scales, secondary task performance). Consequently, the ground-truth
labels for the classification task were derived via a **median split of search time**.

OUTPUT LABELING:
----------------
The resulting classification output MUST be explicitly labeled as:
"Search-Time Estimation"

INTERPRETATION CAUTION:
-----------------------
1. **Proxy Validity**: Search time is used as a proxy for cognitive load. While 
   theoretically correlated, it is not a direct measure of mental effort.
   
2. **Threshold Sensitivity**: The median split creates a binary classification 
   (High/Low) that may not reflect the continuous nature of cognitive load.
   Results should be interpreted with this discretization in mind.
   
3. **Circularity Risk**: If search time is also used as a feature in the model,
   this introduces circularity. Ensure features used for classification are 
   distinct from the labeling metric.

4. **UNFULFILLABLE Handling**: If the 'search_time' feature was marked as 
   'UNFULFILLABLE' in the preprocessing stage (T015) due to missing metadata 
   or stimulus data, those trials were excluded from this labeling process.

RECOMMENDATION:
---------------
Future iterations should integrate an independent cognitive load measure (e.g., 
NASA-TLX, dual-task performance) to validate and replace the search-time proxy.

================================================================================
Generated: {timestamp}
================================================================================
""".format(timestamp=pd.Timestamp.now().isoformat())
    
    with open(output_path, 'w') as f:
        f.write(note_content)
    
    logger.info(f"Limitations note saved to {output_path}")
    
    return output_path

def update_classification_metrics(df: pd.DataFrame, metrics_dict: Dict[str, float]) -> Dict[str, float]:
    """
    Update classification metrics with the labeling methodology note.
    
    Args:
        df: DataFrame used for labeling (for reference).
        metrics_dict: Dictionary of current metrics to update.
    
    Returns:
        Dict[str, float]: Updated metrics dictionary.
    """
    metrics_dict['labeling_method'] = 'Search-Time Median Split'
    metrics_dict['labeling_source'] = 'Estimated (No Independent Measure)'
    
    if 'search_time' in df.columns:
        metrics_dict['search_time_median'] = float(df['search_time'].median())
    
    return metrics_dict

def main():
    """
    Main entry point for the ground-truth labeling pipeline.
    
    This function:
    1. Loads processed search time data.
    2. Validates data integrity.
    3. Applies median split labeling.
    4. Saves labeled data.
    5. Writes a limitations note documenting the "Search-Time Estimation" nature.
    """
    logger.info("Starting Ground-Truth Labeling Pipeline (T029)...")
    
    try:
        # Step 1: Load data
        logger.info("Loading search time data...")
        df = load_search_time_data()
        
        # Step 2: Apply median split labeling
        logger.info("Applying median split labeling...")
        df_labeled = label_by_median_split(df, column='search_time')
        
        # Step 3: Save labeled data
        logger.info("Saving labeled data...")
        save_path = save_labeled_data(df_labeled)
        
        # Step 4: Write limitations note
        logger.info("Writing limitations note...")
        note_path = write_limitations_note()
        
        # Step 5: Update metrics (placeholder for integration with T030)
        metrics = {}
        update_classification_metrics(df_labeled, metrics)
        
        logger.info(f"Pipeline completed successfully.")
        logger.info(f"Labeled data: {save_path}")
        logger.info(f"Limitations note: {note_path}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())