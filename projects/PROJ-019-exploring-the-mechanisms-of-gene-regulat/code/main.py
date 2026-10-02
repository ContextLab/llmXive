"""
Main orchestration module for the gene regulation pipeline.
Implements the run_validation_report function to generate the final validation report.
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration
from code.config import DATA_PROCESSED_DIR, DATA_INTERIM_DIR, TMP_DIR

# Import pipeline components
from code.utils.disk_check import check_disk_space
from code.utils.memory_check import check_memory
from code.utils.time_check import start_timer, check_time_limit
from code.download import download_all_peaks
from code.preprocess import preprocess_all_cell_types, aggregate_background_model
from code.scan import scan_all_cell_types, save_scan_results
from code.enrichment import aggregate_enrichment_results
from code.visualize import generate_heatmap, calculate_silhouette_score
from code.validate import (
    load_silhouette_score,
    enforce_silhouette_threshold,
    validate_motifs,
    load_validation_stats
)
from code.provenance import initialize_provenance, save_provenance, add_encode_accession, set_jaspar_version

def run_preflight_checks():
    """Run pre-flight checks for disk, memory, and time."""
    logger.info("Running pre-flight checks...")
    
    # Check disk space
    check_disk_space()
    
    # Check memory
    check_memory()
    
    # Start time tracking
    start_timer()
    
    logger.info("Pre-flight checks passed.")

def run_ingestion():
    """Run the data ingestion pipeline."""
    logger.info("Starting data ingestion...")
    
    # Download peaks
    peak_files = download_all_peaks()
    
    # Preprocess peaks
    processed_peaks = preprocess_all_cell_types()
    
    # Aggregate background model
    background_model = aggregate_background_model(processed_peaks)
    
    # Generate ingestion summary
    ingestion_summary = {
        "total_peaks": sum(len(peaks) for peaks in processed_peaks.values()),
        "cell_types": list(processed_peaks.keys()),
        "parsed_count": len(processed_peaks)
    }
    
    # Write ingestion summary
    ingestion_summary_path = DATA_PROCESSED_DIR / "ingestion_summary.json"
    with open(ingestion_summary_path, 'w') as f:
        json.dump(ingestion_summary, f, indent=2)
    
    logger.info(f"Ingestion summary written to {ingestion_summary_path}")
    return ingestion_summary, processed_peaks, background_model

def run_enrichment(processed_peaks, background_model):
    """Run the enrichment analysis pipeline."""
    logger.info("Starting enrichment analysis...")
    
    # Scan for motifs
    motif_matches = scan_all_cell_types(processed_peaks)
    
    # Save scan results
    save_scan_results(motif_matches)
    
    # Calculate enrichment
    enrichment_results = aggregate_enrichment_results(motif_matches, background_model)
    
    # Write enrichment matrix
    enrichment_matrix_path = DATA_PROCESSED_DIR / "enrichment_matrix.csv"
    with open(enrichment_matrix_path, 'w') as f:
        f.write("motif_id,cell_type,p_value,q_value\n")
        for result in enrichment_results:
            f.write(f"{result['motif_id']},{result['cell_type']},{result['p_value']},{result['q_value']}\n")
    
    logger.info(f"Enrichment matrix written to {enrichment_matrix_path}")
    return enrichment_results

def run_visualization_and_validation_pipeline(enrichment_results):
    """Run the visualization and validation pipeline."""
    logger.info("Starting visualization and validation...")
    
    # Generate heatmap
    heatmap_path = DATA_PROCESSED_DIR / "heatmap.png"
    generate_heatmap(enrichment_results, heatmap_path)
    logger.info(f"Heatmap written to {heatmap_path}")
    
    # Calculate silhouette score
    silhouette_score = calculate_silhouette_score(enrichment_results)
    
    # Write silhouette score
    silhouette_score_path = DATA_PROCESSED_DIR / "silhouette_score.json"
    with open(silhouette_score_path, 'w') as f:
        json.dump({"silhouette_score": round(silhouette_score, 2)}, f, indent=2)
    logger.info(f"Silhouette score written to {silhouette_score_path}")
    
    # Enforce silhouette threshold
    silhouette_test_passed = enforce_silhouette_threshold(silhouette_score)
    
    # Validate motifs
    validation_stats = validate_motifs(enrichment_results)
    
    # Write validation stats
    validation_stats_path = DATA_PROCESSED_DIR / "validation_stats.json"
    with open(validation_stats_path, 'w') as f:
        json.dump(validation_stats, f, indent=2)
    logger.info(f"Validation stats written to {validation_stats_path}")
    
    # Determine overlap test passed
    overlap_test_passed = validation_stats.get("overlap_pct", 0) >= 60.0 if validation_stats.get("overlap_pct") is not None else False
    
    return {
        "silhouette_score": silhouette_score,
        "silhouette_test_passed": silhouette_test_passed,
        "overlap_test_passed": overlap_test_passed,
        "validation_stats": validation_stats
    }

def run_validation_report(heatmap_data, chip_data, score, silhouette_flag, overlap_flag):
    """
    Generate the final validation report.
    
    Args:
        heatmap_data: Dictionary containing heatmap-related data (unused in final report structure)
        chip_data: Dictionary containing ChIP-seq validation stats
        score: The silhouette score (float)
        silhouette_flag: Boolean indicating if silhouette test passed
        overlap_flag: Boolean indicating if overlap test passed
    
    Returns:
        Dictionary containing the validation report
    """
    logger.info("Generating validation report...")
    
    # Load top motifs from enrichment results (filtered by q < 0.05)
    enrichment_matrix_path = DATA_PROCESSED_DIR / "enrichment_matrix.csv"
    top_motifs = []
    
    try:
        with open(enrichment_matrix_path, 'r') as f:
            lines = f.readlines()[1:]  # Skip header
            motif_data = {}
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 4:
                    motif_id, cell_type, p_value, q_value = parts[0], parts[1], float(parts[2]), float(parts[3])
                    if q_value < 0.05:
                        if motif_id not in motif_data or q_value < motif_data[motif_id]['q_value']:
                            motif_data[motif_id] = {
                                'motif_id': motif_id,
                                'q_value': q_value,
                                'cell_type': cell_type
                            }
            
            # Get top motifs (sorted by q_value)
            sorted_motifs = sorted(motif_data.values(), key=lambda x: x['q_value'])
            
            # Calculate overlap for each top motif (simplified: use overall overlap from validation_stats)
            overall_overlap = chip_data.get("overlap_pct") if chip_data else None
            for motif in sorted_motifs[:10]:  # Top 10 motifs
                top_motifs.append({
                    "motif_id": motif['motif_id'],
                    "q_value": round(motif['q_value'], 4),
                    "overlap_pct": round(overall_overlap, 2) if overall_overlap is not None else None
                })
    except FileNotFoundError:
        logger.warning("Enrichment matrix not found, using empty top_motifs list")
        top_motifs = []
    
    # Determine overall validation status
    validation_passed = silhouette_flag and overlap_flag
    
    # Construct report
    report = {
        "overlap_pct": round(chip_data.get("overlap_pct"), 2) if chip_data and chip_data.get("overlap_pct") is not None else None,
        "top_motifs": top_motifs,
        "silhouette_score": round(score, 2),
        "silhouette_test_passed": silhouette_flag,
        "overlap_test_passed": overlap_flag,
        "validation_passed": validation_passed
    }
    
    # Write report
    report_path = DATA_PROCESSED_DIR / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {report_path}")
    return report

def run_ingestion_pipeline():
    """Run the full ingestion pipeline."""
    run_preflight_checks()
    ingestion_summary, processed_peaks, background_model = run_ingestion()
    return ingestion_summary, processed_peaks, background_model

def run_enrichment_pipeline(processed_peaks, background_model):
    """Run the full enrichment pipeline."""
    return run_enrichment(processed_peaks, background_model)

def run_visualization_and_validation_pipeline_wrapper(enrichment_results):
    """Wrapper for visualization and validation pipeline."""
    return run_visualization_and_validation_pipeline(enrichment_results)

def main():
    """Main entry point for the pipeline."""
    logger.info("Starting gene regulation analysis pipeline...")
    
    try:
        # Run ingestion
        ingestion_summary, processed_peaks, background_model = run_ingestion_pipeline()
        
        # Run enrichment
        enrichment_results = run_enrichment_pipeline(processed_peaks, background_model)
        
        # Run visualization and validation
        validation_data = run_visualization_and_validation_pipeline_wrapper(enrichment_results)
        
        # Generate validation report
        validation_report = run_validation_report(
            heatmap_data={},  # Heatmap data is not needed for the report structure
            chip_data=validation_data.get("validation_stats", {}),
            score=validation_data.get("silhouette_score", 0.0),
            silhouette_flag=validation_data.get("silhouette_test_passed", False),
            overlap_flag=validation_data.get("overlap_test_passed", False)
        )
        
        # Check if validation passed
        if not validation_report["validation_passed"]:
            logger.error("Validation failed. Check logs for details.")
            sys.exit(1)
        
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        raise

if __name__ == "__main__":
    main()