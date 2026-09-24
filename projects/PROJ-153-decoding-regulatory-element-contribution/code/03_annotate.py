"""
code/03_annotate.py

Annotates merged peak regions (from T008) to classify them as promoter or distal
relative to the nearest transcription start site (TSS), and outputs the annotated
BED file.

This script reconciles the run-book (quickstart.md) which invokes this script,
ensuring the pipeline step exists and produces the declared output.

Input:  data/processed/CRE_merged.bed (Output of T008)
Output: data/processed/CRE_annotated.bed

Logic:
- Reads the merged CRE BED file.
- Uses the gene coordinates (assumed to be in a reference TSS file or derived
  from the gene annotation GFF/GTF if provided, but per T008 spec, we assume
  the 'gene_id' column in the merged file already links to TSS info or we
  calculate distance based on the CRE start vs known TSS positions).
- Since T008 output `data/processed/CRE_merged.bed` is the source, and T008
  logic defines promoter as <= 500bp from TSS, this script performs that
  annotation explicitly if not already present, or adds a 'region_type' column.
- For this implementation, we assume `CRE_merged.bed` has columns:
  chrom, start, end, cre_id, gene_id, strand, [optional tss_pos].
- If `tss_pos` is missing, we assume the gene_id maps to a TSS provided in
  a reference file `data/raw/yeast_tss.tsv` (standard S288C annotation).
  If that file is missing, we fall back to a heuristic: if the CRE overlaps
  the gene body (start < gene_end and end > gene_start), it's promoter if
  within 500bp of start.

However, to strictly follow the "real data" constraint and avoid faking TSS
coordinates, we will read the `data/processed/CRE_merged.bed` which T008
generated. T008 logic (from tasks.md) implies it already merged peaks and
annotated promoter vs distal. If T008 did not write the `region_type` column,
this script will compute it based on the `distance_to_tss` column if present,
or by reading a TSS reference.

Given the task history, T008 output `data/processed/CRE_merged.bed` is the
authoritative source. We will read it, ensure it has the `region_type`
annotation (Promoter/Distal), and write `data/processed/CRE_annotated.bed`.

If `data/processed/CRE_merged.bed` lacks TSS distance, we will attempt to
load `data/raw/yeast_tss.bed` (if it exists) to compute distances.
If neither is sufficient, we will log a warning and default to 'Distal'
for non-overlapping regions, but this task assumes T008 provided necessary
context or we use the standard S288C TSS list.

To ensure robustness without external dependencies not in the API:
We assume `CRE_merged.bed` has at least: chrom, start, end, name, gene_id, strand.
We will assume a standard TSS lookup is available or the distance is pre-calculated.
If not, we will use a hardcoded mapping of known yeast gene TSSs for common genes
ONLY IF the file `data/raw/yeast_tss.tsv` exists. Otherwise, we will mark as 'Unknown'.

Correction: The task T008 description says "annotate promoter (≤500bp) vs distal".
If T008 didn't output the column, this script must do it.
We will look for `data/raw/yeast_tss.tsv` (chrom, tss_pos, gene_id).
If found, we compute distance. If not, we default to 'Distal' for safety
(or 'Promoter' if overlapping gene start, but that's risky without TSS).

Actually, looking at the execution failure, the script is missing entirely.
We will implement a robust version that:
1. Loads `data/processed/CRE_merged.bed`.
2. Attempts to load `data/raw/yeast_tss.tsv` (or similar) if available.
3. Computes distance to TSS for each CRE.
4. Classifies as 'Promoter' if distance <= 500, else 'Distal'.
5. Writes `data/processed/CRE_annotated.bed`.

If no TSS reference is found, we will log a warning and assume all are 'Distal'
(conservative) or check overlap with gene bodies if gene coordinates are known.
For this implementation, we will assume a standard TSS file exists or we use
the gene_id to infer TSS if the gene_id matches a standard list.

To be safe and reproducible:
We will require `data/raw/yeast_tss.tsv` (chrom, tss, gene_id).
If missing, we will try to download it from a public source (SGD) if possible,
but per "real data" rules, we must fail loudly if we can't get it.
However, T008 already ran. It likely produced a file with gene_id.
We will assume the user has `data/raw/yeast_tss.tsv`.
If not, we will provide a fallback using a small hardcoded set for demo genes
ONLY IF the file is missing, but this violates "real data".

Decision: We will implement the script to read `data/processed/CRE_merged.bed`.
We will attempt to load `data/raw/yeast_tss.tsv`.
If it fails, we will raise an error: "TSS reference file not found. Cannot annotate."
This ensures we don't fake data.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_bed_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a BED line into a dictionary."""
    parts = line.strip().split('\t')
    if len(parts) < 4:
        return None
    # Standard BED: chrom, start, end, name, score, strand, ...
    # T008 output likely: chrom, start, end, cre_id, gene_id, strand, ...
    # We assume at least 6 columns for strand.
    if len(parts) >= 6:
        return {
            'chrom': parts[0],
            'start': int(parts[1]),
            'end': int(parts[2]),
            'name': parts[3],
            'score': parts[4] if len(parts) > 4 else '.',
            'strand': parts[5] if len(parts) > 5 else '.',
            'fields': parts[6:]
        }
    return None

def load_tss_reference(tss_file: Path) -> Dict[str, Dict[str, int]]:
    """
    Load TSS reference file. Expected format: chrom, tss_pos, gene_id
    Returns a dict: { (chrom, gene_id): tss_pos }
    """
    tss_map = {}
    if not tss_file.exists():
        raise FileNotFoundError(f"TSS reference file not found: {tss_file}")
    
    with open(tss_file, 'r') as f:
        # Skip header if present
        for line in f:
            if line.startswith('#') or line.startswith('chrom'):
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                chrom = parts[0]
                tss_pos = int(parts[1])
                gene_id = parts[2]
                tss_map[(chrom, gene_id)] = tss_pos
    return tss_map

def calculate_distance_to_tss(cre: Dict[str, Any], tss_map: Dict[str, Dict[str, int]]) -> int:
    """
    Calculate distance from CRE to the nearest TSS of the associated gene.
    Returns a large number if TSS not found.
    """
    gene_id = cre.get('gene_id')
    chrom = cre['chrom']
    if not gene_id:
        return 999999999
    
    key = (chrom, gene_id)
    if key in tss_map:
        tss = tss_map[key]
        cre_start = cre['start']
        # Distance is absolute difference between CRE start and TSS
        # For promoter, we care if CRE is within 500bp of TSS
        return abs(cre_start - tss)
    return 999999999

def annotate_cre(cre: Dict[str, Any], tss_map: Dict[str, Dict[str, int]]) -> str:
    """
    Annotate CRE as 'Promoter' or 'Distal'.
    Promoter: distance to TSS <= 500
    Distal: otherwise
    """
    dist = calculate_distance_to_tss(cre, tss_map)
    if dist <= 500:
        return 'Promoter'
    return 'Distal'

def main():
    parser = argparse.ArgumentParser(description='Annotate CREs as Promoter or Distal')
    parser.add_argument('--input', type=str, default='data/processed/CRE_merged.bed',
                        help='Input merged CRE BED file')
    parser.add_argument('--output', type=str, default='data/processed/CRE_annotated.bed',
                        help='Output annotated CRE BED file')
    parser.add_argument('--tss-ref', type=str, default='data/raw/yeast_tss.tsv',
                        help='TSS reference file (chrom, tss, gene_id)')
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    tss_ref_path = Path(args.tss_ref)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Load TSS reference
    try:
        tss_map = load_tss_reference(tss_ref_path)
        logger.info(f"Loaded TSS reference with {len(tss_map)} entries from {tss_ref_path}")
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Cannot proceed without TSS reference. Aborting.")
        sys.exit(1)

    # Process CREs
    annotated_cre_list = []
    with open(input_path, 'r') as f_in:
        for line in f_in:
            if line.startswith('#'):
                continue
            cre = parse_bed_line(line)
            if not cre:
                continue
            
            # Extract gene_id if available in fields or specific column
            # Assuming T008 output format: chrom, start, end, cre_id, gene_id, strand
            # If gene_id is in the 5th column (index 4)
            if len(cre['fields']) >= 1:
                # Check if gene_id is in fields or if we need to parse from name
                # We assume the 5th column (index 4) is gene_id based on T008 description
                # But parse_bed_line puts fields[0] as the 7th column (index 6)
                # Let's assume the input has: chrom, start, end, name, score, strand, gene_id
                # If so, gene_id is in fields[0]
                cre['gene_id'] = cre['fields'][0] if cre['fields'] else None
            
            region_type = annotate_cre(cre, tss_map)
            cre['region_type'] = region_type
            annotated_cre_list.append(cre)
            logger.debug(f"Annotated {cre['name']}: {region_type}")

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f_out:
        f_out.write("# chrom\tstart\tend\tname\tscore\tstrand\tgene_id\tregion_type\n")
        for cre in annotated_cre_list:
            # Reconstruct line
            # chrom, start, end, name, score, strand, gene_id, region_type
            line = f"{cre['chrom']}\t{cre['start']}\t{cre['end']}\t{cre['name']}\t{cre['score']}\t{cre['strand']}\t{cre.get('gene_id', '.')}\t{cre['region_type']}\n"
            f_out.write(line)

    logger.info(f"Annotated {len(annotated_cre_list)} CREs. Output written to {output_path}")

if __name__ == '__main__':
    main()
