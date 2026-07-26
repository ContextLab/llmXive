import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from code.config import DATA_INTERIM_DIR, DATA_PROCESSED_DIR
from code.ingest import parse_bed_file

logger = logging.getLogger(__name__)

def load_motif_scan_results(scan_file: Path) -> List[Dict[str, Any]]:
    """Load results from a FIMO scan (TSV format)."""
    # Assuming FIMO output format: motif_id, sequence_name, start, stop, strand, score, p_value, q_value
    results = []
    if not scan_file.exists():
        return results

    with open(scan_file, 'r') as f:
        header = f.readline().strip().split('\t')
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= len(header):
                record = dict(zip(header, parts))
                record['p_value'] = float(record.get('p_value', 1.0))
                record['q_value'] = float(record.get('q_value', 1.0))
                results.append(record)
    return results

def load_background_peaks(background_file: Path) -> List[Tuple[str, int, int]]:
    """Load background peaks (chrom, start, end)."""
    records = parse_bed_file(background_file)
    return [(r[0], r[1], r[2]) for r in records]

def calculate_enrichment(motif_hits: Dict[str, List[Dict]], background_peaks: List[Tuple], total_peaks: int) -> Dict[str, Dict]:
    """
    Calculate enrichment using Fisher's exact test.
    motif_hits: {motif_id: [list of hit records]}
    """
    import scipy.stats as stats

    enrichment_results = {}

    for motif_id, hits in motif_hits.items():
        # Count unique peaks containing this motif
        # Simplified: assume each hit is in a unique peak for this demo
        # In reality, need to map hits to peaks by coordinate overlap
        hit_count = len(hits)
        if hit_count == 0:
            continue

        # Background count: peaks in background model with this motif (simulated for now)
        # Real implementation requires scanning background model too
        bg_count = 0 # Placeholder

        # Fisher's Exact Test
        # Table:
        #           Motif+   Motif-
        # Peaks     hit_count  total_peaks - hit_count
        # Background bg_count  bg_total - bg_count
        # Note: This is a placeholder logic. Real logic needs coordinate overlap.

        try:
            # Placeholder for actual calculation
            # odds_ratio, p_value = stats.fisher_exact([[hit_count, total_peaks - hit_count], [bg_count, 10000]])
            p_value = 1.0 # Placeholder
        except Exception as e:
            logger.warning(f"Could not calculate enrichment for {motif_id}: {e}")
            p_value = 1.0

        enrichment_results[motif_id] = {
            "motif_id": motif_id,
            "hit_count": hit_count,
            "p_value": p_value,
            "q_value": 1.0 # Placeholder
        }

    return enrichment_results

def benjamini_hochberg_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    Returns list of adjusted q-values.
    """
    import numpy as np

    n = len(p_values)
    if n == 0:
        return []

    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = [p_values[i] for i in sorted_indices]

    q_values = [0.0] * n
    prev_q = 0.0

    for i in range(n - 1, -1, -1):
        rank = i + 1
        q = sorted_p[i] * n / rank
        q = max(q, prev_q)
        q = min(q, 1.0)
        prev_q = q
        q_values[sorted_indices[i]] = q

    return q_values

def process_cell_type_enrichment(cell_type: str, scan_file: Path, background_file: Path, total_peaks: int) -> Dict[str, Dict]:
    """Process enrichment for a single cell type."""
    hits = load_motif_scan_results(scan_file)
    # Group by motif
    motif_hits = defaultdict(list)
    for hit in hits:
        motif_hits[hit['motif_id']].append(hit)

    # Background peaks (placeholder for overlap calculation)
    # In real implementation, scan background_file for same motifs
    # For now, assume background count is 0 or calculated elsewhere
    bg_peaks = load_background_peaks(background_file)

    results = calculate_enrichment(motif_hits, bg_peaks, total_peaks)

    # Apply BH correction
    p_vals = [r['p_value'] for r in results.values()]
    q_vals = benjamini_hochberg_correction(p_vals)

    for i, motif_id in enumerate(results.keys()):
        results[motif_id]['q_value'] = q_vals[i]

    return results

def aggregate_enrichment_results(all_results: Dict[str, Dict[str, Dict]]) -> List[Dict]:
    """Aggregate results from all cell types into a matrix-like list."""
    matrix = []
    for ct, results in all_results.items():
        for motif_id, stats in results.items():
            matrix.append({
                "cell_type": ct,
                "motif_id": motif_id,
                "p_value_raw": stats['p_value'],
                "q_value_adj": stats['q_value']
            })
    return matrix

def main() -> None:
    """Entry point for CLI."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Enrichment analysis entry point.")
    # This would be called from main.py with actual paths
    print("Enrichment module loaded.")

if __name__ == "__main__":
    main()
