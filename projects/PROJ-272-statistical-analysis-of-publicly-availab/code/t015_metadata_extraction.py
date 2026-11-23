"""
T015: Metadata Extraction
Parses cognitive status (Control, MCI, AD) from ADReSS headers and generates
specific reason codes for excluded records.
"""
import logging
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
from config import get_path

# Configure logging
logger = logging.getLogger(__name__)

def parse_cognitive_status_from_filename(filename: str) -> str:
    """
    Parse cognitive status from ADReSS filename conventions.
    ADReSS filenames typically follow: <ID>_<group>.txt or similar.
    Common patterns: 'p01_control.txt', 'p02_mci.txt', 'p03_ad.txt'
    
    Args:
        filename: The filename of the transcript record
        
    Returns:
        One of 'Control', 'MCI', 'AD', or 'Unknown' if pattern doesn't match
    """
    filename_lower = filename.lower()
    
    # Try to match common ADReSS naming patterns
    if re.search(r'control|cnt', filename_lower):
        return 'Control'
    elif re.search(r'mci|mild', filename_lower):
        return 'MCI'
    elif re.search(r'\bad\b|dementia', filename_lower):
        return 'AD'
    else:
        # Fallback: try to extract from common ID patterns if available
        # Some datasets use prefixes like 'C_' for control, 'M_' for MCI, 'A_' for AD
        if filename_lower.startswith('c_') or filename_lower.startswith('control_'):
            return 'Control'
        elif filename_lower.startswith('m_') or filename_lower.startswith('mci_'):
            return 'MCI'
        elif filename_lower.startswith('a_') or filename_lower.startswith('ad_'):
            return 'AD'
        
    return 'Unknown'

def generate_exclusion_reason_code(record: Dict[str, Any], reason_type: str, details: str = "") -> str:
    """
    Generate a specific reason code for excluded records.
    
    Args:
        record: The record being excluded
        reason_type: The type of exclusion (e.g., 'NULL_LABEL', 'SHORT_TEXT', 'UNKNOWN_STATUS')
        details: Additional details about the exclusion
        
    Returns:
        A formatted reason code string
    """
    participant_id = record.get('participant_id', 'UNKNOWN')
    return f"{reason_type}_{participant_id}_{details.replace(' ', '_')}"

def extract_metadata_and_log_exclusions(
    df: pd.DataFrame, 
    exclusion_log_path: Path
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Extract metadata (cognitive status) from records and log exclusions with reason codes.
    
    This function:
    1. Parses cognitive status from filenames/headers
    2. Identifies records that should be excluded (null labels, short text, unknown status)
    3. Generates specific reason codes for each exclusion
    4. Logs exclusions to the specified file
    5. Returns the dataframe with added metadata columns
    
    Args:
        df: DataFrame with transcript data (must have 'filename' or 'participant_id' column)
        exclusion_log_path: Path to write exclusion logs
        
    Returns:
        Tuple of (updated DataFrame, list of exclusion records)
    """
    exclusions = []
    
    # Ensure exclusion log directory exists
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize exclusion log file
    with open(exclusion_log_path, 'w', encoding='utf-8') as log_file:
        log_file.write("exclusion_reason_code,participant_id,reason_type,details\n")
    
    # Process each record
    for idx, row in df.iterrows():
        participant_id = row.get('participant_id', f'record_{idx}')
        filename = row.get('filename', '')
        label = row.get('label', None)
        text = row.get('text', '')
        
        # Extract cognitive status from filename
        cognitive_status = parse_cognitive_status_from_filename(filename)
        
        # Add cognitive status to the dataframe
        df.at[idx, 'cognitive_status'] = cognitive_status
        
        # Check for exclusion conditions
        exclusion_reason = None
        exclusion_details = ""
        
        # Condition 1: Null or missing label
        if pd.isna(label) or label is None or label == '':
            exclusion_reason = 'NULL_LABEL'
            exclusion_details = 'missing_cognitive_label'
        
        # Condition 2: Text too short (less than 50 words)
        elif text and isinstance(text, str):
            word_count = len(text.split())
            if word_count < 50:
                exclusion_reason = 'SHORT_TEXT'
                exclusion_details = f'word_count_{word_count}'
        
        # Condition 3: Unknown cognitive status (if we couldn't parse it)
        elif cognitive_status == 'Unknown':
            exclusion_reason = 'UNKNOWN_STATUS'
            exclusion_details = 'unparsable_filename'
        
        # If there's an exclusion reason, log it
        if exclusion_reason:
            reason_code = generate_exclusion_reason_code(
                row, exclusion_reason, exclusion_details
            )
            
            exclusion_record = {
                'reason_code': reason_code,
                'participant_id': participant_id,
                'reason_type': exclusion_reason,
                'details': exclusion_details
            }
            exclusions.append(exclusion_record)
            
            # Append to log file
            with open(exclusion_log_path, 'a', encoding='utf-8') as log_file:
                log_file.write(
                    f"{reason_code},{participant_id},{exclusion_reason},{exclusion_details}\n"
                )
            
            logger.warning(f"Excluding {participant_id}: {exclusion_reason} - {exclusion_details}")
        else:
            # Log successful metadata extraction for valid records
            logger.info(f"Extracted status for {participant_id}: {cognitive_status}")
    
    logger.info(f"Metadata extraction complete. {len(exclusions)} records excluded.")
    return df, exclusions

def main():
    """
    Main entry point for T015 metadata extraction task.
    Reads cleaned transcripts, extracts metadata, logs exclusions, and saves results.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(get_path('data/interim', 't015_extraction.log')),
            logging.StreamHandler()
        ]
    )
    
    logger.info("Starting T015: Metadata Extraction")
    
    # Define paths
    input_path = get_path('data/interim', 'cleaned_transcripts.csv')
    exclusion_log_path = get_path('data/interim', 'exclusions.log')
    output_path = get_path('data/interim', 'cleaned_adress.csv')
    
    # Check if input file exists
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run T014 (filter_records) first to generate cleaned_transcripts.csv")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load the cleaned transcripts
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records")
    
    # Extract metadata and log exclusions
    df_with_metadata, exclusions = extract_metadata_and_log_exclusions(
        df, exclusion_log_path
    )
    
    # Save the final dataset with metadata
    logger.info(f"Saving final dataset to {output_path}")
    df_with_metadata.to_csv(output_path, index=False)
    
    # Log summary statistics
    status_counts = df_with_metadata['cognitive_status'].value_counts().to_dict()
    logger.info(f"Status distribution: {status_counts}")
    logger.info(f"Total exclusions: {len(exclusions)}")
    
    # Save exclusion summary to a JSON file for downstream tasks
    exclusion_summary_path = get_path('data/results', 'exclusion_summary.json')
    exclusion_summary_path.parent.mkdir(parents=True, exist_ok=True)
    
    summary = {
        'total_records': len(df),
        'excluded_count': len(exclusions),
        'valid_count': len(df) - len(exclusions),
        'status_distribution': status_counts,
        'exclusions': exclusions[:10]  # First 10 for preview
    }
    
    with open(exclusion_summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Metadata extraction complete. Summary saved to {exclusion_summary_path}")
    logger.info("T015 completed successfully")

if __name__ == '__main__':
    main()
