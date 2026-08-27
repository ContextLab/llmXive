"""
Preprocessing module for mitochondrial DNA analysis.
Handles variant filtering, burden calculation, and haplogroup assignment.
"""
import os
import sys
import logging
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
import vcfpy

from config.environment import get_local_paths, ensure_directories

logger = logging.getLogger(__name__)

# --- Helper Functions for Refactored Burden Calculation ---

def _is_valid_variant(variant: vcfpy.Variant) -> bool:
    """Check if a variant is on chrM and has PASS filter."""
    if variant.CHROM != 'chrM':
        return False
    if 'PASS' not in variant.FILTER:
        return False
    return True

def _get_sample_genotypes(variant: vcfpy.Variant) -> Dict[str, Dict[str, Any]]:
    """Extract genotype info for all samples from a variant."""
    genotypes = {}
    for sample in variant.samples:
        # Ensure sample data exists
        if not sample.data:
            continue
        gt_info = sample.data.get('GT')
        if gt_info:
            genotypes[sample.sample_name] = {
                'gt': gt_info,
                'dp': sample.data.get('DP', 0),
                'ad': sample.data.get('AD', []),
                'vaf': sample.data.get('VAF', 0.0)
            }
    return genotypes

def _calculate_vaf_from_ad(ad: List[int]) -> float:
    """Calculate Variant Allele Frequency from Allelic Depth."""
    if not ad or len(ad) < 2:
        return 0.0
    ref_depth = ad[0]
    alt_depth = sum(ad[1:])
    total_depth = ref_depth + alt_depth
    if total_depth == 0:
        return 0.0
    return alt_depth / total_depth

def _accumulate_sample_burden(
    sample_burden: Dict[str, float],
    sample_depths: Dict[str, int],
    sample_vafs: Dict[str, float],
    genotypes: Dict[str, Dict[str, Any]],
    vaf_threshold: float,
    min_depth: int
) -> None:
    """
    Accumulate burden counts for a single variant across all samples.
    Updates the dictionaries in place.
    """
    for sample_name, info in genotypes.items():
        vaf = info['vaf']
        dp = info['dp']

        # If VAF not pre-calculated, compute from AD
        if vaf == 0.0 and info['ad']:
            vaf = _calculate_vaf_from_ad(info['ad'])

        # Apply thresholds
        if vaf >= vaf_threshold and dp >= min_depth:
            sample_burden[sample_name] = sample_burden.get(sample_name, 0) + 1
            sample_depths[sample_name] = sample_depths.get(sample_name, 0) + dp
            # Track max VAF or sum? Spec implies count, but let's track sum of VAFs for depth stratification later if needed
            # For now, just count
            sample_vafs[sample_name] = sample_vafs.get(sample_name, 0) + vaf

# --- Main Refactored Function ---

def calculate_burden_per_sample(
    vcf_path: Path,
    vaf_threshold: float = 0.01,
    min_depth: int = 10
) -> pd.DataFrame:
    """
    Calculate heteroplasmy burden per sample from a VCF file.

    Refactored to reduce cyclomatic complexity:
    - Extracted validation logic to _is_valid_variant
    - Extracted genotype extraction to _get_sample_genotypes
    - Extracted VAF calculation to _calculate_vaf_from_ad
    - Extracted accumulation logic to _accumulate_sample_burden
    - Removed nested conditionals in main loop.

    Args:
        vcf_path: Path to the VCF file.
        vaf_threshold: Minimum Variant Allele Frequency (0.01 = 1%).
        min_depth: Minimum sequencing depth required.

    Returns:
        DataFrame with columns: sample_id, heteroplasmy_burden, total_depth.
    """
    if not vcf_path.exists():
        raise FileNotFoundError(f"VCF file not found: {vcf_path}")

    sample_burden: Dict[str, int] = {}
    sample_depths: Dict[str, int] = {}
    sample_vafs: Dict[str, float] = {}

    logger.info(f"Streaming VCF: {vcf_path}")

    try:
        with vcfpy.Reader.from_path(str(vcf_path)) as reader:
            for variant in reader:
                if not _is_valid_variant(variant):
                    continue

                genotypes = _get_sample_genotypes(variant)
                if not genotypes:
                    continue

                _accumulate_sample_burden(
                    sample_burden, sample_depths, sample_vafs,
                    genotypes, vaf_threshold, min_depth
                )

    except Exception as e:
        logger.error(f"Error processing VCF {vcf_path}: {e}")
        raise

    # Convert to DataFrame
    data = {
        'sample_id': list(sample_burden.keys()),
        'heteroplasmy_burden': list(sample_burden.values()),
        'total_depth': [sample_depths.get(s, 0) for s in sample_burden.keys()],
        'avg_vaf': [sample_vafs.get(s, 0.0) / max(1, sample_burden[s]) for s in sample_burden.keys()]
    }

    df = pd.DataFrame(data)
    if df.empty:
        logger.warning("No variants passed filtering. Returning empty DataFrame.")
    else:
        logger.info(f"Burden calculation complete. Processed {len(df)} samples.")

    return df

def calculate_depth_stratified_burden(
    df: pd.DataFrame,
    depth_bins: Dict[str, Tuple[int, int]]
) -> pd.DataFrame:
    """
    Calculate burden stratified by sequencing depth.

    Args:
        df: DataFrame with sample_id, heteroplasmy_burden, total_depth.
        depth_bins: Dict mapping bin name to (min_depth, max_depth).

    Returns:
        DataFrame with additional columns for each bin's burden count.
    """
    result = df.copy()
    
    # Initialize bin columns
    for bin_name in depth_bins.keys():
        result[bin_name] = 0

    for idx, row in result.iterrows():
        depth = row['total_depth']
        for bin_name, (min_d, max_d) in depth_bins.items():
            if min_d <= depth < max_d:
                result.at[idx, bin_name] = row['heteroplasmy_burden']
                break
    
    return result

def filter_variants(input_vcf: Path, output_vcf: Path) -> None:
    """Filter VCF for chrM and PASS only."""
    logger.info(f"Filtering VCF: {input_vcf} -> {output_vcf}")
    # Implementation would use vcfpy.Writer and Reader similar to load_data
    # For this task, we assume the streaming logic in load_data handles the heavy lifting
    # and this function is a wrapper or placeholder for specific filtering steps if needed.
    pass

def assign_haplogroups(vcf_path: Path, output_path: Path) -> None:
    """Assign haplogroups using haplogrep2 via subprocess."""
    logger.info("Assigning haplogroups...")
    # Command construction depends on installed haplogrep2 version
    # Assuming 'haplogrep classify' interface
    cmd = [
        "haplogrep", "classify",
        "--input", str(vcf_path),
        "--output", str(output_path),
        "--format", "vcf"
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Haplogroup assignment complete.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Haplogrep failed: {e.stderr}")
        raise

def ensure_dirs() -> None:
    """Ensure required directories exist."""
    paths = get_local_paths()
    ensure_directories([
        paths['data_processed'],
        paths['logs']
    ])

def main():
    """Main entry point for preprocessing."""
    ensure_dirs()
    paths = get_local_paths()
    
    # Example execution flow
    vcf_file = paths['data_raw'] / "mito_vcf.vcf.gz"
    if vcf_file.exists():
        df = calculate_burden_per_sample(vcf_file)
        output_csv = paths['data_processed'] / "mito_burden.csv"
        df.to_csv(output_csv, index=False)
        logger.info(f"Saved burden data to {output_csv}")
    else:
        logger.warning(f"VCF file not found at {vcf_file}. Skipping burden calculation.")

if __name__ == "__main__":
    main()
