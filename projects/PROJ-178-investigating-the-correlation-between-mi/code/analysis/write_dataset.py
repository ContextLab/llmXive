import os
import sys
import logging
import hashlib
import pandas as pd
from pathlib import Path
from config.environment import get_local_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal digest string
    """
    hash_obj = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum calculation: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise

def write_processed_dataset(df: pd.DataFrame, output_path: Path, generate_checksum: bool = True) -> dict:
    """
    Write the processed dataset to CSV and optionally generate a checksum file.

    Args:
        df: The processed pandas DataFrame to write
        output_path: Path where the CSV file will be written
        generate_checksum: Whether to generate a .sha256 file

    Returns:
        Dictionary containing metadata about the written file
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the dataset
        df.to_csv(output_path, index=False)
        logger.info(f"Wrote processed dataset to {output_path} with {len(df)} rows and {len(df.columns)} columns")

        result = {
            'path': str(output_path),
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': list(df.columns)
        }

        if generate_checksum:
            checksum = calculate_file_checksum(output_path)
            checksum_path = Path(str(output_path) + '.sha256')
            with open(checksum_path, 'w') as f:
                f.write(f"{checksum}  {output_path.name}\n")
            result['checksum'] = checksum
            result['checksum_path'] = str(checksum_path)
            logger.info(f"Generated checksum {checksum} and saved to {checksum_path}")

        return result

    except Exception as e:
        logger.error(f"Failed to write processed dataset: {e}")
        raise

def main():
    """
    Main entry point for writing the processed dataset.
    Loads the merged dataset from the expected location, validates it,
    writes it to the final output path, and generates a checksum.
    """
    logger.info("Starting dataset write process for T020")

    # Get paths from environment config
    local_paths = get_local_paths()
    input_path = local_paths.get('processed_dataset_path', 'code/data/processed/mito_aging_dataset.csv')
    input_path = Path(input_path)

    # Validate input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("T018 must complete successfully before T020 can run.")
        sys.exit(1)

    try:
        # Load the merged dataset
        logger.info(f"Loading dataset from {input_path}")
        df = pd.read_csv(input_path)

        # Basic validation
        if df.empty:
            logger.error("Dataset is empty. Cannot write empty dataset.")
            sys.exit(1)

        required_columns = ['sample_id', 'heteroplasmy_burden', 'age']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            sys.exit(1)

        # Determine output path (same as input for this task, but we ensure checksum generation)
        output_path = input_path

        # Write dataset with checksum
        result = write_processed_dataset(df, output_path, generate_checksum=True)

        logger.info("T020 completed successfully.")
        logger.info(f"Output: {result['path']}")
        logger.info(f"Checksum: {result.get('checksum', 'N/A')}")

        return result

    except Exception as e:
        logger.error(f"Critical error in main: {e}")
        raise

if __name__ == '__main__':
    main()
