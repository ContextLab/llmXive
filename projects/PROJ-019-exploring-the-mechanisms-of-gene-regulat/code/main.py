"""
Main orchestration script for the gene regulation analysis pipeline.

This script performs pre-flight checks, including disk space verification,
before initiating the data ingestion, preprocessing, scanning, and enrichment workflow.
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

from code.config import TMP_DIR, DATA_PROCESSED_DIR, DATA_RAW_DIR, DATA_INTERIM_DIR
from code.utils.disk_check import check_disk_space, InsufficientDiskSpaceError
from code.download import download_all_peaks
from code.preprocess import preprocess_all_cell_types
from code.provenance import initialize_provenance, save_provenance, set_jaspar_version, add_encode_accession
from code.scan import scan_all_cell_types
from code.enrichment import process_cell_type_enrichment, aggregate_enrichment_results, main as enrichment_main

REQUIRED_SPACE_GB = 14
JASPAR_VERSION = "2024"
# Mapping of cell types to ENCODE accession IDs for provenance
ENCODE_ACCESSIONS = {
    "GM12878": "ENCFF151VJN",
    "K562": "ENCFF001TDO",
    "HepG2": "ENCFF001NQP",
    "H1-hESC": "ENCFF001NQE",
    "IMR90": "ENCFF001NQF"
}

def generate_ingestion_summary(peak_counts: dict) -> dict:
    """
    Generate the ingestion summary report.
    
    Args:
        peak_counts: Dictionary mapping cell_type -> count of peaks.
        
    Returns:
        Dictionary containing the summary metadata and counts.
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "jaspar_version": JASPAR_VERSION,
        "total_cell_types": len(peak_counts),
        "peak_counts_by_cell_type": peak_counts,
        "output_directories": {
            "raw": str(DATA_RAW_DIR),
            "interim": str(DATA_INTERIM_DIR),
            "processed": str(DATA_PROCESSED_DIR)
        }
    }

def generate_enrichment_matrix(enrichment_results: dict) -> Path:
    """
    Aggregate enrichment results into a CSV matrix file.
    
    Args:
        enrichment_results: Dictionary mapping cell_type -> list of motif enrichment records.
        
    Returns:
        Path to the generated CSV file.
    """
    import csv
    
    output_path = Path(DATA_PROCESSED_DIR) / "enrichment_matrix.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Flatten results for CSV
    rows = []
    for cell_type, records in enrichment_results.items():
        for record in records:
            rows.append({
                "cell_type": cell_type,
                "motif_id": record.get("motif_id", ""),
                "p_value_raw": record.get("p_value_raw", 0.0),
                "q_value_adj": record.get("q_value_adj", 0.0),
                "fold_enrichment": record.get("fold_enrichment", 0.0)
            })
    
    if not rows:
        logger.warning("No enrichment results found to write to matrix.")
        # Write empty file with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["cell_type", "motif_id", "p_value_raw", "q_value_adj", "fold_enrichment"])
            writer.writeheader()
        return output_path

    fieldnames = ["cell_type", "motif_id", "p_value_raw", "q_value_adj", "fold_enrichment"]
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Enrichment matrix written to: {output_path}")
    return output_path

def main() -> int:
    """
    Entry point for the pipeline.
    
    Returns:
        int: 0 if successful, 1 if pre-flight checks fail or pipeline execution fails.
    """
    logger.info("Starting gene regulation analysis pipeline pre-flight checks...")
    
    # Ensure TMP_DIR exists
    tmp_path = Path(TMP_DIR)
    if not tmp_path.exists():
        logger.info(f"Creating temporary directory: {tmp_path}")
        try:
            tmp_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create temporary directory {tmp_path}: {e}")
            return 1

    logger.info(f"Verifying disk space in {tmp_path} (required: {REQUIRED_SPACE_GB} GB)...")
    
    try:
        check_disk_space(
            path=tmp_path,
            required_gb=REQUIRED_SPACE_GB,
            logger=logger
        )
        logger.info("Disk space check passed.")
    except InsufficientDiskSpaceError as e:
        logger.error(f"Pre-flight check failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during disk space check: {e}")
        return 1

    logger.info("Pre-flight checks completed successfully.")
    logger.info("Pipeline ready to proceed with data ingestion.")

    # Initialize provenance
    try:
        initialize_provenance()
        set_jaspar_version(JASPAR_VERSION)
        for cell_type, accession in ENCODE_ACCESSIONS.items():
            add_encode_accession(cell_type, accession)
    except Exception as e:
        logger.error(f"Failed to initialize provenance: {e}")
        return 1

    try:
        # Step 1: Download raw data
        logger.info("Step 1: Downloading ENCODE peak files...")
        downloaded_files = download_all_peaks(logger=logger)
        
        if not downloaded_files:
            logger.error("No files were downloaded successfully.")
            return 1

        # Step 2: Preprocess (parse, standardize, annotate, aggregate background)
        logger.info("Step 2: Preprocessing downloaded files (parsing, standardizing, annotating)...")
        peak_counts = preprocess_all_cell_types(logger=logger)

        # Step 3: Generate and save ingestion summary
        logger.info("Step 3: Generating ingestion summary report...")
        summary_data = generate_ingestion_summary(peak_counts)
        
        output_path = Path(DATA_PROCESSED_DIR) / "ingestion_summary.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)
        
        logger.info(f"Ingestion summary written to: {output_path}")

        # Step 4: Scan for motifs (US2 - T021)
        logger.info("Step 4: Scanning peaks for TF motifs using FIMO...")
        scan_results = scan_all_cell_types(logger=logger)
        if not scan_results:
            logger.warning("No motif scan results generated.")
            # Continue to enrichment with empty results if necessary, or fail?
            # Spec implies enrichment depends on scan. If no scan, enrichment will be empty.
        
        # Step 5: Calculate enrichment (US2 - T022, T023, T025)
        logger.info("Step 5: Calculating motif enrichment and applying BH correction...")
        enrichment_results = process_cell_type_enrichment(scan_results, logger=logger)
        
        # Aggregate and write final matrix
        final_matrix_path = generate_enrichment_matrix(enrichment_results)
        
        # Save provenance
        save_provenance()

        logger.info("Pipeline execution completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())