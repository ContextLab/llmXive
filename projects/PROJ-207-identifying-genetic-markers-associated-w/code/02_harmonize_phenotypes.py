"""
Phenotype Harmonization for Honeybee CCD Study (FR-011).

This module maps CCD diagnosis codes from raw metadata to the CCD Working Group
criteria (FR-011) and produces a PLINK-compatible .fam file with the harmonized
phenotype in column 6.

It enforces the Varroa covariate coverage gate: if <80% of samples have Varroa
data, the pipeline halts with ERR_VARROA_COVARIATE_MISSING.

Inputs:
    - data/processed/ncbi_metadata_only.json: Metadata from T012a (T012a)
    - data/raw/fastq_files/: Directory containing FASTQ files (T012b)

Outputs:
    - data/interim/phenotypes_harmonized.fam: PLINK .fam file with CCD status (0/1)
    - data/interim/harmonization_log.json: Detailed log of mapping decisions and coverage stats
"""

import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd

# Error codes as defined in tasks.md
ERR_VARROA_COVARIATE_MISSING = "ERR_VARROA_COVARIATE_MISSING"
ERR_SAMPLE_SIZE_INSUFFICIENT = "ERR_SAMPLE_SIZE_INSUFFICIENT"

# CCD Working Group (2007) Criteria Mapping
# 'Colony collapse' = dead adult bees, no dead pupae, < 10% live bee population.
# Map 'CCD', 'Colony Collapse' -> 1
# Map 'Healthy', 'Control' -> 0
# 'colony loss' -> ambiguous (exclude unless mapped)
CCD_POSITIVE_TERMS = ['CCD', 'Colony Collapse', 'Colony Collapse Disorder']
CCD_NEGATIVE_TERMS = ['Healthy', 'Control', 'Non-CCD']
AMBIGUOUS_TERMS = ['colony loss', 'unknown', 'missing']

def load_raw_phenotypes(metadata_path: Path) -> pd.DataFrame:
    """
    Load metadata from T012a and extract phenotype-relevant fields.
    """
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    with open(metadata_path, 'r') as f:
        data = json.load(f)

    # Expected structure based on T012a output:
    # {
    #   "samples": [
    #     {
    #       "sample_accession": "...",
    #       "attributes": {
    #         "ccd_status": "CCD",
    #         "varroa_load": 12.5,
    #         "geographic_region": "North America",
    #         "sampling_year": 2015
    #       }
    #     },
    #     ...
    #   ]
    # }
    
    samples = data.get("samples", [])
    if not samples:
        raise ValueError("No samples found in metadata file.")

    records = []
    for s in samples:
        attrs = s.get("attributes", {})
        records.append({
            "sample_id": s.get("sample_accession", "UNKNOWN"),
            "ccd_status": attrs.get("ccd_status", "unknown"),
            "varroa_load": attrs.get("varroa_load"),
            "geographic_region": attrs.get("geographic_region", "Unknown"),
            "sampling_year": attrs.get("sampling_year", 0)
        })

    df = pd.DataFrame(records)
    return df

def validate_and_clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Map CCD diagnosis codes to binary phenotype (1=CCD, 0=Healthy).
    Flag ambiguous codes and calculate Varroa coverage.

    Returns:
        - Cleaned DataFrame with 'phenotype' column (1, 0, or -9 for missing)
        - Log dictionary with stats
    """
    log = {
        "total_samples": len(df),
        "ccd_mapped": 0,
        "healthy_mapped": 0,
        "ambiguous": 0,
        "varroa_coverage": 0.0,
        "varroa_count": 0,
        "ambiguous_ids": []
    }

    def map_status(status):
        if pd.isna(status):
            return -9, "missing"
        status_str = str(status).strip()
        if any(term.lower() in status_str.lower() for term in CCD_POSITIVE_TERMS):
            return 1, "ccd"
        if any(term.lower() in status_str.lower() for term in CCD_NEGATIVE_TERMS):
            return 0, "healthy"
        return -9, "ambiguous"

    # Apply mapping
    df['phenotype'], df['map_reason'] = zip(*df['ccd_status'].apply(map_status))

    # Calculate Varroa coverage
    df['has_varroa'] = ~df['varroa_load'].isna()
    log['varroa_count'] = int(df['has_varroa'].sum())
    log['varroa_coverage'] = log['varroa_count'] / log['total_samples'] if log['total_samples'] > 0 else 0.0

    # Log counts
    log['ccd_mapped'] = int((df['phenotype'] == 1).sum())
    log['healthy_mapped'] = int((df['phenotype'] == 0).sum())
    ambiguous_mask = df['phenotype'] == -9
    log['ambiguous'] = int(ambiguous_mask.sum())
    log['ambiguous_ids'] = df.loc[ambiguous_mask, 'sample_id'].tolist()

    return df, log

def check_varroa_gate(df: pd.DataFrame, log: dict) -> None:
    """
    Enforce the Varroa coverage gate.
    If < 80% of samples have Varroa data, exit with ERR_VARROA_COVARIATE_MISSING.
    """
    if log['varroa_coverage'] < 0.80:
        print(f"ERROR: Varroa coverage ({log['varroa_coverage']:.2%}) is below 80% threshold.", file=sys.stderr)
        print(f"Samples with Varroa: {log['varroa_count']}/{log['total_samples']}", file=sys.stderr)
        sys.exit(ERR_VARROA_COVARIATE_MISSING)

def write_plink_fam(df: pd.DataFrame, output_path: Path) -> None:
    """
    Write PLINK .fam file.
    PLINK .fam format:
    1. Family ID
    2. Individual ID
    3. Paternal ID (0)
    4. Maternal ID (0)
    5. Sex (0=unknown)
    6. Phenotype (1=control, 2=case, -9=missing)
    
    We map: CCD (1) -> 2, Healthy (0) -> 1, Missing (-9) -> -9
    """
    fam_data = df.copy()
    fam_data['fam_id'] = fam_data['sample_id']
    fam_data['ind_id'] = fam_data['sample_id']
    fam_data['pat_id'] = 0
    fam_data['mat_id'] = 0
    fam_data['sex'] = 0
    
    # Map phenotype: 1 (CCD) -> 2, 0 (Healthy) -> 1, -9 -> -9
    def plink_pheno(p):
        if p == 1: return 2
        if p == 0: return 1
        return -9

    fam_data['phenotype'] = fam_data['phenotype'].apply(plink_pheno)

    fam_data[['fam_id', 'ind_id', 'pat_id', 'mat_id', 'sex', 'phenotype']].to_csv(
        output_path, sep='\t', header=False, index=False
    )

def write_pheno_file(df: pd.DataFrame, output_path: Path) -> None:
    """
    Write a separate phenotype file for PLINK covariates if needed.
    Format: FID IID PHENO COV1 COV2 ...
    """
    pheno_data = df.copy()
    pheno_data['FID'] = pheno_data['sample_id']
    pheno_data['IID'] = pheno_data['sample_id']
    # Map phenotype for PLINK
    pheno_data['PHENO'] = pheno_data['phenotype'].apply(lambda p: 2 if p == 1 else (1 if p == 0 else -9))
    
    # Include covariates
    covariates = ['varroa_load', 'geographic_region', 'sampling_year']
    # Ensure columns exist
    for c in covariates:
        if c not in pheno_data.columns:
            pheno_data[c] = None

    cols = ['FID', 'IID', 'PHENO'] + covariates
    pheno_data[cols].to_csv(output_path, sep='\t', index=False)

def write_harmonization_log(log: dict, output_path: Path) -> None:
    """Write detailed log of harmonization process."""
    with open(output_path, 'w') as f:
        json.dump(log, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Harmonize CCD phenotypes from NCBI metadata.")
    parser.add_argument("--input", required=True, help="Path to ncbi_metadata_only.json (from T012a)")
    parser.add_argument("--output-dir", type=Path, default=Path("data/interim"), help="Output directory for .fam and logs")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading metadata from {input_path}...")
    try:
        df = load_raw_phenotypes(input_path)
    except Exception as e:
        print(f"ERROR: Failed to load metadata: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(df)} samples. Validating and mapping...")
    df, log = validate_and_clean(df)

    print(f"Varroa Coverage: {log['varroa_coverage']:.2%} ({log['varroa_count']}/{log['total_samples']})")
    check_varroa_gate(df, log)

    fam_path = output_dir / "phenotypes_harmonized.fam"
    print(f"Writing PLINK .fam to {fam_path}...")
    write_plink_fam(df, fam_path)

    pheno_path = output_dir / "phenotypes_cleaned.fam" # Also write as .fam for downstream compatibility
    write_pheno_file(df, pheno_path)

    log_path = output_dir / "harmonization_log.json"
    write_harmonization_log(log, log_path)

    print("Harmonization complete.")
    print(f"  - CCD samples: {log['ccd_mapped']}")
    print(f"  - Healthy samples: {log['healthy_mapped']}")
    print(f"  - Ambiguous/Excluded: {log['ambiguous']}")
    print(f"  - Output: {fam_path}")

if __name__ == "__main__":
    main()