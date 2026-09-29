import pandas as pd
import os
import logging

def scan_parquet_for_nans(parquet_file: str) -> bool:
    """
    Scans a Parquet file for NaN values in all columns.

    Args:
        parquet_file: The path to the Parquet file.

    Returns:
        True if any NaN values are found, False otherwise.
    """
    try:
        df = pd.read_parquet(parquet_file)
        return df.isna().any().any()
    except FileNotFoundError:
        logging.error(f"File not found: {parquet_file}")
        return True  # Treat file not found as having NaNs
    except Exception as e:
        logging.error(f"Error reading Parquet file: {e}")
        return True

def validate_time_bound_baseline(parquet_file: str) -> bool:
    """
    Checks if the 'Time-Bound' flag is present in a Parquet file and if the
    number of steps is >= 1000.

    Args:
        parquet_file: The path to the Parquet file.

    Returns:
        True if both conditions are met, False otherwise.
    """
    try:
        df = pd.read_parquet(parquet_file)
        if 'Time-Bound' not in df.columns:
            logging.error("Time-Bound flag not found in Parquet file.")
            return False
        if not df['Time-Bound'].iloc[0]:
            logging.error("Time-Bound flag is not set.")
            return False

        if len(df) < 1000:
            logging.error(f"Number of steps is less than 1000: {len(df)}")
            return False
        return True
    except FileNotFoundError:
        logging.error(f"File not found: {parquet_file}")
        return False
    except Exception as e:
        logging.error(f"Error reading Parquet file: {e}")
        return False

def validate_metrics_directory(directory: str) -> bool:
    """
    Validates all Parquet files in a directory.

    Args:
        directory: The path to the directory.

    Returns:
        True if all files are valid, False otherwise.
    """
    for filename in os.listdir(directory):
        if filename.endswith(".parquet"):
            filepath = os.path.join(directory, filename)
            if scan_parquet_for_nans(filepath) or not validate_time_bound_baseline(filepath):
                logging.error(f"Validation failed for file: {filepath}")
                return False
    return True

def main():
    """
    Main function to validate metrics in the data/raw directory.
    """
    directory = "data/raw"
    if not validate_metrics_directory(directory):
        logging.error("Metrics validation failed.")
        exit(1)
    else:
        logging.info("Metrics validation successful.")
        exit(0)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()