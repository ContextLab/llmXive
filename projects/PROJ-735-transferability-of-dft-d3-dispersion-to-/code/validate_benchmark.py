"""
Validation script for the IL-Benchmark dataset.
Ensures each record has a valid reference energy and a unique pair identifier.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def validate_benchmark_records():
    """
    Reads data/raw/metadata.csv and ensures each row contains a non-null
    reference_energy and a unique pair_id.
    """
    input_path = paths.data("raw", "metadata.csv")
    log_path = paths.code("validation.log")
    output_path = paths.data("processed", "validated_metadata.csv")

    if not input_path.exists():
        log.error(f"Input metadata file not found: {input_path}")
        raise FileNotFoundError(f"Input metadata file not found: {input_path}")

    log.info(f"Reading benchmark metadata from {input_path}")
    df = pd.read_csv(input_path)

    # 1. Identify records with missing reference energy
    missing_energy_mask = df["reference_energy"].isna()
    
    # 2. Identify records with non-unique pair_id
    # keep=False marks all occurrences of duplicates as True
    duplicate_id_mask = df.duplicated(subset=["pair_id"], keep=False)

    # Combine masks to find all rows to omit
    omit_mask = missing_energy_mask | duplicate_id_mask
    omitted_df = df[omit_mask]
    valid_df = df[~omit_mask].copy()

    # Log violations
    with open(log_path, "w") as log_f:
        if omitted_df.empty:
            log_f.write("No records omitted during validation.\n")
            log.info("Validation successful: No records omitted.")
        else:
            log_f.write("Omitted records (validation failures):\n")
            for idx, row in omitted_df.iterrows():
                reasons = []
                if pd.isna(row.get("reference_energy")):
                    reasons.append("missing reference_energy")
                if df["pair_id"].duplicated(keep=False).loc[idx]:
                    reasons.append("duplicate pair_id")
                
                pair_id = row.get("pair_id", "UNKNOWN")
                log_f.write(f"Row {idx} (pair_id={pair_id}): {', '.join(reasons)}\n")
            
            log.warning(f"Validation complete: {len(omitted_df)} records omitted. See {log_path} for details.")

    # Write cleaned metadata
    output_path.parent.mkdir(parents=True, exist_ok=True)
    valid_df.to_csv(output_path, index=False)
    log.info(f"Cleaned metadata written to {output_path} ({len(valid_df)} records).")

if __name__ == "__main__":
    try:
        validate_benchmark_records()
    except Exception as e:
        log.critical(f"Benchmark validation failed: {e}")
        exit(1)