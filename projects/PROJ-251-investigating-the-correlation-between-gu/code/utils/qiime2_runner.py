"""
QIIME2 Runner Module

Provides utilities for running QIIME2 pipelines, specifically DADA2 denoising
for 16S rRNA amplicon data processing.

This module handles:
- Importing raw FASTQ data into QIIME2 format
- Running DADA2 denoising with configurable parameters
- Exporting results from QIIME2 artifacts
"""
import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from utils.logging_config import get_logger, log_error_context
from utils.sra_downloader import DataUnavailableError

logger = get_logger(__name__)

def run_dada2_denoising(
    fastq_files: List[Path],
    output_dir: Path,
    trunc_len: int = 240,
    chimera_method: str = "pooled",
    random_seed: int = 42
) -> Tuple[Path, Path]:
    """
    Run DADA2 denoising on paired-end or single-end FASTQ files.
    
    This function assumes the input files are already demultiplexed or
    handles single-end data. For paired-end data, files should be provided
    in order (R1, R2, R1, R2, ...).
    
    Args:
        fastq_files: List of paths to FASTQ files (single-end or interleaved paired)
        output_dir: Directory to write QIIME2 artifacts
        trunc_len: Truncation length for reads (default 240)
        chimera_method: Chimeric sequence removal method ("pooled", "per_sample", "none")
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (feature_table_path, representative_sequences_path)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine if we have paired-end data (even number of files)
    is_paired = len(fastq_files) > 1 and len(fastq_files) % 2 == 0
    
    if is_paired:
        logger.info(f"Processing {len(fastq_files)//2} paired-end samples")
        return _run_dada2_paired(fastq_files, output_dir, trunc_len, chimera_method, random_seed)
    else:
        logger.info(f"Processing {len(fastq_files)} single-end samples")
        return _run_dada2_single(fastq_files, output_dir, trunc_len, chimera_method, random_seed)

def _run_dada2_single(
    fastq_files: List[Path],
    output_dir: Path,
    trunc_len: int,
    chimera_method: str,
    random_seed: int
) -> Tuple[Path, Path]:
    """Run DADA2 on single-end data."""
    # Create manifest file for single-end data
    manifest_path = output_dir / "single-end-manifest.tsv"
    with open(manifest_path, 'w') as f:
        f.write("sample-id,absolute-filepath,direction\n")
        for i, fq in enumerate(fastq_files):
            sample_id = f"sample_{i}"
            f.write(f"{sample_id},{fq.absolute()},forward\n")
    
    logger.info(f"Created manifest: {manifest_path}")
    
    # Import single-end data
    import_cmd = [
        "qiime", "import",
        "--type", "SampleData[SequencesWithQuality]",
        "--input-format", "CasavaOneEightSingleLanePerSampleDirFmt",
        "--input-path", str(output_dir),
        "--output-path", str(output_dir / "demux.qza"),
        "--m-manifest-file", str(manifest_path)
    ]
    
    # Actually, let's use a simpler approach with direct file import
    # First, organize files into a Casava-like structure
    casava_dir = output_dir / "casava_import"
    casava_dir.mkdir(exist_ok=True)
    
    for i, fq in enumerate(fastq_files):
        sample_id = f"sample_{i}"
        sample_dir = casava_dir / sample_id
        sample_dir.mkdir(exist_ok=True)
        # Copy or symlink the file
        import shutil
        dest = sample_dir / f"{sample_id}_L001_R1_001.fastq.gz"
        if fq.exists():
            shutil.copy(fq, dest)
        else:
            raise DataUnavailableError(f"FASTQ file not found: {fq}")
    
    import_cmd = [
        "qiime", "import",
        "--type", "SampleData[SequencesWithQuality]",
        "--input-format", "CasavaOneEightSingleLanePerSampleDirFmt",
        "--input-path", str(casava_dir),
        "--output-path", str(output_dir / "demux.qza")
    ]
    
    logger.info(f"Running import command: {' '.join(import_cmd)}")
    try:
        result = subprocess.run(import_cmd, capture_output=True, text=True, check=True)
        logger.debug(f"Import stdout: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Import failed: {e.stderr}")
        log_error_context("qiime2_import_failure", str(e.stderr))
        raise
    
    # Run DADA2 denoise-single
    denoise_cmd = [
        "qiime", "dada2", "denoise-single",
        "--i-demultiplexed-seqs", str(output_dir / "demux.qza"),
        "--p-trunc-len", str(trunc_len),
        "--p-chimera-method", chimera_method,
        "--p-n-threads", "4",
        "--o-table", str(output_dir / "table.qza"),
        "--o-representative-sequences", str(output_dir / "rep-seqs.qza"),
        "--o-denoising-stats", str(output_dir / "stats.qza")
    ]
    
    logger.info(f"Running DADA2 denoise-single: {' '.join(denoise_cmd)}")
    try:
        result = subprocess.run(denoise_cmd, capture_output=True, text=True, check=True)
        logger.debug(f"DADA2 stdout: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"DADA2 denoise-single failed: {e.stderr}")
        log_error_context("dada2_denoise_failure", str(e.stderr))
        raise
    
    return output_dir / "table.qza", output_dir / "rep-seqs.qza"

def _run_dada2_paired(
    fastq_files: List[Path],
    output_dir: Path,
    trunc_len: int,
    chimera_method: str,
    random_seed: int
) -> Tuple[Path, Path]:
    """Run DADA2 on paired-end data."""
    # Organize into Casava structure for paired-end
    casava_dir = output_dir / "casava_import_pe"
    casava_dir.mkdir(exist_ok=True)
    
    num_samples = len(fastq_files) // 2
    for i in range(num_samples):
        sample_id = f"sample_{i}"
        sample_dir = casava_dir / sample_id
        sample_dir.mkdir(exist_ok=True)
        
        r1_path = fastq_files[i * 2]
        r2_path = fastq_files[i * 2 + 1]
        
        dest_r1 = sample_dir / f"{sample_id}_L001_R1_001.fastq.gz"
        dest_r2 = sample_dir / f"{sample_id}_L001_R2_001.fastq.gz"
        
        import shutil
        if r1_path.exists():
            shutil.copy(r1_path, dest_r1)
        else:
            raise DataUnavailableError(f"R1 FASTQ file not found: {r1_path}")
            
        if r2_path.exists():
            shutil.copy(r2_path, dest_r2)
        else:
            raise DataUnavailableError(f"R2 FASTQ file not found: {r2_path}")
    
    # Import paired-end data
    import_cmd = [
        "qiime", "import",
        "--type", "SampleData[PairedEndSequencesWithQuality]",
        "--input-format", "CasavaOneEightSingleLanePerSampleDirFmt",
        "--input-path", str(casava_dir),
        "--output-path", str(output_dir / "demux-paired.qza")
    ]
    
    logger.info(f"Running import command: {' '.join(import_cmd)}")
    try:
        result = subprocess.run(import_cmd, capture_output=True, text=True, check=True)
        logger.debug(f"Import stdout: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Import failed: {e.stderr}")
        log_error_context("qiime2_import_failure", str(e.stderr))
        raise
    
    # Run DADA2 denoise-paired
    denoise_cmd = [
        "qiime", "dada2", "denoise-paired",
        "--i-demultiplexed-seqs", str(output_dir / "demux-paired.qza"),
        "--p-trunc-len", str(trunc_len),
        "--p-trunc-len-r", str(trunc_len),
        "--p-chimera-method", chimera_method,
        "--p-n-threads", "4",
        "--o-table", str(output_dir / "table.qza"),
        "--o-representative-sequences", str(output_dir / "rep-seqs.qza"),
        "--o-denoising-stats", str(output_dir / "stats.qza")
    ]
    
    logger.info(f"Running DADA2 denoise-paired: {' '.join(denoise_cmd)}")
    try:
        result = subprocess.run(denoise_cmd, capture_output=True, text=True, check=True)
        logger.debug(f"DADA2 stdout: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"DADA2 denoise-paired failed: {e.stderr}")
        log_error_context("dada2_denoise_failure", str(e.stderr))
        raise
    
    return output_dir / "table.qza", output_dir / "rep-seqs.qza"

def run_strategy_b_qiime2(
    fastq_files: List[Path],
    output_dir: Path,
    trunc_len: int = 240,
    chimera_method: str = "pooled",
    random_seed: int = 42
) -> Tuple[Path, Path]:
    """
    Main entry point for running the Strategy B QIIME2 pipeline.
    
    This is a wrapper that ensures proper error handling and logging
    for the full DADA2 workflow.
    
    Args:
        fastq_files: List of FASTQ file paths
        output_dir: Output directory for QIIME2 artifacts
        trunc_len: Truncation length
        chimera_method: Chimeric sequence removal method
        random_seed: Random seed
        
    Returns:
        Tuple of (feature_table.qza, rep-seqs.qza) paths
    """
    logger.info(f"Starting QIIME2 DADA2 pipeline with {len(fastq_files)} files")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Parameters: trunc_len={trunc_len}, chimera_method={chimera_method}")
    
    try:
        feature_table, rep_seqs = run_dada2_denoising(
            fastq_files, output_dir, trunc_len, chimera_method, random_seed
        )
        logger.info("DADA2 pipeline completed successfully")
        return feature_table, rep_seqs
    except Exception as e:
        logger.error(f"QIIME2 pipeline failed: {e}")
        log_error_context("qiime2_pipeline_failure", str(e))
        raise
