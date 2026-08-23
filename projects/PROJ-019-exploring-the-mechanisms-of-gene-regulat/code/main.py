import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Import existing utilities and modules as per API surface
from code.config import DATA_PROCESSED_DIR, TMP_DIR
from code.utils.disk_check import check_disk_space, InsufficientDiskSpaceError
from code.utils.memory_check import check_memory, InsufficientMemoryError
from code.utils.time_check import check_time_limit, TimeLimitExceededError
from code.download import download_all_peaks, DataFetchError
from code.preprocess import preprocess_all_cell_types, DataParseError
from code.scan import scan_all_cell_types, FimoExecutionError, FimoParseError
from code.enrichment import aggregate_enrichment_results
from code.visualize import generate_heatmap, calculate_silhouette_score
from code.validate import (
    load_enrichment_results,
    get_top_motifs_per_cell_type,
    validate_motifs,
    generate_top_motifs_summary,
    generate_validation_report,
    DataValidationError
)
from code.summary_table import generate_summary_table
from code.provenance import initialize_provenance, save_provenance, add_encode_accession, set_jaspar_version

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Expected cell types as per task specification
EXPECTED_CELL_TYPES = ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']

def run_preflight_checks():
    """
    Execute pre-flight checks for disk, memory, and time limits.
    Raises appropriate errors if constraints are not met.
    """
    logger.info("Running pre-flight checks...")
    
    # Check disk space (FR-002)
    try:
        check_disk_space()
        logger.info("Disk space check passed.")
    except InsufficientDiskSpaceError as e:
        logger.error(f"Disk space check failed: {e}")
        raise
    
    # Check memory (SC-004)
    try:
        check_memory()
        logger.info("Memory check passed.")
    except InsufficientMemoryError as e:
        logger.error(f"Memory check failed: {e}")
        raise
    
    # Initialize time tracking
    try:
        check_time_limit()
        logger.info("Time limit check initialized.")
    except TimeLimitExceededError as e:
        logger.error(f"Time limit exceeded: {e}")
        raise

    logger.info("All pre-flight checks passed.")

def run_ingestion(peak_files: Dict[str, str]) -> Dict[str, Any]:
    """
    Orchestrate data ingestion and generate ingestion summary.
    
    Args:
        peak_files: Dictionary mapping cell type names to file paths.
                    Expected keys: ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']
    
    Returns:
        Dictionary with keys:
            - total_peaks: int, sum of all parsed files
            - cell_types: list, exact values from EXPECTED_CELL_TYPES
            - parsed_count: int, count of successfully parsed files
    
    Raises:
        ValueError: If input contains unexpected cell types.
        DataParseError: If parsing fails for any file.
    """
    logger.info("Starting ingestion pipeline...")
    
    # Validate cell types
    input_types = list(peak_files.keys())
    unexpected_types = [ct for ct in input_types if ct not in EXPECTED_CELL_TYPES]
    if unexpected_types:
        raise ValueError(f"Unexpected cell types in input: {unexpected_types}. "
                         f"Expected one of: {EXPECTED_CELL_TYPES}")
    
    # Process each cell type
    total_peaks = 0
    parsed_count = 0
    
    for cell_type, file_path in peak_files.items():
        try:
            # Parse the peak file
            logger.info(f"Parsing peaks for {cell_type} from {file_path}...")
            # Assuming preprocess.py has a function to parse a single file
            # We'll use the existing API from preprocess.py
            from code.preprocess import parse_downloaded_file
            peaks = parse_downloaded_file(file_path, cell_type)
            
            peak_count = len(peaks) if isinstance(peaks, list) else 0
            total_peaks += peak_count
            parsed_count += 1
            
            logger.info(f"Successfully parsed {peak_count} peaks for {cell_type}")
            
        except Exception as e:
            logger.error(f"Failed to parse peaks for {cell_type}: {e}")
            raise DataParseError(f"Failed to parse peaks for {cell_type}: {e}")
    
    # Generate summary
    summary = {
        "total_peaks": total_peaks,
        "cell_types": EXPECTED_CELL_TYPES,  # Use exact expected values
        "parsed_count": parsed_count,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Write summary to file
    output_path = DATA_PROCESSED_DIR / "ingestion_summary.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Ingestion summary written to {output_path}")
    logger.info(f"Total peaks: {total_peaks}, Parsed files: {parsed_count}")
    
    return summary

def run_ingestion_pipeline():
    """
    Full ingestion pipeline: download, parse, and summarize.
    """
    logger.info("Starting full ingestion pipeline...")
    
    # Download peaks
    logger.info("Downloading peak files...")
    try:
        peak_files = download_all_peaks()
        logger.info(f"Downloaded peaks for {len(peak_files)} cell types")
    except DataFetchError as e:
        logger.error(f"Failed to download peaks: {e}")
        raise
    
    # Run ingestion
    try:
        summary = run_ingestion(peak_files)
        logger.info("Ingestion pipeline completed successfully.")
        return summary
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise

def run_enrichment_pipeline():
    """
    Full enrichment pipeline: scan, enrich, and aggregate.
    """
    logger.info("Starting enrichment pipeline...")
    
    # Run scanning
    try:
        scan_results = scan_all_cell_types()
        logger.info("Motif scanning completed.")
    except (FimoExecutionError, FimoParseError) as e:
        logger.error(f"Motif scanning failed: {e}")
        raise
    
    # Run enrichment
    try:
        enrichment_results = aggregate_enrichment_results(scan_results)
        logger.info("Enrichment analysis completed.")
    except Exception as e:
        logger.error(f"Enrichment analysis failed: {e}")
        raise
    
    # Write enrichment matrix
    output_path = DATA_PROCESSED_DIR / "enrichment_matrix.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert results to CSV format
    import pandas as pd
    df = pd.DataFrame(enrichment_results)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Enrichment matrix written to {output_path}")
    return enrichment_results

def run_visualization_and_validation_pipeline():
    """
    Full visualization and validation pipeline.
    """
    logger.info("Starting visualization and validation pipeline...")
    
    # Load enrichment results
    enrichment_csv = DATA_PROCESSED_DIR / "enrichment_matrix.csv"
    if not enrichment_csv.exists():
        raise FileNotFoundError(f"Enrichment matrix not found: {enrichment_csv}")
    
    # Generate heatmap
    try:
        heatmap_path = generate_heatmap(enrichment_csv)
        logger.info(f"Heatmap generated at {heatmap_path}")
    except Exception as e:
        logger.error(f"Heatmap generation failed: {e}")
        raise
    
    # Calculate silhouette score
    try:
        silhouette_score = calculate_silhouette_score(enrichment_csv)
        logger.info(f"Silhouette score: {silhouette_score}")
        
        # Write silhouette score
        score_path = DATA_PROCESSED_DIR / "silhouette_score.json"
        with open(score_path, 'w') as f:
            json.dump({"silhouette_score": silhouette_score}, f, indent=2)
        
        # Validate score threshold
        if silhouette_score < 0.4:
            raise ValueError(f"Silhouette score {silhouette_score} is below threshold 0.4")
            
    except Exception as e:
        logger.error(f"Silhouette score calculation failed: {e}")
        raise
    
    # Validate motifs
    try:
        validation_results = validate_motifs(enrichment_csv)
        logger.info("Motif validation completed.")
    except DataValidationError as e:
        logger.error(f"Motif validation failed: {e}")
        raise
    
    # Generate validation report
    try:
        report = generate_validation_report(validation_results, silhouette_score)
        
        # Write validation report
        report_path = DATA_PROCESSED_DIR / "validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report written to {report_path}")
    except Exception as e:
        logger.error(f"Validation report generation failed: {e}")
        raise
    
    return report

def run_validation_report(heatmap_data, chip_data, score, silhouette_flag, overlap_flag):
    """
    Generate final validation report.
    
    Args:
        heatmap_data: Data from heatmap generation
        chip_data: Data from ChIP-seq validation
        score: Silhouette score
        silhouette_flag: Boolean indicating if silhouette test passed
        overlap_flag: Boolean indicating if overlap test passed
    
    Returns:
        Dictionary with validation report
    """
    report = {
        "overlap_pct": chip_data.get("overlap_pct") if chip_data else None,
        "top_motifs": chip_data.get("top_motifs", []) if chip_data else [],
        "silhouette_score": round(score, 2) if score is not None else None,
        "silhouette_test_passed": silhouette_flag,
        "overlap_test_passed": overlap_flag,
        "validation_passed": silhouette_flag and overlap_flag,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    output_path = DATA_PROCESSED_DIR / "validation_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {output_path}")
    return report

def main():
    """
    Main entry point for the pipeline.
    """
    try:
        # Run pre-flight checks
        run_preflight_checks()
        
        # Run ingestion pipeline
        run_ingestion_pipeline()
        
        # Run enrichment pipeline
        run_enrichment_pipeline()
        
        # Run visualization and validation pipeline
        run_visualization_and_validation_pipeline()
        
        logger.info("Pipeline completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
