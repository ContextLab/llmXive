"""
Data download module for fetching QM9 and IR spectra datasets.
"""
import os
import sys
import logging
from pathlib import Path
import numpy as np
import pandas as pd

# Configure paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
LOGS_DIR = PROJECT_ROOT / "logs"

def download_qm9(output_dir: Optional[Path] = None) -> Path:
    """
    Download QM9 dataset.

    Args:
        output_dir: Directory to save the dataset. If None, uses default path.

    Returns:
        Path to the downloaded file.
    """
    if output_dir is None:
        output_dir = RAW_DIR / "qm9"

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "qm9.csv"

    logger = logging.getLogger(__name__)
    logger.info(f"Downloading QM9 dataset to {output_path}")

    # Try to load from Hugging Face datasets
    try:
        from datasets import load_dataset

        logger.info("Loading QM9 from Hugging Face datasets...")
        dataset = load_dataset("qm9", split="train")

        # Convert to DataFrame
        df = dataset.to_pandas()

        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"QM9 dataset saved to {output_path} ({len(df)} samples)")

        return output_path

    except Exception as e:
        logger.error(f"Failed to load QM9 from Hugging Face: {str(e)}")
        raise FileNotFoundError(
            "Could not download QM9 dataset. Please ensure 'datasets' package is installed "
            "and you have network access to Hugging Face."
        )

def download_ir_spectra(output_dir: Optional[Path] = None) -> Path:
    """
    Download IR spectra dataset.

    Args:
        output_dir: Directory to save the dataset. If None, uses default path.

    Returns:
        Path to the downloaded file.
    """
    if output_dir is None:
        output_dir = RAW_DIR / "ir_spectra"

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "ir_spectra.csv"

    logger = logging.getLogger(__name__)
    logger.info(f"Downloading IR spectra dataset to {output_path}")

    # Try to load from Hugging Face datasets
    try:
        from datasets import load_dataset

        logger.info("Loading IR spectra from Hugging Face datasets...")
        # Note: This is a placeholder - actual dataset name may vary
        dataset = load_dataset("spectra/ir_spectra", split="train")

        # Convert to DataFrame
        df = dataset.to_pandas()

        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"IR spectra dataset saved to {output_path} ({len(df)} samples)")

        return output_path

    except Exception as e:
        logger.error(f"Failed to load IR spectra from Hugging Face: {str(e)}")
        raise FileNotFoundError(
            "Could not download IR spectra dataset. Please ensure 'datasets' package is installed "
            "and you have network access to Hugging Face with the correct dataset identifier."
        )

def align_datasets(
    qm9_df: pd.DataFrame,
    ir_df: pd.DataFrame,
    key: str = "InChIKey"
) -> Tuple[pd.DataFrame, int]:
    """
    Align QM9 and IR spectra datasets on InChIKey.

    Args:
        qm9_df: QM9 DataFrame.
        ir_df: IR spectra DataFrame.
        key: Column name to join on.

    Returns:
        Tuple of (aligned DataFrame, count of discarded samples).
    """
    logger = logging.getLogger(__name__)

    qm9_count = len(qm9_df)
    ir_count = len(ir_df)

    # Perform inner join
    aligned_df = pd.merge(qm9_df, ir_df, on=key, how="inner")
    aligned_count = len(aligned_df)

    discarded_count = qm9_count + ir_count - aligned_count

    logger.info(f"Alignment: {qm9_count} + {ir_count} -> {aligned_count} "
               f"(discarded: {discarded_count})")

    return aligned_df, discarded_count

def save_aligned_data(
    aligned_df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Path:
    """
    Save aligned data to a file.

    Args:
        aligned_df: Aligned DataFrame.
        output_path: Path to save the file. If None, uses default path.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = RAW_DIR / "aligned_data.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    aligned_df.to_csv(output_path, index=False)

    logger = logging.getLogger(__name__)
    logger.info(f"Aligned data saved to {output_path} ({len(aligned_df)} samples)")

    return output_path

def main():
    """
    Main entry point for the data download script.
    """
    # Set up logging
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOGS_DIR / "data_ingestion.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting data download")

    try:
        # Download QM9
        qm9_path = download_qm9()
        qm9_df = pd.read_csv(qm9_path)

        # Download IR spectra
        ir_path = download_ir_spectra()
        ir_df = pd.read_csv(ir_path)

        # Align datasets
        aligned_df, discarded_count = align_datasets(qm9_df, ir_df)

        # Save aligned data
        output_path = save_aligned_data(aligned_df)

        logger.info("Data download and alignment completed successfully")

    except Exception as e:
        logger.error(f"Data download failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
