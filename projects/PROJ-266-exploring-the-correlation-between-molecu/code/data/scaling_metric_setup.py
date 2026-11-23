import logging
import sys
from pathlib import Path
import pandas as pd
from utils.logging import get_logger, configure_root_logger
from utils.checksum import scan_and_register_data_files

def load_enriched_data(input_path: Path) -> pd.DataFrame:
    """
    Load the enriched dataset from the processed data directory.
    
    Args:
        input_path: Path to the enriched_data.csv file.
        
    Returns:
        DataFrame containing the enriched dataset.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the required 'mw' column is missing.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Enriched data file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    if 'mw' not in df.columns:
        raise ValueError("Required column 'mw' not found in enriched data.")
        
    return df

def add_complexity_metric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'complexity_metric' column as a copy of the 'mw' column.
    
    This prepares the dataset for Scaling Law analysis by explicitly
    defining molecular weight as the complexity metric.
    
    Args:
        df: DataFrame containing the enriched dataset with 'mw' column.
        
    Returns:
        DataFrame with the new 'complexity_metric' column appended.
    """
    logger = get_logger(__name__)
    logger.info("Adding complexity_metric column based on molecular weight (mw).")
    
    # Create a copy to avoid SettingWithCopyWarning
    df_out = df.copy()
    df_out['complexity_metric'] = df_out['mw']
    
    logger.info(f"Added 'complexity_metric' column. Total rows: {len(df_out)}")
    return df_out

def save_enriched_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the updated DataFrame to the specified CSV path.
    
    Args:
        df: DataFrame to save.
        output_path: Path where the CSV file will be written.
    """
    logger = get_logger(__name__)
    logger.info(f"Saving enriched data to: {output_path}")
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info("Successfully saved enriched data.")

def main():
    """
    Main entry point for the scaling metric setup task (T025).
    
    Reads enriched_data.csv, adds complexity_metric, saves the result,
    and updates the checksum registry.
    """
    configure_root_logger()
    logger = get_logger(__name__)
    
    project_root = Path(__file__).resolve().parents[2]
    input_path = project_root / "data" / "processed" / "enriched_data.csv"
    output_path = project_root / "data" / "processed" / "enriched_data.csv"
    
    try:
        # Load data
        df = load_enriched_data(input_path)
        
        # Process data
        df_processed = add_complexity_metric(df)
        
        # Save data
        save_enriched_data(df_processed, output_path)
        
        # Update checksums
        logger.info("Invoking checksum utility to register updated file.")
        scan_and_register_data_files(project_root)
        
        logger.info("Task T025 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        logger.error("Ensure T010b (enriched_data.csv generation) has been completed first.")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during scaling metric setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
