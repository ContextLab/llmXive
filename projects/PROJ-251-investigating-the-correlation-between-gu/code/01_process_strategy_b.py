"""
Strategy B: Run 16S processing pipeline on raw FASTQ to generate the OTU table.

This module implements the DADA2 pipeline using QIIME2 to process raw FASTQ files
downloaded in T011b. It handles:
1. Discovery of downloaded FASTQ files
2. Execution of the DADA2 denoising pipeline via QIIME2
3. Export of the resulting feature table to CSV

Output: data/raw/otutable_raw.csv
"""
import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

# Import project utilities
from utils.config import get_raw_path, get_processed_path, get_random_seed, ensure_directories
from utils.logging_config import get_logger, log_error_context
from utils.qiime2_runner import run_dada2_denoising, run_strategy_b_qiime2
from utils.sra_downloader import DataUnavailableError

# Setup logging
logger = get_logger(__name__)

# Configuration constants
TRUNC_LEN = 240
CHIMERA_METHOD = "pooled"
RANDOM_SEED = get_random_seed()

def find_fastq_files(raw_dir: Path) -> List[Path]:
    """
    Locate all downloaded FASTQ files in the raw directory.
    
    Args:
        raw_dir: Path to the data/raw directory
        
    Returns:
        List of Path objects for .fastq.gz files
        
    Raises:
        DataUnavailableError: If no FASTQ files are found
    """
    if not raw_dir.exists():
        raise DataUnavailableError(f"Raw directory does not exist: {raw_dir}")
        
    fastq_files = sorted(raw_dir.glob("*.fastq.gz"))
    
    if not fastq_files:
        raise DataUnavailableError(
            f"No FASTQ files found in {raw_dir}. "
            "Ensure T011b (download) has completed successfully."
        )
        
    logger.info(f"Found {len(fastq_files)} FASTQ files in {raw_dir}")
    for f in fastq_files:
        logger.debug(f"  - {f.name}")
        
    return fastq_files

def run_dada2_pipeline(fastq_files: List[Path], output_dir: Path) -> Tuple[Path, Path]:
    """
    Run the DADA2 pipeline on the provided FASTQ files.
    
    This function orchestrates the QIIME2 DADA2 denoising process:
    1. Imports raw FASTQ data into QIIME2 artifact format
    2. Runs DADA2 denoising with specified parameters
    3. Exports the feature table and representative sequences
    
    Args:
        fastq_files: List of paths to raw FASTQ files
        output_dir: Directory to write intermediate and final results
        
    Returns:
        Tuple of (feature_table_path, sequences_path)
        
    Raises:
        subprocess.CalledProcessError: If QIIME2 or DADA2 fails
        DataUnavailableError: If required tools are missing
    """
    ensure_directories()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting DADA2 pipeline with {len(fastq_files)} files")
    logger.info(f"Parameters: truncLen={TRUNC_LEN}, chimeraMethod={CHIMERA_METHOD}")
    
    # Check for QIIME2 environment
    try:
        qiime2_check = subprocess.run(
            ["qiime", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if qiime2_check.returncode != 0:
            raise DataUnavailableError(
                "QIIME2 is not available in the environment. "
                "Please install QIIME2 or activate the conda environment."
            )
        logger.info(f"QIIME2 available: {qiime2_check.stdout.strip()}")
    except FileNotFoundError:
        raise DataUnavailableError(
            "QIIME2 command not found. Ensure QIIME2 is installed and in PATH."
        )
    
    # Run the full pipeline using the helper
    try:
        feature_table_path, sequences_path = run_strategy_b_qiime2(
            fastq_files=fastq_files,
            output_dir=output_dir,
            trunc_len=TRUNC_LEN,
            chimera_method=CHIMERA_METHOD,
            random_seed=RANDOM_SEED
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"DADA2 pipeline failed: {e}")
        log_error_context("dada2_pipeline_failure", str(e))
        raise
    
    logger.info(f"DADA2 pipeline completed successfully")
    logger.info(f"Feature table: {feature_table_path}")
    logger.info(f"Sequences: {sequences_path}")
    
    return feature_table_path, sequences_path

def export_otu_table_to_csv(feature_table_path: Path, output_csv_path: Path) -> None:
    """
    Export the QIIME2 feature table to a CSV file.
    
    The output CSV will have:
    - Rows: Samples
    - Columns: Taxa (feature IDs)
    - Values: Counts
    - Plus a 'subject_id' column if derivable from sample names
    
    Args:
        feature_table_path: Path to the QIIME2 feature table artifact
        output_csv_path: Path where the CSV will be written
    """
    logger.info(f"Exporting feature table to CSV: {output_csv_path}")
    
    # Use QIIME2 to export the table
    export_dir = output_csv_path.parent / "qiime2_export"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    export_cmd = [
        "qiime", "features", "table", "export",
        "--i-data", str(feature_table_path),
        "--o-exported-data", str(export_dir)
    ]
    
    try:
        result = subprocess.run(
            export_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        logger.debug(f"Export command stdout: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to export feature table: {e.stderr}")
        log_error_context("table_export_failure", str(e.stderr))
        raise
    
    # Find the exported BIOM file
    biom_file = export_dir / "feature-table.biom"
    if not biom_file.exists():
        raise RuntimeError(f"BIOM file not found after export: {biom_file}")
    
    # Convert BIOM to CSV using biom-format
    try:
        import biom
        from biom.util import biom_open
        import pandas as pd
        
        with biom_open(biom_file) as biom_fp:
            table = biom.load_table(biom_fp)
            
            # Convert to pandas DataFrame
            df = table.to_dataframe()
            
            # Transpose so rows are samples, columns are features
            df = df.T
            
            # Reset index to get sample_id as a column
            df = df.reset_index()
            df = df.rename(columns={'index': 'sample_id'})
            
            # Attempt to extract subject_id from sample_id
            # Assuming sample_id format like "SRR123456_subjectA" or similar
            # If not, we'll just keep sample_id
            if 'sample_id' in df.columns:
                df['subject_id'] = df['sample_id'].apply(
                    lambda x: x.split('_')[-1] if '_' in x else x
                )
                # Reorder columns to put subject_id first
                cols = ['subject_id'] + [c for c in df.columns if c != 'subject_id']
                df = df[cols]
            
            # Write to CSV
            df.to_csv(output_csv_path, index=False)
            logger.info(f"Wrote {len(df)} samples to {output_csv_path}")
            
    except ImportError:
        # Fallback: use biom command line tool
        logger.warning("Python biom package not available, using CLI")
        csv_temp = output_csv_path.with_suffix('.tsv')
        biom_convert_cmd = [
            "biom", "convert",
            "-i", str(biom_file),
            "-o", str(csv_temp),
            "--to-tsv"
        ]
        try:
            subprocess.run(biom_convert_cmd, check=True)
            # Convert TSV to CSV
            df = pd.read_csv(csv_temp, sep='\t', index_col=0)
            df.to_csv(output_csv_path)
            csv_temp.unlink()
            logger.info(f"Converted BIOM to CSV using CLI: {output_csv_path}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"BIOM conversion failed: {e}")

def main() -> None:
    """
    Main entry point for the Strategy B 16S processing pipeline.
    
    Workflow:
    1. Find FASTQ files in data/raw
    2. Run DADA2 pipeline via QIIME2
    3. Export feature table to CSV
    4. Write to data/raw/otutable_raw.csv
    """
    logger.info("=" * 60)
    logger.info("Starting Strategy B: 16S Processing Pipeline (T011c)")
    logger.info("=" * 60)
    
    try:
        # Get paths
        raw_dir = get_raw_path()
        output_csv_path = raw_dir / "otutable_raw.csv"
        output_dir = raw_dir / "qiime2_output"
        
        # Step 1: Find FASTQ files
        logger.info("Step 1: Locating FASTQ files...")
        fastq_files = find_fastq_files(raw_dir)
        
        # Step 2: Run DADA2 pipeline
        logger.info("Step 2: Running DADA2 pipeline...")
        feature_table_path, sequences_path = run_dada2_pipeline(
            fastq_files, output_dir
        )
        
        # Step 3: Export to CSV
        logger.info("Step 3: Exporting OTU table to CSV...")
        export_otu_table_to_csv(feature_table_path, output_csv_path)
        
        logger.info("=" * 60)
        logger.info("Strategy B Pipeline Completed Successfully")
        logger.info(f"Output: {output_csv_path}")
        logger.info("=" * 60)
        
    except DataUnavailableError as e:
        logger.error(f"Data unavailable: {e}")
        log_error_context("data_unavailable", str(e))
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Pipeline execution failed: {e}")
        log_error_context("pipeline_execution_failure", str(e))
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        log_error_context("unexpected_error", str(e))
        raise

if __name__ == "__main__":
    main()
