"""
Wrapper for featureCounts to quantify alignments into TPM matrices.

This script takes aligned BAM files produced by HISAT2 and generates
count matrices, subsequently converting them to TPM (Transcripts Per Million).
It respects the project's synthetic mode flag to skip execution when real data
is unavailable.
"""
import os
import sys
import subprocess
import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.utils.config import get_data_path, get_config
from src.utils.schemas import ExpressionMatrixMetadata, ManifestEntry, create_manifest_entry, compute_sha256
from src.utils.provenance import record_provenance, ArtifactType

logger = get_logger(__name__)

def check_featurecounts_available() -> bool:
    """Check if featureCounts is installed and available in PATH."""
    try:
        result = subprocess.run(
            ["featureCounts", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info(f"featureCounts found: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"featureCounts returned error: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        logger.error("featureCounts not found in PATH. Please install subread package.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Timeout checking featureCounts version.")
        return False

def run_featurecounts(
    bam_file: Path,
    gtf_file: Path,
    output_dir: Path,
    accession_id: str,
    threads: int = 4
) -> Optional[Path]:
    """
    Run featureCounts on a single BAM file to generate counts.

    Args:
        bam_file: Path to the input BAM file.
        gtf_file: Path to the annotation GTF file.
        output_dir: Directory to save output files.
        accession_id: Study accession ID for naming.
        threads: Number of threads to use.

    Returns:
        Path to the generated counts file, or None if failed.
    """
    if not bam_file.exists():
        logger.error(f"BAM file not found: {bam_file}")
        return None
    
    if not gtf_file.exists():
        logger.error(f"GTF file not found: {gtf_file}")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    counts_file = output_dir / f"{accession_id}_counts.txt"
    summary_file = output_dir / f"{accession_id}_featurecounts_summary.txt"

    cmd = [
        "featureCounts",
        "-T", str(threads),
        "-p",  # Paired-end
        "-a", str(gtf_file),
        "-o", str(counts_file),
        str(bam_file)
    ]

    logger.info(f"Running featureCounts: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode != 0:
            logger.error(f"featureCounts failed for {accession_id}: {result.stderr}")
            return None
        
        logger.info(f"featureCounts completed successfully for {accession_id}")
        if result.stdout:
            logger.debug(result.stdout)
        
        return counts_file
    except subprocess.TimeoutExpired:
        logger.error(f"featureCounts timed out for {accession_id}")
        return None
    except Exception as e:
        logger.error(f"Error running featureCounts for {accession_id}: {str(e)}")
        return None

def calculate_tpm(counts_file: Path, output_dir: Path, accession_id: str) -> Optional[Path]:
    """
    Convert raw counts to TPM.
    
    Note: featureCounts outputs raw counts. To get TPM, we need gene lengths.
    Since featureCounts doesn't directly output TPM, we calculate it here.
    We assume the GTF file contains gene length information or we use the 
    sum of exon lengths per gene.
    
    For simplicity in this wrapper, we perform a standard TPM calculation:
    1. Sum counts per gene (if multiple entries exist).
    2. Calculate RPK (Reads Per Kilobase) = Count / (GeneLength / 1000).
    3. TPM = (RPK / Sum(RPK)) * 1,000,000.
    
    This implementation assumes the counts file has a specific format from featureCounts
    and requires a gene length mapping. If gene lengths are not available, 
    we fall back to a normalized count (CPM) but log a warning, as true TPM 
    requires length.
    
    However, to strictly follow the task "Quantify alignments into TPM matrices",
    we will attempt to extract lengths from the GTF if possible, or use a 
    placeholder length if not found, but ideally, we need the GTF.
    
    Since this is a wrapper and we want to be robust:
    We will parse the featureCounts output. The 7th column is usually the length.
    featureCounts output columns: Geneid, Chr, Start, End, Strand, Length, Count...
    Wait, featureCounts -o output usually produces a summary and a counts file.
    The counts file (output) has: Geneid, Chr, Start, End, Strand, Length, Status, Sample1...
    
    Let's verify the column index for Length.
    According to subread docs: 
    Column 1: GeneID
    Column 2: Chr
    Column 3: Start
    Column 4: End
    Column 5: Strand
    Column 6: Length
    Column 7: Status (Assigned, Unassigned_...)
    Column 8+: Counts
    
    So we can extract Length from column 6.
    """
    import pandas as pd
    
    if not counts_file.exists():
        logger.error(f"Counts file not found: {counts_file}")
        return None

    try:
        # Read the featureCounts output
        # Skip the first 5 comment lines (starting with #)
        df = pd.read_csv(counts_file, sep='\t', comment='#')
        
        # Identify columns
        # Expected: Geneid, Chr, Start, End, Strand, Length, Status, [Sample Counts]
        if 'Length' not in df.columns:
            logger.warning("Length column not found in counts file. Cannot calculate true TPM. Falling back to CPM.")
            # Fallback to CPM
            count_cols = [c for c in df.columns if c not in ['Geneid', 'Chr', 'Start', 'End', 'Strand', 'Length', 'Status']]
            if not count_cols:
                logger.error("No count columns found.")
                return None
            
            total_counts = df[count_cols].sum(axis=1)
            df['TPM'] = (df[count_cols[0]] / (total_counts + 1e-6)) * 1e6 # CPM approximation if single sample
            # Actually, let's just normalize the first count column as a placeholder if multiple samples
            # But the task implies a matrix. Let's assume single sample per run for now or handle all.
            # Re-calc logic for CPM if no length:
            # CPM = (Count / Total_Counts) * 1e6
            # We will output a column 'TPM' which is actually CPM if length missing, but named TPM for interface
            # Better: Calculate CPM for all sample columns
            for col in count_cols:
                total = df[col].sum()
                df[f"{col}_CPM"] = (df[col] / (total + 1e-6)) * 1e6
            
            output_file = output_dir / f"{accession_id}_tpm.csv"
            df[['Geneid'] + [f"{c}_CPM" for c in count_cols]].to_csv(output_file, index=False)
            logger.warning(f"Saved CPM as TPM approximation for {accession_id} due to missing length data.")
            return output_file

        # Extract Length column
        lengths = df['Length']
        
        # Identify count columns (exclude metadata columns)
        metadata_cols = ['Geneid', 'Chr', 'Start', 'End', 'Strand', 'Length', 'Status']
        count_cols = [c for c in df.columns if c not in metadata_cols]
        
        if not count_cols:
            logger.error("No sample count columns found in featureCounts output.")
            return None

        # Calculate RPK: Count / (Length / 1000)
        # Handle zero length
        lengths_safe = lengths.replace(0, 1)
        rpk = df[count_cols].div(lengths_safe / 1000, axis=0)
        
        # Calculate TPM: (RPK / Sum(RPK)) * 1e6
        tpm = rpk.div(rpk.sum(axis=0), axis=1) * 1e6
        
        # Create output dataframe
        output_df = pd.DataFrame({'Geneid': df['Geneid']})
        for i, col in enumerate(count_cols):
            output_df[f'{col}_TPM'] = tpm[col]
        
        output_file = output_dir / f"{accession_id}_tpm.csv"
        output_df.to_csv(output_file, index=False)
        
        logger.info(f"TPM matrix saved to {output_file}")
        return output_file

    except Exception as e:
        logger.error(f"Error calculating TPM for {accession_id}: {str(e)}")
        return None

def create_manifest_entry_tpm(
    file_path: Path,
    accession_id: str,
    source_bam: Path,
    source_gtf: Path
) -> Dict[str, Any]:
    """Create a manifest entry for the TPM file."""
    checksum = compute_sha256(file_path)
    return {
        "accession_id": accession_id,
        "file_name": file_path.name,
        "file_path": str(file_path),
        "checksum": checksum,
        "source_type": "featurecounts",
        "input_bam": str(source_bam),
        "input_gtf": str(source_gtf),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "provenance": {
            "tool": "featureCounts",
            "version": "subread", # Version determined at runtime ideally
            "output_format": "TPM"
        }
    }

def save_tpm_manifest(manifest_entries: List[Dict[str, Any]], output_path: Path):
    """Save the TPM manifest to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({"manifest_version": "1.0", "entries": manifest_entries}, f, indent=2)
    logger.info(f"TPM manifest saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run featureCounts and generate TPM matrices.")
    parser.add_argument("--bam-dir", type=str, required=True, help="Directory containing BAM files.")
    parser.add_argument("--gtf", type=str, required=True, help="Path to annotation GTF file.")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory for TPM matrices.")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads.")
    parser.add_argument("--mode", type=str, default="real", choices=["real", "synthetic"], help="Run mode.")
    args = parser.parse_args()

    if args.mode == "synthetic":
        logger.info("Synthetic mode active. Skipping featureCounts execution.")
        # Create a dummy flag or just exit cleanly
        return

    # Check prerequisites
    if not check_featurecounts_available():
        logger.error("featureCounts is not available. Cannot proceed.")
        sys.exit(1)

    bam_dir = Path(args.bam_dir)
    gtf_file = Path(args.gtf)
    output_dir = Path(args.output_dir)
    manifest_entries = []

    # Find BAM files
    bam_files = list(bam_dir.glob("*.bam"))
    if not bam_files:
        logger.error(f"No BAM files found in {bam_dir}")
        sys.exit(1)

    logger.info(f"Found {len(bam_files)} BAM files to process.")

    for bam_file in bam_files:
        accession_id = bam_file.stem # e.g., SRR123456.bam -> SRR123456
        
        # Run featureCounts
        counts_file = run_featurecounts(
            bam_file=bam_file,
            gtf_file=gtf_file,
            output_dir=output_dir / "counts",
            accession_id=accession_id,
            threads=args.threads
        )
        
        if counts_file is None:
            logger.warning(f"Skipping TPM generation for {accession_id} due to featureCounts failure.")
            continue

        # Calculate TPM
        tpm_file = calculate_tpm(
            counts_file=counts_file,
            output_dir=output_dir / "count_matrices",
            accession_id=accession_id
        )

        if tpm_file is None:
            logger.warning(f"Failed to generate TPM for {accession_id}.")
            continue

        # Create manifest entry
        entry = create_manifest_entry_tpm(
            file_path=tpm_file,
            accession_id=accession_id,
            source_bam=bam_file,
            source_gtf=gtf_file
        )
        manifest_entries.append(entry)

        # Record provenance
        record_provenance(
            artifact_type=ArtifactType.EXPRESSION_MATRIX,
            artifact_path=str(tpm_file),
            metadata=entry
        )

    if manifest_entries:
        manifest_path = output_dir / "tpm_manifest.json"
        save_tpm_manifest(manifest_entries, manifest_path)
        logger.info(f"Processed {len(manifest_entries)} samples successfully.")
    else:
        logger.warning("No samples were successfully processed.")

if __name__ == "__main__":
    main()
