import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from code.config import DATA_RAW_DIR, DATA_INTERIM_DIR, TMP_DIR
import pybedtools
from pybedtools import BedTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class DataParseError(Exception):
    """Custom exception for data parsing failures."""
    pass

def parse_downloaded_file(file_path: Path, cell_type: str) -> List[Dict]:
    """
    Parse a downloaded peak file (BED-like) into a list of dictionaries.
    
    Args:
        file_path: Path to the downloaded peak file.
        cell_type: Identifier for the cell type (e.g., 'GM12878').
        
    Returns:
        List of dictionaries with keys: 'chrom', 'start', 'end', 'name', 'score', 'strand'.
        
    Raises:
        DataParseError: If the file cannot be parsed or is malformed.
    """
    if not file_path.exists():
        raise DataParseError(f"File not found: {file_path}")
    
    peaks = []
    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('\t')
                if len(parts) < 3:
                    raise DataParseError(f"Malformed BED line at {line_num}: {line}")
                
                chrom = parts[0]
                start = int(parts[1])
                end = int(parts[2])
                name = parts[3] if len(parts) > 3 else f"{cell_type}_peak_{line_num}"
                score = parts[4] if len(parts) > 4 else '0'
                strand = parts[5] if len(parts) > 5 else '.'
                
                peaks.append({
                    'chrom': chrom,
                    'start': start,
                    'end': end,
                    'name': name,
                    'score': score,
                    'strand': strand,
                    'cell_type': cell_type
                })
    except ValueError as e:
        raise DataParseError(f"Error parsing file {file_path}: {e}")
    
    logger.info(f"Parsed {len(peaks)} peaks for {cell_type} from {file_path}")
    return peaks

def write_standardized_bed(peaks: List[Dict], output_path: Path) -> Path:
    """
    Write a list of peak dictionaries to a standardized BED file.
    
    Args:
        peaks: List of peak dictionaries.
        output_path: Path to the output BED file.
        
    Returns:
        Path to the created file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for peak in peaks:
            line = f"{peak['chrom']}\t{peak['start']}\t{peak['end']}\t{peak['name']}\t{peak['score']}\t{peak['strand']}\n"
            f.write(line)
    
    logger.info(f"Wrote {len(peaks)} peaks to {output_path}")
    return output_path

def annotate_with_gene_symbols(bed_file: Path, gtf_file: Optional[Path] = None) -> BedTool:
    """
    Annotate peaks with gene symbols using pybedtools.
    
    Args:
        bed_file: Path to the BED file of peaks.
        gtf_file: Optional path to a GTF file. If None, uses a default hg38 annotation.
        
    Returns:
        BedTool object with annotations.
    """
    # Default GTF path if not provided (assuming standard location or download)
    # In a real pipeline, this would be a specific path to hg38 annotation
    if gtf_file is None:
        # Attempt to use a standard annotation file if available
        # For this implementation, we assume the environment has the necessary annotation
        # or we rely on pybedtools' built-in functionality if configured
        logger.warning("No GTF file provided. Using default annotation strategy.")
        # In a real scenario, we might download or specify a path like:
        # gtf_file = Path("/path/to/hg38.gtf")
        # For now, we proceed with the bed file and assume annotation can be done
        # or we return the bed tool as is if no GTF is available, 
        # but the task requires mapping to gene symbols.
        # We will assume a standard path or that the user has configured the environment.
        # If the file doesn't exist, we raise an error to fail loudly as per constraints.
        default_gtf = Path("/data/hg38/genes.gtf")
        if not default_gtf.exists():
            # Try to find a common location or raise error
            # For the purpose of this task, we assume the file exists in a standard location 
            # or we use a mock annotation if the real one is missing (but task says NO synthetic)
            # We will raise an error if the annotation file is missing to fail loudly.
            raise FileNotFoundError(f"Annotation GTF file not found at {default_gtf}. "
                                    "Please provide a valid GTF file for hg38.")
        gtf_file = default_gtf

    bed_tool = BedTool(str(bed_file))
    gtf_tool = BedTool(str(gtf_file))
    
    # Intersect peaks with genes to get annotations
    # Using 'wa' to keep the peak (left) and 'wb' to get the gene info (right)
    # We assume the GTF is formatted such that the 4th column is gene_id or gene_name
    annotated = bed_tool.intersect(gtf_tool, wa=True, wb=True)
    
    logger.info(f"Annotated peaks against GTF: {gtf_file}")
    return annotated

def process_cell_type_peaks(cell_type: str, raw_files: Dict[str, Path]) -> Path:
    """
    Process peaks for a single cell type: parse, standardize, and annotate.
    
    Args:
        cell_type: The cell type identifier.
        raw_files: Dictionary mapping cell type to raw file path.
        
    Returns:
        Path to the processed/annotated BED file.
    """
    if cell_type not in raw_files:
        raise ValueError(f"Raw file not found for cell type: {cell_type}")
    
    raw_path = raw_files[cell_type]
    logger.info(f"Processing peaks for {cell_type} from {raw_path}")
    
    # Parse
    peaks = parse_downloaded_file(raw_path, cell_type)
    
    # Write standardized BED
    interim_path = TMP_DIR / f"{cell_type}_peaks_standardized.bed"
    write_standardized_bed(peaks, interim_path)
    
    # Annotate
    annotated_bed_path = TMP_DIR / f"{cell_type}_peaks_annotated.bed"
    # Note: In a real pipeline, we would perform the annotation here.
    # For this task, we assume the annotation step is performed or the file is prepared.
    # If annotation is strictly required to produce the file, we would call annotate_with_gene_symbols.
    # However, the primary output for T014 is the background model.
    # We will create the annotated file by copying the standardized one if annotation is not feasible
    # without a specific GTF, but we must fail loudly if GTF is missing.
    # To satisfy the task requirement of "map peak coordinates to gene symbols",
    # we assume the GTF is available.
    try:
        annotated_tool = annotate_with_gene_symbols(interim_path)
        annotated_tool.saveas(str(annotated_bed_path))
    except FileNotFoundError as e:
        # If GTF is missing, we cannot annotate. We raise the error to fail loudly.
        raise e
        
    return annotated_bed_path

def aggregate_background_model(cell_types: List[str], processed_files: Dict[str, Path]) -> Path:
    """
    Aggregate peaks from all cell types EXCEPT the current one to form the dynamic background model.
    This implements the requirement: "for each target cell type, aggregate peaks from the remaining cell types".
    However, the task output is a single file: data/interim/background_union.bed.
    This implies a union of ALL peaks from ALL cell types to serve as a global background,
    or a specific union for a specific target. 
    Given the output path is singular, we will create a UNION of ALL peaks from ALL cell types
    to serve as the background model for enrichment analysis (FR-004).
    
    Args:
        cell_types: List of all cell types.
        processed_files: Dictionary mapping cell type to processed BED file path.
        
    Returns:
        Path to the aggregated background union BED file.
    """
    logger.info(f"Aggregating background model from {len(processed_files)} cell types.")
    
    all_peaks = []
    for ct, file_path in processed_files.items():
        if not file_path.exists():
            raise FileNotFoundError(f"Processed file missing for {ct}: {file_path}")
        logger.info(f"Loading peaks from {ct} for background aggregation.")
        bed_tool = BedTool(str(file_path))
        all_peaks.append(bed_tool)
    
    if not all_peaks:
        raise ValueError("No peaks found to aggregate for background model.")
    
    # Union all peaks
    # pybedtools can merge multiple BedTools
    background_tool = all_peaks[0]
    for tool in all_peaks[1:]:
        background_tool = background_tool.cat(tool, postmerge=False)
    
    # Merge overlapping intervals to create a clean union
    # We use merge to combine overlapping regions
    background_union = background_tool.merge()
    
    output_path = DATA_INTERIM_DIR / "background_union.bed"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    background_union.saveas(str(output_path))
    
    logger.info(f"Background union written to {output_path}")
    logger.info(f"Total unique regions in background: {background_union.count()}")
    
    return output_path

def preprocess_all_cell_types(cell_types: List[str], raw_files: Dict[str, Path]) -> Dict[str, Path]:
    """
    Process all cell types and aggregate the background model.
    
    Args:
        cell_types: List of cell types to process.
        raw_files: Dictionary mapping cell type to raw file path.
        
    Returns:
        Dictionary mapping cell type to processed BED file path.
    """
    processed_files = {}
    
    # Process each cell type
    for ct in cell_types:
        try:
            processed_path = process_cell_type_peaks(ct, raw_files)
            processed_files[ct] = processed_path
        except Exception as e:
            logger.error(f"Failed to process {ct}: {e}")
            raise DataParseError(f"Error processing {ct}: {e}")
    
    # Aggregate background model
    aggregate_background_model(cell_types, processed_files)
    
    return processed_files

def main():
    """
    Main entry point for preprocessing.
    """
    # Define cell types and their raw files (this would typically come from config or download step)
    # For this task, we assume the raw files are already downloaded by T012
    cell_types = ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']
    
    # Map cell types to expected raw file paths (adjust based on T012 output)
    # Assuming T012 downloads to DATA_RAW_DIR with specific naming
    raw_files = {}
    for ct in cell_types:
        # Example naming convention: adjust as needed based on actual download filenames
        raw_files[ct] = DATA_RAW_DIR / f"{ct}_peaks.bed"
    
    logger.info("Starting preprocessing pipeline...")
    logger.info(f"Cell types: {cell_types}")
    logger.info(f"Raw files: {raw_files}")
    
    try:
        processed_files = preprocess_all_cell_types(cell_types, raw_files)
        logger.info("Preprocessing completed successfully.")
        logger.info(f"Processed files: {processed_files}")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()