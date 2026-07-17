import logging
import pandas as pd
from pathlib import Path
from typing import List, Optional, Tuple

from src.utils.logging_config import setup_logging

# Define the keywords that indicate DFT/Simulation data
DFT_KEYWORDS = ['DFT', 'Calculated', 'Simulation']
MATERIALS_PROJECT_TARGET = 'Materials Project'

logger = logging.getLogger(__name__)

def is_dft_entry(row: pd.Series) -> bool:
    """
    Check if a single row represents a DFT/Calculated/Simulation entry.
    
    Returns True if:
    - 'source_type' column (case-insensitive) contains any of DFT_KEYWORDS
    - 'target_source' column (case-insensitive) equals 'Materials Project'
    
    Returns False otherwise.
    """
    # Check source_type
    source_type = str(row.get('source_type', '')).lower()
    for keyword in DFT_KEYWORDS:
        if keyword.lower() in source_type:
            return True
    
    # Check target_source
    target_source = str(row.get('target_source', '')).lower()
    if target_source == MATERIALS_PROJECT_TARGET.lower():
        return True
        
    return False

def filter_dft_entries(
    df: pd.DataFrame,
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    log_excluded: bool = True
) -> Tuple[pd.DataFrame, List[dict]]:
    """
    Filter out DFT/Calculated/Simulation entries from the dataset.
    
    Args:
        df: Input DataFrame containing alloy data.
        input_path: Optional path to the input CSV (for logging context).
        output_path: Optional path to save the filtered CSV.
        log_excluded: If True, log details of excluded entries.
        
    Returns:
        Tuple of (filtered_df, list_of_excluded_entries_metadata)
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Nothing to filter.")
        return df, []

    # Identify DFT entries
    dft_mask = df.apply(is_dft_entry, axis=1)
    excluded_indices = df.index[dft_mask].tolist()
    excluded_count = len(excluded_indices)
    total_count = len(df)
    
    # Prepare excluded entries metadata for logging/reporting
    excluded_entries = []
    if log_excluded and excluded_count > 0:
        excluded_df = df.loc[excluded_indices]
        for idx, row in excluded_df.iterrows():
            reason = []
            source_type = str(row.get('source_type', ''))
            target_source = str(row.get('target_source', ''))
            
            if any(kw.lower() in source_type.lower() for kw in DFT_KEYWORDS):
                reason.append(f"source_type contains DFT keyword: '{source_type}'")
            if target_source.lower() == MATERIALS_PROJECT_TARGET.lower():
                reason.append(f"target_source is '{MATERIALS_PROJECT_TARGET}'")
            
            excluded_entries.append({
                'index': int(idx),
                'composition': row.get('composition', 'N/A'),
                'source_type': source_type,
                'target_source': target_source,
                'reason': "; ".join(reason)
            })

    # Filter the DataFrame
    filtered_df = df[~dft_mask].reset_index(drop=True)
    
    # Log summary
    logger.info(f"Filtered {excluded_count} DFT/Calculated/Simulation entries from {total_count} total entries.")
    logger.info(f"Remaining entries: {len(filtered_df)} ({len(filtered_df)/total_count*100:.2f}%)")
    
    if log_excluded and excluded_count > 0:
        logger.info("Excluded entries details:")
        for entry in excluded_entries:
            logger.info(f"  - Index {entry['index']}: {entry['composition']} | Reason: {entry['reason']}")
    
    # Save to disk if output_path is provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        filtered_df.to_csv(output_path, index=False)
        logger.info(f"Filtered dataset saved to: {output_path}")
        
        # Also save a JSON log of excluded entries for audit trail
        excluded_log_path = output_path.with_suffix('.excluded_log.json')
        import json
        with open(excluded_log_path, 'w') as f:
            json.dump(excluded_entries, f, indent=2)
        logger.info(f"Excluded entries log saved to: {excluded_log_path}")

    return filtered_df, excluded_entries

def main():
    """
    Main entry point for the DFT filter script.
    Expects input from a processed CSV file (e.g., from T020) and outputs a filtered CSV.
    """
    setup_logging()
    
    # Default paths relative to project root
    # Assuming this runs from project root or code/
    project_root = Path(__file__).resolve().parent.parent.parent
    input_file = project_root / 'data' / 'processed' / 'alloys_normalized.csv'
    output_file = project_root / 'data' / 'processed' / 'alloys_filtered.csv'
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T020 (unit_normalizer) has run and produced the normalized CSV.")
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    logger.info(f"Loading data from: {input_file}")
    df = pd.read_csv(input_file)
    
    logger.info(f"Loaded {len(df)} rows. Applying DFT filter...")
    filtered_df, excluded_entries = filter_dft_entries(
        df,
        input_path=input_file,
        output_path=output_file,
        log_excluded=True
    )
    
    logger.info("DFT filtering completed successfully.")
    return filtered_df

if __name__ == "__main__":
    main()
