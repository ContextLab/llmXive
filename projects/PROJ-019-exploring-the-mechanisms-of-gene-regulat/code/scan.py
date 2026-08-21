import os
import sys
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import json

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import DATA_RAW_DIR, DATA_INTERIM_DIR, TMP_DIR
from code.provenance import load_provenance, set_jaspar_version

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FimoExecutionError(Exception):
    """Raised when FIMO execution fails."""
    pass

class FimoParseError(Exception):
    """Raised when FIMO output parsing fails."""
    pass

def find_motif_database() -> Path:
    """
    Locate the JASPAR CORE database file.
    Tries common installation paths or environment variables.
    """
    # Common locations for JASPAR database
    possible_paths = [
        Path("/usr/share/jaspar/MATRIX/JASPAR2024_CORE_non-redundant_pfms_meme.txt"),
        Path("/usr/local/share/jaspar/MATRIX/JASPAR2024_CORE_non-redundant_pfms_meme.txt"),
        Path("./data/motifs/JASPAR2024_CORE_non-redundant_pfms_meme.txt"),
        Path("./data/raw/JASPAR2024_CORE_non-redundant_pfms_meme.txt"),
    ]

    # Check environment variable first
    env_path = os.getenv("JASPAR_DB")
    if env_path and Path(env_path).exists():
        logger.info(f"Using JASPAR database from environment variable: {env_path}")
        return Path(env_path)

    for p in possible_paths:
        if p.exists():
            logger.info(f"Found JASPAR database at: {p}")
            return p

    # If not found, try to download it if internet is available
    # For now, we assume it should be pre-downloaded or installed
    raise FileNotFoundError(
        "JASPAR database not found. Please download JASPAR2024_CORE_non-redundant_pfms_meme.txt "
        "and place it in data/raw/ or set JASPAR_DB environment variable."
    )

def prepare_input_bed(peaks_path: Path, output_path: Path) -> Path:
    """
    Prepare a BED file for FIMO input from standardized peak file.
    FIMO requires MEME format or specific BED format.
    We assume peaks are already in a standard BED-like format.
    """
    if not peaks_path.exists():
        raise FileNotFoundError(f"Input peaks file not found: {peaks_path}")

    # FIMO can accept BED files directly in some versions, but we ensure format compatibility
    # Read and write to ensure clean format
    with open(peaks_path, 'r') as f_in, open(output_path, 'w') as f_out:
        for line in f_in:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 3:
                logger.warning(f"Skipping malformed BED line: {line}")
                continue
            # Ensure chromosome, start, end are present
            chrom = parts[0]
            start = parts[1]
            end = parts[2]
            # FIMO needs 0-based start, BED is already 0-based
            # Write standard 3-column BED
            f_out.write(f"{chrom}\t{start}\t{end}\n")

    logger.info(f"Prepared FIMO input BED: {output_path}")
    return output_path

def run_fimo(motif_db: Path, input_bed: Path, output_dir: Path, pvalue_threshold: float = 0.0001) -> Path:
    """
    Run FIMO to scan for motifs.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / "fimo.tsv"

    # Check if FIMO is installed
    try:
        subprocess.run(["fimo", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise FimoExecutionError(
            "FIMO is not installed or not in PATH. Please install MEME suite."
        )

    cmd = [
        "fimo",
        "--thresh", str(pvalue_threshold),
        "--text",  # Output text format (TSV)
        "--bgfile", "/dev/null",  # Use uniform background if no specific file
        str(motif_db),
        str(input_bed)
    ]

    # FIMO outputs to stdout with --text, or to file with --output
    # Let's use --output to get fimo.tsv directly
    cmd = [
        "fimo",
        "--thresh", str(pvalue_threshold),
        "--output", str(output_dir),
        str(motif_db),
        str(input_bed)
    ]

    logger.info(f"Running FIMO: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        if result.stderr:
            logger.warning(f"FIMO stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        raise FimoExecutionError(f"FIMO execution failed: {e.stderr}")
    except subprocess.TimeoutExpired:
        raise FimoExecutionError("FIMO execution timed out")

    # FIMO outputs fimo.tsv in the output directory
    if not results_file.exists():
        # Sometimes it's named differently or in a subdirectory
        potential_files = list(output_dir.glob("fimo.*"))
        if potential_files:
            results_file = potential_files[0]
        else:
            raise FimoExecutionError(f"FIMO did not produce expected output in {output_dir}")

    logger.info(f"FIMO completed. Results: {results_file}")
    return results_file

def parse_fimo_output(fimo_results_path: Path) -> List[Dict[str, Any]]:
    """
    Parse FIMO TSV output into a standardized list of motif matches.

    FIMO output columns (from MEME suite):
    motif_id, motif_alt_id, sequence_name, start, stop, strand, score, p-value, q-value, matched_sequence

    Returns a list of dicts with keys:
      - motif_id: str (JASPAR ID, e.g., 'MA0001.1')
      - sequence_name: str (chromosome or peak ID)
      - start: int (0-based start coordinate)
      - stop: int (end coordinate)
      - strand: str ('+' or '-')
      - score: float
      - p_value: float
      - q_value: float
      - matched_sequence: str
    """
    if not fimo_results_path.exists():
        raise FileNotFoundError(f"FIMO results file not found: {fimo_results_path}")

    matches = []
    with open(fimo_results_path, 'r') as f:
        header = None
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                continue

            parts = line.split('\t')

            # Parse header to map indices
            if header is None:
                header = parts
                # Validate expected columns
                expected_cols = ['motif_id', 'motif_alt_id', 'sequence_name', 'start', 'stop',
                                 'strand', 'score', 'p-value', 'q-value', 'matched_sequence']
                if header != expected_cols:
                    logger.warning(f"FIMO header mismatch. Expected: {expected_cols}, Got: {header}")
                continue

            # Parse data row
            try:
                if len(parts) < 10:
                    logger.warning(f"Skipping malformed FIMO line (too few columns): {line}")
                    continue

                match = {
                    'motif_id': parts[0],
                    'motif_alt_id': parts[1],
                    'sequence_name': parts[2],
                    'start': int(parts[3]),
                    'stop': int(parts[4]),
                    'strand': parts[5],
                    'score': float(parts[6]),
                    'p_value': float(parts[7]),
                    'q_value': float(parts[8]),
                    'matched_sequence': parts[9]
                }
                matches.append(match)

            except (ValueError, IndexError) as e:
                logger.warning(f"Skipping malformed FIMO line (parse error): {line} - {e}")
                continue

    logger.info(f"Parsed {len(matches)} motif matches from FIMO output.")
    return matches

def scan_cell_type(cell_type: str, peaks_path: Path, output_dir: Path,
                   motif_db: Optional[Path] = None, pvalue_threshold: float = 0.0001) -> List[Dict[str, Any]]:
    """
    Run FIMO scan for a single cell type.
    """
    if motif_db is None:
        motif_db = find_motif_database()

    # Prepare input
    input_bed = output_dir / f"{cell_type}_input.bed"
    prepare_input_bed(peaks_path, input_bed)

    # Run FIMO
    fimo_output_dir = output_dir / fimo_output_dir
    fimo_output_dir.mkdir(parents=True, exist_ok=True)
    fimo_results = run_fimo(motif_db, input_bed, fimo_output_dir, pvalue_threshold)

    # Parse results
    matches = parse_fimo_output(fimo_results)

    # Filter to only matches within the original peaks if needed
    # (FIMO already operates on the input BED regions)

    return matches

def scan_all_cell_types(cell_types: List[str], peaks_dir: Path, output_dir: Path,
                        motif_db: Optional[Path] = None, pvalue_threshold: float = 0.0001) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scan peaks for all cell types.
    """
    all_results = {}
    for cell_type in cell_types:
        peaks_path = peaks_dir / f"{cell_type}_peaks.bed"
        if not peaks_path.exists():
            logger.warning(f"Peaks file not found for {cell_type}: {peaks_path}")
            all_results[cell_type] = []
            continue

        cell_type_output_dir = output_dir / cell_type
        cell_type_output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Scanning {cell_type}...")
        matches = scan_cell_type(cell_type, peaks_path, cell_type_output_dir, motif_db, pvalue_threshold)
        all_results[cell_type] = matches

        # Save individual scan results for provenance/debugging
        save_scan_results(matches, cell_type_output_dir / f"{cell_type}_scan_results.json")

    return all_results

def save_scan_results(matches: List[Dict[str, Any]], output_path: Path):
    """
    Save scan results to JSON for later use.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(matches, f, indent=2)
    logger.info(f"Saved {len(matches)} matches to {output_path}")

def main():
    """
    Main entry point for scanning motifs.
    """
    # Load configuration
    provenance = load_provenance()
    jaspar_version = provenance.get('jaspar_version', 'JASPAR2024')
    set_jaspar_version(jaspar_version)

    cell_types = ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']
    peaks_dir = DATA_INTERIM_DIR  # Assuming peaks are preprocessed here
    output_dir = DATA_INTERIM_DIR / "fimo_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find motif database
    try:
        motif_db = find_motif_database()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Run scanning
    results = scan_all_cell_types(cell_types, peaks_dir, output_dir, motif_db)

    # Aggregate and save all results
    all_matches = []
    for cell_type, matches in results.items():
        for match in matches:
            match['cell_type'] = cell_type
        all_matches.extend(matches)

    # Save combined results
    combined_output = output_dir / "all_matches.json"
    save_scan_results(all_matches, combined_output)

    logger.info(f"Total motif matches across all cell types: {len(all_matches)}")
    return all_matches

if __name__ == "__main__":
    main()
