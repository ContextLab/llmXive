"""
Real Data Ingestion Module for Transient-Absorption Data.

This module implements the ingestion of real transient-absorption data from
user-provided file paths. It enforces strict real-data requirements when
the USE_REAL_DATA environment variable is set, raising FileNotFoundError
with exit code 1 if data is missing.

If USE_REAL_DATA is false or unset, it proceeds to fallback logic (T015).
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

# Constants
ENV_VAR_REAL_DATA = "USE_REAL_DATA"
DEFAULT_FALLBACK_PATH = "data/raw/synthetic_traces.csv"
OUTPUT_PATH = "data/processed/real_traces.csv"

def ingest_real_transient_absorption_data(
    data_path: Optional[str] = None,
    force_real: Optional[bool] = None
) -> pd.DataFrame:
    """
    Ingest real transient-absorption data from a user-provided file path.

    Args:
        data_path: Optional explicit path to the real data file. If None,
                   defaults to checking environment variable or standard path.
        force_real: Optional boolean to force real data requirement. If None,
                    inferred from USE_REAL_DATA environment variable.

    Returns:
        pd.DataFrame: The ingested transient-absorption data.

    Raises:
        FileNotFoundError: If real data is required (USE_REAL_DATA=true) but
                           the file is missing. Exits with code 1.
        ValueError: If the data file exists but cannot be parsed as CSV.
    """
    # Determine if we must use real data
    if force_real is None:
        use_real_env = os.getenv(ENV_VAR_REAL_DATA, "").lower()
        force_real = use_real_env == "true" or use_real_env == "1"

    logger.info(f"Ingestion mode: {'REAL DATA REQUIRED' if force_real else 'FALLBACK ALLOWED'}")

    # Resolve data path
    if data_path is None:
        # Default expected path for real data
        data_path = "data/raw/real_traces.csv"

    path_obj = Path(data_path)

    # Check if file exists
    if not path_obj.exists():
        if force_real:
            error_msg = (
                f"CRITICAL: Real data file not found at '{data_path}'.\n"
                f"Environment variable '{ENV_VAR_REAL_DATA}' is set to 'true'.\n"
                f"The system requires real experimental data for research analysis.\n"
                f"Please provide the data file at the specified path or unset "
                f"'{ENV_VAR_REAL_DATA}' to allow synthetic fallback."
            )
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            sys.exit(1)
        else:
            logger.warning(
                f"Real data file '{data_path}' not found, but '{ENV_VAR_REAL_DATA}' "
                f"is not set. Proceeding to synthetic fallback (T015)."
            )
            return _load_fallback_data()

    # Attempt to load the real data
    try:
        logger.info(f"Loading real data from: {path_obj.absolute()}")
        df = pd.read_csv(path_obj)

        # Basic validation
        required_columns = ['time_ns', 'absorbance', 'wavelength_nm', 'solvent']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Data file missing required columns: {missing_cols}")

        logger.info(f"Successfully loaded {len(df)} rows from real data file.")
        return df

    except pd.errors.EmptyDataError:
        error_msg = f"Data file at '{data_path}' is empty."
        logger.error(error_msg)
        if force_real:
            sys.exit(1)
        else:
            return _load_fallback_data()
    except pd.errors.ParserError as e:
        error_msg = f"Failed to parse CSV at '{data_path}': {str(e)}"
        logger.error(error_msg)
        if force_real:
            sys.exit(1)
        else:
            return _load_fallback_data()
    except Exception as e:
        error_msg = f"Unexpected error loading data from '{data_path}': {str(e)}"
        logger.error(error_msg)
        if force_real:
            sys.exit(1)
        else:
            return _load_fallback_data()

def _load_fallback_data() -> pd.DataFrame:
    """
    Load synthetic fallback data from T015 (generate_synthetic.py).

    This function is only called when USE_REAL_DATA is false/unset and
    real data is missing. It delegates to the synthetic generator.

    Returns:
        pd.DataFrame: Synthetic transient-absorption data.
    """
    logger.info("Invoking synthetic data generator (T015) as fallback...")
    try:
        # Import the synthetic generator function
        from data.generate_synthetic import generate_synthetic_traces
        
        # Generate synthetic data to the default path
        output_path = Path(DEFAULT_FALLBACK_PATH).parent
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Call the generator
        generate_synthetic_traces(output_file=str(DEFAULT_FALLBACK_PATH))
        
        # Load the generated file
        df = pd.read_csv(DEFAULT_FALLBACK_PATH)
        logger.info(f"Loaded {len(df)} rows from synthetic fallback.")
        return df
    except ImportError:
        logger.error("FATAL: Synthetic fallback generator (T015) not found.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"FATAL: Failed to generate/load synthetic fallback: {str(e)}")
        sys.exit(1)

def main():
    """
    CLI entry point for real data ingestion.
    
    Usage:
        python code/data/ingest.py [--data-path PATH] [--force-real]
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest real transient-absorption data for Photo-Fries analysis."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to the real data CSV file. Default: data/raw/real_traces.csv"
    )
    parser.add_argument(
        "--force-real",
        action="store_true",
        default=None,
        help="Force real data requirement (equivalent to USE_REAL_DATA=true)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_PATH,
        help=f"Output path for ingested data. Default: {OUTPUT_PATH}"
    )

    args = parser.parse_args()

    # Determine force_real from args or env
    force_real = args.force_real
    if force_real is None:
        use_real_env = os.getenv(ENV_VAR_REAL_DATA, "").lower()
        force_real = use_real_env == "true" or use_real_env == "1"

    try:
        df = ingest_real_transient_absorption_data(
            data_path=args.data_path,
            force_real=force_real
        )

        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to disk
        df.to_csv(output_path, index=False)
        logger.info(f"Real data ingestion complete. Output written to: {output_path}")
        print(f"Success: Data written to {output_path}")

    except SystemExit:
        # Re-raise exit codes from ingest function
        raise
    except Exception as e:
        logger.critical(f"Data ingestion failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()