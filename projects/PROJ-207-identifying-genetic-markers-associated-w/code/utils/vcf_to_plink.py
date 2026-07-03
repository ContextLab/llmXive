"""
T015: Convert VCF to PLINK format.

Reads data/interim/variants.vcf and outputs PLINK files:
- data/processed/synthetic.fam
- data/processed/synthetic.bim
- data/processed/synthetic.bed

Requires PLINK 1.9 or 2.0.
"""
import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

INPUT_VCF = INTERIM_DIR / "variants.vcf"
OUTPUT_PREFIX = PROCESSED_DIR / "synthetic"

def main():
    if not INPUT_VCF.exists():
        print(f"Error: Input VCF not found: {INPUT_VCF}")
        print("Please run code/02_align_call.sh first (T014) or generate synthetic data.")
        sys.exit(1)

    # Check for plink
    plink_cmd = None
    try:
        subprocess.run(["plink", "--version"], capture_output=True, check=True)
        plink_cmd = "plink"
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Try plink2
        try:
            subprocess.run(["plink2", "--version"], capture_output=True, check=True)
            plink_cmd = "plink2"
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: PLINK (1.9 or 2.0) not found in PATH.")
            sys.exit(1)

    print(f"Converting VCF to PLINK format using {plink_cmd}...")
    
    cmd = [
        plink_cmd,
        "--vcf", str(INPUT_VCF),
        "--make-bed",
        "--out", str(OUTPUT_PREFIX)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    if result.returncode != 0:
        print(f"PLINK conversion failed: {result.stderr}")
        sys.exit(1)

    # Verify outputs
    fam_file = f"{OUTPUT_PREFIX}.fam"
    bim_file = f"{OUTPUT_PREFIX}.bim"
    bed_file = f"{OUTPUT_PREFIX}.bed"
    
    if not (os.path.exists(fam_file) and os.path.exists(bim_file) and os.path.exists(bed_file)):
        print("Error: PLINK output files not generated.")
        print(f"Expected: {fam_file}, {bim_file}, {bed_file}")
        sys.exit(1)

    print(f"Successfully converted to PLINK format: {OUTPUT_PREFIX}")
    print(f"Output files created:")
    print(f"  - {fam_file}")
    print(f"  - {bim_file}")
    print(f"  - {bed_file}")

if __name__ == "__main__":
    main()