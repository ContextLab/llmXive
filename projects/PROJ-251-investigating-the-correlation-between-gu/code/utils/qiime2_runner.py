import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Optional

from utils.logging_config import get_logger
from utils.config import get_raw_path, get_processed_path, get_random_seed

logger = get_logger(__name__)

# Constants for QIIME2 execution
DOCKER_IMAGE = "qiime2/2023.7"
TRUNC_LEN = 240
CHIMERA_METHOD = "pooled"
RANDOM_SEED = 42

def run_dada2_denoising(
    forward_fastq_files: List[Path],
    reverse_fastq_files: Optional[List[Path]] = None,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Runs the DADA2 denoising pipeline using QIIME2 Docker container on raw FASTQ files.
    
    This implements Strategy B for T011c: processing raw FASTQ to generate an OTU table.
    
    Args:
        forward_fastq_files: List of paths to forward read FASTQ files (R1).
        reverse_fastq_files: Optional list of paths to reverse read FASTQ files (R2).
        output_dir: Directory to store QIIME2 artifacts. Defaults to data/processed.
    
    Returns:
        Path to the generated feature table artifact (feature-table.qza).
    
    Raises:
        RuntimeError: If the QIIME2 Docker container fails to execute.
        FileNotFoundError: If input FASTQ files do not exist.
    """
    if not forward_fastq_files:
        raise ValueError("At least one forward FASTQ file is required.")
    
    for f in forward_fastq_files:
        if not f.exists():
            raise FileNotFoundError(f"Forward FASTQ file not found: {f}")
    
    if reverse_fastq_files:
        for f in reverse_fastq_files:
            if not f.exists():
                raise FileNotFoundError(f"Reverse FASTQ file not found: {f}")

    if output_dir is None:
        output_dir = get_processed_path()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare output paths
    denoised_stats = output_dir / "denoising-stats.qza"
    feature_table = output_dir / "feature-table.qza"
    representative_seqs = output_dir / "representative-seqs.qza"
    chimera_removed_table = output_dir / "feature-table-chimera-removed.qza"
    
    # Build command arguments
    # We mount the local data directory to /data in the container
    raw_path = get_raw_path()
    mount_cmd = f"-v {raw_path}:/data/raw -v {output_dir}:/data/processed"
    
    # Determine if paired-end or single-end
    is_paired = reverse_fastq_files is not None and len(reverse_fastq_files) > 0
    
    # Construct the QIIME2 command
    # We use the 'qiime dada2 denoise-paired' or 'denoise-single' command
    # Since we are running raw FASTQ, we need to import them first or pass them directly
    # QIIME2 typically requires .qza imports first, but we can use the 'import' action
    # However, for a direct script, it's often easier to run the full pipeline in one go
    # if we have the raw files. But QIIME2 requires specific import formats.
    # Strategy: Import FASTQ -> Denoise -> Remove Chimeras -> Export to CSV
    
    # Step 1: Import FASTQ files
    logger.info(f"Importing FASTQ files from {raw_path}")
    
    # We will create a temporary manifest file for the import
    # This is a robust way to handle multiple files in QIIME2
    manifest_path = output_dir / "manifest.csv"
    
    if is_paired:
        # Paired end
        with open(manifest_path, 'w') as f:
            f.write("sample-id,forward-absolute-filepath,reverse-absolute-filepath\n")
            for i, (fwd, rev) in enumerate(zip(forward_fastq_files, reverse_fastq_files)):
                # We need to map the sample ID from the filename or use a counter
                # Assuming filenames contain sample IDs or we derive them
                sample_id = f"sample_{i:04d}"
                # Map to relative paths inside the container mount
                fwd_rel = f"/data/raw/{fwd.name}"
                rev_rel = f"/data/raw/{rev.name}"
                f.write(f"{sample_id},{fwd_rel},{rev_rel}\n")
        
        import_cmd = [
            "docker", "run", "--rm", "-it",
            mount_cmd,
            DOCKER_IMAGE,
            "qiime", "import",
            "--type", "SampleData[PairedEndSequencesWithQuality]",
            "--input-format", "PairedEndFastqManifestPhred33V2",
            "--input-path", "/data/processed/manifest.csv",
            "--output-path", "/data/processed/paired-end-demux.qza"
        ]
    else:
        # Single end
        with open(manifest_path, 'w') as f:
            f.write("sample-id,absolute-filepath\n")
            for i, fwd in enumerate(forward_fastq_files):
                sample_id = f"sample_{i:04d}"
                fwd_rel = f"/data/raw/{fwd.name}"
                f.write(f"{sample_id},{fwd_rel}\n")
        
        import_cmd = [
            "docker", "run", "--rm", "-it",
            mount_cmd,
            DOCKER_IMAGE,
            "qiime", "import",
            "--type", "SampleData[SequencesWithQuality]",
            "--input-format", "SingleEndFastqManifestPhred33V2",
            "--input-path", "/data/processed/manifest.csv",
            "--output-path", "/data/processed/single-end-demux.qza"
        ]
    
    logger.info("Running QIIME2 Import...")
    try:
        subprocess.run(import_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"QIIME2 Import failed: {e.stderr}")
        raise RuntimeError(f"Failed to import FASTQ files: {e.stderr}")

    # Step 2: Run DADA2 Denoising
    if is_paired:
        denoise_cmd = [
            "docker", "run", "--rm", "-it",
            mount_cmd,
            DOCKER_IMAGE,
            "qiime", "dada2", "denoise-paired",
            "--i-demultiplexed-seqs", "/data/processed/paired-end-demux.qza",
            "--p-trunc-len-f", str(TRUNC_LEN),
            "--p-trunc-len-r", str(TRUNC_LEN),
            "--p-chimera-method", CHIMERA_METHOD,
            "--p-n-threads", "4", # Use 4 threads for speed
            "--o-table", "/data/processed/feature-table-chimera-removed.qza",
            "--o-representative-sequences", "/data/processed/representative-seqs.qza",
            "--o-denoising-stats", "/data/processed/denoising-stats.qza"
        ]
    else:
        denoise_cmd = [
            "docker", "run", "--rm", "-it",
            mount_cmd,
            DOCKER_IMAGE,
            "qiime", "dada2", "denoise-single",
            "--i-demultiplexed-seqs", "/data/processed/single-end-demux.qza",
            "--p-trunc-len", str(TRUNC_LEN),
            "--p-chimera-method", CHIMERA_METHOD,
            "--p-n-threads", "4",
            "--o-table", "/data/processed/feature-table-chimera-removed.qza",
            "--o-representative-sequences", "/data/processed/representative-seqs.qza",
            "--o-denoising-stats", "/data/processed/denoising-stats.qza"
        ]
    
    logger.info(f"Running QIIME2 DADA2 (truncLen={TRUNC_LEN}, chimera={CHIMERA_METHOD})...")
    try:
        subprocess.run(denoise_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"QIIME2 DADA2 failed: {e.stderr}")
        raise RuntimeError(f"Failed to run DADA2 denoising: {e.stderr}")
    
    # Step 3: Export Feature Table to BIOM and then to CSV
    # QIIME2 feature tables are .qza (ZIP of HDF5/JSON). We need to export to BIOM first.
    export_table_cmd = [
        "docker", "run", "--rm", "-it",
        mount_cmd,
        DOCKER_IMAGE,
        "qiime", "tools", "export",
        "--input-path", "/data/processed/feature-table-chimera-removed.qza",
        "--output-path", "/data/processed/exported"
    ]
    
    logger.info("Exporting feature table to BIOM format...")
    try:
        subprocess.run(export_table_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"QIIME2 Export failed: {e.stderr}")
        raise RuntimeError(f"Failed to export feature table: {e.stderr}")
    
    # The export creates feature-table.biom
    biom_path = output_dir / "exported" / "feature-table.biom"
    if not biom_path.exists():
        raise FileNotFoundError(f"Exported BIOM file not found at {biom_path}")
    
    # Convert BIOM to TSV/CSV using biom-format python API
    # We assume biom-format is installed in the host environment or we run another docker
    # Since the project requirements include biom-format, we assume it's available on host
    # or we can use a simple docker command to convert if needed.
    # Let's use the host python environment to convert, as it's more robust for CSV generation
    # if the docker environment is isolated.
    
    # However, to keep it self-contained and avoid host dependency issues if biom isn't installed:
    # We can use `qiime tools export` again or `biom convert` if available.
    # The safest bet in a pipeline is to use `biom convert` if the tool is in path, 
    # or use the python library if available.
    
    csv_output_path = output_dir / "otutable_raw.csv"
    
    # Try using biom convert command if available
    try:
        convert_cmd = [
            "biom", "convert",
            "-i", str(biom_path),
            "-o", str(csv_output_path),
            "--to-tsv"
        ]
        subprocess.run(convert_cmd, check=True, capture_output=True, text=True)
        logger.info(f"Feature table exported to {csv_output_path}")
    except FileNotFoundError:
        logger.warning("biom command not found. Attempting to use Python biom library...")
        try:
            import biom
            table = biom.load_table(str(biom_path))
            df = table.to_dataframe()
            # Reset index to make sample_id a column
            df_reset = df.reset_index()
            df_reset.to_csv(csv_output_path, index=False)
            logger.info(f"Feature table exported to {csv_output_path} using Python biom library")
        except ImportError:
            raise RuntimeError(
                "Failed to export BIOM to CSV: 'biom' CLI not found and 'biom' Python library not installed. "
                "Please install biom-format package."
            )
    
    return csv_output_path

def run_strategy_b_qiime2(
    forward_fastq_files: List[Path],
    reverse_fastq_files: Optional[List[Path]] = None
) -> Path:
    """
    Orchestrates the full Strategy B pipeline for T011c.
    
    Args:
        forward_fastq_files: List of paths to forward FASTQ files.
        reverse_fastq_files: Optional list of paths to reverse FASTQ files.
    
    Returns:
        Path to the generated OTU table CSV.
    """
    logger.info("Starting QIIME2 DADA2 pipeline (Strategy B)...")
    otu_table_path = run_dada2_denoising(forward_fastq_files, reverse_fastq_files)
    logger.info(f"Strategy B complete. OTU table generated at: {otu_table_path}")
    return otu_table_path
