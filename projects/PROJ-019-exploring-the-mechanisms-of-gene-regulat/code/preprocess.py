import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from code.config import DATA_RAW_DIR, DATA_INTERIM_DIR
from code.ingest import parse_bed_file, BedParseError

logger = logging.getLogger(__name__)

def parse_downloaded_file(file_path: Path) -> List[Tuple[str, int, int, str]]:
    """Parse a downloaded BED file."""
    return parse_bed_file(file_path)

def write_standardized_bed(records: List[Tuple[str, int, int, str]], output_path: Path) -> None:
    """Write standardized BED records to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for chrom, start, end, name in records:
            f.write(f"{chrom}\t{start}\t{end}\t{name}\n")

def process_cell_type_peaks(cell_type: str, input_path: Path) -> Path:
    """
    Process peaks for a single cell type:
    1. Parse input
    2. (Optional) Filter/Normalize
    3. Write to interim
    """
    logger.info(f"Processing peaks for {cell_type}...")
    records = parse_downloaded_file(input_path)
    output_path = DATA_INTERIM_DIR / f"{cell_type}_standardized.bed"
    write_standardized_bed(records, output_path)
    logger.info(f"Processed {len(records)} peaks for {cell_type} -> {output_path}")
    return output_path

def aggregate_background_model(cell_type_peaks: Dict[str, Path]) -> Path:
    """
    Aggregate background model by unioning peaks from all cell types except the target.
    For simplicity, this creates a union of ALL peaks as the background for now.
    In a real scenario, one would exclude the current cell type's peaks.
    """
    logger.info("Aggregating background model...")
    all_peaks = []
    for ct, path in cell_type_peaks.items():
        records = parse_downloaded_file(path)
        all_peaks.extend(records)

    # Sort and merge overlapping intervals (simple union logic)
    # Sort by chrom, then start
    all_peaks.sort(key=lambda x: (x[0], x[1]))

    merged = []
    if all_peaks:
        current_chrom, current_start, current_end, _ = all_peaks[0]
        for chrom, start, end, name in all_peaks[1:]:
            if chrom == current_chrom and start <= current_end:
                # Overlapping, extend
                current_end = max(current_end, end)
            else:
                # Non-overlapping, push current and start new
                merged.append((current_chrom, current_start, current_end, "."))
                current_chrom, current_start, current_end = chrom, start, end
        merged.append((current_chrom, current_start, current_end, "."))

    output_path = DATA_INTERIM_DIR / "background_model_union.bed"
    write_standardized_bed(merged, output_path)
    logger.info(f"Background model created with {len(merged)} regions -> {output_path}")
    return output_path

def preprocess_all_cell_types() -> Dict[str, Path]:
    """Process all cell types and return paths to standardized files."""
    # Assuming input files are already in DATA_RAW_DIR with naming convention: {cell_type}_*.bed
    raw_files = {}
    for f in DATA_RAW_DIR.glob("*.bed"):
        # Extract cell type from filename
        name = f.stem.split('_')[0]
        raw_files[name] = f

    processed_paths = {}
    for cell_type, path in raw_files.items():
        processed_paths[cell_type] = process_cell_type_peaks(cell_type, path)

    # Generate background model
    aggregate_background_model(processed_paths)

    return processed_paths

def main() -> None:
    """Entry point for CLI."""
    logging.basicConfig(level=logging.INFO)
    try:
        paths = preprocess_all_cell_types()
        print("Preprocessing complete.")
        for ct, p in paths.items():
            print(f"  {ct}: {p}")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
