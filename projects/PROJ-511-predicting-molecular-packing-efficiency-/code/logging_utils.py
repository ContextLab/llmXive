import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime

def setup_pipeline_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger for the pipeline with consistent formatting.
    
    Args:
        log_file: Optional path to a log file. If None, logs only to stderr.
        level: Logging level (default: INFO).
    
    Returns:
        The configured root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates in repeated runs
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_download_statistics(
    logger: logging.Logger,
    total_requested: int,
    successfully_downloaded: int,
    failed_downloads: int,
    skipped_existing: int
) -> None:
    """
    Log summary statistics for the CIF download phase.
    
    Args:
        logger: The logger instance to use.
        total_requested: Total number of CIF files requested.
        successfully_downloaded: Number of files successfully downloaded.
        failed_downloads: Number of downloads that failed.
        skipped_existing: Number of files skipped because they already existed.
    """
    logger.info("=" * 60)
    logger.info("DOWNLOAD STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Total requested:      {total_requested}")
    logger.info(f"Successfully downloaded: {successfully_downloaded}")
    logger.info(f"Failed downloads:     {failed_downloads}")
    logger.info(f"Skipped (existing):   {skipped_existing}")
    logger.info(f"Success rate:         {(successfully_downloaded / total_requested * 100):.2f}%")
    logger.info("=" * 60)

def log_parsing_results(
    logger: logging.Logger,
    total_processed: int,
    successfully_parsed: int,
    parse_failures: int,
    smiles_generated: int,
    smiles_extracted: int
) -> None:
    """
    Log summary statistics for the CIF parsing phase.
    
    Args:
        logger: The logger instance to use.
        total_processed: Total number of CIF files processed.
        successfully_parsed: Number of files successfully parsed.
        parse_failures: Number of files that failed to parse.
        smiles_generated: Number of SMILES strings generated from 3D geometry.
        smiles_extracted: Number of SMILES strings extracted from metadata.
    """
    logger.info("=" * 60)
    logger.info("PARSING STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Total processed:      {total_processed}")
    logger.info(f"Successfully parsed:  {successfully_parsed}")
    logger.info(f"Parse failures:       {parse_failures}")
    logger.info(f"SMILES generated:     {smiles_generated}")
    logger.info(f"SMILES extracted:     {smiles_extracted}")
    logger.info(f"Success rate:         {(successfully_parsed / total_processed * 100):.2f}%")
    logger.info("=" * 60)

def log_filtering_results(
    logger: logging.Logger,
    input_count: int,
    removed_missing_smiles: int,
    removed_invalid_cape: int,
    removed_invalid_raw_pc: int,
    output_count: int
) -> None:
    """
    Log detailed statistics for the dataset filtering phase (T016).
    
    This ensures traceability as required by FR-001 and FR-017.
    
    Args:
        logger: The logger instance to use.
        input_count: Number of records in the input dataset.
        removed_missing_smiles: Count of records removed due to missing/invalid SMILES.
        removed_invalid_cape: Count of records removed due to invalid CAPE values.
        removed_invalid_raw_pc: Count of records removed due to invalid Raw PC values.
        output_count: Number of records remaining in the filtered dataset.
    """
    logger.info("=" * 60)
    logger.info("FILTERING STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Input records:          {input_count}")
    logger.info(f"Removed (missing SMILES): {removed_missing_smiles}")
    logger.info(f"Removed (invalid CAPE):   {removed_invalid_cape}")
    logger.info(f"Removed (invalid Raw PC): {removed_invalid_raw_pc}")
    logger.info(f"Total removed:          {removed_missing_smiles + removed_invalid_cape + removed_invalid_raw_pc}")
    logger.info(f"Output records:         {output_count}")
    
    if input_count > 0:
        retention_rate = (output_count / input_count) * 100
        logger.info(f"Retention rate:         {retention_rate:.2f}%")
    
    logger.info("=" * 60)

def log_conclusion(
    logger: logging.Logger,
    final_dataset_size: int,
    output_file: str
) -> None:
    """
    Log final pipeline conclusion statistics.
    
    Args:
        logger: The logger instance to use.
        final_dataset_size: Number of records in the final dataset.
        output_file: Path to the final output file.
    """
    logger.info("=" * 60)
    logger.info("PIPELINE CONCLUSION")
    logger.info("=" * 60)
    logger.info(f"Final dataset size: {final_dataset_size}")
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 60)