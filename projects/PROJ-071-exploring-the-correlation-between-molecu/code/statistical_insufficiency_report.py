"""
Statistical Insufficiency Artifact Generation (Task T021d).

Generates the specific artifacts required when the Statistical Gate fails (N < 30 in standard_subset).

Artifacts:
1. data/processed/statistical_insufficiency_report.md
2. data/processed/full_processed_state.csv
3. data/processed/analysis_log.txt
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

# Import shared logging utilities from the central module
from logging_config import get_logger, log_operation, handle_pipeline_exception

# Import error handlers
from error_handlers import StatisticalInsufficiencyError

# Project root resolution
def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Traverse up to find the project root (usually where 'data' and 'code' are siblings)
    # Assuming structure: projects/PROJ-.../code/statistical_insufficiency_report.py
    # We look for the 'data' directory relative to the project root.
    # A safe bet is to go up 2 levels from code/ if 'data' exists there.
    potential_root = current.parent.parent
    if (potential_root / "data").exists():
        return potential_root
    # Fallback: search up
    for parent in current.parents:
        if (parent / "data").exists() and (parent / "code").exists():
            return parent
    return Path.cwd()

def generate_insufficiency_report(
    n_count: int,
    reason: str,
    decision: str = "Skip Analysis",
    output_dir: Optional[Path] = None
) -> Path:
    """
    Generate the statistical insufficiency report (Markdown).
    
    Args:
        n_count: The number of records found.
        reason: The specific reason for insufficiency.
        decision: The decision made (e.g., "Skip Analysis").
        output_dir: Directory to save the report. Defaults to data/processed/.
        
    Returns:
        Path to the generated report.
    """
    if output_dir is None:
        output_dir = get_project_root() / "data" / "processed"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = output_dir / "statistical_insufficiency_report.md"
    
    timestamp = datetime.utcnow().isoformat()
    
    content = f"""# Statistical Insufficiency Report

**Generated**: {timestamp}
**Status**: Gate Failed (Statistical)

## Summary
- **Record Count (N)**: {n_count}
- **Reason**: {reason}
- **Decision**: {decision}

## Details
The statistical gate requires a minimum of 30 records in the standard condition subset 
to perform valid correlation analysis and regression modeling. The current dataset 
contains only {n_count} records, which is below the required threshold.

Consequently, the analysis pipeline has been halted to prevent spurious statistical 
inferences. No regression models were trained, and no correlation coefficients were 
calculated for this run.

## Recommendation
1. Verify the data ingestion and standardization steps (T012, T020).
2. Check if the 'Standard' condition filter (25°C, pH 7.4) is too restrictive.
3. If possible, expand the dataset or relax the condition criteria while documenting 
   the methodological change.
"""
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    logging.info(f"Generated statistical insufficiency report: {report_path}")
    return report_path

def generate_full_processed_state(
    records: list[dict[str, Any]],
    included_indices: set[int],
    output_dir: Optional[Path] = None
) -> Path:
    """
    Generate the full processed state CSV.
    
    This file contains ALL records with an `is_included` boolean and `derivation_source` string.
    
    Args:
        records: List of all processed record dictionaries.
        included_indices: Set of indices that were included in the standard subset.
        output_dir: Directory to save the CSV.
        
    Returns:
        Path to the generated CSV.
    """
    if output_dir is None:
        output_dir = get_project_root() / "data" / "processed"
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / "full_processed_state.csv"
    
    # Schema: smiles, is_included, derivation_source, ...other fields
    # We assume 'smiles' is a key in the records. If not, we use a placeholder or first key.
    
    import csv
    
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        # Header
        # We need to ensure 'is_included' and 'derivation_source' are present
        # and that 'smiles' (or equivalent) is present.
        # Let's construct the header dynamically but enforce the required columns.
        
        # Base required columns
        required_cols = ["smiles", "is_included", "derivation_source"]
        
        # Collect all other keys from the first record if it exists
        other_keys = set()
        if records:
            for key in records[0].keys():
                if key not in required_cols:
                    other_keys.add(key)
        
        # Sort other keys for determinism
        other_keys = sorted(other_keys)
        
        header = required_cols + other_keys
        writer.writerow(header)
        
        for i, record in enumerate(records):
            row = []
            # Required fields
            smiles = record.get("smiles", "")
            is_included = i in included_indices
            derivation_source = "standard_subset" if is_included else "excluded_by_gate"
            
            row.append(smiles)
            row.append(str(is_included).lower()) # CSV boolean usually 'true'/'false' or 1/0, but string is safer
            row.append(derivation_source)
            
            # Other fields
            for key in other_keys:
                val = record.get(key, "")
                # Handle None or complex objects
                if val is None:
                    val = ""
                elif isinstance(val, (list, dict)):
                    val = json.dumps(val)
                row.append(val)
            
            writer.writerow(row)
            
    logging.info(f"Generated full processed state: {csv_path}")
    return csv_path

def generate_analysis_log(
    excluded_reason: str = "Arrhenius normalization excluded due to statistical insufficiency",
    output_dir: Optional[Path] = None
) -> Path:
    """
    Generate the analysis log documenting the exclusion of Arrhenius normalization.
    
    Args:
        excluded_reason: The reason for exclusion.
        output_dir: Directory to save the log.
        
    Returns:
        Path to the generated log file.
    """
    if output_dir is None:
        output_dir = get_project_root() / "data" / "processed"
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = output_dir / "analysis_log.txt"
    
    timestamp = datetime.utcnow().isoformat()
    
    content = f"""Analysis Execution Log
======================
Timestamp: {timestamp}
Status: ABORTED (Statistical Gate Failure)

Events:
- Data Availability Gate: PASSED (or FAILED previously, see gate_status.json)
- Statistical Gate: FAILED (N < 30 in standard_subset)
- Action: Excluded Arrhenius normalization and regression analysis.
- Reason: {excluded_reason}

Details:
The pipeline detected insufficient data points in the standard condition subset 
(25°C, pH 7.4). To maintain statistical validity, the analysis step was skipped.
No regression models (MLR or LASSO) were fitted. No correlation matrices were computed.
"""
    
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    logging.info(f"Generated analysis log: {log_path}")
    return log_path

def main() -> None:
    """
    Main entry point for generating statistical insufficiency artifacts.
    
    This function is designed to be called when a StatisticalInsufficiencyError 
    is caught, or to be run manually to generate the artifacts if the state is known.
    For T021d, we assume the caller provides the necessary context or we read 
    from the latest gate status if available.
    """
    logger = get_logger("statistical_insufficiency_report")
    log_operation("start_statistical_insufficiency_generation")
    
    try:
        project_root = get_project_root()
        gate_status_path = project_root / "data" / "gate_status.json"
        processed_dir = project_root / "data" / "processed"
        
        # Determine N and Reason
        # If gate_status.json exists and says FAIL, we might get info there.
        # However, the specific "Statistical" failure might be distinct from "Data Availability".
        # The task T021d is specifically for when T020 raises StatisticalInsufficiencyError.
        # We will attempt to read the most recent state or use defaults if not found.
        
        n_count = 0
        reason = "Insufficient standard condition records"
        
        # Try to load gate status if it exists
        if gate_status_path.exists():
            try:
                with open(gate_status_path, "r", encoding="utf-8") as f:
                    gate_data = json.load(f)
                    # If it's a statistical failure, it might be in a specific field or we infer
                    if gate_data.get("status") == "FAIL":
                        # Check if it's a data availability failure or statistical
                        # T020 specifically checks N < 30 in standard_subset.
                        # We assume the error handler passed this info, but if not, we use defaults.
                        reason = gate_data.get("reason", reason)
                        # Sometimes N is stored
                        if "N" in gate_data:
                            n_count = gate_data["N"]
            except (json.JSONDecodeError, KeyError) as e:
                logging.warning(f"Could not parse gate_status.json: {e}")
        
        # If we don't have the exact N for the standard subset, we might need to 
        # read the standard_subset.csv if it was partially written, or rely on the error context.
        # For this task, we assume the context is passed or we use the gate status N.
        # If the gate failed at T020, the N in gate_status.json might be the standard subset N.
        
        # Generate Artifacts
        # 1. Report
        generate_insufficiency_report(n_count, reason, output_dir=processed_dir)
        
        # 2. Full Processed State
        # We need the records. If standard_subset.csv was not fully written, 
        # we might need to load from merged_drugs.csv and re-filter or read from a temp file.
        # However, T020 is supposed to generate full_processed_state.csv BEFORE raising the error?
        # The task says: "Generate ... full_processed_state.csv ... containing all records".
        # Let's try to load the merged dataset if available, or an empty list if not.
        
        merged_path = project_root / "data" / "processed" / "merged_drugs.csv"
        all_records = []
        included_indices = set()
        
        if merged_path.exists():
            try:
                import pandas as pd
                df = pd.read_csv(merged_path)
                # We need to know which ones were in the standard subset.
                # If T020 failed before writing standard_subset, we might not have the exact list.
                # But T020 logic: "If resulting standard_subset has N < 30 ... generate full_processed_state.csv".
                # This implies T020 *should* have the data. Since T020 failed to write, we might be in a recovery state.
                # For T021d, we generate the artifacts based on the *current* state.
                # If we can't determine inclusion, we mark all as excluded or try to infer from standard_subset.csv if it exists.
                
                std_path = project_root / "data" / "processed" / "standard_subset.csv"
                if std_path.exists():
                    std_df = pd.read_csv(std_path)
                    # Find intersection
                    # This is tricky if IDs aren't unique. Assuming smiles is unique enough for this check.
                    std_smiles = set(std_df['smiles'].astype(str))
                    for idx, row in df.iterrows():
                        smiles = str(row['smiles'])
                        if smiles in std_smiles:
                            included_indices.add(idx)
                            all_records.append(row.to_dict())
                        else:
                            all_records.append(row.to_dict())
                else:
                    # If standard_subset wasn't saved, we assume all are excluded for the purpose of this report
                    # or we just list all as excluded.
                    for idx, row in df.iterrows():
                        all_records.append(row.to_dict())
            except Exception as e:
                logging.warning(f"Could not load merged_drugs.csv for full_processed_state: {e}")
        else:
            logging.warning("merged_drugs.csv not found. Generating empty/full_processed_state.")
        
        generate_full_processed_state(all_records, included_indices, output_dir=processed_dir)
        
        # 3. Analysis Log
        generate_analysis_log(output_dir=processed_dir)
        
        log_operation("complete_statistical_insufficiency_generation")
        
    except Exception as e:
        handle_pipeline_exception(e, "statistical_insufficiency_generation")
        raise

if __name__ == "__main__":
    main()