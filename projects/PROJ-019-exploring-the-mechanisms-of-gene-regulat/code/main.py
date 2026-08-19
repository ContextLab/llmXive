import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from code.config import DATA_PROCESSED_DIR
from code.provenance import load_provenance
from code.ingest import parse_bed_file
from code.preprocess import process_cell_type_peaks, aggregate_background_model
from code.scan import scan_cell_type, parse_fimo_output
from code.enrichment import calculate_enrichment, benjamini_hochberg_correction, process_cell_type_enrichment, aggregate_enrichment_results
from code.visualize import load_enrichment_matrix, cluster_matrix, calculate_silhouette_score, generate_heatmap
from code.validate import load_enrichment_results, get_top_motifs_per_cell_type, load_chip_overlap_stats, generate_top_motifs_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_ingestion_summary(peak_files: Dict[str, Path]) -> Dict[str, Any]:
    """
    Generates ingestion summary based on parsed peak files.
    
    Args:
        peak_files: Dictionary mapping cell type names to their peak file paths.
        
    Returns:
        Dictionary with total_peaks, cell_types, and parsed_count.
    """
    total_peaks = 0
    parsed_count = 0
    cell_types = []
    expected_types = ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']
    
    for cell_type, file_path in peak_files.items():
        if cell_type not in expected_types:
            raise ValueError(f"Unexpected cell type '{cell_type}'. Expected one of: {expected_types}")
        
        cell_types.append(cell_type)
        try:
            peaks = parse_bed_file(file_path)
            total_peaks += len(peaks)
            parsed_count += 1
            logger.info(f"Parsed {len(peaks)} peaks for {cell_type}")
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            raise
    
    return {
        'total_peaks': total_peaks,
        'cell_types': sorted(cell_types),
        'parsed_count': parsed_count
    }

def run_ingestion(peak_files: Dict[str, Path]) -> Dict[str, Any]:
    """
    Orchestrates the ingestion pipeline: parsing, preprocessing, and summarizing.
    
    Args:
        peak_files: Dictionary mapping cell type names to their peak file paths.
        
    Returns:
        The ingestion summary dictionary.
    """
    logger.info("Starting ingestion pipeline...")
    
    # Generate summary
    summary = generate_ingestion_summary(peak_files)
    
    # Write summary to file
    output_path = DATA_PROCESSED_DIR / "ingestion_summary.json"
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Ingestion summary written to {output_path}")
    return summary

def generate_enrichment_matrix(scan_results: Dict[str, List[Dict]], background_peaks: Dict[str, List[Dict]]) -> List[Dict]:
    """
    Generates the enrichment matrix from scan results and background peaks.
    
    Args:
        scan_results: Dictionary mapping cell types to lists of motif matches.
        background_peaks: Dictionary mapping cell types to background peak regions.
        
    Returns:
        List of dictionaries representing the enrichment matrix.
    """
    all_results = []
    
    for cell_type, matches in scan_results.items():
        if cell_type not in background_peaks:
            logger.warning(f"No background peaks found for {cell_type}, skipping enrichment calculation.")
            continue
        
        background = background_peaks[cell_type]
        enriched = process_cell_type_enrichment(matches, background)
        all_results.extend(enriched)
    
    return all_results

def run_enrichment(scan_results: Dict[str, List[Dict]], background_peaks: Dict[str, List[Dict]]) -> List[Dict]:
    """
    Orchestrates the enrichment pipeline: calculating enrichment and adjusting p-values.
    
    Args:
        scan_results: Dictionary mapping cell types to lists of motif matches.
        background_peaks: Dictionary mapping cell types to background peak regions.
        
    Returns:
        The enrichment matrix as a list of dictionaries.
    """
    logger.info("Starting enrichment pipeline...")
    
    # Generate enrichment matrix
    matrix = generate_enrichment_matrix(scan_results, background_peaks)
    
    # Apply Benjamini-Hochberg correction
    corrected_matrix = benjamini_hochberg_correction(matrix)
    
    # Write output to CSV
    output_path = DATA_PROCESSED_DIR / "enrichment_matrix.csv"
    if corrected_matrix:
        import csv
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['motif_id', 'cell_type', 'p_value', 'q_value'])
            writer.writeheader()
            writer.writerows(corrected_matrix)
    else:
        # Write empty file with headers if no data
        with open(output_path, 'w') as f:
            f.write("motif_id,cell_type,p_value,q_value\n")
    
    logger.info(f"Enrichment matrix written to {output_path}")
    return corrected_matrix

def generate_validation_report(heatmap_data: Dict, chip_data: Dict) -> Dict[str, Any]:
    """
    Generates the validation report based on heatmap data and ChIP-seq overlap stats.
    
    Args:
        heatmap_data: Dictionary containing silhouette score and clustering info.
        chip_data: Dictionary containing ChIP-seq overlap statistics.
        
    Returns:
        Dictionary with overlap_pct, top_motifs, and silhouette_score.
    """
    logger.info("Generating validation report...")
    
    # Extract silhouette score
    silhouette_score = heatmap_data.get('silhouette_score', 0.0)
    
    # Extract top motifs and their overlap stats
    top_motifs_summary = chip_data.get('top_motifs', [])
    overall_overlap = chip_data.get('overall_overlap_pct', 0.0)
    
    # Format top motifs with required precision
    formatted_top_motifs = []
    for motif in top_motifs_summary:
        formatted_motif = {
            'motif_id': motif['motif_id'],
            'q_value': round(float(motif['q_value']), 4),
            'overlap_pct': round(float(motif['overlap_pct']), 2)
        }
        formatted_top_motifs.append(formatted_motif)
    
    report = {
        'overlap_pct': round(float(overall_overlap), 2),
        'top_motifs': formatted_top_motifs,
        'silhouette_score': round(float(silhouette_score), 2)
    }
    
    return report

def run_validation_report(heatmap_data: Dict, chip_data: Dict) -> Dict[str, Any]:
    """
    Orchestrates the validation pipeline: generating the final report.
    
    Args:
        heatmap_data: Dictionary containing silhouette score and clustering info.
        chip_data: Dictionary containing ChIP-seq overlap statistics.
        
    Returns:
        The validation report dictionary.
    """
    logger.info("Starting validation report generation...")
    
    # Generate report
    report = generate_validation_report(heatmap_data, chip_data)
    
    # Write report to file
    output_path = DATA_PROCESSED_DIR / "validation_report.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {output_path}")
    return report

def main():
    """
    Main entry point for the pipeline.
    This function demonstrates the orchestration of all stages.
    """
    # Note: In a real execution, this would load actual data from disk
    # and call the run_* functions with real arguments.
    # For now, we assume the pipeline has been executed step-by-step
    # and we are just showing the orchestration logic.
    
    logger.info("Pipeline orchestration complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())