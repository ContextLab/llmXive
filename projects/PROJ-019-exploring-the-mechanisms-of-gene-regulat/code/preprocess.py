import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from code.config import DATA_RAW_DIR, DATA_INTERIM_DIR, TMP_DIR

# Import network utilities for potential future fetches if needed, 
# though T012 handles the initial download.
from code.utils.network import fetch_file_with_retry, DataFetchError

# Import pybedtools for BED manipulation and annotation
try:
    import pybedtools
except ImportError:
    raise ImportError(
        "pybedtools is required for T014 (gene annotation and background aggregation). "
        "Please install it via 'pip install pybedtools'."
    )

# Import genome data for annotation (hg38)
try:
    import genomepy
except ImportError:
    # Fallback: We will use a hardcoded path or standard UCSC file if genomepy isn't strictly available
    # but pybedtools usually needs a reference file. We'll assume the reference file 
    # 'hg38.genepred.txt' or similar exists or use a standard approach.
    # For robustness, we will attempt to use a standard UCSC gene annotation file.
    # If the environment lacks it, we might need to download it.
    # However, to strictly follow "Real Data" and "No Fabrication", we must have a source.
    # We will assume the project has access to a standard hg38 annotation file or 
    # we download a small reference file if needed. 
    # For this implementation, we will use a standard approach assuming the file 
    # 'hg38_refseq.txt' is available in a standard location or downloaded.
    # To be safe and self-contained, we will download the hg38 gene annotation from UCSC 
    # if it's not present, as this is a standard reference file.
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

class DataParseError(Exception):
    """Custom exception for data parsing errors."""
    pass

def parse_downloaded_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parses a downloaded peak file (assumed to be BED-like) into a list of dictionaries.
    Expected format: chrom, start, end, name, score, strand (at least first 3 columns).
    """
    peaks = []
    if not file_path.exists():
        raise DataParseError(f"File not found: {file_path}")
    
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split('\t')
            if len(parts) < 3:
                logger.warning(f"Skipping malformed line {line_num} in {file_path}: {line}")
                continue
            
            try:
                chrom = parts[0]
                start = int(parts[1])
                end = int(parts[2])
                name = parts[3] if len(parts) > 3 else f"{chrom}:{start}-{end}"
                score = float(parts[4]) if len(parts) > 4 and parts[4] != '.' else 0.0
                strand = parts[5] if len(parts) > 5 else '.'
                
                peaks.append({
                    'chrom': chrom,
                    'start': start,
                    'end': end,
                    'name': name,
                    'score': score,
                    'strand': strand,
                    'source_file': str(file_path)
                })
            except ValueError as e:
                logger.warning(f"Error parsing line {line_num} in {file_path}: {e}")
                continue
    
    return peaks

def write_standardized_bed(peaks: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Writes a list of peak dictionaries to a BED file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for peak in peaks:
            f.write(f"{peak['chrom']}\t{peak['start']}\t{peak['end']}\t{peak['name']}\t{peak['score']}\t{peak['strand']}\n")
    logger.info(f"Wrote {len(peaks)} peaks to {output_path}")

def annotate_with_gene_symbols(peak_bed_path: Path, output_path: Path) -> None:
    """
    Annotates peaks with gene symbols using pybedtools and hg38 annotation.
    This function downloads the hg38 gene annotation if not present (standard reference).
    """
    logger.info(f"Starting annotation for {peak_bed_path}")
    
    # Ensure input exists
    if not peak_bed_path.exists():
        raise DataParseError(f"Input file not found: {peak_bed_path}")

    # Define reference file path
    # We will use a standard UCSC RefSeq file for hg38. 
    # To avoid large downloads in CI, we assume a small reference or download a specific one.
    # For this task, we will use the 'hg38' genome from pybedtools's built-in support 
    # or download a standard genePred file.
    # Let's try to use pybedtools' built-in genome support if available, 
    # otherwise download a standard file.
    
    # Strategy: Use pybedtools to intersect with a known gene annotation file.
    # We will download the hg38 genePred file from UCSC if it doesn't exist.
    ref_url = "http://hgdownload.cse.ucsc.edu/goldenPath/hg38/database/refGene.txt.gz"
    ref_file = TMP_DIR / "refGene.txt.gz"
    ref_file_uncompressed = TMP_DIR / "refGene.txt"
    
    if not ref_file.exists():
        logger.info(f"Downloading hg38 reference gene annotation from {ref_url}")
        try:
            fetch_file_with_retry(ref_url, str(ref_file))
            # Uncompress
            import gzip
            with gzip.open(ref_file, 'rt') as f_in:
                with open(ref_file_uncompressed, 'w') as f_out:
                    f_out.write(f_in.read())
            logger.info(f"Decompressed reference to {ref_file_uncompressed}")
        except Exception as e:
            raise DataParseError(f"Failed to download or process reference gene file: {e}")
    
    # Create BedTool objects
    peaks_bt = pybedtools.BedTool(str(peak_bed_path))
    
    # Create a BedTool for the reference genes
    # refGene.txt format: bin name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds score name2 cdsStartStat cdsEndStat
    # We need name2 (gene symbol)
    genes_bt = pybedtools.BedTool(str(ref_file_uncompressed))
    
    # Intersect peaks with genes to find overlapping genes
    # We want to annotate peaks with the gene symbols they overlap
    # Using 'closest' or 'intersect' with -wa -wb
    # Let's use intersect -wa -wb to get all overlaps
    try:
        # -wa: write the original A entry
        # -wb: write the original B entry
        # -f 0.0: any overlap
        # -r: require reciprocal overlap? No, just any overlap
        intersected = peaks_bt.intersect(genes_bt, wa=True, wb=True)
        
        # Parse results to map peak -> gene symbols
        peak_gene_map = {}
        for line in intersected:
            fields = line.split('\t')
            # A fields (peak): 0-5
            # B fields (gene): 6+
            # refGene columns: 0=bin, 1=name, 2=chrom, 3=strand, 4=txStart, 5=txEnd, 6=cdsStart, 7=cdsEnd, 8=exonCount, 9=exonStarts, 10=exonEnds, 11=score, 12=name2 (gene symbol)
            if len(fields) < 13:
                continue
            
            peak_key = f"{fields[0]}:{fields[1]}-{fields[2]}"
            gene_symbol = fields[12] # name2 column
            
            if peak_key not in peak_gene_map:
                peak_gene_map[peak_key] = []
            if gene_symbol and gene_symbol != "-":
                peak_gene_map[peak_key].append(gene_symbol)
        
        # Write annotated BED
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            # Write header if needed, but standard BED usually doesn't have one
            for line in intersected:
                fields = line.split('\t')
                peak_key = f"{fields[0]}:{fields[1]}-{fields[2]}"
                genes = peak_gene_map.get(peak_key, ['NA'])
                gene_str = ','.join(sorted(list(set(genes))))
                # Append gene symbol as a new column
                f.write(f"{line.rstrip()}\t{gene_str}\n")
        
        logger.info(f"Annotation complete. Output written to {output_path}")
        
    except Exception as e:
        logger.error(f"Error during annotation: {e}")
        raise DataParseError(f"Annotation failed: {e}")

def process_cell_type_peaks(cell_type: str, raw_files: List[Path]) -> Path:
    """
    Processes peaks for a single cell type: parses, standardizes, and annotates.
    Returns the path to the annotated BED file.
    """
    logger.info(f"Processing cell type: {cell_type}")
    
    # Aggregate peaks from all raw files for this cell type
    all_peaks = []
    for raw_file in raw_files:
        try:
            peaks = parse_downloaded_file(raw_file)
            all_peaks.extend(peaks)
        except DataParseError as e:
            logger.error(f"Error processing {raw_file} for {cell_type}: {e}")
            # Continue with other files if possible
    
    if not all_peaks:
        logger.warning(f"No peaks found for {cell_type}")
        # Return an empty file to avoid crashes downstream
        empty_bed = DATA_INTERIM_DIR / f"{cell_type}_empty.bed"
        empty_bed.touch()
        return empty_bed
    
    # Write standardized bed
    standardized_path = DATA_INTERIM_DIR / f"{cell_type}_standardized.bed"
    write_standardized_bed(all_peaks, standardized_path)
    
    # Annotate with gene symbols
    annotated_path = DATA_INTERIM_DIR / f"{cell_type}_annotated.bed"
    annotate_with_gene_symbols(standardized_path, annotated_path)
    
    return annotated_path

def aggregate_background_model(cell_types: List[str], cell_type_peaks: Dict[str, Path]) -> Path:
    """
    Aggregates peaks from ALL OTHER cell types to form the dynamic background model for EACH target cell type.
    However, the task description says: "for each target cell type, aggregate peaks from the remaining cell types".
    And the output is a SINGLE file: `data/interim/background_union.bed`.
    This implies we need a UNION of ALL peaks from ALL cell types EXCEPT the one being tested?
    Or is it a single global background model?
    Re-reading: "aggregate peaks from the remaining cell types to form the dynamic background model".
    Usually, for a specific cell type A, the background is Union(B, C, D, E).
    But the output file is singular: `background_union.bed`.
    This suggests we might be creating a SINGLE background model that represents the union of ALL cell types
    (or all except the current one, but we can't write multiple files with one name).
    
    Let's interpret the requirement as: Create a UNION of peaks from ALL cell types.
    This global union can then be used as a background for any specific comparison, 
    OR the task implies we generate one file that contains the union of ALL peaks (which is the superset of any "remaining" set).
    Given the singular output path `data/interin/background_union.bed`, we will create the UNION of ALL available cell type peaks.
    
    If the logic requires per-cell-type background, that would be handled in T022 (enrichment) by filtering this file.
    But T014 explicitly says "Writes `data/interim/background_union.bed`".
    So we will write the union of all peaks from all processed cell types.
    """
    logger.info("Aggregating background model from all cell types")
    
    if not cell_type_peaks:
        raise DataParseError("No cell type peaks provided for background aggregation")
    
    # Collect all BedTool objects
    bed_files = list(cell_type_peaks.values())
    
    # Filter out empty files
    valid_files = [f for f in bed_files if f.exists() and f.stat().st_size > 0]
    
    if not valid_files:
        logger.warning("No valid peak files found for background aggregation")
        output_path = DATA_INTERIM_DIR / "background_union.bed"
        output_path.touch()
        return output_path
    
    # Use pybedtools to merge/union
    # First, concatenate all files
    try:
        # Create a BedTool from the list of files
        # pybedtools.BedTool can take a list of files
        all_peaks_bt = pybedtools.BedTool(valid_files)
        
        # Sort and merge overlapping regions to create a non-redundant union
        # -i: input, -g: genome file (optional, but good for sorting)
        # We will sort and merge
        merged_bt = all_peaks_bt.sort().merge()
        
        output_path = DATA_INTERIM_DIR / "background_union.bed"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to disk
        merged_bt.saveas(str(output_path))
        
        logger.info(f"Background union created: {output_path} ({len(list(merged_bt))} regions)")
        return output_path
        
    except Exception as e:
        logger.error(f"Error aggregating background model: {e}")
        raise DataParseError(f"Background aggregation failed: {e}")

def preprocess_all_cell_types(cell_type_mapping: Dict[str, List[Path]]) -> Dict[str, Path]:
    """
    Orchestrates processing for all cell types and returns a mapping of cell_type -> annotated_bed_path.
    Also triggers the background model aggregation.
    """
    cell_type_peaks = {}
    
    # Process each cell type
    for cell_type, raw_files in cell_type_mapping.items():
        annotated_path = process_cell_type_peaks(cell_type, raw_files)
        cell_type_peaks[cell_type] = annotated_path
    
    # Aggregate background model
    # Note: The task says "for each target cell type, aggregate peaks from the remaining".
    # But the output is a single file. We will create the union of ALL as the global background.
    # If the downstream logic (T022) needs to exclude the current cell type, it can do so by filtering.
    # However, to strictly follow T014's output requirement:
    aggregate_background_model(list(cell_type_mapping.keys()), cell_type_peaks)
    
    return cell_type_peaks

def main():
    """
    Main entry point for T014.
    Assumes T012 and T013 have run and populated data/raw with downloaded files.
    """
    logger.info("Starting T014: Gene annotation and background model aggregation")
    
    # Define cell types and their raw file mappings
    # This mapping should ideally be derived from the file system or a config,
    # but for this task, we assume the structure from T012/T013.
    # We will scan data_raw for files and group them by cell type based on filename convention.
    # Convention: <cell_type>_<peak_type>.bed or similar.
    # If T012/T013 produced specific files, we need to know their names.
    # Let's assume the files are named like: GM12878_peaks.bed, K562_peaks.bed, etc.
    
    raw_dir = Path(DATA_RAW_DIR)
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        sys.exit(1)
    
    cell_type_mapping = {}
    cell_types = ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']
    
    for ct in cell_types:
        # Look for files containing the cell type name
        matches = list(raw_dir.glob(f"*{ct}*"))
        if matches:
            cell_type_mapping[ct] = matches
        else:
            logger.warning(f"No files found for cell type {ct} in {raw_dir}")
            cell_type_mapping[ct] = []
    
    if not any(cell_type_mapping.values()):
        logger.error("No input files found for any cell type. Cannot proceed.")
        sys.exit(1)
    
    # Run processing
    try:
        processed_peaks = preprocess_all_cell_types(cell_type_mapping)
        logger.info("T014 completed successfully.")
    except Exception as e:
        logger.error(f"T014 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()