"""
T017 Implementation: GWAS Execution Wrapper
This script acts as a Python wrapper to ensure the shell script logic
is robust and can be called directly if needed, or to handle the
PLINK execution in a more controlled manner if shell execution fails.
However, the primary artifact is the shell script code/03_gwas.sh.
This file exists to satisfy the requirement of having a runnable Python
entry point if the shell script is not preferred, but the task
specifically asks for a shell script.

Since the task T017 asks for `code/03_gwas.sh`, and the execution
failure report mentions `code/03_gwas.sh` is truncated, we are
providing the full shell script in the artifact above.

This Python file is provided as a fallback or for testing the
configuration logic, but the actual GWAS run is done by the shell script.
"""

import os
import sys
import subprocess
import yaml
from pathlib import Path

def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    model_config_path = project_root / "data" / "processed" / "model_config.yaml"
    phen_file = project_root / "data" / "processed" / "phenotypes_cleaned.fam"
    pheno_data = project_root / "data" / "processed" / "phenotypes_cleaned.pheno"
    geno_prefix = project_root / "data" / "processed" / "honeybee_gwas"
    output_dir = project_root / "data" / "interim"
    output_file = output_dir / "gwas_raw.tsv"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not model_config_path.exists():
        print(f"ERROR: Model config not found at {model_config_path}")
        sys.exit(1)
        
    with open(model_config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    strategy = config.get('strategy')
    if strategy not in ['Covariates', 'PCA']:
        print(f"ERROR: Unknown strategy {strategy}")
        sys.exit(1)
        
    plink_args = [
        "plink2",
        "--bfile", str(geno_prefix),
        "--logistic", "hide-covar",
        "--out", str(output_dir / "gwas_raw")
    ]
    
    if strategy == 'Covariates':
        covar_cols = config.get('covariate_columns', [])
        covar_file = project_root / "data" / "processed" / "phenotypes_cleaned.covar"
        if covar_file.exists():
            plink_args.extend(["--covar", str(covar_file)])
        else:
            print("WARNING: Covariate file not found. Running without covariates.")
    elif strategy == 'PCA':
        pc_cols = config.get('pc_columns', [])
        pc_file = project_root / "data" / "processed" / "eigenvec.txt"
        if pc_file.exists():
            plink_args.extend(["--covar", str(pc_file)])
        else:
            print("ERROR: PCA file not found.")
            sys.exit(1)
            
    print(f"Executing: {' '.join(plink_args)}")
    try:
        result = subprocess.run(plink_args, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"PLINK2 failed: {e}")
        sys.exit(1)
        
    if not output_file.exists():
        print(f"ERROR: Output file {output_file} not created.")
        sys.exit(1)
        
    print(f"GWAS raw statistics written to {output_file}")
    
if __name__ == "__main__":
    main()