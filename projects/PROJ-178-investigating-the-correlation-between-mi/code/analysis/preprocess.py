import os
import sys
import logging
from pathlib import Path
import vcfpy
import pandas as pd
import subprocess
import json
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('code/logs/preprocess.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Create necessary output directories."""
    dirs = [
        Path('code/data/processed'),
        Path('code/logs'),
        Path('code/temp')
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {dirs}")

def filter_variants(vcf_path: Path, output_path: Path) -> Path:
    """Filter VCF to keep only chrM and PASS variants."""
    logger.info(f"Filtering VCF: {vcf_path}")
    reader = vcfpy.Reader.from_path(str(vcf_path))
    writer = vcfpy.Writer.from_path(str(output_path), reader.header)
    
    count_in = 0
    count_out = 0
    
    with reader:
        with writer:
            for record in reader:
                count_in += 1
                # Filter by chromosome
                if record.CHROM != 'chrM':
                    continue
                # Filter by quality status
                if 'PASS' not in record.FILTER:
                    continue
                writer.write_record(record)
                count_out += 1
    
    logger.info(f"Filtered {count_in} records -> {count_out} kept (chrM, PASS)")
    return output_path

def filter_vcf_file(input_vcf: Path, output_vcf: Path) -> Path:
    """Wrapper to ensure VCF filtering is called correctly."""
    return filter_variants(input_vcf, output_vcf)

def calculate_burden_per_sample(filtered_vcf_path: Path, vaf_threshold: float = 0.01) -> pd.DataFrame:
    """
    Calculate heteroplasmy burden per sample.
    Burden = count of variants with VAF >= vaf_threshold.
    """
    logger.info(f"Calculating burden with VAF threshold {vaf_threshold} from {filtered_vcf_path}")
    reader = vcfpy.Reader.from_path(str(filtered_vcf_path))
    
    sample_ids = reader.header.samples
    sample_counts = {s: 0 for s in sample_ids}
    
    with reader:
        for record in reader:
            for call in record.calls:
                if call.sample_name not in sample_ids:
                    continue
                # Check for GT and AD/DP or similar to calculate VAF
                # Standard 1000G VCFs often have GT:AD:DP:GQ:PL
                if 'AD' in call.data and 'DP' in call.data and call.data['DP'] > 0:
                    ad = call.data['AD']
                    # AD is usually [ref_count, alt_count]
                    if len(ad) >= 2:
                        alt_count = ad[1]
                        total_depth = ad[0] + alt_count
                        if total_depth > 0:
                            vaf = alt_count / total_depth
                            if vaf >= vaf_threshold:
                                sample_counts[call.sample_name] += 1
                                continue
                # Fallback if AD is missing but GT is heterozygous (rare for mito, but safe)
                if 'GT' in call.data:
                    gt = call.data['GT']
                    if gt in ['0/1', '1/0', '0|1', '1|0']:
                        # Assume heterozygous implies some burden, but without VAF we can't be sure
                        # Strictly, we need VAF. Skipping if AD missing.
                        pass
    
    df = pd.DataFrame(list(sample_counts.items()), columns=['sample_id', 'burden_count'])
    logger.info(f"Calculated burden for {len(df)} samples")
    return df

def calculate_depth_stratified_burden(filtered_vcf_path: Path, vaf_threshold: float = 0.01) -> pd.DataFrame:
    """
    Calculate heteroplasmy burden stratified by depth bins.
    Bins: Low (DP < 20), Medium (20 <= DP < 100), High (DP >= 100).
    Returns a wide-format dataframe with counts per bin per sample.
    """
    logger.info(f"Calculating depth-stratified burden from {filtered_vcf_path}")
    reader = vcfpy.Reader.from_path(str(filtered_vcf_path))
    
    sample_ids = reader.header.samples
    # Initialize counters for each bin
    sample_data = {s: {'low': 0, 'medium': 0, 'high': 0} for s in sample_ids}
    
    with reader:
        for record in reader:
            for call in record.calls:
                if call.sample_name not in sample_ids:
                    continue
                if 'AD' in call.data and 'DP' in call.data:
                    ad = call.data['AD']
                    dp = call.data['DP']
                    if len(ad) >= 2 and dp > 0:
                        alt_count = ad[1]
                        total_depth = ad[0] + alt_count
                        vaf = alt_count / total_depth if total_depth > 0 else 0
                        
                        if vaf >= vaf_threshold:
                            if dp < 20:
                                sample_data[call.sample_name]['low'] += 1
                            elif dp < 100:
                                sample_data[call.sample_name]['medium'] += 1
                            else:
                                sample_data[call.sample_name]['high'] += 1
    
    df = pd.DataFrame.from_dict(sample_data, orient='index')
    df.index.name = 'sample_id'
    df = df.reset_index()
    df = df.rename(columns={'low': 'burden_low', 'medium': 'burden_medium', 'high': 'burden_high'})
    logger.info(f"Calculated depth-stratified burden for {len(df)} samples")
    return df

def assign_haplogroups(vcf_path: Path, output_dir: Path = None) -> pd.DataFrame:
    """
    Integrate haplogrep2 via subprocess to assign haplogroups.
    Expects haplogrep2 to be installed in the environment.
    Input: VCF file (filtered for chrM).
    Output: DataFrame with sample_id and haplogroup.
    """
    logger.info("Starting haplogroup assignment via haplogrep2 subprocess")
    
    if output_dir is None:
        output_dir = Path('code/temp')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Haplogrep2 CLI typically requires a reference build.
    # We assume 'GRCh38' or 'rCRS' is available. 
    # Command: haplogrep classify -i <vcf> -o <output> --format vcf --build <build>
    # We capture the output file which is usually JSON or TSV.
    
    # Check if haplogrep2 is available
    try:
        result = subprocess.run(['haplogrep', '--version'], capture_output=True, text=True, timeout=10)
        logger.info(f"Haplogrep2 version: {result.stdout.strip()}")
    except FileNotFoundError:
        logger.error("haplogrep2 command not found. Please install it via: pip install haplogrep2")
        raise RuntimeError("haplogrep2 not found in PATH")
    
    # Prepare input and output paths
    input_vcf = str(vcf_path)
    output_json = output_dir / "haplogrep_output.json"
    
    cmd = [
        'haplogrep', 'classify',
        '-i', input_vcf,
        '-o', str(output_json),
        '--format', 'vcf',
        '--build', 'GRCh38' # Assuming GRCh38 based on 1000G
    ]
    
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300) # 5 min timeout
        if proc.returncode != 0:
            logger.error(f"Haplogrep2 failed: {proc.stderr}")
            raise RuntimeError(f"Haplogrep2 failed with code {proc.returncode}: {proc.stderr}")
        logger.info(f"Haplogrep2 completed successfully. Output: {output_json}")
    except subprocess.TimeoutExpired:
        logger.error("Haplogrep2 timed out")
        raise RuntimeError("Haplogrep2 timed out")
    
    # Parse the JSON output
    if not output_json.exists():
        raise FileNotFoundError(f"Haplogrep2 output file not found: {output_json}")
    
    with open(output_json, 'r') as f:
        raw_data = json.load(f)
    
    # Structure of haplogrep2 JSON output varies, but usually contains a 'samples' list
    # or a dictionary keyed by sample ID.
    # Typical structure: { "samples": [ { "id": "Sample1", "haplogroup": "H1" }, ... ] }
    # or { "Sample1": { "haplogroup": "H1" }, ... }
    
    results = []
    if isinstance(raw_data, dict) and 'samples' in raw_data:
        for item in raw_data['samples']:
            sid = item.get('id')
            hg = item.get('haplogroup')
            if sid and hg:
                results.append({'sample_id': sid, 'haplogroup': hg})
    elif isinstance(raw_data, dict):
        # Assume top-level keys are sample IDs
        for sid, data in raw_data.items():
            if isinstance(data, dict):
                hg = data.get('haplogroup')
            else:
                hg = data # If value is directly the string
            if sid and hg:
                results.append({'sample_id': sid, 'haplogroup': hg})
    else:
        # Fallback: try to find sample entries in a list
        if isinstance(raw_data, list):
            for item in raw_data:
                sid = item.get('id') or item.get('sample_id')
                hg = item.get('haplogroup')
                if sid and hg:
                    results.append({'sample_id': sid, 'haplogroup': hg})
    
    if not results:
        logger.warning("No haplogroup assignments found in output.")
    
    df = pd.DataFrame(results)
    logger.info(f"Assigned haplogroups to {len(df)} samples")
    return df

def main():
    """Main entry point for preprocessing pipeline."""
    ensure_dirs()
    
    # Define paths
    raw_vcf_path = Path('code/data/raw/chrM_filtered.vcf') # Assumed output from T014
    filtered_vcf_path = Path('code/data/processed/chrM_pass.vcf')
    burden_path = Path('code/data/processed/burden.csv')
    depth_burden_path = Path('code/data/processed/burden_depth.csv')
    haplogroup_path = Path('code/data/processed/haplogroups.csv')
    
    # Check if raw VCF exists (from T012/T014)
    if not raw_vcf_path.exists():
        # If T014 hasn't run, try to filter raw VCF directly if it exists
        # Or assume T014 produced the file at this location
        # For robustness, we check for the pre-filtered file
        logger.warning(f"Expected filtered VCF not found at {raw_vcf_path}. Attempting to filter raw.")
        # In a real pipeline, we'd chain these steps. Here we assume the previous task
        # put the filtered file where we expect it, or we filter it now.
        # Let's assume the task T014 produced the file at raw_vcf_path for simplicity,
        # or we re-run filter_variants if the "raw" file is actually the unfiltered one.
        # Given the task flow, T014 produces the filtered VCF.
        # If T014 hasn't run, this script will fail, which is expected behavior for a pipeline step.
        raise FileNotFoundError(f"Input VCF not found at {raw_vcf_path}. Ensure T014 is complete.")
    
    # 1. Filter VCF (if not already done by T014, but T014 is marked done)
    # We assume T014 produced the file at raw_vcf_path. 
    # If T014 output is elsewhere, adjust path.
    # Let's assume T014 output is at 'code/data/processed/chrM_pass.vcf' or similar.
    # Re-reading T014: "Implement variant filtering... in preprocess.py".
    # So T014 likely wrote to a specific output. Let's assume the input to T017 is the output of T014.
    # We'll use a standard path for the filtered VCF.
    input_vcf = Path('code/data/processed/chrM_pass.vcf')
    if not input_vcf.exists():
        # Fallback: try raw if filtered not found
        input_vcf = Path('code/data/raw/1000G_mito.vcf')
        if not input_vcf.exists():
            raise FileNotFoundError("No VCF input found. Ensure T012 and T014 have run.")
        logger.info(f"Using raw VCF for filtering: {input_vcf}")
        filter_vcf_file(input_vcf, Path('code/data/processed/chrM_pass.vcf'))
        input_vcf = Path('code/data/processed/chrM_pass.vcf')
    
    # 2. Calculate Burden
    burden_df = calculate_burden_per_sample(input_vcf)
    burden_df.to_csv(burden_path, index=False)
    logger.info(f"Saved burden to {burden_path}")
    
    # 3. Calculate Depth-Stratified Burden
    depth_burden_df = calculate_depth_stratified_burden(input_vcf)
    depth_burden_df.to_csv(depth_burden_path, index=False)
    logger.info(f"Saved depth-stratified burden to {depth_burden_path}")
    
    # 4. Assign Haplogroups (T017 Core Task)
    try:
        hg_df = assign_haplogroups(input_vcf)
        hg_df.to_csv(haplogroup_path, index=False)
        logger.info(f"Saved haplogroups to {haplogroup_path}")
    except Exception as e:
        logger.error(f"Failed to assign haplogroups: {e}")
        # Create an empty file to prevent downstream crashes, but log failure
        pd.DataFrame(columns=['sample_id', 'haplogroup']).to_csv(haplogroup_path, index=False)
        raise

if __name__ == "__main__":
    main()