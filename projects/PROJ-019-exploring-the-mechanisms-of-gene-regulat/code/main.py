"""
Main orchestration module for the gene regulation analysis pipeline.
Coordinates data ingestion, motif scanning, enrichment analysis, visualization, and validation.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Import configuration
from code.config import DATA_PROCESSED_DIR, DATA_INTERIM_DIR, TMP_DIR

# Import utility modules
from code.utils.disk_check import check_disk_space
from code.utils.memory_check import check_memory

# Import pipeline stage modules
from code.download import download_all_peaks
from code.preprocess import preprocess_all_cell_types
from code.ingest import parse_bed_file
from code.scan import scan_all_cell_types, save_scan_results
from code.enrichment import (
    load_motif_scan_results,
    load_background_peaks,
    calculate_enrichment,
    benjamini_hochberg_correction,
    process_cell_type_enrichment,
    aggregate_enrichment_results,
    main as enrichment_main
)
from code.visualize import (
    load_enrichment_matrix,
    calculate_euclidean_distance_matrix,
    cluster_matrix,
    calculate_silhouette_score,
    generate_heatmap,
    main as visualize_main
)
from code.validate import (
    load_enrichment_results,
    get_top_motifs_per_cell_type,
    calculate_silhouette_score_from_heatmap_data,
    validate_motifs,
    generate_top_motifs_summary,
    main as validate_main
)
from code.summary_table import generate_summary_table, main as summary_main
from code.provenance import initialize_provenance, save_provenance, set_jaspar_version, add_encode_accession

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def run_preflight_checks() -> bool:
    """Run pre-flight checks for disk space and memory."""
    logger.info("Running pre-flight checks...")
    
    # Check disk space
    if not check_disk_space(TMP_DIR, min_space_bytes=14 * 1024**3):
        logger.error("Insufficient disk space. Aborting.")
        return False
    
    # Check memory
    if not check_memory(min_ram_gb=7):
        logger.warning("Memory below recommended 16GB but above 7GB minimum. Proceeding with caution.")
    
    logger.info("Pre-flight checks passed.")
    return True

def run_ingestion_pipeline() -> Dict[str, Any]:
    """Run the data ingestion pipeline: download, parse, and preprocess peaks."""
    logger.info("Starting data ingestion pipeline...")
    
    # Download peak files
    logger.info("Downloading ENCODE peak files...")
    downloaded_files = download_all_peaks()
    
    if not downloaded_files:
        logger.error("Failed to download any peak files.")
        return {}
    
    # Preprocess and annotate peaks
    logger.info("Preprocessing and annotating peaks...")
    processed_peaks = preprocess_all_cell_types(downloaded_files)
    
    if not processed_peaks:
        logger.error("Failed to preprocess peak files.")
        return {}
    
    # Generate ingestion summary
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_peaks": sum(len(peaks) for peaks in processed_peaks.values()),
        "cell_types": list(processed_peaks.keys()),
        "parsed_count": len(downloaded_files)
    }
    
    summary_path = DATA_PROCESSED_DIR / "ingestion_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Ingestion summary written to {summary_path}")
    return summary

def run_enrichment_pipeline() -> Dict[str, Any]:
    """Run the enrichment analysis pipeline: scan motifs and calculate enrichment."""
    logger.info("Starting enrichment analysis pipeline...")
    
    # Scan for motifs in all cell types
    logger.info("Scanning for TF motifs...")
    scan_results = scan_all_cell_types()
    
    if not scan_results:
        logger.error("Failed to scan for motifs.")
        return {}
    
    # Save scan results
    save_scan_results(scan_results)
    
    # Calculate enrichment for each cell type
    all_enrichments = {}
    for cell_type, matches in scan_results.items():
        logger.info(f"Calculating enrichment for {cell_type}...")
        
        # Load background model (union of other cell types)
        background = load_background_peaks(cell_type)
        
        # Calculate enrichment
        enrichment = calculate_enrichment(matches, background)
        
        # Apply Benjamini-Hochberg correction
        corrected = benjamini_hochberg_correction(enrichment)
        
        all_enrichments[cell_type] = corrected
    
    # Aggregate enrichment results
    aggregated = aggregate_enrichment_results(all_enrichments)
    
    # Write enrichment matrix to CSV
    output_path = DATA_PROCESSED_DIR / "enrichment_matrix.csv"
    with open(output_path, 'w') as f:
        f.write("motif_id,cell_type,p_value,q_value\n")
        for entry in aggregated:
            f.write(f"{entry['motif_id']},{entry['cell_type']},{entry['p_value']},{entry['q_value']}\n")
    
    logger.info(f"Enrichment matrix written to {output_path}")
    return {"enrichment_matrix_path": str(output_path)}

def run_visualization_and_validation_pipeline() -> Dict[str, Any]:
    """Run the visualization and validation pipeline."""
    logger.info("Starting visualization and validation pipeline...")
    
    # Load enrichment matrix
    enrichment_path = DATA_PROCESSED_DIR / "enrichment_matrix.csv"
    if not enrichment_path.exists():
        logger.error(f"Enrichment matrix not found at {enrichment_path}")
        return {}
    
    matrix = load_enrichment_matrix(str(enrichment_path))
    
    # Calculate distance matrix and cluster
    distance_matrix = calculate_euclidean_distance_matrix(matrix)
    clustered_matrix = cluster_matrix(matrix, distance_matrix)
    
    # Calculate silhouette score
    silhouette_score = calculate_silhouette_score(clustered_matrix)
    logger.info(f"Silhouette score: {silhouette_score}")
    
    # Save silhouette score
    score_path = DATA_PROCESSED_DIR / "silhouette_score.json"
    with open(score_path, 'w') as f:
        json.dump({"silhouette_score": round(silhouette_score, 2)}, f, indent=2)
    logger.info(f"Silhouette score written to {score_path}")
    
    # Generate heatmap
    heatmap_path = DATA_PROCESSED_DIR / "heatmap.png"
    generate_heatmap(clustered_matrix, heatmap_path)
    logger.info(f"Heatmap written to {heatmap_path}")
    
    return {
        "silhouette_score": silhouette_score,
        "heatmap_path": str(heatmap_path),
        "score_path": str(score_path)
    }

def run_validation_report() -> Dict[str, Any]:
    """Generate the final validation report."""
    logger.info("Generating validation report...")
    
    # Load enrichment results
    enrichment_path = DATA_PROCESSED_DIR / "enrichment_matrix.csv"
    enrichment_results = load_enrichment_results(str(enrichment_path))
    
    # Get top motifs per cell type
    top_motifs = get_top_motifs_per_cell_type(enrichment_results, q_threshold=0.05)
    
    # Validate motifs against ChIP-seq data
    validation_results = validate_motifs(top_motifs)
    
    # Calculate silhouette score (if not already done)
    score_path = DATA_PROCESSED_DIR / "silhouette_score.json"
    silhouette_score = None
    validation_passed = False
    
    if score_path.exists():
        with open(score_path, 'r') as f:
            score_data = json.load(f)
            silhouette_score = score_data.get("silhouette_score")
            validation_passed = silhouette_score >= 0.4
    
    # Generate top motifs summary
    summary = generate_top_motifs_summary(top_motifs, validation_results)
    
    # Create validation report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "silhouette_score": round(silhouette_score, 2) if silhouette_score else None,
        "validation_passed": validation_passed,
        "top_motifs": summary,
        "overlap_pct": validation_results.get("average_overlap_pct")
    }
    
    # Write validation report
    report_path = DATA_PROCESSED_DIR / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {report_path}")
    
    # Generate summary table
    summary_table_path = DATA_PROCESSED_DIR / "summary_table.csv"
    generate_summary_table(str(enrichment_path), str(report_path), str(summary_table_path))
    logger.info(f"Summary table written to {summary_table_path}")
    
    return report

def main():
    """Main entry point for the pipeline."""
    logger.info("Starting gene regulation analysis pipeline...")
    
    # Run pre-flight checks
    if not run_preflight_checks():
        logger.error("Pre-flight checks failed. Aborting.")
        sys.exit(1)
    
    # Run ingestion pipeline
    ingestion_summary = run_ingestion_pipeline()
    if not ingestion_summary:
        logger.error("Ingestion pipeline failed. Aborting.")
        sys.exit(1)
    
    # Run enrichment pipeline
    enrichment_results = run_enrichment_pipeline()
    if not enrichment_results:
        logger.error("Enrichment pipeline failed. Aborting.")
        sys.exit(1)
    
    # Run visualization and validation pipeline
    viz_results = run_visualization_and_validation_pipeline()
    if not viz_results:
        logger.error("Visualization and validation pipeline failed. Aborting.")
        sys.exit(1)
    
    # Generate validation report
    report = run_validation_report()
    if not report:
        logger.error("Failed to generate validation report.")
        sys.exit(1)
    
    logger.info("Pipeline completed successfully!")
    logger.info(f"Validation passed: {report.get('validation_passed', False)}")
    logger.info(f"Silhouette score: {report.get('silhouette_score', 'N/A')}")
    
    return report

if __name__ == "__main__":
    main()