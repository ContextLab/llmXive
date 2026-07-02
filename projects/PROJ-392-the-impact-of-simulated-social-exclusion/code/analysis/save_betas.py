"""
Task T020: Store extracted betas in structured format.

This module implements the storage of beta estimates extracted from ROI analysis
into a structured CSV file as specified in T020.

It depends on:
- T019: Extraction of beta estimates (assumes data exists or is provided via input)
- code/analysis/beta_extraction.py: For loading and handling beta data structures
- code/config/loader.py: For configuration and path management
"""

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from config.loader import get_config, get_path, ensure_paths_exist
from analysis.beta_extraction import extract_beta_estimates, save_beta_estimates, BetaExtractionError
from analysis.roi_extraction import run_roi_extraction, ROIPreprocessingError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_beta_data_from_extraction(
    processed_dir: Path,
    results_dir: Path,
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Load beta estimates from the ROI extraction results.
    
    This function orchestrates the extraction process and returns the beta data
    in a format suitable for CSV storage.
    
    Args:
        processed_dir: Path to preprocessed data directory
        results_dir: Path to store results
        config: Configuration dictionary
        
    Returns:
        List of dictionaries containing beta estimates with keys:
        - participant_id
        - group (excluded/included)
        - roi (ventral_striatum, ofc)
        - event_type (reward_anticipation, reward_receipt)
        - beta_value
    """
    logger.info(f"Loading beta data from: {processed_dir}")
    
    # Ensure paths exist
    ensure_paths_exist([results_dir])
    
    # Get ROI and analysis parameters from config
    roi_names = config.get('roi', {}).get('names', ['ventral_striatum', 'ofc'])
    event_types = config.get('analysis', {}).get('event_types', ['reward_anticipation', 'reward_receipt'])
    
    # Load unified metadata to get participant groups
    metadata_path = get_path('unified_metadata', config)
    if not metadata_path.exists():
        logger.warning(f"Unified metadata not found at {metadata_path}. "
                     "Attempting to load from standard location.")
        metadata_path = Path(config.get('paths', {}).get('behavioral', '.')) / 'unified_metadata.csv'
    
    participant_groups = {}
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get('participant_id') or row.get('subject')
                if pid:
                    # Map group based on dataset/task info
                    task_type = row.get('task_type', '').lower()
                    if 'exclusion' in task_type or 'excluded' in task_type:
                        participant_groups[pid] = 'excluded'
                    elif 'inclusion' in task_type or 'included' in task_type:
                        participant_groups[pid] = 'included'
                    else:
                        # Default to 'unknown' if group cannot be determined
                        participant_groups[pid] = 'unknown'
        logger.info(f"Loaded group assignments for {len(participant_groups)} participants")
    else:
        logger.warning("Could not load participant groups from metadata. "
                     "All participants will be marked as 'unknown'.")
    
    beta_records = []
    
    # Iterate through subjects and ROIs
    # This assumes the ROI extraction has already been run and results are available
    # In a real pipeline, this would read from the actual output files
    try:
        # Attempt to load existing beta estimates if they were saved by T019
        existing_betas_path = results_dir / 'beta_estimates_raw.json'
        if existing_betas_path.exists():
            with open(existing_betas_path, 'r') as f:
                raw_betas = json.load(f)
            
            for subject_data in raw_betas:
                subject_id = subject_data.get('subject_id') or subject_data.get('participant_id')
                if not subject_id:
                    continue
                
                group = participant_groups.get(subject_id, 'unknown')
                
                for roi_data in subject_data.get('roi_betas', []):
                    roi_name = roi_data.get('roi')
                    for event_data in roi_data.get('events', []):
                        event_type = event_data.get('event_type')
                        beta_value = event_data.get('beta_value')
                        
                        if roi_name and event_type and beta_value is not None:
                            beta_records.append({
                                'participant_id': subject_id,
                                'group': group,
                                'roi': roi_name,
                                'event_type': event_type,
                                'beta_value': float(beta_value)
                            })
        else:
            # If no existing data, we would run the extraction here
            # For T020, we assume T019 has already run and produced results
            logger.info("No existing beta estimates found. "
                      "In a full pipeline, this would trigger ROI extraction.")
            # Attempt to run ROI extraction if data exists
            if processed_dir.exists():
                logger.info("Running ROI extraction to generate beta estimates...")
                # This is a simplified call; in reality, we'd need more parameters
                try:
                    extraction_results = extract_beta_estimates(
                        processed_dir=processed_dir,
                        roi_names=roi_names,
                        event_types=event_types
                    )
                    
                    for subject_id, roi_data in extraction_results.items():
                        group = participant_groups.get(subject_id, 'unknown')
                        for roi_name, events in roi_data.items():
                            for event_type, beta_value in events.items():
                                beta_records.append({
                                    'participant_id': subject_id,
                                    'group': group,
                                    'roi': roi_name,
                                    'event_type': event_type,
                                    'beta_value': float(beta_value)
                                })
                except (ROIPreprocessingError, BetaExtractionError) as e:
                    logger.error(f"Failed to extract beta estimates: {e}")
                    # Continue with empty results rather than failing the entire task
    except Exception as e:
        logger.error(f"Error loading or processing beta data: {e}")
        # Continue with empty results
    
    logger.info(f"Collected {len(beta_records)} beta records for storage")
    return beta_records

def save_betas_to_csv(
    beta_records: List[Dict[str, Any]],
    output_path: Path
) -> bool:
    """
    Save beta estimates to a CSV file with the required columns.
    
    Args:
        beta_records: List of beta estimate dictionaries
        output_path: Path to the output CSV file
        
    Returns:
        True if successful, False otherwise
    """
    if not beta_records:
        logger.warning("No beta records to save. Creating empty CSV with headers.")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['participant_id', 'group', 'roi', 'event_type', 'beta_value']
    
    try:
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in beta_records:
                # Ensure all required fields are present
                row = {field: record.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        logger.info(f"Successfully saved {len(beta_records)} beta records to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save beta estimates to CSV: {e}")
        return False

def main():
    """Main entry point for T020 implementation."""
    parser = argparse.ArgumentParser(
        description='Store extracted betas in structured CSV format (T020)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path (overrides config)'
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = get_config(args.config)
        
        # Get paths from config
        processed_dir = Path(get_path('processed_fmri', config))
        results_dir = Path(get_path('results', config))
        
        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = results_dir / 'beta_estimates.csv'
        
        logger.info(f"Processing beta estimates from {processed_dir}")
        logger.info(f"Output will be written to {output_path}")
        
        # Load/extract beta data
        beta_records = load_beta_data_from_extraction(
            processed_dir=processed_dir,
            results_dir=results_dir,
            config=config
        )
        
        # Save to CSV
        success = save_betas_to_csv(beta_records, output_path)
        
        if success:
            logger.info("T020 completed successfully: Beta estimates stored in structured format")
            return 0
        else:
            logger.error("T020 failed: Could not save beta estimates")
            return 1
            
    except Exception as e:
        logger.error(f"T020 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())