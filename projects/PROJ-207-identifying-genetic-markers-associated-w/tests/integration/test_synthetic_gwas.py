"""
Integration test for full synthetic GWAS pipeline run (T011).

This test verifies the end-to-end execution of the synthetic pipeline:
1. Ensures synthetic data generation (T009) has produced valid inputs.
2. Runs the alignment and variant calling simulation (T013, T014).
3. Executes the GWAS pipeline (T017).
4. Validates that output files exist and conform to the expected schema.

Prerequisites:
- T009 must have run successfully to generate data/interim/synthetic.vcf
- T013 (simulated FASTQ generation) must be runnable
- T014 (alignment/calling) must be runnable
- T017 (GWAS execution) must be runnable
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import yaml

# Add project root to path for imports if needed, though we rely on scripts
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"

# Expected artifacts from previous tasks
SYNTHETIC_VCF = DATA_DIR / "interim" / "synthetic.vcf"
SYNTHETIC_R1 = DATA_DIR / "interim" / "synthetic_R1.fastq"
SYNTHETIC_R2 = DATA_DIR / "interim" / "synthetic_R2.fastq"
GWAS_RAW_TSV = DATA_DIR / "interim" / "gwas_raw.tsv"
FAMS_FILE = DATA_DIR / "processed" / "synthetic.fam"
BED_FILE = DATA_DIR / "processed" / "synthetic.bed"
BIM_FILE = DATA_DIR / "processed" / "synthetic.bim"

def run_script(script_name: str, args: list = None, check: bool = True) -> subprocess.CompletedProcess:
    """Helper to run a Python script from the code directory."""
    cmd = [sys.executable, str(CODE_DIR / script_name)]
    if args:
        cmd.extend(args)
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
        
    if check and result.returncode != 0:
        raise RuntimeError(f"Script {script_name} failed with code {result.returncode}")
    return result

def run_shell_script(script_name: str, args: list = None, check: bool = True) -> subprocess.CompletedProcess:
    """Helper to run a shell script from the code directory."""
    cmd = ["bash", str(CODE_DIR / script_name)]
    if args:
        cmd.extend(args)
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
        
    if check and result.returncode != 0:
        raise RuntimeError(f"Script {script_name} failed with code {result.returncode}")
    return result

def test_synthetic_pipeline_integration():
    """
    Integration test: Verify the full synthetic pipeline produces GWAS results.
    
    Steps:
    1. Verify T009 output (synthetic.vcf) exists.
    2. Run T013 (generate_simulated_fastq.py) to create FASTQs.
    3. Run T014 (align_call.sh) to generate VCF from FASTQs.
    4. Run T015 (vcf_to_plink.py) to convert to PLINK format.
    5. Run T016 (preprocess_phenotype.py) to prepare phenotypes.
    6. Run T017 (03_gwas.sh) to execute GWAS.
    7. Verify output files exist and have content.
    """
    
    # Step 1: Check prerequisites (T009)
    if not SYNTHETIC_VCF.exists():
        raise FileNotFoundError(
            f"Prerequisite T009 not met: {SYNTHETIC_VCF} does not exist. "
            "Please run code/00_generate_synthetic_data.py first."
        )
    print(f"Found synthetic VCF: {SYNTHETIC_VCF}")

    # Step 2: Run T013 - Generate simulated FASTQ
    # This script reads synthetic.vcf and outputs R1/R2 fastqs using dwgsim
    try:
        run_script("00_generate_simulated_fastq.py")
    except FileNotFoundError:
        # If the script doesn't exist yet, we skip this specific step but note it
        # In a real CI, this would be a failure if the task was claimed done
        if not SYNTHETIC_R1.exists():
            print("Warning: T013 script not found or failed. Skipping FASTQ generation.")
            # We might need to mock this if T013 isn't implemented, but per constraints
            # we assume the pipeline is sequential. If T013 is missing, we can't proceed.
            # For this integration test, we assume T013 is implemented.
            raise
    except RuntimeError as e:
        raise e

    # Step 3: Run T014 - Align and Call Variants
    # This script uses bwa mem and freebayes
    try:
        # T014 accepts input from synthetic fastqs
        run_shell_script("02_align_call.sh", ["--input", "synthetic"])
    except FileNotFoundError:
        raise FileNotFoundError("T014 script (02_align_call.sh) not found.")
    except RuntimeError as e:
        raise e

    # Step 4: Run T015 - VCF to PLINK
    try:
        run_script("utils/vcf_to_plink.py")
    except FileNotFoundError:
        raise FileNotFoundError("T015 script (utils/vcf_to_plink.py) not found.")
    except RuntimeError as e:
        raise e

    # Step 5: Run T016 - Preprocess Phenotypes
    try:
        run_script("utils/preprocess_phenotype.py")
    except FileNotFoundError:
        raise FileNotFoundError("T016 script (utils/preprocess_phenotype.py) not found.")
    except RuntimeError as e:
        raise e

    # Step 6: Run T017 - Execute GWAS
    try:
        run_shell_script("03_gwas.sh")
    except FileNotFoundError:
        raise FileNotFoundError("T017 script (03_gwas.sh) not found.")
    except RuntimeError as e:
        raise e

    # Step 7: Verify Outputs
    # Check that GWAS raw output exists
    if not GWAS_RAW_TSV.exists():
        raise FileNotFoundError(f"GWAS output {GWAS_RAW_TSV} was not generated.")
    
    # Verify file is not empty and has expected header
    with open(GWAS_RAW_TSV, 'r') as f:
        header = f.readline()
        if not header:
            raise ValueError(f"{GWAS_RAW_TSV} is empty.")
        
        # Basic schema check: should contain CHROM, POS, ID, REF, ALT, P, etc.
        expected_cols = ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'P']
        cols = header.strip().split()
        for col in expected_cols:
            if col not in cols:
                raise ValueError(f"Missing expected column '{col}' in GWAS output. Columns: {cols}")
        
        # Check for data rows
        line_count = 1 + sum(1 for _ in f)
        if line_count < 2:
            raise ValueError(f"{GWAS_RAW_TSV} has no data rows.")

    # Verify PLINK files exist
    if not FAMS_FILE.exists():
        raise FileNotFoundError(f"PLINK FAM file {FAMS_FILE} not found.")
    if not BED_FILE.exists():
        raise FileNotFoundError(f"PLINK BED file {BED_FILE} not found.")
    if not BIM_FILE.exists():
        raise FileNotFoundError(f"PLINK BIM file {BIM_FILE} not found.")

    print("Integration test PASSED: Full synthetic pipeline executed successfully.")
    print(f"Generated artifacts: {GWAS_RAW_TSV}, {FAMS_FILE}, {BED_FILE}, {BIM_FILE}")

if __name__ == "__main__":
    test_synthetic_pipeline_integration()
