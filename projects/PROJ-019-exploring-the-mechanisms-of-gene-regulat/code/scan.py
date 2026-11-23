import os
import sys
import logging
import subprocess
import tempfile
import re
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Union
from code.config import TMP_DIR, DATA_INTERIM_DIR
from code.utils.network import fetch_file_with_retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FimoExecutionError(Exception):
    """Raised when FIMO execution fails."""
    pass

class FimoParseError(Exception):
    """Raised when FIMO output cannot be parsed."""
    pass

def find_motif_database() -> Path:
    """
    Locate the JASPAR motif database file.
    
    Returns:
        Path: Path to the JASPAR motif database file.
        
    Raises:
        FileNotFoundError: If the database is not found.
    """
    # Common locations for JASPAR database
    possible_paths = [
        Path("/usr/share/jaspar/motifs.meme"),
        Path("/usr/local/share/jaspar/motifs.meme"),
        Path.home() / ".jaspar" / "motifs.meme",
        Path("./data/jaspar/motifs.meme"),
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found JASPAR database at {path}")
            return path
    
    # Try to download if not found
    logger.warning("JASPAR database not found locally, attempting to download...")
    download_url = "https://jaspar.genereg.net/download/data/2024/CORE/JASPAR2024_CORE_non-redundant_pfms_meme.txt"
    dest_path = Path("./data/jaspar/motifs.meme")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        fetch_file_with_retry(download_url, dest_path)
        logger.info(f"Downloaded JASPAR database to {dest_path}")
        return dest_path
    except Exception as e:
        raise FileNotFoundError(f"Could not find or download JASPAR database: {e}")

def prepare_input_bed(input_bed_path: Path, output_bed_path: Path) -> Path:
    """
    Prepare input BED file for FIMO if necessary.
    
    Args:
        input_bed_path: Path to input BED file.
        output_bed_path: Path to write prepared BED file.
        
    Returns:
        Path: Path to the prepared BED file.
    """
    # FIMO accepts BED format directly, but we ensure it's properly formatted
    # Read and validate input
    if not input_bed_path.exists():
        raise FileNotFoundError(f"Input BED file not found: {input_bed_path}")
    
    # Copy input to output (FIMO can read BED directly)
    with open(input_bed_path, 'r') as infile:
        with open(output_bed_path, 'w') as outfile:
            for line in infile:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Ensure at least 3 columns (chrom, start, end)
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        outfile.write(line + '\n')
    
    logger.info(f"Prepared input BED file: {output_bed_path}")
    return output_bed_path

def run_fimo(
    motif_db: Path,
    input_bed: Path,
    output_dir: Path,
    pvalue_threshold: float = 0.0001,
    max_memory: str = "2G"
) -> Path:
    """
    Run FIMO to scan for motifs.
    
    Args:
        motif_db: Path to JASPAR motif database.
        input_bed: Path to input BED file with peak regions.
        output_dir: Directory to write FIMO output.
        pvalue_threshold: P-value threshold for motif matches.
        max_memory: Maximum memory for FIMO.
        
    Returns:
        Path: Path to FIMO output directory.
        
    Raises:
        FimoExecutionError: If FIMO execution fails.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "fimo",
        "--thresh", str(pvalue_threshold),
        "--max-memory", max_memory,
        "--bgfile", "/dev/null",  # Use default background
        "--oc", str(output_dir),
        str(motif_db),
        str(input_bed)
    ]
    
    logger.info(f"Running FIMO: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("FIMO completed successfully")
        return output_dir
    except subprocess.CalledProcessError as e:
        error_msg = f"FIMO execution failed: {e.stderr}" if e.stderr else str(e)
        raise FimoExecutionError(error_msg)

def parse_fimo_output(fimo_output_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse FIMO output into a standardized list of motif matches.
    
    Args:
        fimo_output_dir: Directory containing FIMO output files.
        
    Returns:
        List[Dict]: List of motif match dictionaries with keys:
            - motif_id: JASPAR motif ID (e.g., 'MA0001.1')
            - sequence_name: Peak region identifier
            - start: Start coordinate (0-based)
            - stop: Stop coordinate
            - strand: '+' or '-'
            - score: Log-likelihood score
            - p_value: P-value of the match
            - q_value: Q-value (FDR-adjusted p-value) - set to None if not available
            - matched_motif: Motif sequence
            
    Raises:
        FimoParseError: If FIMO output cannot be parsed.
    """
    matches_file = fimo_output_dir / "fimo.tsv"
    
    if not matches_file.exists():
        # Check for fimo.txt (older format)
        matches_file = fimo_output_dir / "fimo.txt"
        if not matches_file.exists():
            raise FimoParseError(
                f"No FIMO output file found in {fimo_output_dir}. "
                f"Expected 'fimo.tsv' or 'fimo.txt'."
            )
    
    matches = []
    
    try:
        with open(matches_file, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        raise FimoParseError(f"Failed to read FIMO output file: {e}")
    
    if not lines:
        logger.warning("FIMO output file is empty")
        return matches
    
    # Parse header to find column indices
    header_line = lines[0].strip()
    headers = header_line.split('\t')
    
    # Expected columns in fimo.tsv
    # motif_id, group_id, sequence_name, start, stop, strand, score, p-value, q-value, matched_motif
    col_map = {col: idx for idx, col in enumerate(headers)}
    
    required_cols = ['motif_id', 'sequence_name', 'start', 'stop', 'strand', 'score', 'p-value', 'matched_motif']
    missing_cols = [col for col in required_cols if col not in col_map]
    
    if missing_cols:
        raise FimoParseError(f"Missing required columns in FIMO output: {missing_cols}")
    
    # Parse data rows
    for line_num, line in enumerate(lines[1:], start=2):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        try:
            parts = line.split('\t')
            
            match = {
                'motif_id': parts[col_map['motif_id']],
                'sequence_name': parts[col_map['sequence_name']],
                'start': int(parts[col_map['start']]),
                'stop': int(parts[col_map['stop']]),
                'strand': parts[col_map['strand']],
                'score': float(parts[col_map['score']]),
                'p_value': float(parts[col_map['p-value']]),
                'q_value': None,  # Will be calculated later if needed
                'matched_motif': parts[col_map['matched_motif']],
                'line_number': line_num
            }
            
            # Handle q-value if present
            if 'q-value' in col_map and col_map['q-value'] < len(parts):
                try:
                    q_val = float(parts[col_map['q-value']])
                    match['q_value'] = q_val
                except (ValueError, IndexError):
                    match['q_value'] = None
            
            matches.append(match)
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Skipping malformed line {line_num}: {e}")
            continue
    
    logger.info(f"Parsed {len(matches)} motif matches from FIMO output")
    return matches

def scan_cell_type(
    cell_type: str,
    peak_bed_path: Path,
    motif_db: Optional[Path] = None,
    pvalue_threshold: float = 0.0001
) -> List[Dict[str, Any]]:
    """
    Scan peaks for a specific cell type.
    
    Args:
        cell_type: Name of the cell type.
        peak_bed_path: Path to BED file with peak regions.
        motif_db: Path to JASPAR motif database.
        pvalue_threshold: P-value threshold for motif matches.
        
    Returns:
        List[Dict]: List of motif matches.
    """
    if motif_db is None:
        motif_db = find_motif_database()
    
    # Create temporary directory for FIMO output
    fimo_output_dir = TMP_DIR / f"fimo_{cell_type}"
    fimo_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare input BED
    prepared_bed = TMP_DIR / f"prepared_{cell_type}.bed"
    prepare_input_bed(peak_bed_path, prepared_bed)
    
    # Run FIMO
    run_fimo(motif_db, prepared_bed, fimo_output_dir, pvalue_threshold)
    
    # Parse results
    matches = parse_fimo_output(fimo_output_dir)
    
    # Add cell type info to each match
    for match in matches:
        match['cell_type'] = cell_type
    
    return matches

def scan_all_cell_types(
    cell_types: List[str],
    peak_files: Dict[str, Path],
    motif_db: Optional[Path] = None,
    pvalue_threshold: float = 0.0001
) -> List[Dict[str, Any]]:
    """
    Scan peaks for all cell types.
    
    Args:
        cell_types: List of cell type names.
        peak_files: Dictionary mapping cell type to peak BED file path.
        motif_db: Path to JASPAR motif database.
        pvalue_threshold: P-value threshold for motif matches.
        
    Returns:
        List[Dict]: Combined list of motif matches for all cell types.
    """
    all_matches = []
    
    for cell_type in cell_types:
        if cell_type not in peak_files:
            logger.warning(f"No peak file found for cell type: {cell_type}")
            continue
        
        logger.info(f"Scanning peaks for cell type: {cell_type}")
        matches = scan_cell_type(
            cell_type,
            peak_files[cell_type],
            motif_db,
            pvalue_threshold
        )
        all_matches.extend(matches)
    
    logger.info(f"Total motif matches across all cell types: {len(all_matches)}")
    return all_matches

def save_scan_results(
    matches: List[Dict[str, Any]],
    output_path: Path
) -> Path:
    """
    Save motif scan results to a JSON file.
    
    Args:
        matches: List of motif match dictionaries.
        output_path: Path to output JSON file.
        
    Returns:
        Path: Path to the saved file.
    """
    import json
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(matches, f, indent=2)
    
    logger.info(f"Saved {len(matches)} motif matches to {output_path}")
    return output_path

def main():
    """Main entry point for motif scanning."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage - in production, this would be called from main.py
    # with actual paths and cell types
    logger.info("Motif scanning module ready")
    logger.info("Use scan_cell_type() or scan_all_cell_types() to perform scanning")

if __name__ == "__main__":
    main()