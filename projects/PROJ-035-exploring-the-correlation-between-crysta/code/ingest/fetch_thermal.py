"""
Fetch thermal conductivity data from literature/NIST CSV files.

This module loads thermal conductivity values from peer-reviewed literature
and NIST databases (NOT from Materials Project thermal properties endpoint,
per FR-010). The data is loaded from pre-downloaded CSV files.

FR-010: Load thermal conductivity from literature/NIST ONLY, exclude MP thermal endpoint
"""
import os
import sys
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd

# Import from sibling modules
from utils.validation import setup_logger, handle_error


# Module-level logger
logger = setup_logger(__name__, level="INFO")


def load_api_key(key_name: str, default: Optional[str] = None) -> str:
    """
    Load API key from environment variable.

    Args:
        key_name: Environment variable name
        default: Default value if not found

    Returns:
        API key string

    Note: This function is kept for API consistency with fetch_structures.py,
    though thermal data loading does not require an API key (per FR-010).
    """
    api_key = os.environ.get(key_name, default)
    if api_key is None:
        logger.warning(f"API key '{key_name}' not found in environment")
    return api_key or ""


def fetch_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> Tuple[bool, Optional[Exception]]:
    """
    Execute function with exponential backoff retry logic.

    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Tuple of (success: bool, error: Optional[Exception])

    Note: This function is kept for API consistency. Thermal data loading
    does not require network retries since data is loaded from local CSV files.
    """
    import time

    delay = base_delay
    for attempt in range(max_retries + 1):
        try:
            func()
            return True, None
        except Exception as e:
            if attempt == max_retries:
                return False, e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
            delay = min(delay * 2, max_delay)
    return False, Exception("Unexpected retry loop termination")


def is_valid_thermal_record(record: dict) -> bool:
    """
    Validate a thermal conductivity record.

    Args:
        record: Dictionary with thermal data fields

    Returns:
        True if record has all required fields with valid values
    """
    required_fields = ["structure_id", "thermal_conductivity", "temperature", "source_reference"]

    for field in required_fields:
        if field not in record:
            return False
        if record[field] is None or record[field] == "":
            return False

    # Validate numeric fields
    try:
        float(record["thermal_conductivity"])
        float(record["temperature"])
    except (ValueError, TypeError):
        return False

    return True


def load_thermal_data(csv_path: str) -> Tuple[pd.DataFrame, int]:
    """
    Load thermal conductivity data from CSV file.

    This function reads thermal conductivity values from literature/NIST
    CSV files. The data must contain the following columns:
    - structure_id: Unique identifier for the crystal structure
    - thermal_conductivity: Thermal conductivity in W/(m·K)
    - temperature: Measurement temperature in Kelvin
    - source_reference: Peer-reviewed literature or NIST reference

    Args:
        csv_path: Path to the thermal conductivity CSV file

    Returns:
        Tuple of (DataFrame, number of valid records loaded)

    Raises:
        FileNotFoundError: If CSV file does not exist
        ValueError: If required columns are missing
    """
    path = Path(csv_path)

    if not path.exists():
        error_msg = f"Thermal data file not found: {csv_path}"
        handle_error(error_msg, level="ERROR")
        raise FileNotFoundError(error_msg)

    # Load CSV
    df = pd.read_csv(csv_path)

    # Validate required columns
    required_columns = ["structure_id", "thermal_conductivity", "temperature", "source_reference"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        error_msg = f"Missing required columns in thermal data: {missing_columns}"
        handle_error(error_msg, level="ERROR")
        raise ValueError(error_msg)

    # Validate each record
    valid_records = []
    for _, row in df.iterrows():
        if is_valid_thermal_record(row.to_dict()):
            valid_records.append(row.to_dict())

    logger.info(f"Loaded {len(valid_records)} valid thermal conductivity records from {csv_path}")

    if len(valid_records) == 0:
        error_msg = "No valid thermal conductivity records found in input file"
        handle_error(error_msg, level="ERROR")
        raise ValueError(error_msg)

    return pd.DataFrame(valid_records), len(valid_records)


def fetch_perovskite_thermal_data(
    input_path: str,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch and prepare thermal conductivity data for perovskite analysis.

    This is the main entry point for thermal data loading. It loads data
    from the specified CSV file and returns a validated DataFrame.

    Args:
        input_path: Path to input thermal conductivity CSV file
        output_path: Optional path to save cleaned data CSV

    Returns:
        DataFrame with thermal conductivity data
    """
    df, count = load_thermal_data(input_path)

    # Ensure numeric types
    df["thermal_conductivity"] = pd.to_numeric(df["thermal_conductivity"], errors="coerce")
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")

    # Drop any rows with NaN after conversion
    df = df.dropna(subset=["thermal_conductivity", "temperature"])

    logger.info(f"Thermal data: {len(df)} records after numeric validation")

    # Save to output if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved thermal data to {output_path}")

    return df


def main():
    """
    Main entry point for thermal data fetching script.

    This script loads thermal conductivity data from literature/NIST CSV files
    and saves the validated output to data/cleaned/thermal_data.csv.

    FR-010 compliance: Uses literature/NIST data ONLY, does NOT call
    Materials Project thermal properties endpoint.
    """
    # Define file paths
    base_dir = Path(__file__).parent.parent.parent
    input_file = base_dir / "data" / "raw" / "thermal_conductivity_literature.csv"
    output_file = base_dir / "data" / "cleaned" / "thermal_data.csv"

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Log start
    logger.info("=" * 60)
    logger.info("T012: Fetch Thermal Conductivity Data from Literature/NIST")
    logger.info("FR-010: Loading from CSV files ONLY (no Materials Project thermal endpoint)")
    logger.info("=" * 60)

    # Check if input file exists
    if not input_file.exists():
        error_msg = f"Input thermal data file not found: {input_file}"
        handle_error(error_msg, level="ERROR")
        sys.exit(1)

    # Fetch thermal data
    try:
        df = fetch_perovskite_thermal_data(
            input_path=str(input_file),
            output_path=str(output_file)
        )

        # Summary statistics
        logger.info(f"\nThermal Data Summary:")
        logger.info(f"  Total records: {len(df)}")
        logger.info(f"  Thermal conductivity range: {df['thermal_conductivity'].min():.3f} - {df['thermal_conductivity'].max():.3f} W/(m·K)")
        logger.info(f"  Temperature range: {df['temperature'].min():.1f} - {df['temperature'].max():.1f} K")
        logger.info(f"  Unique sources: {df['source_reference'].nunique()}")
        logger.info(f"\nOutput saved to: {output_file}")
        logger.info("=" * 60)

    except (FileNotFoundError, ValueError) as e:
        handle_error(str(e), level="ERROR")
        sys.exit(1)
    except Exception as e:
        handle_error(f"Unexpected error: {e}", level="ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
