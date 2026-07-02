"""
Preprocessing module for plant disease resistance data.

Wraps external tools (fastp, bcftools) and implements MetaboAnalyst-compatible
normalization. Handles alignment of sample IDs across modalities and logs
exclusions as mandated by FR-001.
"""
import os
import subprocess
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
import yaml

from config import get_processed_data_path, get_data_path
from utils.logging import get_logger, log_sample_exclusion, log_pipeline_step
from utils.exceptions import EX_DATA_INTEGRITY
from data.manifest import load_manifest

logger = get_logger(__name__)

def run_fastp(input_fastq: Path, output_prefix: Path, threads: int = 4) -> bool:
    """
    Run fastp for quality control and adapter trimming.
    
    Args:
        input_fastq: Path to input FASTQ file.
        output_prefix: Prefix for output files (fastp adds extensions).
        threads: Number of threads to use.
        
    Returns:
        True if successful, False otherwise.
    """
    cmd = [
        "fastp",
        "-i", str(input_fastq),
        "-o", f"{output_prefix}_clean.fastq",
        "--json", f"{output_prefix}_fastp.json",
        "--html", f"{output_prefix}_fastp.html",
        "-j", str(threads),
        "--thread", str(threads)
    ]
    
    logger.info(f"Running fastp: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("fastp completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"fastp failed: {e.stderr}")
        return False

def run_bcftools_call(bam_file: Path, reference_fasta: Path, output_vcf: Path) -> bool:
    """
    Run bcftools for variant calling.
    
    Args:
        bam_file: Path to sorted BAM file.
        reference_fasta: Path to reference genome FASTA.
        output_vcf: Path to output VCF file.
        
    Returns:
        True if successful, False otherwise.
    """
    # Index reference if needed
    if not Path(f"{reference_fasta}.fai").exists():
        cmd_idx = ["samtools", "faidx", str(reference_fasta)]
        subprocess.run(cmd_idx, check=True)
    
    # Call variants
    cmd = [
        "bcftools", "mpileup",
        "-f", str(reference_fasta),
        "-Ou",
        str(bam_file),
        "|", "bcftools", "call",
        "-mv", "-Oz", "-o", str(output_vcf)
    ]
    
    # Build command without pipe for subprocess
    cmd_pileup = ["bcftools", "mpileup", "-f", str(reference_fasta), "-Ou", str(bam_file)]
    cmd_call = ["bcftools", "call", "-mv", "-Oz", "-o", str(output_vcf)]
    
    logger.info(f"Running bcftools mpileup and call")
    try:
        p1 = subprocess.Popen(cmd_pileup, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(cmd_call, stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p1.stdout.close()
        _, stderr = p2.communicate()
        
        if p2.returncode != 0:
            logger.error(f"bcftools failed: {stderr.decode()}")
            return False
        
        # Index VCF
        subprocess.run(["bcftools", "index", str(output_vcf)], check=True)
        logger.info("bcftools completed successfully")
        return True
    except Exception as e:
        logger.error(f"bcftools error: {str(e)}")
        return False

def normalize_metabolomics(dataframe: pd.DataFrame, method: str = "log2") -> pd.DataFrame:
    """
    Apply MetaboAnalyst-compatible normalization.
    
    Args:
        dataframe: Input DataFrame with samples as rows, features as columns.
        method: Normalization method ('log2', 'pareto', 'autoscale').
        
    Returns:
        Normalized DataFrame.
    """
    df = dataframe.copy()
    
    if method == "log2":
        # Add small constant to avoid log(0)
        df = np.log2(df + 1e-6)
    elif method == "pareto":
        # Pareto scaling: divide by square root of standard deviation
        std = df.std(axis=0)
        std[std == 0] = 1
        df = df / np.sqrt(std)
    elif method == "autoscale":
        # Z-score normalization
        mean = df.mean(axis=0)
        std = df.std(axis=0)
        std[std == 0] = 1
        df = (df - mean) / std
    
    return df

def align_modalities(
    snp_data: pd.DataFrame,
    metabolite_data: pd.DataFrame,
    snp_id_col: str = "sample_id",
    metabolite_id_col: str = "sample_id",
    exclusion_log_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict[str, Any]]]:
    """
    Align sample IDs across SNP and metabolite modalities.
    
    Performs exact string matching on sample IDs. Drops samples that do not
    appear in both modalities and logs exclusions.
    
    Args:
        snp_data: DataFrame with SNP data.
        metabolite_data: DataFrame with metabolite data.
        snp_id_col: Column name for sample IDs in SNP data.
        metabolite_id_col: Column name for sample IDs in metabolite data.
        exclusion_log_path: Path to write exclusion log CSV.
        
    Returns:
        Tuple of (aligned_snp_data, aligned_metabolite_data, exclusion_records)
    """
    # Ensure ID columns exist
    if snp_id_col not in snp_data.columns:
        raise EX_DATA_INTEGRITY(f"SNP data missing ID column: {snp_id_col}")
    if metabolite_id_col not in metabolite_data.columns:
        raise EX_DATA_INTEGRITY(f"Metabolite data missing ID column: {metabolite_id_col}")
    
    # Get unique IDs from each modality
    snp_ids = set(snp_data[snp_id_col].astype(str))
    metabolite_ids = set(metabolite_data[metabolite_id_col].astype(str))
    
    # Find matching IDs
    matching_ids = snp_ids.intersection(metabolite_ids)
    missing_in_snp = metabolite_ids - snp_ids
    missing_in_metabolite = snp_ids - metabolite_ids
    
    exclusion_records = []
    timestamp = datetime.now().isoformat()
    
    # Log exclusions for missing in SNP (present in metabolite only)
    for sample_id in missing_in_snp:
        record = {
            "sample_id": sample_id,
            "missing_modality": "snp",
            "timestamp": timestamp
        }
        exclusion_records.append(record)
        log_sample_exclusion(
            sample_id=sample_id,
            reason="missing_in_snp",
            modality="snp"
        )
    
    # Log exclusions for missing in metabolite (present in SNP only)
    for sample_id in missing_in_metabolite:
        record = {
            "sample_id": sample_id,
            "missing_modality": "metabolite",
            "timestamp": timestamp
        }
        exclusion_records.append(record)
        log_sample_exclusion(
            sample_id=sample_id,
            reason="missing_in_metabolite",
            modality="metabolite"
        )
    
    # Filter data to matching IDs
    aligned_snp = snp_data[snp_data[snp_id_col].astype(str).isin(matching_ids)].copy()
    aligned_metabolite = metabolite_data[metabolite_data[metabolite_id_col].astype(str).isin(matching_ids)].copy()
    
    # Sort by sample_id for consistency
    aligned_snp = aligned_snp.sort_values(by=snp_id_col).reset_index(drop=True)
    aligned_metabolite = aligned_metabolite.sort_values(by=metabolite_id_col).reset_index(drop=True)
    
    # Write exclusion log if path provided
    if exclusion_log_path and exclusion_records:
        exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
        exclusion_df = pd.DataFrame(exclusion_records)
        exclusion_df.to_csv(exclusion_log_path, index=False)
        logger.info(f"Written exclusion log to {exclusion_log_path} with {len(exclusion_records)} entries")
    
    logger.info(f"Aligned {len(matching_ids)} samples across modalities. "
               f"Dropped {len(missing_in_snp)} samples missing in SNP, "
               f"{len(missing_in_metabolite)} samples missing in metabolite.")
    
    return aligned_snp, aligned_metabolite, exclusion_records

def process_pipeline(
    manifest_path: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline.
    
    Args:
        manifest_path: Path to data manifest YAML.
        output_dir: Directory for processed outputs.
        
    Returns:
        Dictionary with pipeline results and paths.
    """
    if manifest_path is None:
        manifest_path = get_data_path() / "data_manifest.yaml"
    
    if output_dir is None:
        output_dir = get_processed_data_path()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_pipeline_step(step="preprocess_start", details={"manifest": str(manifest_path)})
    
    # Load manifest
    manifest = load_manifest(manifest_path)
    
    # Initialize results
    results = {
        "aligned_samples": 0,
        "excluded_samples": 0,
        "snp_output": None,
        "metabolite_output": None,
        "exclusion_log": None
    }
    
    # Check if we have data to process
    datasets = manifest.get("datasets", [])
    if not datasets:
        logger.warning("No datasets found in manifest")
        return results
    
    # Identify SNP and metabolite datasets
    snp_dataset = None
    metabolite_dataset = None
    
    for ds in datasets:
        modality = ds.get("modality", "")
        if modality == "snp":
            snp_dataset = ds
        elif modality == "metabolite":
            metabolite_dataset = ds
    
    # Load data files
    snp_data = None
    metabolite_data = None
    
    if snp_dataset:
        snp_path = get_data_path() / snp_dataset.get("file", "")
        if snp_path.exists():
            snp_data = pd.read_csv(snp_path)
            logger.info(f"Loaded SNP data from {snp_path}")
        else:
            logger.warning(f"SNP data file not found: {snp_path}")
    
    if metabolite_dataset:
        metabo_path = get_data_path() / metabolite_dataset.get("file", "")
        if metabo_path.exists():
            metabolite_data = pd.read_csv(meto_path)
            logger.info(f"Loaded metabolite data from {metabo_path}")
        else:
            logger.warning(f"Metabolite data file not found: {metabo_path}")
    
    if snp_data is None or metabolite_data is None:
        logger.error("Missing required data files for alignment")
        raise EX_DATA_INTEGRITY("Cannot preprocess: missing SNP or metabolite data files")
    
    # Align modalities
    exclusion_log_path = output_dir / "exclusion_log.csv"
    aligned_snp, aligned_metabolite, exclusions = align_modalities(
        snp_data=snp_data,
        metabolite_data=metabolite_data,
        exclusion_log_path=exclusion_log_path
    )
    
    # Normalize metabolite data (MetaboAnalyst style)
    # Assume first column is sample_id, rest are features
    sample_col = "sample_id"
    feature_cols = [c for c in aligned_metabolite.columns if c != sample_col]
    
    if feature_cols:
        normalized_metabolite = aligned_metabolite.copy()
        normalized_metabolite[feature_cols] = normalize_metabolomics(
            aligned_metabolite[feature_cols],
            method="log2"
        )
    else:
        normalized_metabolite = aligned_metabolite
    
    # Save outputs
    snp_output_path = output_dir / "snp_aligned.csv"
    metabo_output_path = output_dir / "metabolite_normalized.csv"
    
    aligned_snp.to_csv(snp_output_path, index=False)
    normalized_metabolite.to_csv(meto_output_path, index=False)
    
    results["aligned_samples"] = len(aligned_snp)
    results["excluded_samples"] = len(exclusions)
    results["snp_output"] = str(snp_output_path)
    results["metabolite_output"] = str(meto_output_path)
    results["exclusion_log"] = str(exclusion_log_path) if exclusions else None
    
    log_pipeline_step(
        step="preprocess_complete",
        details={
            "aligned": results["aligned_samples"],
            "excluded": results["excluded_samples"],
            "snp_file": str(snp_output_path),
            "metabo_file": str(meto_output_path)
        }
    )
    
    return results

def main():
    """Entry point for preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline")
    
    try:
        results = process_pipeline()
        logger.info(f"Pipeline completed: {results['aligned_samples']} samples aligned")
        
        if results["excluded_samples"] > 0:
            logger.warning(f"{results['excluded_samples']} samples excluded due to missing modalities")
            
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()