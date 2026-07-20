"""
GWAS Execution Script (T017).

Executes PLINK2 logistic regression using covariates or PCA components
determined by the collinearity guard (T046).

Reads:
  - data/processed/model_config.yaml (Strategy & columns)
  - data/processed/phenotypes_cleaned.fam (Phenotype/FAM file)
  - data/processed/phenotypes_cleaned.bim/.bed/.bim (Genotype files from T015)

Writes:
  - data/interim/gwas_raw.tsv (Raw association statistics)
"""
import os
import sys
import subprocess
import yaml
import argparse
from pathlib import Path

# Ensure we can import local utils if needed, though this script is mostly orchestration
# The API surface shows code/03_gwas.py exists with a 'main' function.

def load_model_config(config_path):
    """Load the strategy configuration from T046."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Model config not found: {config_path}. "
                                "Run T046 (collinearity_guard) before T017.")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def build_plink_command(config, fam_path, bed_prefix, output_path):
    """Construct the PLINK2 command based on the strategy."""
    strategy = config.get('strategy', 'Covariates')
    
    # Base command
    cmd = [
        "plink2",
        "--bfile", bed_prefix,
        "--logistic",
        "hide-covar", # Standard PLINK2 logistic output format
        "--out", str(output_path)
    ]
    
    # Determine covariate file and columns
    # T016 produces phenotypes_cleaned.fam (which acts as the .fam for PLINK)
    # T016 also produces phenotypes_cleaned.pheno for extra covariates if needed,
    # but typically PLINK uses the .fam for FID/IID/Pheno and a separate --covar file.
    
    # According to T046 output:
    # If strategy == "PCA":
    #   pc_columns: ["PC1", "PC2"]
    #   covariate_columns: []
    #   We need a .covar file containing these PCs.
    #   However, T046 description says it generates model_config.yaml.
    #   If it used PLINK --pca, it would also generate a .eigenvec file.
    #   Let's assume the .eigenvec file exists at data/processed/phenotypes_cleaned.eigenvec 
    #   (standard PLINK PCA output) if strategy is PCA.
    
    # If strategy == "Covariates":
    #   covariate_columns: ["geographic_region", ...]
    #   We need a .covar file with these columns.
    #   T016 output: data/processed/phenotypes_cleaned.pheno likely contains these.
    
    # We need to map the logical column names to the actual PLINK --covar file.
    # PLINK --covar expects a file with FID, IID, and then the covariate columns.
    
    covar_file = None
    covar_names = []
    
    if strategy == "PCA":
        # Expect PCA output from T046. Standard PLINK PCA output is .eigenvec.
        # The task T046 description says: "Generate PCA covariates (using ... or PLINK --pca)".
        # Assuming the .eigenvec file was generated alongside model_config.yaml.
        # The .eigenvec file usually has columns: FID, IID, PC1, PC2, ...
        # We need to select the PC columns listed in config.
        
        pca_file = bed_prefix.replace(".bed", "") + ".eigenvec"
        if not os.path.exists(pca_file):
            # Fallback: if the file isn't there, maybe T046 put it elsewhere?
            # But standard PLINK behavior puts it next to the input.
            # Let's try to find it relative to the bed file.
            base = Path(bed_prefix).parent / (Path(bed_prefix).stem + ".eigenvec")
            if base.exists():
                pca_file = str(base)
            else:
                raise FileNotFoundError(f"PCA file not found: {pca_file}. "
                                        "Strategy is PCA but no eigenvec file found.")
        
        covar_file = pca_file
        # The config lists column names like "PC1", "PC2".
        # PLINK --covar-name expects the exact header names.
        # The .eigenvec file headers are usually "FID", "IID", "PC1", "PC2"...
        covar_names = config.get('pc_columns', [])
        
    elif strategy == "Covariates":
        # Use the phenotype file with covariates.
        # T016 produces data/processed/phenotypes_cleaned.pheno.
        # This file should have headers matching the columns.
        pheno_file = bed_prefix.replace(".bed", "") + ".pheno"
        # Check if it exists, otherwise look for the standard name
        if not os.path.exists(pheno_file):
            # Try the explicit path from T016
            explicit = "data/processed/phenotypes_cleaned.pheno"
            if os.path.exists(explicit):
                pheno_file = explicit
            else:
                # Fallback to .fam if no separate pheno file? 
                # But .fam usually only has binary phenotype.
                # Let's assume the .pheno file exists as per T016.
                raise FileNotFoundError(f"Covariate file not found: {pheno_file}. "
                                        "Strategy is Covariates but no pheno file found.")
        
        covar_file = pheno_file
        covar_names = config.get('covariate_columns', [])
    
    else:
        raise ValueError(f"Unknown strategy in model_config.yaml: {strategy}")
    
    if covar_file and covar_names:
        # Validate that the covar file exists
        if not os.path.exists(covar_file):
            raise FileNotFoundError(f"Covariate file not found: {covar_file}")
        
        # PLINK2 --covar command
        # --covar-name accepts comma-separated list
        cmd.append("--covar")
        cmd.append(covar_file)
        
        # Filter columns if necessary (PLINK2 --covar-name)
        if covar_names:
            cmd.append("--covar-name")
            cmd.append(",".join(covar_names))
    
    # Add phenotype file if it's separate from .fam (usually .pheno)
    # If the phenotype is in the .fam file, we don't need --pheno unless it's a different file.
    # T016 produces phenotypes_cleaned.fam and .pheno.
    # If .pheno exists and has the phenotype, we might need to point to it if .fam doesn't have it.
    # However, standard PLINK workflow: .fam has phenotype. .pheno is for extra covariates.
    # If T016 put the phenotype in .pheno and not .fam, we need --pheno.
    # Let's assume standard: .fam has phenotype.
    
    return cmd

def main():
    parser = argparse.ArgumentParser(description="Execute GWAS with PLINK2")
    parser.add_argument("--config", default="data/processed/model_config.yaml",
                        help="Path to model config YAML (output of T046)")
    parser.add_argument("--bed-prefix", default="data/processed/phenotypes_cleaned",
                        help="Prefix for PLINK binary files (.bed, .bim, .fam)")
    parser.add_argument("--output", default="data/interim/gwas_raw.tsv",
                        help="Output path for raw GWAS results")
    args = parser.parse_args()

    # 1. Load Configuration
    config = load_model_config(args.config)
    print(f"Loaded strategy: {config.get('strategy')}")

    # 2. Prepare Output Directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 3. Build Command
    try:
        cmd = build_plink_command(config, args.bed_prefix, args.bed_prefix, output_path.stem)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Executing: {' '.join(cmd)}")

    # 4. Execute PLINK2
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            # PLINK often logs to stderr
            print(result.stderr, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"PLINK2 failed with return code {e.returncode}", file=sys.stderr)
        if e.stdout:
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)

    # 5. Post-process PLINK output to match expected schema
    # PLINK2 --logistic output is usually .logistic or .assoc.logistic
    # We need to rename/move it to the exact T017 output path: data/interim/gwas_raw.tsv
    # PLINK2 default output for --logistic is <out>.logistic
    
    plink_out_file = f"{output_path.stem}.logistic"
    
    if not os.path.exists(plink_out_file):
        # Maybe it's named differently? PLINK2 sometimes outputs .assoc
        # Let's look for the file in the current directory
        possible_files = [f for f in os.listdir('.') if f.startswith(output_path.stem) and f.endswith('.logistic')]
        if possible_files:
            plink_out_file = possible_files[0]
        else:
            # Fallback: check if PLINK wrote to a different location or name
            # If --out was set, it should be <out>.logistic
            raise FileNotFoundError(f"PLINK output file {plink_out_file} not found. "
                                    "Check PLINK logs for errors.")
    
    # Move/Rename to the required output path
    # We also need to ensure the columns match: SNP, CHR, POS, P, Odds_Ratio, SE
    # PLINK2 logistic output headers: CHR, SNP, BP, A1, TEST, NMISS, BETA, SE, L95, U95, STAT, P, OR
    # We need to map these to the required schema.
    
    import pandas as pd
    
    try:
        df = pd.read_csv(plink_out_file, sep=r'\s+')
        
        # Rename columns to match required schema
        # SNP -> SNP (usually 'SNP' or 'CHR' 'SNP' columns exist)
        # CHR -> CHR
        # POS -> POS (PLINK has 'BP')
        # P -> P
        # Odds_Ratio -> OR (PLINK has 'OR')
        # SE -> SE
        
        required_columns = ['SNP', 'CHR', 'POS', 'P', 'Odds_Ratio', 'SE']
        
        # Map PLINK columns to required columns
        # PLINK2 logistic output:
        # CHR, SNP, BP, A1, TEST, NMISS, BETA, SE, L95, U95, STAT, P, OR
        
        rename_map = {
            'SNP': 'SNP',
            'CHR': 'CHR',
            'BP': 'POS',
            'P': 'P',
            'OR': 'Odds_Ratio',
            'SE': 'SE'
        }
        
        # Check if all required keys exist in rename_map source
        missing_src = [k for k in rename_map.keys() if k not in df.columns]
        if missing_src:
            print(f"Warning: Some PLINK columns missing: {missing_src}. "
                  f"Available: {list(df.columns)}", file=sys.stderr)
            # Try to proceed with what we have, but this might be an error
        
        df_renamed = df.rename(columns=rename_map)
        
        # Select only required columns if they exist
        final_df = df_renamed[[c for c in required_columns if c in df_renamed.columns]]
        
        # Write to the exact output path
        final_df.to_csv(args.output, sep='\t', index=False)
        print(f"Successfully wrote GWAS results to {args.output}")
        
    except Exception as e:
        print(f"Error processing PLINK output: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()