import os
import sys
import logging
from pathlib import Path
import vcfpy
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure output directories exist."""
    raw_dir = Path("code/data/raw")
    processed_dir = Path("code/data/processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir, processed_dir

def filter_variants(record):
    """
    Filter VCF records to keep only:
    1. Variants on chromosome 'chrM' (or 'MT')
    2. Variants with FILTER status 'PASS'
    """
    # Check chromosome
    chrom = record.CHROM
    if chrom not in ['chrM', 'MT', 'M']:
        return False

    # Check filter status
    if record.FILTER and record.FILTER != 'PASS':
        return False

    return True

def filter_vcf_file(input_vcf_path, output_vcf_path):
    """
    Filter a VCF file to keep only mitochondrial PASS variants.
    Writes a new filtered VCF file.
    """
    logger.info(f"Filtering VCF: {input_vcf_path}")
    
    if not os.path.exists(input_vcf_path):
        raise FileNotFoundError(f"Input VCF file not found: {input_vcf_path}")

    reader = vcfpy.Reader.from_path(str(input_vcf_path))
    
    with vcfpy.Writer.from_path(str(output_vcf_path), reader.header) as writer:
        count_in = 0
        count_out = 0
        for record in reader:
            count_in += 1
            if filter_variants(record):
                writer.write_record(record)
                count_out += 1
            if count_in % 100000 == 0:
                logger.info(f"Processed {count_in} records, kept {count_out}")
        
        logger.info(f"Filtering complete. Input: {count_in}, Output: {count_out}")
    
    return output_vcf_path

def calculate_burden_per_sample(filtered_vcf_path, vaf_threshold=0.01):
    """
    Calculate heteroplasmy burden per sample.
    
    Heteroplasmy burden is defined as the count of mitochondrial variants
    with Variant Allele Frequency (VAF) >= threshold (default 1%).
    
    Args:
        filtered_vcf_path: Path to the filtered VCF file (only chrM, PASS)
        vaf_threshold: Minimum VAF to count as heteroplasmic (default 0.01 = 1%)
    
    Returns:
        pd.DataFrame with columns: sample_id, burden_count
    """
    logger.info(f"Calculating burden with VAF threshold {vaf_threshold} from {filtered_vcf_path}")
    
    if not os.path.exists(filtered_vcf_path):
        raise FileNotFoundError(f"Filtered VCF file not found: {filtered_vcf_path}")

    reader = vcfpy.Reader.from_path(str(filtered_vcf_path))
    
    # Initialize counters for each sample
    sample_ids = reader.header.samples
    burden_counts = {sample: 0 for sample in sample_ids}
    
    total_variants = 0
    heteroplasmic_variants = 0
    
    for record in reader:
        total_variants += 1
        
        # Get AD (Allelic Depth) and DP (Depth) from INFO or FORMAT
        # Standard VCF: FORMAT fields include GT:AD:DP:GQ:PL
        # We need AD to calculate VAF = alt_depth / (ref_depth + alt_depth)
        
        ad_field = record.INFO.get('AD')  # INFO AD (if present)
        
        # Iterate over samples to get per-sample AD
        for i, sample in enumerate(sample_ids):
            sample_call = record.get_call(sample)
            if sample_call is None:
                continue
            
            # Get AD from FORMAT field
            ad = sample_call.data.AD
            if ad is None or len(ad) < 2:
                continue
            
            ref_depth = ad[0]
            alt_depth = ad[1]
            total_depth = ref_depth + alt_depth
            
            if total_depth == 0:
                continue
            
            vaf = alt_depth / total_depth
            
            # Check if VAF meets threshold
            if vaf >= vaf_threshold:
                burden_counts[sample] += 1
                heteroplasmic_variants += 1

        if total_variants % 100000 == 0:
            logger.info(f"Processed {total_variants} variants, found {heteroplasmic_variants} heteroplasmic calls")
    
    # Create DataFrame
    df = pd.DataFrame([
        {'sample_id': sample, 'burden_count': count}
        for sample, count in burden_counts.items()
    ])
    
    logger.info(f"Burden calculation complete. Total variants: {total_variants}, "
               f"Total heteroplasmic calls: {heteroplasmic_variants}, "
               f"Samples: {len(df)}")
    
    return df

def calculate_depth_stratified_burden(filtered_vcf_path, vaf_threshold=0.01, depth_bins=[10, 50, 100]):
    """
    Calculate heteroplasmy burden stratified by sequencing depth.
    
    Bins:
    - Low: DP < depth_bins[0]
    - Medium: depth_bins[0] <= DP < depth_bins[1]
    - High: DP >= depth_bins[1]
    
    Args:
        filtered_vcf_path: Path to filtered VCF
        vaf_threshold: Minimum VAF threshold
        depth_bins: List of depth thresholds for binning
    
    Returns:
        pd.DataFrame with columns: sample_id, burden_low, burden_medium, burden_high
    """
    logger.info(f"Calculating depth-stratified burden from {filtered_vcf_path}")
    
    if not os.path.exists(filtered_vcf_path):
        raise FileNotFoundError(f"Filtered VCF file not found: {filtered_vcf_path}")

    reader = vcfpy.Reader.from_path(str(filtered_vcf_path))
    sample_ids = reader.header.samples
    
    # Initialize counters for each sample and depth bin
    burden_counts = {
        sample: {'low': 0, 'medium': 0, 'high': 0}
        for sample in sample_ids
    }
    
    total_variants = 0
    
    for record in reader:
        total_variants += 1
        
        for i, sample in enumerate(sample_ids):
            sample_call = record.get_call(sample)
            if sample_call is None:
                continue
            
            # Get DP (Depth) and AD (Allelic Depth)
            dp = sample_call.data.DP
            ad = sample_call.data.AD
            
            if dp is None or ad is None or len(ad) < 2:
                continue
            
            ref_depth = ad[0]
            alt_depth = ad[1]
            total_depth = ref_depth + alt_depth
            
            if total_depth == 0:
                continue
            
            vaf = alt_depth / total_depth
            
            if vaf < vaf_threshold:
                continue
            
            # Determine depth bin
            if dp < depth_bins[0]:
                bin_name = 'low'
            elif dp < depth_bins[1]:
                bin_name = 'medium'
            else:
                bin_name = 'high'
            
            burden_counts[sample][bin_name] += 1
        
        if total_variants % 100000 == 0:
            logger.info(f"Processed {total_variants} variants")
    
    # Create DataFrame
    df = pd.DataFrame([
        {
            'sample_id': sample,
            'burden_low': counts['low'],
            'burden_medium': counts['medium'],
            'burden_high': counts['high']
        }
        for sample, counts in burden_counts.items()
    ])
    
    logger.info(f"Depth-stratified burden calculation complete. Samples: {len(df)}")
    
    return df

def assign_haplogroups(processed_dataset_path):
    """
    Assign mitochondrial haplogroups using haplogrep2 via subprocess.
    
    This function expects a processed dataset with sequence data or VCF
    that can be passed to haplogrep2.
    
    Args:
        processed_dataset_path: Path to processed dataset or VCF
    
    Returns:
        pd.DataFrame with sample_id and haplogroup columns
    """
    logger.info(f"Assigning haplogroups using haplogrep2")
    
    # This is a placeholder for haplogrep2 integration
    # In a real implementation, we would:
    # 1. Prepare input file for haplogrep2
    # 2. Run haplogrep2 as a subprocess
    # 3. Parse the output and return results
    
    # For now, return an empty DataFrame with expected structure
    # This will be implemented in T017
    logger.warning("Haplogroup assignment not yet implemented (T017)")
    
    return pd.DataFrame(columns=['sample_id', 'haplogroup'])

def main():
    """Main entry point for preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline")
    
    raw_dir, processed_dir = ensure_dirs()
    
    # Step 1: Download and filter VCF (T012, T014)
    # Assuming T012 has downloaded the VCF to code/data/raw/1000g_mito.vcf.gz
    input_vcf = raw_dir / "1000g_mito.vcf.gz"
    filtered_vcf = processed_dir / "1000g_mito_filtered.vcf"
    
    if not input_vcf.exists():
        logger.error(f"Input VCF not found: {input_vcf}")
        logger.error("Please run T012 to download the VCF first")
        sys.exit(1)
    
    # Filter variants (T014)
    if not filtered_vcf.exists():
        filter_vcf_file(str(input_vcf), str(filtered_vcf))
    
    # Step 2: Calculate burden (T015)
    burden_df = calculate_burden_per_sample(str(filtered_vcf), vaf_threshold=0.01)
    
    # Save burden data
    burden_output = processed_dir / "burden_per_sample.csv"
    burden_df.to_csv(burden_output, index=False)
    logger.info(f"Saved burden data to {burden_output}")
    
    # Step 3: Depth-stratified burden (T016)
    depth_burden_df = calculate_depth_stratified_burden(str(filtered_vcf), vaf_threshold=0.01)
    depth_burden_output = processed_dir / "burden_depth_stratified.csv"
    depth_burden_df.to_csv(depth_burden_output, index=False)
    logger.info(f"Saved depth-stratified burden to {depth_burden_output}")
    
    logger.info("Preprocessing pipeline complete")

if __name__ == "__main__":
    main()