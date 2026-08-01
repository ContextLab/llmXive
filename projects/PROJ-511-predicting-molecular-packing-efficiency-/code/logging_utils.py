"""
Logging utilities for the molecular packing efficiency pipeline.

Provides centralized logging configuration and helper functions to log
download statistics, parsing failures, and filtering counts as required
by FR-001 and FR-017.
"""
import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Configure root logger for the project
def setup_pipeline_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = "data/pipeline.log"
) -> logging.Logger:
    """
    Configure the root logger for the pipeline.
    
    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If None, logs only to stdout.
        
    Returns:
        The root logger instance.
    """
    logger = logging.getLogger("molecular_packing_pipeline")
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Ensure directory exists (simple check)
        import os
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger

def log_download_statistics(
    logger: logging.Logger,
    total_requested: int,
    successful_downloads: int,
    failed_downloads: int,
    skipped_existing: int,
    duration_seconds: float
) -> None:
    """
    Log summary statistics for the CIF download phase (FR-001).
    
    Args:
        logger: The logger instance.
        total_requested: Total number of CIFs requested.
        successful_downloads: Number of successfully downloaded CIFs.
        failed_downloads: Number of failed downloads.
        skipped_existing: Number of files skipped because they already existed.
        duration_seconds: Total time taken for the download phase.
    """
    logger.info("=" * 60)
    logger.info("DOWNLOAD STATISTICS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total requested: {total_requested}")
    logger.info(f"Successful downloads: {successful_downloads}")
    logger.info(f"Failed downloads: {failed_downloads}")
    logger.info(f"Skipped (existing): {skipped_existing}")
    logger.info(f"Duration: {duration_seconds:.2f} seconds")
    logger.info(f"Success rate: {(successful_downloads / total_requested * 100) if total_requested > 0 else 0:.2f}%")
    logger.info("=" * 60)

def log_parsing_results(
    logger: logging.Logger,
    total_processed: int,
    successful_parses: int,
    failed_parses: int,
    smiles_generated: int,
    smiles_extracted: int,
    confounders_recorded: int
) -> None:
    """
    Log summary statistics for the CIF parsing phase (FR-001).
    
    Args:
        logger: The logger instance.
        total_processed: Total number of CIFs processed.
        successful_parses: Number of successfully parsed CIFs.
        failed_parses: Number of failed parses.
        smiles_generated: Number of SMILES generated from 3D geometry.
        smiles_extracted: Number of SMILES extracted from metadata.
        confounders_recorded: Number of records with confounders extracted.
    """
    logger.info("=" * 60)
    logger.info("PARSING STATISTICS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total processed: {total_processed}")
    logger.info(f"Successful parses: {successful_parses}")
    logger.info(f"Failed parses: {failed_parses}")
    logger.info(f"SMILES generated (from geometry): {smiles_generated}")
    logger.info(f"SMILES extracted (from metadata): {smiles_extracted}")
    logger.info(f"Confounders recorded: {confounders_recorded}")
    logger.info(f"Parsing success rate: {(successful_parses / total_processed * 100) if total_processed > 0 else 0:.2f}%")
    logger.info("=" * 60)

def log_filtering_results(
    logger: logging.Logger,
    input_count: int,
    output_count: int,
    removed_count: int,
    removal_reasons: Dict[str, int]
) -> None:
    """
    Log detailed filtering results for traceability (FR-017).
    
    This function logs the counts of records removed during the filtering
    phase (T016) and the specific reasons for removal, ensuring full
    traceability of the dataset curation process.
    
    Args:
        logger: The logger instance.
        input_count: Number of records in the input dataset.
        output_count: Number of records in the filtered output dataset.
        removed_count: Total number of records removed.
        removal_reasons: Dictionary mapping removal reason strings to counts.
    """
    logger.info("=" * 60)
    logger.info("FILTERING STATISTICS SUMMARY (T016)")
    logger.info("=" * 60)
    logger.info(f"Input records: {input_count}")
    logger.info(f"Output records: {output_count}")
    logger.info(f"Total removed: {removed_count}")
    
    if removal_reasons:
        logger.info("Removal reasons breakdown:")
        for reason, count in sorted(removal_reasons.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / removed_count * 100) if removed_count > 0 else 0
            logger.info(f"  - {reason}: {count} ({percentage:.1f}%)")
    else:
        logger.info("No records were removed.")
        
    logger.info("=" * 60)

def log_conclusion(
    logger: logging.Logger,
    final_dataset_size: int,
    total_duration_seconds: float
) -> None:
    """
    Log the final conclusion of the pipeline run.
    
    Args:
        logger: The logger instance.
        final_dataset_size: The number of records in the final dataset.
        total_duration_seconds: Total time taken for the entire pipeline.
    """
    logger.info("=" * 60)
    logger.info("PIPELINE CONCLUSION")
    logger.info("=" * 60)
    logger.info(f"Final dataset size: {final_dataset_size} records")
    logger.info(f"Total pipeline duration: {total_duration_seconds:.2f} seconds")
    logger.info("=" * 60)