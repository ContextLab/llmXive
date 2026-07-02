"""
Preprocessing module for plant disease resistance data.

Wrappers for fastp (QC), bcftools (variant calling), and MetaboAnalyst-compatible
normalization. Handles alignment of sample IDs across modalities.
"""
import os
import subprocess
import sys
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

from config import get_path
from utils.logging import get_logger, log_pipeline_step, log_sample_exclusion, setup_exclusion_logger

logger = get_logger(__name__)
exclusion_logger = setup_exclusion_logger()

def run_fastp(input_file: Path, output_file: Path, log_file: Path) -> bool:
    """
    Wrapper for fastp to perform quality control on FASTQ files.
    
    Args:
        input_file: Path to input FASTQ file
        output_file: Path to output FASTQ file
        log_file: Path to fastp log file
        
    Returns:
        bool: True if successful, False otherwise
    """
    cmd = [
        "fastp",
        "-i", str(input_file),
        "-o", str(output_file),
        "--json", str(log_file),
        "--html", str(log_file.with_suffix('.html'))
    ]
    
    try:
        logger.info(f"Running fastp on {input_file}")
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"fastp completed successfully for {input_file}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"fastp failed for {input_file}: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("fastp executable not found. Please install fastp.")
        return False

def run_bcftools_call(bcf_file: Path, output_vcf: Path) -> bool:
    """
    Wrapper for bcftools call to perform variant calling.
    
    Args:
        bcf_file: Path to input BCF file
        output_vcf: Path to output VCF file
        
    Returns:
        bool: True if successful, False otherwise
    """
    cmd = [
        "bcftools", "call",
        "-mv",
        "-Oz",
        "-o", str(output_vcf),
        str(bcf_file)
    ]
    
    try:
        logger.info(f"Running bcftools call on {bcf_file}")
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"bcftools call completed successfully for {bcf_file}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"bcftools call failed for {bcf_file}: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("bcftools executable not found. Please install bcftools.")
        return False

def normalize_metabolomics(data: pd.DataFrame, method: str = "pareto") -> pd.DataFrame:
    """
    Apply MetaboAnalyst-compatible normalization to metabolomics data.
    
    Args:
        data: DataFrame with metabolite features (columns) and samples (rows)
        method: Normalization method ('pareto', 'log', 'autoscale', 'max')
        
    Returns:
        Normalized DataFrame
    """
    if method not in ["pareto", "log", "autoscale", "max"]:
        raise ValueError(f"Unknown normalization method: {method}")
    
    # Ensure numeric columns only
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        logger.warning("No numeric columns found for normalization")
        return data
    
    normalized = data.copy()
    
    if method == "pareto":
        # Pareto scaling: divide by square root of standard deviation
        std_vals = normalized[numeric_cols].std(axis=0)
        std_vals[std_vals == 0] = 1  # Avoid division by zero
        normalized[numeric_cols] = normalized[numeric_cols] / np.sqrt(std_vals)
        
    elif method == "log":
        # Log transformation (log2(x + 1) to handle zeros)
        normalized[numeric_cols] = np.log2(normalized[numeric_cols] + 1)
        
    elif method == "autoscale":
        # Autoscaling: mean center and divide by standard deviation
        means = normalized[numeric_cols].mean(axis=0)
        std_vals = normalized[numeric_cols].std(axis=0)
        std_vals[std_vals == 0] = 1
        normalized[numeric_cols] = (normalized[numeric_cols] - means) / std_vals
        
    elif method == "max":
        # Max normalization: divide by maximum value
        max_vals = normalized[numeric_cols].max(axis=0)
        max_vals[max_vals == 0] = 1
        normalized[numeric_cols] = normalized[numeric_cols] / max_vals
    
    return normalized

def align_sample_ids(
    snp_data: pd.DataFrame,
    metabo_data: pd.DataFrame,
    snp_id_col: str = "sample_id",
    metabo_id_col: str = "sample_id",
    output_dir: Path = None
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict[str, Any]]]:
    """
    Align sample IDs across SNP and metabolomics modalities using exact string match.
    Drop samples that don't match in both modalities and log exclusions.
    
    Args:
        snp_data: DataFrame with SNP data
        metabo_data: DataFrame with metabolomics data
        snp_id_col: Column name for sample IDs in SNP data
        metabo_id_col: Column name for sample IDs in metabolomics data
        output_dir: Directory to write exclusion log
        
    Returns:
        Tuple of (aligned_snp_data, aligned_metabo_data, exclusion_log)
    """
    if output_dir is None:
        output_dir = get_path("data_processed")
    
    # Ensure ID columns exist
    if snp_id_col not in snp_data.columns:
        raise ValueError(f"SNP ID column '{snp_id_col}' not found in SNP data")
    if metabo_id_col not in metabo_data.columns:
        raise ValueError(f"Metabolite ID column '{metabo_id_col}' not found in metabolomics data")
    
    # Convert to string for exact matching
    snp_ids = set(snp_data[snp_id_col].astype(str))
    metabo_ids = set(metabo_data[metabo_id_col].astype(str))
    
    # Find matching IDs
    common_ids = snp_ids & metabo_ids
    missing_in_snp = metabo_ids - snp_ids
    missing_in_metabo = snp_ids - metabo_ids
    
    exclusion_log = []
    timestamp = datetime.now().isoformat()
    
    # Log exclusions
    for sample_id in missing_in_snp:
        exclusion_entry = {
            "sample_id": sample_id,
            "missing_modality": "SNP",
            "timestamp": timestamp
        }
        exclusion_log.append(exclusion_entry)
        log_sample_exclusion(
            sample_id=sample_id,
            reason="Missing in SNP modality",
            missing_modality="SNP"
        )
        
    for sample_id in missing_in_metabo:
        exclusion_entry = {
            "sample_id": sample_id,
            "missing_modality": "Metabolomics",
            "timestamp": timestamp
        }
        exclusion_log.append(exclusion_entry)
        log_sample_exclusion(
            sample_id=sample_id,
            reason="Missing in Metabolomics modality",
            missing_modality="Metabolomics"
        )
    
    # Log summary
    logger.info(f"Alignment: {len(common_ids)} matching samples, "
               f"{len(missing_in_snp)} missing in SNP, "
               f"{len(missing_in_metabo)} missing in Metabolomics")
    
    # Filter data to common IDs
    aligned_snp = snp_data[snp_data[snp_id_col].astype(str).isin(common_ids)].reset_index(drop=True)
    aligned_metabo = metabo_data[metabo_data[metabo_id_col].astype(str).isin(common_ids)].reset_index(drop=True)
    
    # Write exclusion log
    if exclusion_log:
        exclusion_log_path = output_dir / "exclusion_log.csv"
        with open(exclusion_log_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["sample_id", "missing_modality", "timestamp"])
            writer.writeheader()
            writer.writerows(exclusion_log)
        logger.info(f"Wrote exclusion log to {exclusion_log_path}")
    
    return aligned_snp, aligned_metabo, exclusion_log

def preprocess_snps(
    input_vcf: Path,
    output_csv: Path,
    sample_id_col: str = "sample_id"
) -> pd.DataFrame:
    """
    Process SNP data from VCF to a feature table.
    
    Args:
        input_vcf: Path to input VCF file
        output_csv: Path to output CSV file
        sample_id_col: Name for the sample ID column
        
    Returns:
        DataFrame with SNP features
    """
    if not input_vcf.exists():
        raise FileNotFoundError(f"Input VCF file not found: {input_vcf}")
    
    # Check if bcftools is available and convert VCF to TSV
    try:
        # Use bcftools to convert VCF to a more manageable format
        temp_tsv = input_vcf.with_suffix('.tsv')
        cmd = [
            "bcftools", "query",
            "-f", "%CHROM\t%POS\t%REF\t%ALT[\t%GT]\n",
            str(input_vcf)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Parse the TSV output
        # This is a simplified parser; in production, use a proper VCF parser
        snp_data = []
        with open(temp_tsv, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 4:
                    chrom, pos, ref, alt = parts[:4]
                    genotypes = parts[4:]
                    snp_data.append({
                        "sample_id": sample_id_col,  # Placeholder - actual sample IDs would come from VCF header
                        "chrom": chrom,
                        "pos": pos,
                        "ref": ref,
                        "alt": alt,
                        "genotypes": genotypes
                    })
        
        # In a real implementation, we would properly extract sample IDs from VCF header
        # and create a proper feature matrix
        logger.warning("Simplified VCF parsing used. Full implementation requires proper VCF parsing.")
        
    except FileNotFoundError:
        logger.error("bcftools not found. Cannot process VCF.")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"bcftools query failed: {e.stderr}")
        raise
    
    # For now, return an empty DataFrame - real implementation would parse properly
    df = pd.DataFrame()
    df.to_csv(output_csv, index=False)
    return df

def preprocess_metabolomics(
    input_csv: Path,
    output_csv: Path,
    normalization_method: str = "pareto",
    sample_id_col: str = "sample_id"
) -> pd.DataFrame:
    """
    Process metabolomics data with normalization.
    
    Args:
        input_csv: Path to input CSV file
        output_csv: Path to output CSV file
        normalization_method: Method for normalization
        sample_id_col: Name for the sample ID column
        
    Returns:
        Normalized DataFrame
    """
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV file not found: {input_csv}")
    
    # Load data
    data = pd.read_csv(input_csv)
    
    # Apply normalization
    normalized_data = normalize_metabolomics(data, method=normalization_method)
    
    # Save
    normalized_data.to_csv(output_csv, index=False)
    logger.info(f"Normalized metabolomics data saved to {output_csv}")
    
    return normalized_data

def main():
    """
    Main function to run the preprocessing pipeline.
    
    This function demonstrates the preprocessing workflow:
    1. Load raw data (SNP and Metabolomics)
    2. Align sample IDs across modalities
    3. Normalize metabolomics data
    4. Save aligned datasets
    """
    log_pipeline_step("preprocess_start", {"message": "Starting preprocessing pipeline"})
    
    # Get paths
    data_dir = get_path("data_raw")
    output_dir = get_path("data_processed")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Example: Load synthetic data for demonstration
    # In real usage, this would load from downloaded files
    try:
        # Load SNP data (if exists)
        snp_path = data_dir / "snps.csv"
        if snp_path.exists():
            snp_data = pd.read_csv(snp_path)
            logger.info(f"Loaded SNP data: {len(snp_data)} samples")
        else:
            logger.warning("SNP data not found. Skipping SNP preprocessing.")
            snp_data = None
        
        # Load Metabolomics data (if exists)
        metabo_path = data_dir / "metabolites.csv"
        if metabo_path.exists():
            metabo_data = pd.read_csv(metabo_path)
            logger.info(f"Loaded Metabolomics data: {len(metabo_data)} samples")
        else:
            logger.warning("Metabolomics data not found. Skipping metabolomics preprocessing.")
            metabo_data = None
        
        if snp_data is not None and metabo_data is not None:
            # Align sample IDs
            aligned_snp, aligned_metabo, exclusions = align_sample_ids(
                snp_data, metabo_data,
                output_dir=output_dir
            )
            
            logger.info(f"Aligned dataset: {len(aligned_snp)} samples")
            
            # Normalize metabolomics
            normalized_metabo = normalize_metabolomics(aligned_metabo, method="pareto")
            
            # Save results
            aligned_snp.to_csv(output_dir / "snps_aligned.csv", index=False)
            normalized_metabo.to_csv(output_dir / "metabolites_normalized.csv", index=False)
            
            logger.info("Preprocessing completed successfully")
            log_pipeline_step("preprocess_end", {
                "aligned_samples": len(aligned_snp),
                "exclusions": len(exclusions)
            })
        else:
            logger.warning("Could not process data. Both SNP and Metabolomics data required for alignment.")
            
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        log_pipeline_step("preprocess_error", {"error": str(e)})
        raise

if __name__ == "__main__":
    main()