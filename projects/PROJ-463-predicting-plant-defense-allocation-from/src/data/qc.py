import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys
import json
import logging
from datetime import datetime

from src.utils.logger import get_logger
from src.utils.config import get_data_path

logger = get_logger(__name__)

def check_replicates(metadata_df: pd.DataFrame, min_replicates: int = 2) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Filter studies to ensure they have at least min_replicates biological replicates.
    
    Args:
        metadata_df: DataFrame containing study metadata with 'replicates' column.
        min_replicates: Minimum number of biological replicates required (default 2).
        
    Returns:
        Tuple of (filtered_df, exclusion_list) where exclusion_list contains dicts
        with 'species' and 'exclusion_reason'.
    """
    exclusion_list = []
    if 'replicates' not in metadata_df.columns:
        logger.warning("Column 'replicates' not found in metadata. Excluding all entries.")
        return pd.DataFrame(), [
            {"species": "unknown", "exclusion_reason": "Missing replicates metadata"}
        ]
    
    valid_df = metadata_df[metadata_df['replicates'] >= min_replicates].copy()
    excluded_df = metadata_df[metadata_df['replicates'] < min_replicates]
    
    for _, row in excluded_df.iterrows():
        species = row.get('species', 'unknown')
        reps = row.get('replicates', 'N/A')
        exclusion_list.append({
            "species": str(species),
            "exclusion_reason": f"Insufficient biological replicates (found {reps}, required >= {min_replicates})"
        })
        
    return valid_df, exclusion_list

def check_metadata_completeness(metadata_df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Filter studies to ensure critical metadata fields (tissue, herbivore type) are present.
    
    Args:
        metadata_df: DataFrame containing study metadata.
        
    Returns:
        Tuple of (filtered_df, exclusion_list).
    """
    exclusion_list = []
    required_fields = ['tissue', 'treatment'] # 'treatment' maps to herbivore type in this context
    
    # Identify rows missing any required field
    mask = pd.Series([True] * len(metadata_df), index=metadata_df.index)
    for field in required_fields:
        if field not in metadata_df.columns:
            logger.warning(f"Required column '{field}' missing from metadata.")
            mask = pd.Series([False] * len(metadata_df), index=metadata_df.index)
            break
        else:
            mask = mask & metadata_df[field].notna() & (metadata_df[field] != "")
    
    valid_df = metadata_df[mask].copy()
    excluded_df = metadata_df[~mask]
    
    for _, row in excluded_df.iterrows():
        species = row.get('species', 'unknown')
        missing_fields = [f for f in required_fields if f not in metadata_df.columns or pd.isna(row.get(f)) or row.get(f) == ""]
        exclusion_list.append({
            "species": str(species),
            "exclusion_reason": f"Missing required metadata: {', '.join(missing_fields)}"
        })
        
    return valid_df, exclusion_list

def run_qc_pipeline(input_manifest_path: Optional[str] = None) -> Dict:
    """
    Run the full QC pipeline on the metadata derived from the input manifest.
    
    Args:
        input_manifest_path: Path to the manifest file (real or synthetic). 
                             If None, attempts to find the latest manifest in data/processed or data/synthetic.
                             
    Returns:
        Dictionary containing the post-QC species list and exclusion details.
    """
    # Determine input path
    if input_manifest_path:
        manifest_path = Path(input_manifest_path)
    else:
        # Fallback logic to find manifest
        data_path = get_data_path()
        processed_path = Path(data_path) / "processed"
        synthetic_path = Path(data_path) / "synthetic"
        
        # Check processed first
        if processed_path.exists():
            manifests = list(processed_path.glob("*manifest*.json"))
            if manifests:
                manifest_path = sorted(manifests)[-1]
            else:
                logger.warning("No manifest found in data/processed. Checking data/synthetic...")
                manifests = list(synthetic_path.glob("*manifest*.json"))
                if manifests:
                    manifest_path = sorted(manifests)[-1]
                else:
                    raise FileNotFoundError("No metadata manifest found in data/processed or data/synthetic. Run T011a or T015 first.")
        else:
            raise FileNotFoundError("data/processed directory not found.")

    logger.info(f"Loading metadata from manifest: {manifest_path}")
    
    # Load manifest
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)
    
    # The manifest might be a list of entries or a single entry object.
    # We need to extract the unique species list and their metadata.
    # Since the manifest structure varies (real vs synthetic), we need to be flexible.
    # For this task, we assume the manifest contains enough info or we load the associated metadata file.
    # However, T011a produces a specific report. Let's check if we can derive from that or the manifest.
    # The task T014 says "Input: Files from T011-real (or synthetic data)".
    # T011a produces `data/processed/metadata_verification_report.json`.
    # Let's try to load the verification report if it exists, as it contains the validated metadata.
    
    verification_report_path = Path(data_path) / "processed" / "metadata_verification_report.json"
    if verification_report_path.exists():
        with open(verification_report_path, 'r') as f:
            verification_data = json.load(f)
        
        # Extract studies from the verification report
        # Assuming structure: { "studies": [ { "species": "...", "replicates": N, "tissue": "...", ... } ] }
        studies = verification_data.get("studies", [])
        if not studies and "mode" in verification_data:
            # Synthetic mode might have different structure
            studies = verification_data.get("synthetic_studies", [])
    else:
        # Fallback: Try to parse the manifest directly if it has study details
        # This is less robust but handles cases where the verification report is missing
        logger.warning("Verification report not found. Attempting to parse manifest directly.")
        if isinstance(manifest_data, list):
            studies = manifest_data
        elif isinstance(manifest_data, dict) and "entries" in manifest_data:
            studies = manifest_data["entries"]
        else:
            # If it's a single entry
            studies = [manifest_data]

    if not studies:
        logger.warning("No studies found in metadata source.")
        return {
            "post_qc_species_list": [],
            "excluded_studies": [],
            "total_input": 0,
            "total_passed": 0
        }

    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(studies)
    
    # Ensure columns exist (fill with defaults if missing)
    if 'species' not in df.columns:
        # Try to infer from other fields or assign unknown
        df['species'] = "unknown"
    if 'replicates' not in df.columns:
        df['replicates'] = 0 # Will trigger exclusion
    if 'tissue' not in df.columns:
        df['tissue'] = None
    if 'treatment' not in df.columns:
        df['treatment'] = None

    all_exclusions = []

    # 1. Check Replicates
    df, exclusions = check_replicates(df, min_replicates=2)
    all_exclusions.extend(exclusions)

    # 2. Check Metadata Completeness (tissue, treatment)
    df, exclusions = check_metadata_completeness(df)
    all_exclusions.extend(exclusions)

    # Construct the output list
    post_qc_species_list = []
    for _, row in df.iterrows():
        post_qc_species_list.append({
            "species": str(row['species']),
            "tissue": row.get('tissue'),
            "treatment": row.get('treatment'),
            "replicates": row.get('replicates')
        })

    # Prepare the final report structure
    output_data = {
        "post_qc_species_list": post_qc_species_list,
        "excluded_studies": all_exclusions,
        "total_input_studies": len(studies),
        "total_passed_studies": len(post_qc_species_list),
        "timestamp": datetime.now().isoformat(),
        "thresholds": {
            "min_replicates": 2,
            "required_metadata_fields": ["tissue", "treatment"]
        }
    }

    # Write output
    output_path = Path(data_path) / "processed" / "post_qc_species_list.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"QC pipeline complete. {len(post_qc_species_list)} species passed. Output saved to {output_path}")
    return output_data

def main():
    """CLI entry point for QC pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run QC pipeline on metadata.")
    parser.add_argument("--input-manifest", type=str, help="Path to input manifest file.")
    args = parser.parse_args()
    
    try:
        result = run_qc_pipeline(input_manifest_path=args.input_manifest)
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"QC pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
