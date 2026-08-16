import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from code.config import TMP_DIR, DATA_PROCESSED_DIR, DATA_RAW_DIR, DATA_INTERIM_DIR
from code.utils.disk_check import check_disk_space, InsufficientDiskSpaceError
from code.download import download_all_peaks
from code.preprocess import preprocess_all_cell_types, aggregate_background_model
from code.scan import scan_all_cell_types, save_scan_results
from code.enrichment import process_cell_type_enrichment, aggregate_enrichment_results
from code.visualize import load_enrichment_matrix, generate_heatmap
from code.validate import load_enrichment_results, get_top_motifs_per_cell_type, calculate_silhouette_score, validate_motifs
from code.provenance import initialize_provenance, save_provenance, add_encode_accession, set_jaspar_version, get_provenance_report
from code.config import ENCODE_VERSION, JASPAR_VERSION

logger = logging.getLogger(__name__)

def generate_ingestion_summary(downloaded_files: dict, processed_files: dict) -> dict:
    """Generate ingestion summary report with real peak counts per cell type."""
    # Calculate real peak counts from the processed files (standardized BED files)
    peak_counts = {}
    for cell_type, file_path in processed_files.items():
        if file_path.exists():
            with open(file_path, 'r') as f:
                # Count non-empty, non-comment lines as peaks
                count = sum(1 for line in f if line.strip() and not line.startswith('#'))
            peak_counts[cell_type] = count
        else:
            logger.warning(f"Processed file for {cell_type} not found: {file_path}")
            peak_counts[cell_type] = 0

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_files": {k: str(v) for k, v in downloaded_files.items()},
        "processed_files": {k: str(v) for k, v in processed_files.items()},
        "peak_counts": peak_counts,
        "total_peaks": sum(peak_counts.values()),
        "cell_types_processed": list(peak_counts.keys())
    }
    
    output_path = DATA_PROCESSED_DIR / "ingestion_summary.json"
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Ingestion summary saved to {output_path}")
    logger.info(f"Peak counts: {peak_counts}")
    return summary

def generate_enrichment_matrix(enrichment_results: Dict[str, Dict]) -> Path:
    """Generate the enrichment matrix CSV."""
    import pandas as pd
    matrix_data = []
    for ct, results in enrichment_results.items():
        for motif_id, stats in results.items():
            matrix_data.append({
                "cell_type": ct,
                "motif_id": motif_id,
                "p_value_raw": stats['p_value'],
                "q_value_adj": stats['q_value']
            })

    df = pd.DataFrame(matrix_data)
    output_path = DATA_PROCESSED_DIR / "enrichment_matrix.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Enrichment matrix saved to {output_path}")
    return output_path

def generate_validation_report(enrichment_results: Dict[str, Dict]) -> dict:
    """Generate the validation report with ChIP-seq overlap statistics."""
    logger.info("Generating validation report...")
    
    # Get top motifs for validation
    top_motifs = get_top_motifs_per_cell_type(enrichment_results, top_n=10)
    
    # Run validation against independent ChIP-seq data
    validation_stats = validate_motifs(top_motifs)
    
    # Calculate silhouette score from enrichment matrix
    try:
        matrix_df = load_enrichment_matrix()
        if not matrix_df.empty:
            silhouette_score = calculate_silhouette_score(matrix_df)
            validation_stats['silhouette_score'] = silhouette_score
            if silhouette_score < 0.4:
                logger.warning(f"Silhouette score {silhouette_score:.4f} is below threshold 0.4")
            else:
                logger.info(f"Silhouette score {silhouette_score:.4f} meets threshold")
        else:
            logger.warning("Enrichment matrix is empty, skipping silhouette score calculation")
            validation_stats['silhouette_score'] = None
    except Exception as e:
        logger.error(f"Failed to calculate silhouette score: {e}")
        validation_stats['silhouette_score'] = None

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "validation_stats": validation_stats,
        "top_motifs_analyzed": top_motifs,
        "summary": {
            "total_motifs_validated": len(validation_stats.get('overlap_stats', {})),
            "average_overlap_pct": validation_stats.get('average_overlap_pct', 0.0),
            "silhouette_score": validation_stats.get('silhouette_score')
        }
    }
    
    output_path = DATA_PROCESSED_DIR / "validation_report.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to {output_path}")
    logger.info(f"Average ChIP-seq overlap: {validation_stats.get('average_overlap_pct', 0.0):.2f}%")
    return report

def main() -> None:
    """Main orchestration entry point."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 1. Pre-flight checks
    try:
        check_disk_space()
    except InsufficientDiskSpaceError as e:
        logger.error(f"Pre-flight check failed: {e}")
        sys.exit(1)

    # 2. Initialize provenance
    provenance = initialize_provenance()
    set_jaspar_version(provenance, JASPAR_VERSION)
    # Add sample accessions (to be updated with real ones)
    for accession in ["ENCFF001XXX", "ENCFF002XXX"]:
        add_encode_accession(provenance, accession)
    save_provenance(provenance)

    # 3. Download
    logger.info("Starting download phase...")
    try:
        downloaded_files = download_all_peaks()
    except Exception as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)

    # 4. Preprocess
    logger.info("Starting preprocessing phase...")
    try:
        processed_files = preprocess_all_cell_types()
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

    # 5. Generate Ingestion Summary (T015 Implementation)
    # This now generates a REAL summary with actual peak counts from processed files
    generate_ingestion_summary(downloaded_files, processed_files)

    # 6. Scan for Motifs (T021 Implementation)
    logger.info("Starting motif scanning phase...")
    try:
        scan_results = scan_all_cell_types()
        save_scan_results(scan_results)
    except Exception as e:
        logger.error(f"Motif scanning failed: {e}")
        sys.exit(1)

    # 7. Calculate Enrichment (T022, T023, T025 Implementation)
    logger.info("Starting enrichment calculation phase...")
    try:
        enrichment_results = aggregate_enrichment_results()
        generate_enrichment_matrix(enrichment_results)
    except Exception as e:
        logger.error(f"Enrichment calculation failed: {e}")
        sys.exit(1)

    # 8. Visualization (T028 Implementation)
    logger.info("Starting visualization phase...")
    matrix_path = DATA_PROCESSED_DIR / "enrichment_matrix.csv"
    if matrix_path.exists():
        try:
            df = load_enrichment_matrix()
            if not df.empty:
                generate_heatmap(df)
            else:
                logger.warning("Enrichment matrix is empty, skipping heatmap.")
        except Exception as e:
            logger.error(f"Visualization failed: {e}")

    # 9. Validation (T030, T031, T032 Implementation)
    logger.info("Starting validation phase...")
    try:
        generate_validation_report(enrichment_results)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        # Do not exit with error code 1 for validation failures per US-3-SC1
        logger.warning("Validation completed with errors, but continuing pipeline.")

    logger.info("Pipeline execution complete.")

if __name__ == "__main__":
    main()