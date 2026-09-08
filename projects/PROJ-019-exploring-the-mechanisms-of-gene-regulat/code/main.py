import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from code.config import DATA_PROCESSED_DIR, TMP_DIR
from code.utils.disk_check import check_disk_space, InsufficientDiskSpaceError
from code.utils.memory_check import check_memory, InsufficientMemoryError
from code.utils.time_check import TimeTracker
from code.ingest import parse_bed_file
from code.preprocess import process_cell_type_peaks, aggregate_background_model, DataParseError
from code.provenance import initialize_provenance, save_provenance, add_encode_accession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Expected cell types as per specification
EXPECTED_CELL_TYPES = ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']

def run_preflight_checks():
    """Execute pre-flight checks for disk, memory, and time."""
    logger.info("Running pre-flight checks...")
    try:
        check_disk_space()
        check_memory()
        logger.info("Pre-flight checks passed.")
    except (InsufficientDiskSpaceError, InsufficientMemoryError) as e:
        logger.critical(f"Pre-flight check failed: {e}")
        sys.exit(1)

def run_ingestion(peak_files: Dict[str, str]) -> Dict[str, Any]:
    """
    Orchestrate the ingestion of parsed peaks and generate the summary report.
    
    Args:
        peak_files: A dictionary mapping cell type names to file paths of parsed peaks.
                    Expected keys must match EXPECTED_CELL_TYPES.
    
    Returns:
        A dictionary containing the ingestion summary statistics.
    
    Raises:
        ValueError: If the input contains unexpected cell types.
        DataParseError: If parsing fails for any file.
    """
    logger.info("Starting ingestion orchestration...")
    
    # Validate input cell types
    input_types = set(peak_files.keys())
    expected_set = set(EXPECTED_CELL_TYPES)
    
    if input_types != expected_set:
        missing = expected_set - input_types
        extra = input_types - expected_set
        error_msg = f"Input cell types mismatch. Expected: {EXPECTED_CELL_TYPES}. "
        if missing:
            error_msg += f"Missing: {list(missing)}. "
        if extra:
            error_msg += f"Unexpected: {list(extra)}. "
        raise ValueError(error_msg)
    
    total_peaks = 0
    parsed_count = 0
    processed_peaks = {}
    
    # Process each cell type's peak file
    for cell_type, file_path in peak_files.items():
        try:
            logger.info(f"Processing peaks for cell type: {cell_type}")
            # Parse the peak file (assumes file_path is a parsed BED or raw file to be parsed)
            # Depending on T013 implementation, this might be a direct read or a re-parse
            # Assuming T013 outputs a standardized BED-like structure or path to it.
            # If file_path is a string path to a parsed file, we parse it here to count.
            peaks = parse_bed_file(Path(file_path))
            
            if not isinstance(peaks, list):
                raise DataParseError(f"Unexpected output type from parse_bed_file for {cell_type}")
            
            peak_count = len(peaks)
            total_peaks += peak_count
            parsed_count += 1
            processed_peaks[cell_type] = peaks
            
            logger.info(f"Successfully parsed {peak_count} peaks for {cell_type}")
            
        except Exception as e:
            logger.error(f"Failed to process peaks for {cell_type}: {e}")
            raise DataParseError(f"Error processing {cell_type}: {e}")
    
    # Generate background model (union of all other cell types) as per T014
    # Note: T014 logic is embedded here or called if it returns the aggregated object.
    # Based on task description, T014 writes background_union.bed. 
    # We assume process_cell_type_peaks or aggregate_background_model handles the writing.
    # If T014 is separate, we might need to call it explicitly.
    # For this orchestration, we call the aggregation logic to ensure the file is written.
    try:
        logger.info("Aggregating background model...")
        aggregate_background_model(processed_peaks)
    except Exception as e:
        logger.error(f"Failed to aggregate background model: {e}")
        # Depending on strictness, we might fail here. T015 depends on T014 completion.
        # We assume T014 logic is available and successful if called.
        raise e
    
    # Construct summary
    summary = {
        "total_peaks": total_peaks,
        "cell_types": EXPECTED_CELL_TYPES, # Exact values as required
        "parsed_count": parsed_count,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Write output to data/processed/ingestion_summary.json
    output_path = Path(DATA_PROCESSED_DIR) / "ingestion_summary.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Ingestion summary written to {output_path}")
    return summary

def run_ingestion_pipeline():
    """
    Full pipeline for User Story 1: Download -> Parse -> Aggregate -> Summary.
    This function orchestrates T012, T013, T014, and T015.
    """
    logger.info("Starting full ingestion pipeline...")
    run_preflight_checks()
    
    # T012: Download peaks
    from code.download import download_all_peaks
    downloaded_files = download_all_peaks()
    
    # T013: Parse downloaded files
    from code.preprocess import preprocess_all_cell_types
    # This function should return a dict of {cell_type: path_to_parsed_file}
    # or modify internal state to have parsed files ready.
    # Assuming it returns the paths to the parsed intermediate files.
    parsed_files = preprocess_all_cell_types(downloaded_files)
    
    # T015: Run ingestion logic (Summary generation)
    summary = run_ingestion(parsed_files)
    
    # Update provenance
    try:
        initialize_provenance()
        # Add accessions if available in downloaded_files metadata
        save_provenance()
    except Exception as e:
        logger.warning(f"Failed to update provenance: {e}")
    
    return summary

def run_enrichment_pipeline():
    """Orchestrate scanning and enrichment (US2)."""
    logger.info("Starting enrichment pipeline...")
    # Implementation for US2 (T021-T024) would go here.
    # Placeholder for now as T015 is the focus.
    pass

def run_visualization_and_validation_pipeline():
    """Orchestrate visualization and validation (US3)."""
    logger.info("Starting visualization and validation pipeline...")
    # Implementation for US3 (T028-T034) would go here.
    pass

def run_validation_report():
    """Generate the final validation report."""
    logger.info("Generating validation report...")
    # Implementation for final report generation.
    pass

def main():
    """Entry point for the pipeline."""
    if len(sys.argv) > 1 and sys.argv[1] == "--pipeline":
        run_ingestion_pipeline()
    elif len(sys.argv) > 1 and sys.argv[1] == "--enrichment":
        run_enrichment_pipeline()
    elif len(sys.argv) > 1 and sys.argv[1] == "--validate":
        run_visualization_and_validation_pipeline()
    else:
        # Default: run full ingestion pipeline for T015 verification
        run_ingestion_pipeline()

if __name__ == "__main__":
    main()