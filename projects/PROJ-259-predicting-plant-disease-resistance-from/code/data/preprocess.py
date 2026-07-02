"""
Preprocessing module for plant disease resistance prediction pipeline.

Wrappers for:
- fastp (quality control for sequencing data)
- bcftools (variant calling/filtering)
- MetaboAnalyst-compatible normalization

Implements FR-001: Sample alignment across modalities with strict ID matching.
"""

import os
import subprocess
import sys
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

from config import get_path, load_config
from utils.logging import setup_logger, log_pipeline_step, log_sample_exclusion
from utils.exceptions import PipelineException, EX_DATA_INTEGRITY

# Initialize logger
logger = setup_logger("preprocess")

def run_fastp(input_fastq: Path, output_prefix: Path, threads: int = 4) -> bool:
    """
    Run fastp for quality control and adapter trimming.
    
    Args:
        input_fastq: Path to input FASTQ file
        output_prefix: Prefix for output files (fastp will add .html, .json, .fastq)
        threads: Number of threads to use
        
    Returns:
        True if successful, False otherwise
    """
    cmd = [
        "fastp",
        "-i", str(input_fastq),
        "-o", f"{output_prefix}_clean.fastq",
        "-h", f"{output_prefix}_report.html",
        "-j", f"{output_prefix}_report.json",
        "-w", str(threads),
        "--detect_adapter_for_pe" if input_fastq.name.endswith("_R1") else "",
        "--length_required", "50"
    ]
    
    # Remove empty strings from command
    cmd = [arg for arg in cmd if arg]
    
    logger.info(f"Running fastp: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("fastp completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"fastp failed: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("fastp not found. Please install it via conda or apt-get.")
        return False

def run_bcftools_view(vcf_input: Path, output_vcf: Path, samples: Optional[List[str]] = None) -> bool:
    """
    Run bcftools view for variant filtering and sample selection.
    
    Args:
        vcf_input: Path to input VCF file
        output_vcf: Path to output VCF file
        samples: List of sample IDs to include (None for all)
        
    Returns:
        True if successful, False otherwise
    """
    cmd = ["bcftools", "view", "-O", "v", "-o", str(output_vcf), str(vcf_input)]
    
    if samples:
        # Create a temporary sample file
        sample_file = output_vcf.parent / "samples.txt"
        with open(sample_file, "w") as f:
            f.write("\n".join(samples))
        cmd.extend(["-S", str(sample_file)])
    
    logger.info(f"Running bcftools: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("bcftools view completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"bcftools view failed: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("bcftools not found. Please install it via conda or apt-get.")
        return False

def normalize_metabolomics(data: pd.DataFrame, method: str = "pareto") -> pd.DataFrame:
    """
    Apply MetaboAnalyst-compatible normalization to metabolomics data.
    
    Args:
        data: DataFrame with samples as rows, features as columns
        method: Normalization method ('pareto', 'autoscale', 'log', 'none')
        
    Returns:
        Normalized DataFrame
    """
    # Ensure numeric columns
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        logger.warning("No numeric columns found for normalization")
        return data
    
    normalized = data.copy()
    
    if method == "pareto":
        # Pareto scaling: divide by sqrt(std)
        std = normalized[numeric_cols].std()
        std[std == 0] = 1  # Avoid division by zero
        normalized[numeric_cols] = normalized[numeric_cols] / np.sqrt(std)
        
    elif method == "autoscale":
        # Auto-scaling: mean center and divide by std
        mean = normalized[numeric_cols].mean()
        std = normalized[numeric_cols].std()
        std[std == 0] = 1
        normalized[numeric_cols] = (normalized[numeric_cols] - mean) / std
        
    elif method == "log":
        # Log transformation (add small constant to avoid log(0))
        normalized[numeric_cols] = np.log1p(normalized[numeric_cols])
        
    elif method == "none":
        pass
        
    else:
        raise ValueError(f"Unknown normalization method: {method}")
    
    logger.info(f"Applied {method} normalization to metabolomics data")
    return normalized

def align_modalities(
    snp_data: pd.DataFrame,
    metabolite_data: pd.DataFrame,
    snp_id_col: str = "sample_id",
    metabo_id_col: str = "sample_id",
    exclusion_log_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict[str, Any]]]:
    """
    Align SNP and metabolomics data by exact sample ID matching.
    
    Implements FR-001: Drop samples where IDs don't match across modalities.
    
    Args:
        snp_data: DataFrame with SNP data
        metabolite_data: DataFrame with metabolomics data
        snp_id_col: Column name for sample IDs in SNP data
        metabo_id_col: Column name for sample IDs in metabolomics data
        exclusion_log_path: Path to write exclusion log (CSV)
        
    Returns:
        Tuple of (aligned_snp_data, aligned_metabolite_data, exclusion_log)
    """
    # Validate inputs
    if snp_id_col not in snp_data.columns:
        raise PipelineException(
            EX_DATA_INTEGRITY,
            f"SNP ID column '{snp_id_col}' not found in SNP data. Available: {list(snp_data.columns)}"
        )
    if metabo_id_col not in metabolite_data.columns:
        raise PipelineException(
            EX_DATA_INTEGRITY,
            f"Metabolite ID column '{metabo_id_col}' not found in metabolite data. Available: {list(metabolite_data.columns)}"
        )
    
    # Convert IDs to string for exact matching
    snp_ids = set(snp_data[snp_id_col].astype(str))
    metabo_ids = set(metabolite_data[metabo_id_col].astype(str))
    
    # Find matching and non-matching IDs
    matched_ids = snp_ids & metabo_ids
    snp_only_ids = snp_ids - metabo_ids
    metabo_only_ids = metabo_ids - snp_ids
    
    exclusion_log = []
    timestamp = datetime.now().isoformat()
    
    # Log exclusions
    for sample_id in sorted(snp_only_ids):
        exclusion_log.append({
            "sample_id": sample_id,
            "missing_modality": "metabolomics",
            "timestamp": timestamp
        })
    
    for sample_id in sorted(metabo_only_ids):
        exclusion_log.append({
            "sample_id": sample_id,
            "missing_modality": "SNP",
            "timestamp": timestamp
        })
    
    # Log summary
    logger.info(f"Sample alignment: {len(matched_ids)} matched, {len(snp_only_ids)} SNP-only, {len(metabo_only_ids)} metabolomics-only")
    
    # Filter data to matched IDs
    aligned_snp = snp_data[snp_data[snp_id_col].astype(str).isin(matched_ids)].copy()
    aligned_metabolite = metabolite_data[metabolite_data[metabo_id_col].astype(str).isin(matched_ids)].copy()
    
    # Write exclusion log if path provided
    if exclusion_log_path:
        exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(exclusion_log_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["sample_id", "missing_modality", "timestamp"])
            writer.writeheader()
            writer.writerows(exclusion_log)
        logger.info(f"Exclusion log written to {exclusion_log_path}")
    
    return aligned_snp, aligned_metabolite, exclusion_log

def preprocess_pipeline(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute the full preprocessing pipeline:
    1. Load data from manifest
    2. Run fastp/bcftools on raw sequencing data (if present)
    3. Normalize metabolomics data
    4. Align modalities by sample ID
    5. Output aligned feature tables
    
    Args:
        config_path: Optional path to config file (uses default if None)
        
    Returns:
        Dictionary with pipeline results and paths
    """
    logger.info("Starting preprocessing pipeline")
    log_pipeline_step("preprocess_start", {})
    
    config = load_config(config_path)
    data_dir = get_path("data_raw")
    processed_dir = get_path("data_processed")
    
    # Ensure output directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "status": "success",
        "aligned_samples": 0,
        "excluded_samples": 0,
        "output_files": {}
    }
    
    try:
        # Load manifest to get data sources
        from data.manifest import ManifestLoader, load_manifest
        manifest = load_manifest()
        
        # Check for data files
        snp_file = data_dir / manifest.get("snp_file")
        metabo_file = data_dir / manifest.get("metabolite_file")
        
        if not snp_file.exists() or not metabo_file.exists():
            logger.warning("Required data files not found. Checking if synthetic data was generated...")
            # If T009 or T010 generated synthetic data, use those
            snp_file = data_dir / "synthetic_snps.csv"
            metabo_file = data_dir / "synthetic_metabolites.csv"
            
            if not snp_file.exists() or not metabo_file.exists():
                raise PipelineException(
                    EX_DATA_INTEGRITY,
                    "No SNP or metabolite data files found in data/raw or generated synthetic data"
                )
        
        logger.info(f"Loading SNP data from {snp_file}")
        snp_data = pd.read_csv(snp_file)
        
        logger.info(f"Loading metabolomics data from {metabo_file}")
        metabo_data = pd.read_csv(metabo_file)
        
        # Run normalization on metabolomics data
        norm_method = config.get("normalization", {}).get("metabolite_method", "pareto")
        normalized_metabo = normalize_metabolomics(metabo_data, method=norm_method)
        
        # Align modalities
        exclusion_log_path = processed_dir / "exclusion_log.csv"
        aligned_snp, aligned_metabo, exclusion_log = align_modalities(
            snp_data,
            normalized_metabo,
            exclusion_log_path=exclusion_log_path
        )
        
        # Save aligned data
        aligned_snp_path = processed_dir / "aligned_snps.csv"
        aligned_metabo_path = processed_dir / "aligned_metabolites.csv"
        
        aligned_snp.to_csv(aligned_snp_path, index=False)
        aligned_metabo.to_csv(aligned_metabo_path, index=False)
        
        results["aligned_samples"] = len(aligned_snp)
        results["excluded_samples"] = len(exclusion_log)
        results["output_files"] = {
            "aligned_snps": str(aligned_snp_path),
            "aligned_metabolites": str(aligned_metabo_path),
            "exclusion_log": str(exclusion_log_path)
        }
        
        logger.info(f"Preprocessing complete: {results['aligned_samples']} samples aligned, {results['excluded_samples']} excluded")
        log_pipeline_step("preprocess_complete", results)
        
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {str(e)}")
        results["status"] = "failed"
        results["error"] = str(e)
        raise
    
    return results

def main():
    """CLI entry point for preprocessing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess plant disease resistance data")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--normalize", type=str, default="pareto", 
                      choices=["pareto", "autoscale", "log", "none"],
                      help="Normalization method for metabolomics")
    args = parser.parse_args()
    
    # Update config with command-line args
    config = load_config(args.config)
    if "normalization" not in config:
        config["normalization"] = {}
    config["normalization"]["metabolite_method"] = args.normalize
    
    results = preprocess_pipeline()
    
    print(f"Preprocessing completed successfully!")
    print(f"Aligned samples: {results['aligned_samples']}")
    print(f"Excluded samples: {results['excluded_samples']}")
    print(f"Output files: {results['output_files']}")
    
    return results

if __name__ == "__main__":
    main()