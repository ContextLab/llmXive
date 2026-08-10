"""
T043: Compute Delta Peak Signal (ΔPeakSignal)

Explicitly computes ΔPeakSignal = CRE_signal - Null_signal by joining:
- code/CRE_merged.bed (from T008)
- code/null_region_signal.bed (from T009b)

Output: data/delta_peak_signal.tsv

FR-015: Explicitly compute ΔPeakSignal.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CRE_MERGED_PATH = PROJECT_ROOT / "data" / "processed" / "CRE_merged.bed"
NULL_SIGNAL_PATH = PROJECT_ROOT / "data" / "processed" / "null_region_signal.bed"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "delta_peak_signal.tsv"


def parse_bed_line(line: str) -> Tuple[str, int, int, str, Optional[float], str]:
    """
    Parse a BED line.
    Returns: (chrom, start, end, name, score, strand)
    Score is parsed as float if present, else None.
    """
    parts = line.strip().split('\t')
    if len(parts) < 4:
        raise ValueError(f"Invalid BED line (too few columns): {line}")
    
    chrom = parts[0]
    try:
        start = int(parts[1])
        end = int(parts[2])
    except ValueError:
        raise ValueError(f"Invalid coordinates in line: {line}")
    
    name = parts[3]
    
    # Score (column 5)
    score = None
    if len(parts) >= 5:
        try:
            score = float(parts[4]) if parts[4] != '.' else None
        except ValueError:
            logger.warning(f"Could not parse score in line: {line}, setting to None")
            score = None
    
    # Strand (column 6) - optional
    strand = parts[5] if len(parts) >= 6 else '.'
    
    return chrom, start, end, name, score, strand


def load_cre_signal(path: Path) -> Dict[str, Dict[str, float]]:
    """
    Load CRE_merged.bed and return a dict mapping:
    { chrom: { name: signal_value } }
    
    Assumes the signal is in the score column (5th column) or calculated from mean signal.
    For T008 output, we expect the signal to be pre-calculated or in the score column.
    """
    if not path.exists():
        raise FileNotFoundError(f"CRE merged file not found: {path}")
    
    cre_data = {}
    with open(path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip().startswith('#') or not line.strip():
                continue
            
            try:
                chrom, start, end, name, score, strand = parse_bed_line(line)
                
                if score is None:
                    logger.warning(f"Skipping line {line_num}: No signal score found in {path}")
                    continue
                
                if chrom not in cre_data:
                    cre_data[chrom] = {}
                cre_data[chrom][name] = score
                
            except ValueError as e:
                logger.error(f"Error parsing line {line_num} in {path}: {e}")
                continue
    
    logger.info(f"Loaded {sum(len(v) for v in cre_data.values())} CREs from {path}")
    return cre_data


def load_null_signal(path: Path) -> Dict[str, float]:
    """
    Load null_region_signal.bed.
    Since null regions are aggregated to a single mean/median signal per experiment,
    we expect the file to contain a single row or a set of rows that define the global null signal.
    
    However, T009b output `null_region_signal.bed` might contain one signal value per null region.
    The requirement is to compute ΔPeakSignal = CRE_signal - Null_signal.
    If the null signal is a global constant (mean of all null regions), we take the first/average.
    If it's per-region, we need a mapping. Given the task description "join ... with null_region_signal",
    and the typical nature of null regions as a background distribution, we assume the file
    contains a single aggregated signal value or we calculate the mean of the column.
    
    Let's assume the file has one or more rows. We will calculate the global mean signal
    if there are multiple, or take the value if there's one.
    """
    if not path.exists():
        raise FileNotFoundError(f"Null signal file not found: {path}")
    
    signals = []
    with open(path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip().startswith('#') or not line.strip():
                continue
            
            try:
                chrom, start, end, name, score, strand = parse_bed_line(line)
                if score is not None:
                    signals.append(score)
            except ValueError as e:
                logger.warning(f"Skipping malformed line {line_num} in {path}: {e}")
    
    if not signals:
        raise ValueError(f"No valid signal scores found in {path}")
    
    # Calculate global mean null signal
    global_null_signal = sum(signals) / len(signals)
    logger.info(f"Calculated global null signal (mean of {len(signals)} regions): {global_null_signal:.6f}")
    
    return global_null_signal


def compute_delta_signal(cre_data: Dict[str, Dict[str, float]], null_signal: float) -> List[Tuple[str, str, float, float]]:
    """
    Compute ΔPeakSignal for each CRE.
    Returns list of tuples: (chrom, name, cre_signal, delta_signal)
    """
    results = []
    total_cre = 0
    missing_null = 0 # Should not happen if null is global, but for safety
    
    for chrom, cre_dict in cre_data.items():
        for name, cre_signal in cre_dict.items():
            total_cre += 1
            delta = cre_signal - null_signal
            results.append((chrom, name, cre_signal, delta))
    
    logger.info(f"Computed delta signal for {total_cre} CREs.")
    return results


def write_output(results: List[Tuple[str, str, float, float]], output_path: Path):
    """
    Write results to TSV file.
    Columns: chrom, name, cre_signal, delta_peak_signal
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("chrom\tname\tcre_signal\tdelta_peak_signal\n")
        for chrom, name, cre_signal, delta in results:
            f.write(f"{chrom}\t{name}\t{cre_signal:.6f}\t{delta:.6f}\n")
    
    logger.info(f"Wrote {len(results)} records to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Compute Delta Peak Signal (T043)")
    parser.add_argument('--cre-file', type=str, default=str(CRE_MERGED_PATH),
                        help="Path to CRE_merged.bed")
    parser.add_argument('--null-file', type=str, default=str(NULL_SIGNAL_PATH),
                        help="Path to null_region_signal.bed")
    parser.add_argument('--output', type=str, default=str(OUTPUT_PATH),
                        help="Path for output delta_peak_signal.tsv")
    
    args = parser.parse_args()
    
    cre_path = Path(args.cre_file)
    null_path = Path(args.null_file)
    out_path = Path(args.output)
    
    if not cre_path.exists():
        logger.error(f"Input file not found: {cre_path}")
        sys.exit(1)
    if not null_path.exists():
        logger.error(f"Input file not found: {null_path}")
        sys.exit(1)
    
    try:
        logger.info("Loading CRE signals...")
        cre_data = load_cre_signal(cre_path)
        
        logger.info("Loading Null signal...")
        null_signal = load_null_signal(null_path)
        
        logger.info("Computing Delta Peak Signal...")
        results = compute_delta_signal(cre_data, null_signal)
        
        logger.info("Writing output...")
        write_output(results, out_path)
        
        logger.info("T043 completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()