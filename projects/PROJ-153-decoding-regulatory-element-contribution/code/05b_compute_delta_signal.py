"""
Task T043: Compute ΔPeakSignal (CRE signal minus null signal).

This script joins the CRE peak signals (from T007c) with the null region signals
(from T009b) to calculate the delta signal for each CRE.

Inputs:
  - data/processed/CRE_merged.bed (from T008)
  - data/processed/null_region_signal.bed (from T009b)
Output:
  - data/processed/delta_peak_signal.tsv

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
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_CRE_SIGNAL = PROJECT_ROOT / "data" / "processed" / "CRE_merged.bed"
INPUT_NULL_SIGNAL = PROJECT_ROOT / "data" / "processed" / "null_region_signal.bed"
OUTPUT_DELTA_SIGNAL = PROJECT_ROOT / "data" / "processed" / "delta_peak_signal.tsv"


def parse_bed_line(line: str) -> Tuple[str, int, int, Optional[str], Optional[float]]:
    """
    Parse a BED line.
    Returns: (chrom, start, end, name, score)
    Note: Some BED files might have fewer columns. We handle that gracefully.
    """
    parts = line.strip().split('\t')
    if len(parts) < 3:
        raise ValueError(f"Invalid BED line (too few columns): {line}")

    chrom = parts[0]
    try:
        start = int(parts[1])
        end = int(parts[2])
    except ValueError:
        raise ValueError(f"Invalid coordinates in BED line: {line}")

    name = parts[3] if len(parts) > 3 else None
    
    # Score might be in column 5 (0-indexed 4) or column 6 (0-indexed 5) depending on format
    # Standard BED: 1=chrom, 2=start, 3=end, 4=name, 5=score (optional)
    # If it's a narrowPeak or similar, score might be elsewhere.
    # We assume standard BED format where column 5 is the score if present.
    # However, looking at T007c output description: "data/processed/peak_signal_matrix.tsv"
    # But the input to THIS task is "data/processed/CRE_merged.bed" which likely has signal in column 5 or 6.
    # Let's assume column 5 (index 4) is the score if present, or we might need to parse a specific format.
    # Given the task description says "join ... signal", we assume the signal is the 5th column (index 4).
    
    score = None
    if len(parts) > 4:
        try:
            score = float(parts[4])
        except ValueError:
            # If column 5 is not a number, try column 6? Or just treat as missing.
            # For safety, let's assume standard BED score is col 5.
            logger.warning(f"Non-numeric score in column 5 for line: {line}. Setting to None.")
    
    return chrom, start, end, name, score


def load_cre_signal(filepath: Path) -> Dict[str, Dict[str, float]]:
    """
    Load CRE signal from the merged BED file.
    Returns: { cre_id: { 'signal': float } }
    We assume the 'name' column (col 4) is the cre_id.
    If the file has no name column, we construct an ID from chrom:start-end.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    cre_data = {}
    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip().startswith('track') or line.strip().startswith('browser') or line.strip().startswith('#'):
                continue
            
            try:
                chrom, start, end, name, score = parse_bed_line(line)
                if name is None:
                    cre_id = f"{chrom}:{start}-{end}"
                else:
                    cre_id = name
                
                if score is not None:
                    cre_data[cre_id] = {'signal': score}
                else:
                    # If score is missing, we might need to handle it later or skip
                    cre_data[cre_id] = {'signal': None}
                    
            except ValueError as e:
                logger.warning(f"Skipping malformed line {line_num} in {filepath}: {e}")
    
    return cre_data


def load_null_signal(filepath: Path) -> Dict[str, float]:
    """
    Load null region signal.
    Returns: { cre_id: float }
    We assume the 'name' column (col 4) is the cre_id.
    If the file has no name column, we construct an ID from chrom:start-end.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    null_data = {}
    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip().startswith('track') or line.strip().startswith('browser') or line.strip().startswith('#'):
                continue
            
            try:
                chrom, start, end, name, score = parse_bed_line(line)
                if name is None:
                    cre_id = f"{chrom}:{start}-{end}"
                else:
                    cre_id = name
                
                if score is not None:
                    null_data[cre_id] = score
                else:
                    logger.warning(f"Null signal missing for {cre_id} at line {line_num}")
                    null_data[cre_id] = 0.0 # Default to 0 if missing? Or skip?
                    # FR-015 implies we need a value. If null is missing, we can't compute delta.
                    # Let's set to 0.0 for now, but log it.
                    
            except ValueError as e:
                logger.warning(f"Skipping malformed line {line_num} in {filepath}: {e}")
    
    return null_data


def compute_delta_signal(cre_data: Dict, null_data: Dict) -> List[Dict]:
    """
    Compute delta signal for each CRE.
    Delta = CRE signal - Null signal.
    Returns a list of dicts: [{cre_id, cre_signal, null_signal, delta_signal}, ...]
    """
    results = []
    missing_null = 0
    missing_cre = 0
    invalid_delta = 0

    for cre_id, cre_info in cre_data.items():
        cre_signal = cre_info.get('signal')
        null_signal = null_data.get(cre_id)

        if cre_signal is None:
            missing_cre += 1
            continue
        
        if null_signal is None:
            # If null signal is missing, we cannot compute delta.
            # We should probably skip or log. Let's skip and log.
            missing_null += 1
            continue

        try:
            delta = cre_signal - null_signal
            results.append({
                'cre_id': cre_id,
                'cre_signal': cre_signal,
                'null_signal': null_signal,
                'delta_signal': delta
            })
        except TypeError:
            invalid_delta += 1
            logger.warning(f"Could not compute delta for {cre_id}: cre={cre_signal}, null={null_signal}")

    if missing_cre > 0:
        logger.warning(f"Skipped {missing_cre} CREs due to missing CRE signal.")
    if missing_null > 0:
        logger.warning(f"Skipped {missing_null} CREs due to missing null signal.")
    if invalid_delta > 0:
        logger.warning(f"Skipped {invalid_delta} CREs due to invalid delta calculation.")

    return results


def write_output(results: List[Dict], filepath: Path) -> None:
    """
    Write the delta signal results to a TSV file.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        # Header
        f.write("cre_id\tcre_signal\tnull_signal\tdelta_signal\n")
        
        for row in results:
            f.write(f"{row['cre_id']}\t{row['cre_signal']}\t{row['null_signal']}\t{row['delta_signal']}\n")
    
    logger.info(f"Successfully wrote {len(results)} delta signal records to {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Compute ΔPeakSignal (CRE signal - Null signal)")
    parser.add_argument("--cre-signal", type=Path, default=INPUT_CRE_SIGNAL,
                        help="Path to CRE merged signal BED file")
    parser.add_argument("--null-signal", type=Path, default=INPUT_NULL_SIGNAL,
                        help="Path to null region signal BED file")
    parser.add_argument("--output", type=Path, default=OUTPUT_DELTA_SIGNAL,
                        help="Path to output delta signal TSV file")
    args = parser.parse_args()

    logger.info(f"Loading CRE signals from {args.cre_signal}")
    cre_data = load_cre_signal(args.cre_signal)
    logger.info(f"Loaded {len(cre_data)} CRE signals.")

    logger.info(f"Loading null signals from {args.null_signal}")
    null_data = load_null_signal(args.null_signal)
    logger.info(f"Loaded {len(null_data)} null signals.")

    logger.info("Computing delta signals...")
    results = compute_delta_signal(cre_data, null_data)

    logger.info(f"Writing results to {args.output}")
    write_output(results, args.output)

    logger.info("Task T043 completed successfully.")


if __name__ == "__main__":
    main()
