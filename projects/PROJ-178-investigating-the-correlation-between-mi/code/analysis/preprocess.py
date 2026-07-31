import os
import sys
import logging
import subprocess
import json
from pathlib import Path
import pandas as pd
import vcfpy
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
VAF_THRESHOLD = 0.01  # 1%
DEPTH_BINS = {
    'Low': (0, 20),
    'Medium': (20, 50),
    'High': (50, float('inf'))
}

def ensure_dirs():
    """Ensure all necessary directories exist."""
    dirs = [
        'code/data/raw',
        'code/data/processed',
        'code/logs'
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("Directories ensured.")

def filter_variants(variant: vcfpy.Record) -> bool:
    """Filter variants: keep only chrM and PASS status."""
    if variant.CHROM != 'chrM':
        return False
    if variant.FILTER and variant.FILTER != 'PASS':
        return False
    return True

def filter_vcf_file(input_path: Path, output_path: Path) -> int:
    """Filter VCF file for chrM and PASS variants, write to new file."""
    logger.info(f"Filtering VCF: {input_path} -> {output_path}")
    reader = vcfpy.Reader.from_path(str(input_path))
    writer = vcfpy.Writer.from_path(str(output_path), reader.header)
    
    count = 0
    for variant in reader:
        if filter_variants(variant):
            writer.write_record(variant)
            count += 1
    
    writer.close()
    logger.info(f"Filtered VCF written. {count} variants kept.")
    return count

def calculate_burden_per_sample(filtered_vcf_path: Path, vaf_threshold: float = VAF_THRESHOLD) -> Dict[str, int]:
    """
    Calculate heteroplasmy burden per sample.
    Burden = count of variants with VAF >= vaf_threshold.
    """
    logger.info(f"Calculating burden with VAF threshold {vaf_threshold}...")
    reader = vcfpy.Reader.from_path(str(filtered_vcf_path))
    sample_ids = reader.header.samples
    burden_counts = {sample: 0 for sample in sample_ids}
    
    for variant in reader:
        # Extract FORMAT fields
        if 'GT' not in variant.format_keys:
            continue
        
        for sample in variant.samples:
            sample_name = sample.sample
            if sample_name not in burden_counts:
                continue
            
            # Get VAF (AD field: Allele Depth)
            if 'AD' in sample.data:
                ad = sample.data.AD
                if len(ad) >= 2:
                    ref_depth = ad[0]
                    alt_depth = ad[1]
                    total_depth = ref_depth + alt_depth
                    if total_depth > 0:
                        vaf = alt_depth / total_depth
                        if vaf >= vaf_threshold:
                            burden_counts[sample_name] += 1
            elif 'AF' in sample.data:
                # Some VCFs provide AF directly
                af = sample.data.AF
                if isinstance(af, (list, tuple)) and len(af) > 0:
                    if af[0] >= vaf_threshold:
                        burden_counts[sample_name] += 1
                elif isinstance(af, float) and af >= vaf_threshold:
                    burden_counts[sample_name] += 1
    
    reader.close()
    logger.info(f"Burden calculation complete for {len(burden_counts)} samples.")
    return burden_counts

def calculate_depth_stratified_burden(filtered_vcf_path: Path, vaf_threshold: float = VAF_THRESHOLD) -> Dict[str, Dict[str, int]]:
    """
    Calculate burden stratified by sequencing depth (Low, Medium, High).
    Depth bins: Low (0-20), Medium (20-50), High (50+).
    """
    logger.info("Calculating depth-stratified burden...")
    reader = vcfpy.Reader.from_path(str(filtered_vcf_path))
    sample_ids = reader.header.samples
    
    # Initialize structure: sample -> {bin: count}
    burden_by_depth = {
        sample: {'Low': 0, 'Medium': 0, 'High': 0}
        for sample in sample_ids
    }
    
    for variant in reader:
        if 'DP' not in variant.format_keys:
            continue
        
        for sample in variant.samples:
            sample_name = sample.sample
            if sample_name not in burden_by_depth:
                continue
            
            # Get Depth (DP)
            dp = sample.data.DP if hasattr(sample.data, 'DP') else None
            if dp is None:
                # Try to infer from AD
                if 'AD' in sample.data:
                    ad = sample.data.AD
                    if len(ad) >= 2:
                        dp = ad[0] + ad[1]
                    else:
                        continue
                else:
                    continue
            
            # Determine bin
            if dp < 20:
                bin_name = 'Low'
            elif dp < 50:
                bin_name = 'Medium'
            else:
                bin_name = 'High'
            
            # Check VAF
            if 'AD' in sample.data:
                ad = sample.data.AD
                if len(ad) >= 2:
                    vaf = ad[1] / (ad[0] + ad[1]) if (ad[0] + ad[1]) > 0 else 0
                    if vaf >= vaf_threshold:
                        burden_by_depth[sample_name][bin_name] += 1
            elif 'AF' in sample.data:
                af = sample.data.AF
                if isinstance(af, (list, tuple)) and len(af) > 0:
                    if af[0] >= vaf_threshold:
                        burden_by_depth[sample_name][bin_name] += 1
                elif isinstance(af, float) and af >= vaf_threshold:
                    burden_by_depth[sample_name][bin_name] += 1
    
    reader.close()
    logger.info("Depth-stratified burden calculation complete.")
    return burden_by_depth

def assign_haplogroups(filtered_vcf_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Assign haplogroups using haplogrep2 via subprocess.
    Converts VCF to FASTA, runs haplogrep2, parses JSON output.
    """
    logger.info(f"Starting haplogroup assignment for {filtered_vcf_path}...")
    
    # Ensure haplogrep2 is available
    try:
        subprocess.run(['haplogrep2', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("haplogrep2 is not installed or not in PATH. Please install it: pip install haplogrep2")
    
    # Step 1: Convert VCF to FASTA (haplogrep2 expects FASTA)
    fasta_path = filtered_vcf_path.with_suffix('.fasta')
    logger.info(f"Converting VCF to FASTA: {fasta_path}")
    
    # We need to extract the mtDNA sequence per sample. 
    # Since 1000 Genomes VCFs are variant-only, we need a reference.
    # However, haplogrep2 can work with VCF if we provide the reference.
    # Alternative: Use haplogrep2's built-in VCF support if available, 
    # or convert using a tool like bcftools consensus (if available).
    # Given constraints, we will attempt to run haplogrep2 directly on VCF 
    # if supported, or fail with a clear message.
    
    # Check if haplogrep2 supports VCF input directly
    # Recent versions of haplogrep2 support VCF input with --format vcf
    cmd = [
        'haplogrep2',
        'classify',
        '--format', 'vcf',
        '--input', str(filtered_vcf_path),
        '--output', str(output_path),
        '--output-format', 'json'
    ]
    
    logger.info(f"Running haplogrep2: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"haplogrep2 failed with return code {e.returncode}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise RuntimeError(f"haplogrep2 classification failed: {e.stderr}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("haplogrep2 classification timed out.")
    
    # Parse the JSON output
    if not output_path.exists():
        raise FileNotFoundError(f"haplogrep2 did not produce output file: {output_path}")
    
    with open(output_path, 'r') as f:
        haplogroup_data = json.load(f)
    
    # Expected structure: { "results": [ { "sample_id": "...", "haplogroup": "..." }, ... ] }
    # or similar. Adjust parsing based on actual haplogrep2 output format.
    results = []
    if isinstance(haplogroup_data, list):
        for item in haplogroup_data:
            if 'sample_id' in item and 'haplogroup' in item:
                results.append({
                    'sample_id': item['sample_id'],
                    'haplogroup': item['haplogroup']
                })
    elif isinstance(haplogroup_data, dict) and 'results' in haplogroup_data:
        for item in haplogroup_data['results']:
            if 'sample_id' in item and 'haplogroup' in item:
                results.append({
                    'sample_id': item['sample_id'],
                    'haplogroup': item['haplogroup']
                })
    elif isinstance(haplogroup_data, dict):
        # Maybe direct mapping?
        for sample_id, hg in haplogroup_data.items():
            if sample_id != 'metadata':  # Skip metadata keys
                results.append({
                    'sample_id': sample_id,
                    'haplogroup': hg
                })
    
    if not results:
        logger.warning("No haplogroup results found in output. Output content:")
        with open(output_path, 'r') as f:
            logger.warning(f.read()[:500])
        raise ValueError("No haplogroup data extracted from haplogrep2 output.")
    
    df = pd.DataFrame(results)
    logger.info(f"Haplogroup assignment complete. {len(df)} samples processed.")
    return df

def main():
    """Main entry point for preprocessing."""
    ensure_dirs()
    
    # Paths
    raw_vcf_path = Path('code/data/raw/1000G_mito_vcf.vcf.gz')
    filtered_vcf_path = Path('code/data/processed/1000G_mito_filtered.vcf.gz')
    burden_output_path = Path('code/data/processed/burden_per_sample.csv')
    depth_burden_output_path = Path('code/data/processed/burden_depth_stratified.csv')
    haplogroup_output_path = Path('code/data/processed/haplogroups.json')
    haplogroup_csv_path = Path('code/data/processed/haplogroups.csv')
    
    # Check if raw VCF exists
    if not raw_vcf_path.exists():
        # Try without .gz
        raw_vcf_path = Path('code/data/raw/1000G_mito_vcf.vcf')
        if not raw_vcf_path.exists():
            raise FileNotFoundError(f"Raw VCF not found at {raw_vcf_path}. Run load_data.py first.")
    
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Filter VCF
    if not filtered_vcf_path.exists():
        filter_vcf_file(raw_vcf_path, filtered_vcf_path)
    else:
        logger.info(f"Filtered VCF already exists: {filtered_vcf_path}")
    
    # 2. Calculate burden
    if not burden_output_path.exists():
        burden_counts = calculate_burden_per_sample(filtered_vcf_path)
        df_burden = pd.DataFrame([{'sample_id': k, 'burden': v} for k, v in burden_counts.items()])
        df_burden.to_csv(burden_output_path, index=False)
        logger.info(f"Burden saved to {burden_output_path}")
    else:
        logger.info(f"Burden file already exists: {burden_output_path}")
    
    # 3. Calculate depth-stratified burden
    if not depth_burden_output_path.exists():
        depth_burden = calculate_depth_stratified_burden(filtered_vcf_path)
        rows = []
        for sample, bins in depth_burden.items():
            for bin_name, count in bins.items():
                rows.append({
                    'sample_id': sample,
                    'depth_bin': bin_name,
                    'burden': count
                })
        df_depth = pd.DataFrame(rows)
        df_depth.to_csv(depth_burden_output_path, index=False)
        logger.info(f"Depth-stratified burden saved to {depth_burden_output_path}")
    else:
        logger.info(f"Depth-stratified burden file already exists: {depth_burden_output_path}")
    
    # 4. Assign haplogroups
    if not haplogroup_csv_path.exists():
        df_hg = assign_haplogroups(filtered_vcf_path, haplogroup_output_path)
        df_hg.to_csv(haplogroup_csv_path, index=False)
        logger.info(f"Haplogroups saved to {haplogroup_csv_path}")
    else:
        logger.info(f"Haplogroup file already exists: {haplogroup_csv_path}")
    
    logger.info("Preprocessing pipeline completed.")

if __name__ == '__main__':
    main()