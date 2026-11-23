import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import gc
import psutil

# Import existing dependencies
from code.config import DATA_INTERIM_DIR, DATA_PROCESSED_DIR, TMP_DIR
from code.utils.memory_check import get_available_memory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants for memory management
MAX_MEMORY_GB = 7.0
CHUNK_SIZE = 10000  # Number of rows to process at a time if needed

class EnrichmentError(Exception):
    """Base exception for enrichment calculation errors."""
    pass

class MemoryLimitError(EnrichmentError):
    """Raised when memory usage exceeds safe limits."""
    pass

def load_motif_scan_results(scan_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load FIMO output files from the scan directory.
    
    Args:
        scan_dir: Path to directory containing FIMO output files.
        
    Returns:
        Dictionary mapping cell_type to list of motif matches.
    """
    results = defaultdict(list)
    if not scan_dir.exists():
        logger.error(f"Scan directory not found: {scan_dir}")
        return results
        
    for cell_file in scan_dir.glob("*_fimo.tsv"):
        cell_type = cell_file.stem.replace("_fimo", "")
        with open(cell_file, 'r') as f:
            header = f.readline().strip().split('\t')
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= len(header):
                    match = dict(zip(header, parts))
                    match['cell_type'] = cell_type
                    results[cell_type].append(match)
                    
    return dict(results)

def load_background_peaks(background_file: Path) -> List[Tuple[str, int, int]]:
    """
    Load background peak regions from a BED file.
    
    Args:
        background_file: Path to background union BED file.
        
    Returns:
        List of (chrom, start, end) tuples.
    """
    peaks = []
    if not background_file.exists():
        logger.error(f"Background file not found: {background_file}")
        return peaks
        
    with open(background_file, 'r') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                peaks.append((parts[0], int(parts[1]), int(parts[2])))
                
    return peaks

def _check_memory_usage():
    """Check current memory usage and raise if exceeding limit."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    
    if mem_gb > MAX_MEMORY_GB:
        logger.critical(f"Memory usage {mem_gb:.2f}GB exceeds limit {MAX_MEMORY_GB}GB")
        raise MemoryLimitError(f"Memory usage {mem_gb:.2f}GB exceeds limit {MAX_MEMORY_GB}GB")
        
    logger.debug(f"Current memory usage: {mem_gb:.2f}GB")

def calculate_enrichment(motif_matches: List[Dict], background_peaks: List[Tuple], 
                       target_peaks: List[Tuple]) -> Dict[str, float]:
    """
    Calculate enrichment scores using Fisher's exact test.
    
    Args:
        motif_matches: List of motif match dictionaries with genomic coordinates.
        background_peaks: List of (chrom, start, end) tuples for background.
        target_peaks: List of (chrom, start, end) tuples for target cell type.
        
    Returns:
        Dictionary mapping motif_id to p-value.
    """
    from scipy.stats import fisher_exact
    
    # Group matches by motif
    motif_counts = defaultdict(int)
    for match in motif_matches:
        motif_id = match.get('motif_id', match.get('match_id', 'unknown'))
        motif_counts[motif_id] += 1
        
    enrichment_scores = {}
    
    for motif_id, count in motif_counts.items():
        # Count overlaps with target peaks
        target_overlap = 0
        for match in motif_matches:
            if match.get('motif_id', match.get('match_id', 'unknown')) == motif_id:
                # Simple overlap check (chrom, start < end, end > start)
                m_chrom = match.get('chrom', '')
                m_start = int(match.get('start', 0))
                m_end = int(match.get('end', 0))
                
                for t_chrom, t_start, t_end in target_peaks:
                    if m_chrom == t_chrom:
                        if m_start < t_end and m_end > t_start:
                            target_overlap += 1
                            break
        
        # Count overlaps with background
        bg_overlap = 0
        for match in motif_matches:
            if match.get('motif_id', match.get('match_id', 'unknown')) == motif_id:
                m_chrom = match.get('chrom', '')
                m_start = int(match.get('start', 0))
                m_end = int(match.get('end', 0))
                
                for b_chrom, b_start, b_end in background_peaks:
                    if m_chrom == b_chrom:
                        if m_start < b_end and m_end > b_start:
                            bg_overlap += 1
                            break
        
        # Fisher's exact test
        # Table: [[target_overlap, count - target_overlap], 
        #         [bg_overlap, total_bg - bg_overlap]]
        # Simplified: we use total motif matches vs overlaps
        if count > 0 and len(target_peaks) > 0:
            try:
                # Contingency table:
                #                In Peak    Not in Peak
                # Motif Match    a          b
                # No Match       c          d
                a = target_overlap
                b = count - target_overlap
                c = len(target_peaks) - target_overlap
                d = len(background_peaks) - bg_overlap
                
                if a > 0 and c > 0:  # Avoid division by zero
                    odds_ratio, p_value = fisher_exact([[a, b], [c, d]], alternative='greater')
                    enrichment_scores[motif_id] = float(p_value)
            except Exception as e:
                logger.warning(f"Could not calculate enrichment for {motif_id}: {e}")
                enrichment_scores[motif_id] = 1.0
        else:
            enrichment_scores[motif_id] = 1.0
            
    return enrichment_scores

def benjamini_hochberg_correction(p_values: Dict[str, float]) -> Dict[str, float]:
    """
    Apply Benjamini-Hochberg correction to p-values.
    
    Args:
        p_values: Dictionary mapping motif_id to p-value.
        
    Returns:
        Dictionary mapping motif_id to q-value.
    """
    from statsmodels.stats.multitest import multipletests
    
    if not p_values:
        return {}
        
    motifs = list(p_values.keys())
    p_vals = [p_values[m] for m in motifs]
    
    try:
        # Reject if no valid p-values
        if all(p == 1.0 for p in p_vals):
            return {m: 1.0 for m in motifs}
            
        _, q_vals, _, _ = multipletests(p_vals, method='fdr_bh')
        return {motifs[i]: float(q_vals[i]) for i in range(len(motifs))}
    except Exception as e:
        logger.error(f"BH correction failed: {e}")
        return {m: 1.0 for m in motifs}

def process_cell_type_enrichment(cell_type: str, 
                                 motif_matches: List[Dict],
                                 background_peaks: List[Tuple],
                                 target_peaks: List[Tuple]) -> Dict[str, Dict[str, float]]:
    """
    Process enrichment for a single cell type with memory monitoring.
    
    Args:
        cell_type: Name of the cell type.
        motif_matches: List of motif matches for this cell type.
        background_peaks: Background peak regions.
        target_peaks: Target cell type peak regions.
        
    Returns:
        Dictionary with 'p_values' and 'q_values' keys.
    """
    _check_memory_usage()
    
    logger.info(f"Processing enrichment for {cell_type}...")
    
    # Calculate raw enrichment
    p_values = calculate_enrichment(motif_matches, background_peaks, target_peaks)
    
    _check_memory_usage()
    
    # Apply correction
    q_values = benjamini_hochberg_correction(p_values)
    
    # Cleanup
    gc.collect()
    _check_memory_usage()
    
    return {
        'p_values': p_values,
        'q_values': q_values
    }

def aggregate_enrichment_results(results: Dict[str, Dict[str, Dict[str, float]]]) -> List[Dict[str, Any]]:
    """
    Aggregate enrichment results across all cell types into a flat list.
    
    Args:
        results: Nested dictionary: cell_type -> {'p_values': ..., 'q_values': ...}
        
    Returns:
        List of dictionaries with motif_id, cell_type, p_value, q_value.
    """
    aggregated = []
    
    for cell_type, data in results.items():
        p_vals = data.get('p_values', {})
        q_vals = data.get('q_values', {})
        
        # Get all unique motifs
        all_motifs = set(p_vals.keys()) | set(q_vals.keys())
        
        for motif in all_motifs:
            p_val = p_vals.get(motif, 1.0)
            q_val = q_vals.get(motif, 1.0)
            
            aggregated.append({
                'motif_id': motif,
                'cell_type': cell_type,
                'p_value': p_val,
                'q_value': q_val
            })
            
    return aggregated

def main():
    """Main entry point for enrichment analysis with chunked processing."""
    logger.info("Starting enrichment analysis...")
    
    # Load data
    scan_dir = Path(TMP_DIR) / "scan_results"
    if not scan_dir.exists():
        logger.error(f"Scan results not found at {scan_dir}")
        sys.exit(1)
        
    motif_results = load_motif_scan_results(scan_dir)
    
    bg_file = Path(DATA_INTERIM_DIR) / "background_union.bed"
    background_peaks = load_background_peaks(bg_file)
    
    if not background_peaks:
        logger.error("No background peaks loaded")
        sys.exit(1)
        
    # Process each cell type with memory monitoring
    all_results = {}
    
    for cell_type, matches in motif_results.items():
        # Load target peaks for this cell type
        target_bed = Path(DATA_INTERIM_DIR) / f"{cell_type}_peaks.bed"
        if target_bed.exists():
            target_peaks = load_background_peaks(target_bed)
        else:
            logger.warning(f"Target peaks not found for {cell_type}, skipping")
            continue
            
        try:
            result = process_cell_type_enrichment(
                cell_type, matches, background_peaks, target_peaks
            )
            all_results[cell_type] = result
        except MemoryLimitError as e:
            logger.error(f"Memory limit exceeded for {cell_type}: {e}")
            # In a real scenario, we would implement chunked processing here
            # For now, we raise to fail loudly as per requirements
            raise
            
    # Aggregate results
    final_results = aggregate_enrichment_results(all_results)
    
    # Write output
    output_file = Path(DATA_PROCESSED_DIR) / "enrichment_matrix.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write("motif_id,cell_type,p_value,q_value\n")
        for row in final_results:
            f.write(f"{row['motif_id']},{row['cell_type']},{row['p_value']:.6f},{row['q_value']:.6f}\n")
            
    logger.info(f"Enrichment matrix written to {output_file}")
    return final_results

if __name__ == "__main__":
    main()