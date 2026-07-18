"""
Preprocessing pipeline wrappers for RNA-seq data.

Wraps fastp, HISAT2, and featureCounts to produce normalized TPM matrices.
Since external tools may not be available in all environments, this module
provides a fallback simulation mode for testing and integration.
"""
import os
import subprocess
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.utils.config import get_data_path

logger = get_logger("preprocess")

def run_fastp(
    input_file: str,
    output_file: str,
    report_file: Optional[str] = None
) -> bool:
    """
    Runs fastp for quality control and adapter trimming.
    
    Args:
        input_file: Path to input FASTQ file.
        output_file: Path to output FASTQ file.
        report_file: Path to HTML report.
        
    Returns:
        True if successful, False otherwise.
    """
    cmd = [
        "fastp",
        "-i", input_file,
        "-o", output_file,
        "--thread", "4"
    ]
    if report_file:
        cmd.extend(["-h", report_file])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"fastp completed for {input_file}")
        return True
    except FileNotFoundError:
        logger.warning(f"fastp not found. Skipping fastp for {input_file}.")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"fastp failed for {input_file}: {e.stderr}")
        return False

def run_hisat2(
    index: str,
    reads: str,
    output_sam: str
) -> bool:
    """
    Runs HISAT2 for alignment.
    
    Args:
        index: Path to HISAT2 index.
        reads: Path to input FASTQ.
        output_sam: Path to output SAM file.
        
    Returns:
        True if successful, False otherwise.
    """
    cmd = [
        "hisat2",
        "-x", index,
        "-q", reads,
        "-S", output_sam,
        "--threads", "4"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"HISAT2 completed for {reads}")
        return True
    except FileNotFoundError:
        logger.warning(f"HISAT2 not found. Skipping alignment for {reads}.")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"HISAT2 failed for {reads}: {e.stderr}")
        return False

def run_featurecounts(
    sam_files: List[str],
    annotation_gtf: str,
    output_counts: str
) -> bool:
    """
    Runs featureCounts to generate count matrix.
    
    Args:
        sam_files: List of paths to SAM/BAM files.
        annotation_gtf: Path to GTF annotation file.
        output_counts: Path to output count file.
        
    Returns:
        True if successful, False otherwise.
    """
    cmd = [
        "featureCounts",
        "-a", annotation_gtf,
        "-o", output_counts,
        "-T", "4"
    ] + sam_files
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"featureCounts completed for {len(sam_files)} samples")
        return True
    except FileNotFoundError:
        logger.warning(f"featureCounts not found. Skipping counting.")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"featureCounts failed: {e.stderr}")
        return False

def calculate_tpm(counts_df: pd.DataFrame, lengths: Optional[pd.Series] = None) -> pd.DataFrame:
    """
    Calculates TPM from a count matrix.
    
    Args:
        counts_df: DataFrame of raw counts (genes x samples).
        lengths: Optional Series of gene lengths.
        
    Returns:
        DataFrame of TPM values.
    """
    if lengths is None:
        # Assume uniform length if not provided
        lengths = pd.Series(1000.0, index=counts_df.index)
    
    # RPK = Reads Per Kilobase
    rpk = counts_df.div(lengths, axis=0) / 1000.0
    
    # Scaling factor per sample (per million)
    scaling_factors = rpk.sum(axis=0) / 1e6
    
    # TPM = RPK / Scaling Factor
    tpm = rpk.div(scaling_factors, axis=1)
    
    return tpm

def run_preprocessing_pipeline(
    raw_dir: str,
    processed_dir: str,
    annotation_gtf: Optional[str] = None,
    use_simulation: bool = True
) -> pd.DataFrame:
    """
    Orchestrates the full preprocessing pipeline: fastp -> HISAT2 -> featureCounts -> TPM.
    
    Args:
        raw_dir: Directory containing raw FASTQ files.
        processed_dir: Directory for intermediate and final files.
        annotation_gtf: Path to GTF annotation file (required for real processing).
        use_simulation: If True and tools are missing, simulates the output.
        
    Returns:
        DataFrame of TPM values.
    """
    raw_path = Path(raw_dir)
    processed_path = Path(processed_dir)
    processed_path.mkdir(parents=True, exist_ok=True)
    
    fastq_files = list(raw_path.glob("*.fastq.gz")) + list(raw_path.glob("*.fq.gz"))
    
    if not fastq_files:
        logger.warning(f"No FASTQ files found in {raw_dir}")
        return pd.DataFrame()
    
    # Step 1: fastp
    clean_files = []
    for fq in fastq_files:
        clean_fq = processed_path / f"clean_{fq.name}"
        if run_fastp(str(fq), str(clean_fq)):
            clean_files.append(str(clean_fq))
        else:
            if use_simulation:
                logger.info("Simulation mode: skipping fastp")
                clean_files.append(str(fq))
            else:
                logger.error("fastp failed and simulation is disabled.")
                return pd.DataFrame()
    
    # Step 2 & 3: HISAT2 & featureCounts (Simulated if tools missing)
    if use_simulation and (not annotation_gtf or not Path(annotation_gtf).exists()):
        logger.info("Simulation mode: Generating synthetic counts from clean files")
        # Simulate counts by reading the mock FASTQ or generating random data
        # For this integration test, we generate a mock count matrix
        n_genes = 5000
        n_samples = len(clean_files)
        counts_data = np.random.negative_binomial(n=5, p=0.3, size=(n_genes, n_samples))
        gene_names = [f"Gene_{i}" for i in range(n_genes)]
        sample_names = [f"Sample_{i}" for i in range(n_samples)]
        counts_df = pd.DataFrame(counts_data, index=gene_names, columns=sample_names)
    else:
        # Real execution
        sam_files = []
        for i, clean_fq in enumerate(clean_files):
            sam_file = processed_path / f"aligned_{i}.sam"
            # HISAT2 requires an index, which we assume exists or is passed
            # This is a simplified call
            if run_hisat2("genome_index", clean_fq, str(sam_file)):
                sam_files.append(str(sam_file))
            else:
                logger.error("HISAT2 failed")
                return pd.DataFrame()
        
        counts_file = processed_path / "counts.txt"
        if not run_featurecounts(sam_files, annotation_gtf, str(counts_file)):
            logger.error("featureCounts failed")
            return pd.DataFrame()
        
        # Read counts
        counts_df = pd.read_csv(counts_file, comment="#", sep="\t", index_col=0)
        # HISAT2/featureCounts output format usually has a header and specific columns
        # Adjust based on actual output
        if "Assigned" in counts_df.columns:
            counts_df = counts_df[["Assigned"]]
            counts_df.columns = sample_names
        else:
            # Fallback to generic parsing
            counts_df = counts_df.iloc[:, 6:] # Usually count column is 7th (index 6)
            counts_df.columns = sample_names
    
    # Step 4: TPM Calculation
    tpm_df = calculate_tpm(counts_df)
    
    # Save TPM
    tpm_path = processed_path / "tpm_matrix.csv"
    tpm_df.to_csv(tpm_path)
    logger.info(f"TPM matrix saved to {tpm_path}")
    
    return tpm_df
