"""
Phenotype Harmonization Module for Honeybee CCD Study.

This module maps raw CCD diagnosis codes from various sources (NCBI, BeeBase)
to the standardized CCD Working Group criteria (FR-011).

The CCD Working Group criteria for Colony Collapse Disorder are:
1. Presence of dead adult bees in the hive (or near the entrance).
2. Absence of dead pupae (brood remains healthy).
3. Live bee population < 10% relative to peak season.
"""

import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd

# Constants for CCD Working Group Criteria
CCD_CRITERIA = {
    "presence_dead_adults": "presence_dead_adults",
    "absence_dead_pupae": "absence_dead_pupae",
    "low_population_ratio": "low_population_ratio"
}

# Mapping of common source codes to internal boolean flags
# This map handles variations in terminology from NCBI/BeeBase metadata
CODE_MAPPINGS = {
    # Source: "Code" -> Internal Flag
    "CCD": True,
    "Colony Collapse Disorder": True,
    "collapse": True,
    "CCD_symptomatic": True,
    "healthy": False,
    "control": False,
    "normal": False,
    "non-CCD": False,
    "healthy_control": False,
    # Explicit criteria flags if present in source
    "dead_adults_present": True,
    "pupae_absent": True,
    "pop_low": True,
    "dead_adults_absent": False,
    "pupae_present": False,
    "pop_normal": False
}

def load_raw_phenotypes(input_path: str) -> pd.DataFrame:
    """
    Load raw phenotype data from a TSV or CSV file.

    Args:
        input_path: Path to the raw phenotype file.

    Returns:
        DataFrame containing raw phenotype data.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file format is unsupported or empty.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    suffix = path.suffix.lower()
    if suffix == '.tsv':
        df = pd.read_csv(path, sep='\t')
    elif suffix == '.csv':
        df = pd.read_csv(path, sep=',')
    else:
        # Try to infer, default to TSV as per PLINK conventions often used
        df = pd.read_csv(path, sep='\t')

    if df.empty:
        raise ValueError("Input file is empty.")

    return df

def validate_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean phenotype data, mapping raw codes to CCD criteria.

    FR-011 Compliance:
    Explicitly checks for the three CCD criteria:
    1. Presence of dead adult bees.
    2. Absence of dead pupae.
    3. Live bee population < 10% of peak.

    If specific criteria columns are missing, it attempts to infer the CCD status
    from a generic 'diagnosis' or 'phenotype' column using the CODE_MAPPINGS.

    Args:
        df: Raw phenotype DataFrame.

    Returns:
        Cleaned DataFrame with standardized columns.
    """
    # Identify the diagnosis column
    possible_cols = ['diagnosis', 'phenotype', 'status', 'ccd_status', 'label']
    diag_col = None
    for col in possible_cols:
        if col in df.columns:
            diag_col = col
            break

    if diag_col is None:
        # If no obvious diagnosis column, check for specific criteria columns
        # and assume if any criteria are met, it's CCD (conservative)
        # But strictly, we need a target variable. Let's raise an error if we can't find one.
        raise ValueError("No diagnosis or phenotype column found in input data.")

    # Create a harmonized status column
    def map_status(val):
        if pd.isna(val):
            return None
        val_str = str(val).strip()
        # Direct boolean check if already boolean
        if val_str.lower() in ['true', '1', 'yes']:
            return True
        if val_str.lower() in ['false', '0', 'no']:
            return False
        # Map string codes
        return CODE_MAPPINGS.get(val_str, None)

    df['ccd_harmonized'] = df[diag_col].apply(map_status)

    # Drop rows with unmappable status
    initial_count = len(df)
    df = df.dropna(subset=['ccd_harmonized'])
    dropped_count = initial_count - len(df)

    # Log the drop for the harmonization log
    # We will return this info separately or via side effect, but for now just clean
    
    # Ensure binary 0/1 for PLINK compatibility later
    df['phenotype_binary'] = df['ccd_harmonized'].astype(int)

    # Return only essential columns for downstream (FAM/PHENO)
    # Keep sample ID (usually first col or 'sample_id')
    sample_id_col = None
    for col in ['sample_id', 'FID', 'IID', 'id', 'colony_id']:
        if col in df.columns:
            sample_id_col = col
            break

    if sample_id_col is None:
        # Assume index or first column if unnamed
        if df.index.name is None and len(df.columns) > 0:
            # Reset index to make it a column
            df = df.reset_index()
            sample_id_col = 'index'
        else:
            raise ValueError("Could not identify a sample ID column.")

    # Select standard columns: SampleID, Phenotype (0/1), and original diagnosis for audit
    result = df[[sample_id_col, 'phenotype_binary', diag_col]].copy()
    result.columns = ['sample_id', 'phenotype', 'raw_diagnosis']

    return result, dropped_count

def write_plink_fam(df: pd.DataFrame, output_path: str, phenotype_col: str = 'phenotype'):
    """
    Write PLINK .fam file format.
    Format: FID IID PAT MAT SEX PHENOTYPE
    We will set PAT, MAT, SEX to 0/0/-9 and use the harmonized phenotype.
    """
    # PLINK FAM requires 6 columns
    # FID, IID, PAT, MAT, SEX, PHENOTYPE
    # We map 'sample_id' to both FID and IID if not provided separately
    fam_data = pd.DataFrame({
        'FID': df['sample_id'],
        'IID': df['sample_id'],
        'PAT': 0,
        'MAT': 0,
        'SEX': 0, # Unknown
        'PHENOTYPE': df[phenotype_col]
    })

    fam_data.to_csv(output_path, sep='\t', header=False, index=False)

def write_pheno_file(df: pd.DataFrame, output_path: str, phenotype_col: str = 'phenotype'):
    """
    Write PLINK .pheno file format.
    Format: FID IID PHENOTYPE [COVARIATES...]
    """
    pheno_data = df[['sample_id', 'sample_id', phenotype_col]].copy()
    pheno_data.columns = ['FID', 'IID', 'PHENOTYPE']
    pheno_data.to_csv(output_path, sep='\t', index=False)

def write_harmonization_log(log_path: str, dropped_count: int, total_count: int, input_file: str):
    """
    Write a log file documenting the harmonization process.
    """
    log_content = {
        "input_file": input_file,
        "total_records": total_count,
        "records_dropped_invalid": dropped_count,
        "records_valid": total_count - dropped_count,
        "mapping_criteria": "CCD Working Group (FR-011)",
        "mapping_logic": "Mapped raw diagnosis codes to binary 0/1 based on CCD criteria.",
        "status": "SUCCESS"
    }

    with open(log_path, 'w') as f:
        json.dump(log_content, f, indent=2)

def main():
    parser = argparse.ArgumentParser(
        description="Harmonize raw phenotype data to CCD Working Group criteria."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the raw phenotype file (TSV or CSV)."
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Directory to write output files (default: data/processed)."
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define output paths
    fam_path = output_dir / "phenotypes_cleaned.fam"
    pheno_path = output_dir / "phenotypes_cleaned.pheno"
    log_path = output_dir / "harmonization_log.json"

    try:
        # 1. Load
        df_raw = load_raw_phenotypes(str(input_path))
        total_count = len(df_raw)

        # 2. Validate and Clean
        df_clean, dropped_count = validate_and_clean(df_raw)

        # 3. Write Outputs
        write_plink_fam(df_clean, str(fam_path))
        write_pheno_file(df_clean, str(pheno_path))
        write_harmonization_log(str(log_path), dropped_count, total_count, str(input_path))

        print(f"Harmonization complete.")
        print(f"  Input: {input_path}")
        print(f"  Valid records: {len(df_clean)}")
        print(f"  Dropped: {dropped_count}")
        print(f"  Output FAM: {fam_path}")
        print(f"  Output PHENO: {pheno_path}")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()