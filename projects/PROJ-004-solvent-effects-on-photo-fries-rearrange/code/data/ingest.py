"""
Real Data Ingestion Module for Transient-Absorption Data.

This module handles the ingestion of real transient-absorption data from user-provided files.
It enforces strict validation and fails loudly if real data is missing when required.
"""
import os
import sys
import logging
from datetime import datetime
from typing import Optional
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ingest_real_transient_absorption_data(
    data_path: str,
    use_real_data: bool = True
) -> Optional[pd.DataFrame]:
    """
    Ingest real transient-absorption data from a CSV file.

    This function attempts to load real experimental data. If USE_REAL_DATA is True
    and the file is missing, it prints the critical message and exits with code 1.
    If USE_REAL_DATA is False or the file exists, it returns the data.

    Args:
        data_path: Path to the CSV file containing transient-absorption data.
        use_real_data: Boolean flag indicating whether to require real data.

    Returns:
        pd.DataFrame: The loaded transient-absorption data, or None if use_real_data is False.

    Raises:
        SystemExit: If use_real_data is True and the file does not exist.
        ValueError: If the file exists but cannot be parsed as CSV.
    """
    path_obj = Path(data_path)

    if use_real_data:
        if not path_obj.exists():
            error_msg = "CRITICAL: Real data file missing. Aborting."
            logger.critical(error_msg)
            # Print to stdout/stderr as explicitly required by task description
            print(error_msg)
            sys.exit(1)
        
        logger.info(f"Loading real data from: {data_path}")
        try:
            df = pd.read_csv(path_obj)
            
            # Basic validation of required columns
            expected_columns = ['time_ns', 'delta_absorbance', 'wavelength_nm']
            missing_cols = [col for col in expected_columns if col not in df.columns]
            
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            logger.info(f"Successfully loaded {len(df)} rows from {data_path}")
            return df
            
        except pd.errors.EmptyDataError:
            error_msg = f"CRITICAL: Real data file is empty. Aborting."
            logger.critical(error_msg)
            print(error_msg)
            sys.exit(1)
        except pd.errors.ParserError as e:
            error_msg = f"CRITICAL: Failed to parse CSV file: {e}. Aborting."
            logger.critical(error_msg)
            print(error_msg)
            sys.exit(1)
    else:
        logger.warning("USE_REAL_DATA is False. No real data ingestion performed.")
        return None

def main():
    """
    CLI entry point for real data ingestion.
    
    Reads the USE_REAL_DATA environment variable to determine behavior.
    """
    parser = argparse.ArgumentParser(
        description="Ingest real transient-absorption data for analysis."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=os.getenv("REAL_DATA_PATH", "data/raw/real_traces.csv"),
        help="Path to the real data CSV file."
    )
    # We do not override USE_REAL_DATA via CLI arg; it must come from env var
    # as per task specification.
    
    args = parser.parse_args()
    
    # Read the environment variable directly as required
    use_real_env = os.getenv("USE_REAL_DATA", "true").lower()
    use_real = use_real_env in ('true', '1', 'yes')
    
    try:
        df = ingest_real_transient_absorption_data(
            data_path=args.data_path,
            use_real_data=use_real
        )
        
        if df is not None:
            # Write processed data to standard location
            output_dir = Path("data/processed")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "ingested_traces.csv"
            
            df.to_csv(output_path, index=False)
            logger.info(f"Processed data written to: {output_path}")
            
    except SystemExit:
        # Re-raise to ensure exit code propagates
        raise
    except ValueError as e:
        logger.error(str(e))
        print(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    main()