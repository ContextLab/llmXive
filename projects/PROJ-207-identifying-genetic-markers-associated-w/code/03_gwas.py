"""
T017: GWAS Pipeline Execution - PLINK Logistic Regression Wrapper

This script orchestrates the execution of PLINK for logistic regression
to identify SNPs associated with CCD susceptibility. It constructs the
command based on configuration and ensures the output is written to
the expected path: data/interim/gwas_raw.tsv.

Note: FDR correction is handled separately by T020 (utils/fdr_correction.py).
"""
import os
import sys
import subprocess
import yaml
import argparse
from pathlib import Path

def load_model_config(config_path: str) -> dict:
    """Load pipeline configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def build_plink_command(config: dict, output_dir: Path) -> list:
    """
    Build the PLINK2 command list based on configuration.
    
    Args:
        config: Dictionary containing input paths and parameters.
        output_dir: Directory where output files will be written.
        
    Returns:
        List of command arguments for subprocess.
    """
    cmd = ["plink2"]
    
    # Input files
    cmd.extend(["--bfile", str(config['input']['plink_prefix'])])
    cmd.extend(["--pheno", str(config['input']['phenotype_file'])])
    cmd.extend(["--covar", str(config['input']['covariate_file'])])
    
    # Analysis parameters
    cmd.append("--logistic")
    cmd.append("hide-covar") # Hide covariate coefficients in output for cleaner results
    
    # Phenotype column name (from T062/T016)
    pheno_name = config.get('input', {}).get('phenotype_column', 'CCD_Status')
    cmd.extend(["--pheno-name", pheno_name])
    
    # Output
    output_prefix = output_dir / config['output']['prefix']
    cmd.extend(["--out", str(output_prefix)])
    
    return cmd

def main():
    parser = argparse.ArgumentParser(description="Execute PLINK logistic regression for GWAS (T017)")
    parser.add_argument("--config", type=str, default="code/config/pipeline_config.yaml",
                        help="Path to pipeline configuration YAML")
    parser.add_argument("--output-dir", type=str, default="data/interim",
                        help="Directory for output files")
    args = parser.parse_args()

    # Paths
    config_path = Path(args.config)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load config
    try:
        config = load_model_config(str(config_path))
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Validate inputs exist
    for key in ['plink_prefix', 'phenotype_file', 'covariate_file']:
        path = config['input'][key]
        if not os.path.exists(path):
            print(f"ERROR: Required input file not found: {path}")
            print("Ensure previous steps (T015, T016) have completed successfully.")
            sys.exit(1)

    # Build command
    cmd = build_plink_command(config, output_dir)
    
    print(f"Executing: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: PLINK execution failed with return code {e.returncode}")
        sys.exit(1)

    # Post-process: PLINK outputs `*.assoc.logistic`. Rename to `gwas_raw.tsv` as per spec.
    output_prefix = output_dir / config['output']['prefix']
    source_file = output_prefix.with_suffix('.assoc.logistic')
    target_file = output_prefix.with_suffix('.tsv')

    if source_file.exists():
        source_file.rename(target_file)
        print(f"SUCCESS: Raw association statistics written to {target_file}")
    else:
        # Fallback if PLINK version outputs differently, though standard is .assoc.logistic
        # Check for .logistic
        alt_source = output_prefix.with_suffix('.logistic')
        if alt_source.exists():
            alt_source.rename(target_file)
            print(f"SUCCESS: Raw association statistics written to {target_file} (from .logistic)")
        else:
            print("ERROR: PLINK did not produce expected output file.")
            sys.exit(1)

if __name__ == "__main__":
    main()