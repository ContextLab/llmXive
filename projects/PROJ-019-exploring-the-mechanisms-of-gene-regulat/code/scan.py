import os
import sys
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from joblib import Parallel, delayed

from code.config import DATA_INTERIM_DIR, DATA_RAW_DIR
from code.provenance import add_encode_accession, set_jaspar_version

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
JASPAR_CORE_VERSION = "2024"
FIMO_THRESHOLD = 1e-4

def find_motif_database() -> Path:
    """
    Locate the JASPAR CORE motif database.
    Assumes the database is installed via the `jaspar2024` package or available in standard paths.
    """
    # Try to find the database via the jaspar2024 package if installed
    try:
        import jaspar2024
        jaspar_path = Path(jaspar2024.__file__).parent / "motifs" / "JASPAR2024_CORE_non-redundant_pfms_meme.txt"
        if jaspar_path.exists():
            logger.info(f"Found JASPAR database at {jaspar_path}")
            return jaspar_path
    except ImportError:
        logger.warning("jaspar2024 package not found, searching for MEME file manually...")
    
    # Fallback: look for standard locations
    possible_paths = [
        Path("/usr/share/jaspar/JASPAR2024_CORE_non-redundant_pfms_meme.txt"),
        Path(os.path.expanduser("~/.jaspar/JASPAR2024_CORE_non-redundant_pfms_meme.txt")),
        Path("./data/motifs/JASPAR2024_CORE_non-redundant_pfms_meme.txt"),
    ]
    
    for p in possible_paths:
        if p.exists():
            logger.info(f"Found JASPAR database at {p}")
            return p
    
    raise FileNotFoundError(
        "Could not find JASPAR CORE motif database. "
        "Please install the 'jaspar2024' package or provide the MEME file path."
    )

def prepare_input_bed(peaks: List[Tuple[str, str, int, int, str, str]], output_path: Path) -> Path:
    """
    Convert a list of peak tuples to a BED file for FIMO input.
    Format: chrom, start, end, name, score, strand
    """
    with open(output_path, 'w') as f:
        for i, (chrom, start, end, name, score, strand) in enumerate(peaks):
            # FIMO expects 0-based start, 1-based end in some contexts, but standard BED is 0-based start, 0-based end (exclusive)
            # We assume input is standard BED format (0-based start, 0-based end exclusive)
            # FIMO accepts standard BED format
            f.write(f"{chrom}\t{start}\t{end}\t{name}\t{score}\t{strand}\n")
    return output_path

def run_fimo(motif_db: Path, input_bed: Path, output_dir: Path, threshold: float = FIMO_THRESHOLD) -> Path:
    """
    Run FIMO to scan peaks for motifs.
    Returns the path to the FIMO output directory.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    fimo_output_dir = output_dir / "fimo_output"
    fimo_output_dir.mkdir(exist_ok=True)
    
    cmd = [
        "fimo",
        "--thresh", str(threshold),
        "--oc", str(fimo_output_dir),
        str(motif_db),
        str(input_bed)
    ]
    
    logger.info(f"Running FIMO: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stderr:
            logger.warning(f"FIMO stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FIMO failed with return code {e.returncode}")
        if e.stderr:
            logger.error(f"FIMO stderr: {e.stderr}")
        raise
    
    # Return the path to the gapped output file (gapped is usually the main result)
    # FIMO outputs 'fimo.tsv' or 'fimo.txt' depending on version, but 'gapped' is standard in newer versions
    # We'll look for the main TSV file
    tsv_files = list(fimo_output_dir.glob("fimo*.tsv"))
    if tsv_files:
        return tsv_files[0]
    # Fallback to txt if tsv not found
    txt_files = list(fimo_output_dir.glob("fimo*.txt"))
    if txt_files:
        return txt_files[0]
    raise FileNotFoundError("FIMO did not produce expected output files.")

def parse_fimo_output(fimo_tsv: Path) -> List[Dict[str, Any]]:
    """
    Parse FIMO TSV output into a list of motif matches.
    Expected columns: motif_id, motif_alt_id, sequence_name, start, stop, strand, score, p-value, q-value, matched_sequence
    """
    matches = []
    with open(fimo_tsv, 'r') as f:
        header = f.readline().strip().split('\t')
        # Find column indices
        try:
            motif_idx = header.index('motif_id')
            seq_name_idx = header.index('sequence_name')
            start_idx = header.index('start')
            stop_idx = header.index('stop')
            strand_idx = header.index('strand')
            score_idx = header.index('score')
            pval_idx = header.index('p-value')
        except ValueError as e:
            logger.error(f"Missing expected column in FIMO output: {e}")
            raise
        
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < len(header):
                continue
            try:
                match = {
                    'motif_id': parts[motif_idx],
                    'sequence_name': parts[seq_name_idx],
                    'start': int(parts[start_idx]),
                    'stop': int(parts[stop_idx]),
                    'strand': parts[strand_idx],
                    'score': float(parts[score_idx]),
                    'p_value': float(parts[pval_idx]),
                }
                matches.append(match)
            except (ValueError, IndexError) as e:
                logger.warning(f"Skipping malformed FIMO line: {line} - {e}")
                continue
    return matches

def scan_cell_type(cell_type: str, peaks: List[Tuple[str, str, int, int, str, str]], motif_db: Path) -> List[Dict[str, Any]]:
    """
    Scan a single cell type's peaks for motifs.
    Uses joblib.Parallel for parallel execution if the peak list is large.
    However, FIMO itself is a single process per run. The optimization here
    is to parallelize the scanning of *multiple* cell types if called in a batch,
    or to split a very large BED file into chunks if FIMO supports it (it doesn't directly).
    
    Since FIMO runs as a single process per invocation, we cannot parallelize *within* a single FIMO run
    easily without splitting the input BED file. The task asks to use joblib.Parallel in the FIMO loop.
    The most logical interpretation is to parallelize the scanning of multiple cell types 
    OR to parallelize the processing of chunks of peaks if we were running FIMO on chunks.
    Given FIMO's nature, we will parallelize the scanning of multiple cell types if this function 
    is part of a larger loop, but here it's for a single cell type.
    
    To satisfy the requirement "Modify FIMO loop in code/scan.py to use joblib.Parallel",
    we will implement a strategy where we split the peaks into chunks, run FIMO on each chunk in parallel,
    and then merge the results. This is safe if the chunks are independent (which they are).
    Note: FIMO doesn't natively support parallel processing of a single input file, so we split the input.
    
    However, splitting BED for FIMO and merging results is complex because FIMO expects a single file.
    A better approach for "parallelizing the loop" in the context of the whole pipeline is to parallelize
    the `scan_all_cell_types` function. But the task specifically mentions `scan.py` and the FIMO loop.
    
    Let's interpret "FIMO loop" as the loop that processes chunks of data if we were to split the input.
    Since FIMO doesn't support chunked input natively, we will create a wrapper that splits the BED,
    runs FIMO on each chunk in parallel, and merges the TSV outputs.
    
    Wait, FIMO is slow. Splitting the input BED file into N chunks, running FIMO N times in parallel,
    and merging the results is a valid strategy to speed up processing on multi-core machines.
    We must ensure memory usage stays <7GB.
    """
    
    # Strategy: Split peaks into chunks, run FIMO on each chunk in parallel, merge results.
    # Number of jobs: 2 as per task requirement.
    # Max memory per job: 500MB (controlled by joblib's max_nbytes, though FIMO's memory usage is external).
    # We rely on the fact that each FIMO process will use some memory, and 2 processes * ~500MB (est) = ~1GB, well under 7GB.
    
    num_jobs = 2
    chunk_size = max(1000, len(peaks) // num_jobs)
    chunks = [peaks[i:i + chunk_size] for i in range(0, len(peaks), chunk_size)]
    
    logger.info(f"Splitting {len(peaks)} peaks into {len(chunks)} chunks for parallel FIMO execution.")
    
    def run_fimo_on_chunk(chunk_peaks: List[Tuple[str, str, int, int, str, str]], chunk_id: int) -> List[Dict[str, Any]]:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_bed = tmp_path / f"chunk_{chunk_id}.bed"
            prepare_input_bed(chunk_peaks, input_bed)
            fimo_result = run_fimo(motif_db, input_bed, tmp_path)
            return parse_fimo_output(fimo_result)
    
    # Run FIMO on chunks in parallel
    # Note: We use max_nbytes to limit the memory footprint of joblib's serialization,
    # but the actual FIMO process memory is controlled by the OS and FIMO itself.
    # We assume FIMO's memory usage is manageable for 2 concurrent processes.
    results = Parallel(n_jobs=num_jobs, max_nbytes=500*1024*1024)(
        delayed(run_fimo_on_chunk)(chunk, idx) for idx, chunk in enumerate(chunks)
    )
    
    # Flatten results
    all_matches = [match for chunk_results in results for match in chunk_results]
    logger.info(f"Scanned {cell_type}: found {len(all_matches)} motif matches.")
    return all_matches

def scan_all_cell_types(cell_type_peaks: Dict[str, List[Tuple[str, str, int, int, str, str]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scan all cell types for motifs.
    """
    motif_db = find_motif_database()
    set_jaspar_version(JASPAR_CORE_VERSION)
    
    all_results = {}
    for cell_type, peaks in cell_type_peaks.items():
        logger.info(f"Scanning cell type: {cell_type} ({len(peaks)} peaks)")
        matches = scan_cell_type(cell_type, peaks, motif_db)
        all_results[cell_type] = matches
    return all_results

def save_scan_results(results: Dict[str, List[Dict[str, Any]]], output_dir: Path):
    """
    Save scan results to JSON files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for cell_type, matches in results.items():
        output_file = output_dir / f"{cell_type}_motif_matches.json"
        with open(output_file, 'w') as f:
            import json
            json.dump(matches, f, indent=2)
        logger.info(f"Saved {len(matches)} matches for {cell_type} to {output_file}")

def main():
    """
    Main entry point for motif scanning.
    """
    # This would typically be called from main.py with preprocessed data
    # For now, we assume data is in DATA_INTERIM_DIR
    logger.info("Starting motif scanning pipeline...")
    
    # Example: Load peaks from interim directory (simplified)
    # In reality, this would be passed from preprocess.py
    cell_type_peaks = {}
    # Placeholder for loading data
    # for cell_type in ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']:
    #     peaks_file = DATA_INTERIM_DIR / f"{cell_type}_peaks.bed"
    #     if peaks_file.exists():
    #         # Parse BED file
    #         cell_type_peaks[cell_type] = [] # TODO: Implement parsing
    
    if not cell_type_peaks:
        logger.warning("No peaks found. Skipping scan.")
        return
    
    results = scan_all_cell_types(cell_type_peaks)
    save_scan_results(results, DATA_INTERIM_DIR / "scan_results")
    logger.info("Motif scanning completed.")

if __name__ == "__main__":
    main()