"""
Task T021: Implement motif scanning using FIMO.

This module invokes the FIMO tool (from MEME suite) to scan peak regions
against the JASPAR CORE database. It handles:
1. Preparing input BED files for FIMO.
2. Constructing the FIMO command line.
3. Executing FIMO via subprocess.
4. Parsing the raw FIMO output (TSV) into a structured pandas DataFrame.
5. Saving results to the processed data directory.

Dependencies:
- FIMO must be installed and available in $PATH.
- JASPAR database files (motifs.meme) must be available locally.
"""

import os
import sys
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

from code.config import (
    DATA_INTERIM_DIR,
    DATA_PROCESSED_DIR,
    JASPAR_VERSION,
    JASPAR_MOTIF_FILE,
    FIMO_PVALUE_THRESHOLD,
)
from code.preprocess import write_standardized_bed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def find_motif_database() -> Path:
    """
    Locate the JASPAR CORE motif database file.
    Expects the file to be in data/raw/ or a standard location.
    If not found, attempts to download or raise a clear error.
    """
    # Check common locations based on project structure
    possible_paths = [
        Path(DATA_RAW_DIR) / "jaspar" / "JASPAR2024_CORE_non-redundant_pfms_meme.txt",
        Path(DATA_RAW_DIR) / "motifs.meme",
        Path("data/raw/motifs.meme"),
    ]

    for p in possible_paths:
        if p.exists():
            logger.info(f"Found JASPAR database at: {p}")
            return p

    # If not found, raise a specific error
    raise FileNotFoundError(
        f"JASPAR motif database not found. "
        f"Searched: {possible_paths}. "
        f"Please download the MEME format database from JASPAR and place it at "
        f"data/raw/motifs.meme or update the path in config.py."
    )


def prepare_input_bed(cell_type: str, output_dir: Path) -> Path:
    """
    Prepare the input BED file for FIMO for a specific cell type.
    Ensures the file is in the correct format (chrom, start, end, name).
    """
    # The preprocess step should have already created standardized BED files
    # in data/interim/. We verify existence here.
    input_file = Path(DATA_INTERIM_DIR) / f"{cell_type}_peaks.bed"
    
    if not input_file.exists():
        raise FileNotFoundError(
            f"Input peak file for {cell_type} not found at {input_file}. "
            f"Please run T013/T014 (preprocess) first."
        )
    
    # FIMO expects a BED-like format or FASTA. 
    # We will convert BED to FASTA using pybedtools if available, 
    # or assume FIMO can handle BED if the genome is provided.
    # However, standard FIMO usage often requires a genome FASTA to extract sequences.
    # To keep it self-contained and robust, we will assume the input BED is valid
    # and we need to extract sequences.
    # For this implementation, we will generate a FASTA file from the BED using
    # a helper or assume the user has a genome FASTA.
    # Given the constraints, we will assume the input BED is sufficient 
    # if we pass a genome FASTA, OR we convert BED to FASTA.
    
    # Let's create a temporary FASTA file from the BED for robustness.
    # We need a genome FASTA. If not provided, we might need to download hg38.
    # For now, we assume the existence of a genome file or use a helper.
    
    # Simpler approach: FIMO can accept a BED file if --bgfile is provided? 
    # No, FIMO needs sequences.
    # We will assume the presence of 'hg38.fa' in data/raw/ or download it.
    # To strictly follow "no synthetic data" and "real source", we must fetch hg38.
    
    genome_fasta = Path(DATA_RAW_DIR) / "hg38.fa"
    if not genome_fasta.exists():
        logger.warning(f"Genome FASTA not found at {genome_fasta}. "
                       "Attempting to download a subset or raising error.")
        # In a real pipeline, we would download hg38 here.
        # For this task, we assume the user has downloaded hg38.fa or it's provided.
        # If missing, we fail loudly.
        raise FileNotFoundError(
            f"Genome FASTA file (hg38.fa) not found at {genome_fasta}. "
            f"Please download hg38.fa and place it in {DATA_RAW_DIR}."
        )

    # Extract sequences using pybedtools
    try:
        import pybedtools
    except ImportError:
        raise ImportError(
            "pybedtools is required to extract sequences from BED. "
            "Please install it via requirements.txt."
        )

    bed = pybedtools.BedTool(str(input_file))
    fasta_out = output_dir / f"{cell_type}_peaks.fa"
    
    # Extract sequences
    bed.sequence(fi=str(genome_fasta), fo=str(fasta_out))
    logger.info(f"Extracted sequences to {fasta_out}")
    
    return fasta_out


def run_fimo(
    motif_db: Path, 
    query_fasta: Path, 
    output_dir: Path, 
    pvalue_threshold: float = FIMO_PVALUE_THRESHOLD
) -> Path:
    """
    Execute FIMO subprocess.
    
    Args:
        motif_db: Path to JASPAR MEME format file.
        query_fasta: Path to the FASTA file of peak sequences.
        output_dir: Directory to store FIMO output.
        pvalue_threshold: Threshold for p-value (default 1e-4).
        
    Returns:
        Path to the 'fimo.tsv' (or 'fimo.txt') output file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # FIMO command construction
    # fimo --thresh <pval> --oc <output_dir> <motifs> <sequences>
    cmd = [
        "fimo",
        "--thresh", f"{pvalue_threshold}",
        "--oc", str(output_dir),
        str(motif_db),
        str(query_fasta)
    ]
    
    logger.info(f"Executing FIMO: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per cell type
        )
        
        if result.stderr:
            logger.warning(f"FIMO stderr: {result.stderr}")
            
        # FIMO outputs to the --oc directory. The main results are in fimo.tsv
        # (or fimo.txt depending on version, usually fimo.tsv in newer versions)
        # Let's check for common output names
        output_file = output_dir / "fimo.tsv"
        if not output_file.exists():
            output_file = output_dir / "fimo.txt"
            if not output_file.exists():
                # List files to debug
                files = list(output_dir.iterdir())
                raise RuntimeError(
                    f"FIMO completed but no output file found in {output_dir}. "
                    f"Files present: {files}"
                )
        
        logger.info(f"FIMO completed. Output: {output_file}")
        return output_file
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FIMO failed with return code {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        raise RuntimeError(f"FIMO execution failed: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError(
            "FIMO executable not found in PATH. "
            "Please install MEME suite (containing fimo) and ensure it is in your PATH."
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("FIMO execution timed out.")


def parse_fimo_output(fimo_file: Path) -> pd.DataFrame:
    """
    Parse the FIMO TSV output into a DataFrame.
    
    Columns typically: motif_id, motif_alt_id, sequence_name, start, stop, strand,
    score, p_value, q_value, matched_sequence
    """
    if not fimo_file.exists():
        raise FileNotFoundError(f"FIMO output file not found: {fimo_file}")
    
    try:
        # FIMO TSV is tab-separated, with a header line
        df = pd.read_csv(fimo_file, sep="\t")
        
        # Standardize column names if necessary
        # Ensure we have the expected columns for downstream enrichment
        expected_cols = ['motif_id', 'sequence_name', 'start', 'stop', 'strand', 'p_value']
        if not all(col in df.columns for col in expected_cols):
            logger.warning(f"Unexpected columns in FIMO output: {df.columns.tolist()}")
        
        # Convert sequence_name to cell_type if it contains the cell type name
        # The sequence_name in FASTA is usually the peak ID or coordinates.
        # We assume the peak ID encodes the cell type or we can infer it from the file name.
        # For now, we'll leave it as is and let the enrichment step handle grouping.
        
        logger.info(f"Parsed {len(df)} motif hits from {fimo_file}")
        return df
        
    except Exception as e:
        logger.error(f"Error parsing FIMO output: {e}")
        raise


def scan_cell_type(
    cell_type: str, 
    motif_db: Optional[Path] = None,
    pvalue_threshold: float = FIMO_PVALUE_THRESHOLD
) -> pd.DataFrame:
    """
    Scan peaks for a specific cell type.
    
    Args:
        cell_type: Cell type identifier (e.g., 'GM', 'K562').
        motif_db: Path to JASPAR database. Defaults to finding it automatically.
        pvalue_threshold: P-value threshold for FIMO.
        
    Returns:
        DataFrame of motif hits.
    """
    if motif_db is None:
        motif_db = find_motif_database()
        
    # Prepare working directory for this cell type
    work_dir = Path(DATA_PROCESSED_DIR) / "scan" / cell_type
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Prepare input (BED -> FASTA)
    query_fasta = prepare_input_bed(cell_type, work_dir)
    
    # 2. Run FIMO
    fimo_output = run_fimo(motif_db, query_fasta, work_dir, pvalue_threshold)
    
    # 3. Parse output
    df = parse_fimo_output(fimo_output)
    
    # Add cell_type column for downstream aggregation
    df['cell_type'] = cell_type
    
    return df


def scan_all_cell_types(
    cell_types: List[str] = None,
    motif_db: Optional[Path] = None,
    pvalue_threshold: float = FIMO_PVALUE_THRESHOLD
) -> pd.DataFrame:
    """
    Scan all specified cell types and aggregate results.
    """
    if cell_types is None:
        # Default cell types from the project spec
        cell_types = ["GM", "K562", "HepG2", "H1-hESC", "IMR90"]
        
    all_results = []
    
    for ct in cell_types:
        logger.info(f"Processing cell type: {ct}")
        try:
            df = scan_cell_type(ct, motif_db, pvalue_threshold)
            all_results.append(df)
        except Exception as e:
            logger.error(f"Failed to process {ct}: {e}")
            # Depending on requirements, we might want to fail hard or skip.
            # For robustness, we log and continue, but in a strict pipeline,
            # we might raise. The task says "Implement scan.py", so we assume
            # we want to get results for as many as possible, or fail if critical.
            # Given "Fail loudly" constraint, if a critical step fails, we should probably raise.
            # But if one cell type fails, others might succeed. 
            # We'll raise if the first one fails, or collect errors.
            # Let's raise for now to ensure data integrity.
            raise RuntimeError(f"Scanning failed for cell type {ct}: {e}")
    
    if not all_results:
        raise RuntimeError("No results generated for any cell type.")
        
    combined_df = pd.concat(all_results, ignore_index=True)
    return combined_df


def save_scan_results(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the aggregated scan results to a CSV file.
    """
    if output_path is None:
        output_path = Path(DATA_PROCESSED_DIR) / "motif_scan_results.csv"
        
    df.to_csv(output_path, index=False)
    logger.info(f"Saved motif scan results to {output_path}")
    return output_path


def main():
    """
    Main entry point for the scanning task.
    """
    logger.info("Starting motif scanning (T021)...")
    
    try:
        # Run scanning for all cell types
        results = scan_all_cell_types()
        
        # Save results
        output_file = save_scan_results(results)
        
        logger.info(f"Scanning complete. Results saved to {output_file}")
        
    except FileNotFoundError as e:
        logger.error(f"Missing data file: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
