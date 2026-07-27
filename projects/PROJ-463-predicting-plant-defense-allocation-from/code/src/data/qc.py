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

def check_replicates(df: pd.DataFrame, min_replicates: int = 2) -> pd.DataFrame:
    """
    Filter studies/samples to ensure at least `min_replicates` biological replicates.
    
    Args:
        df: DataFrame with columns including 'species', 'treatment', 'replicates' (or similar)
        min_replicates: Minimum number of replicates required (default 2)
        
    Returns:
        DataFrame filtered to valid studies, with an 'included' column indicating status.
    """
    if 'replicates' not in df.columns:
        # If replicate count is not pre-calculated, we assume each row is a sample
        # and group by study identifiers to count them.
        # Assuming 'accession_id' or similar unique study ID exists.
        study_id_col = 'accession_id' if 'accession_id' in df.columns else df.columns[0]
        counts = df.groupby(study_id_col).size().reset_index(name='sample_count')
        valid_studies = counts[counts['sample_count'] >= min_replicates][study_id_col].tolist()
        df['included'] = df[study_id_col].isin(valid_studies)
    else:
        # If 'replicates' column exists (e.g., from metadata verification)
        df['included'] = df['replicates'] >= min_replicates
    
    return df[df['included']]

def check_metadata_completeness(df: pd.DataFrame, required_fields: List[str] = None) -> pd.DataFrame:
    """
    Filter studies where required metadata fields (e.g., 'tissue') are present and non-null.
    
    Args:
        df: DataFrame with metadata columns
        required_fields: List of column names that must be non-null (default: ['tissue'])
        
    Returns:
        DataFrame filtered to complete metadata.
    """
    if required_fields is None:
        required_fields = ['tissue']
    
    valid_mask = pd.Series([True] * len(df), index=df.index)
    
    for field in required_fields:
        if field in df.columns:
            valid_mask &= df[field].notna() & (df[field] != '')
        else:
            logger.warning(f"Required field '{field}' not found in DataFrame. Skipping check.")
    
    return df[valid_mask]

def run_qc_pipeline(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    min_replicates: int = 2,
    required_metadata: List[str] = None
) -> Dict:
    """
    Run the full QC pipeline: check replicates and metadata completeness.
    Excludes studies failing criteria and logs reasons.
    
    Args:
        input_path: Path to the input TPM matrix or metadata JSON/CSV.
                    If None, attempts to load from data/processed/metadata_verification_report.json
        output_path: Path to write the post-QC species list JSON.
        min_replicates: Minimum replicates required.
        required_metadata: List of metadata fields that must be present.
        
    Returns:
        Dictionary containing the results summary and the list of excluded items.
    """
    if input_path is None:
        data_dir = get_data_path()
        input_path = Path(data_dir) / "processed" / "metadata_verification_report.json"
    
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Run T011a (verify_metadata) first.")
    
    logger.info(f"Loading metadata from {input_path}")
    
    # Load data - handle both JSON and CSV if necessary
    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
        # Expecting a list of study records or a dict with a 'studies' key
        if isinstance(data, dict) and 'studies' in data:
            records = data['studies']
        elif isinstance(data, list):
            records = data
        else:
            # Fallback: assume single record wrapped
            records = [data]
        
        df = pd.DataFrame(records)
    except json.JSONDecodeError:
        # Try CSV fallback
        df = pd.read_csv(input_path)
    
    # 1. Check Replicates
    df_valid_rep = check_replicates(df, min_replicates=min_replicates)
    excluded_rep = df[~df.index.isin(df_valid_rep.index)]
    
    # 2. Check Metadata Completeness
    df_valid_meta = check_metadata_completeness(df_valid_rep, required_metadata=required_metadata)
    excluded_meta = df_valid_rep[~df_valid_rep.index.isin(df_valid_meta.index)]
    
    # Combine exclusions
    all_excluded = pd.concat([excluded_rep, excluded_meta])
    
    # Prepare output list
    exclusion_list = []
    for _, row in all_excluded.iterrows():
        reason = []
        # Determine reason based on which check failed
        if row.name in excluded_rep.index:
            if 'replicates' in row:
                reason.append(f"Insufficient replicates: {row['replicates']} < {min_replicates}")
            else:
                reason.append(f"Insufficient replicates (count < {min_replicates})")
        
        if row.name in excluded_meta.index:
            for field in (required_metadata or ['tissue']):
                if field in row and (pd.isna(row[field]) or row[field] == ''):
                    reason.append(f"Missing metadata: {field}")
        
        exclusion_list.append({
            "species": row.get('species', 'Unknown'),
            "accession_id": row.get('accession_id', 'Unknown'),
            "exclusion_reason": "; ".join(reason)
        })
    
    # Prepare species list (unique species from valid studies)
    valid_studies = df_valid_meta.copy()
    # Ensure 'species' column exists
    if 'species' not in valid_studies.columns:
        valid_studies['species'] = valid_studies.get('accession_id', 'Unknown')
    
    unique_species = valid_studies['species'].unique().tolist()
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "total_studies_input": len(df),
        "studies_excluded": len(exclusion_list),
        "studies_remaining": len(valid_studies),
        "exclusions": exclusion_list,
        "species_list": unique_species
    }
    
    # Write output
    if output_path is None:
        data_dir = get_data_path()
        output_path = Path(data_dir) / "processed" / "post_qc_species_list.json"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"QC Pipeline Complete. Excluded {len(exclusion_list)} studies. "
                f"Output written to {output_path}")
    logger.info(f"Species list: {unique_species}")
    
    return result

def main():
    """CLI entry point for QC pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run QC on metadata and generate species list.")
    parser.add_argument("--input", type=str, help="Input metadata JSON/CSV path")
    parser.add_argument("--output", type=str, help="Output JSON path for species list")
    parser.add_argument("--min-replicates", type=int, default=2, help="Minimum replicates required")
    parser.add_argument("--metadata-fields", type=str, nargs="+", default=["tissue"], 
                        help="Required metadata fields")
    
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else None
    output_path = Path(args.output) if args.output else None
    
    try:
        run_qc_pipeline(
            input_path=input_path,
            output_path=output_path,
            min_replicates=args.min_replicates,
            required_metadata=args.metadata_fields
        )
        print("QC Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"QC Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
