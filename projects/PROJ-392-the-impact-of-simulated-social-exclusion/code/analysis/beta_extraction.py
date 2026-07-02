"""
Extract beta estimates for 'reward anticipation' and 'reward receipt' events per participant.

This module implements Task T019: Extract beta estimates from first-level GLM results
for specific event types (reward anticipation, reward receipt) across all participants.
It depends on T018 (first-level GLM execution) and T014 (harmonized metadata).
"""
import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from existing API surface
from analysis.roi_extraction import extract_beta_from_glm_results, get_aal_vs_mask, get_ho_ofo_mask
from utils.config_loader import load_config, get_dataset_by_id
from utils.provenance import generate_provenance_sidecar

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Event types to extract betas for
REWARD_EVENTS = ['reward_anticipation', 'reward_receipt']

# ROIs to extract from (matching T017)
ROIS = {
    'ventral_striatum': 'aal',
    'orbitofrontal_cortex': 'ho'
}

def load_first_level_results(glm_output_dir: Path) -> Dict[str, Any]:
    """
    Load first-level GLM results from the output directory.

    Args:
        glm_output_dir: Path to directory containing GLM results

    Returns:
        Dictionary mapping subject IDs to their GLM results
    """
    results = {}
    if not glm_output_dir.exists():
        raise FileNotFoundError(f"GLM output directory not found: {glm_output_dir}")

    for subject_dir in glm_output_dir.iterdir():
        if subject_dir.is_dir():
            subject_id = subject_dir.name
            # Look for contrast files or beta files
            contrast_files = list(subject_dir.glob('*contrast*.nii.gz'))
            if contrast_files:
                results[subject_id] = {
                    'path': subject_dir,
                    'contrast_files': contrast_files
                }
            else:
                logger.warning(f"No contrast files found for subject {subject_id}")

    return results

def get_event_contrast_mapping() -> Dict[str, str]:
    """
    Return mapping from event types to contrast names/IDs.

    This assumes the first-level GLM (T018) created contrasts named after events.
    Returns:
        Dict mapping event_type to contrast identifier
    """
    return {
        'reward_anticipation': 'reward_anticipation',
        'reward_receipt': 'reward_receipt'
    }

def extract_beta_for_event(
    subject_id: str,
    subject_data: Dict[str, Any],
    roi_name: str,
    event_type: str,
    contrast_mapping: Dict[str, str],
    config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Extract beta estimate for a specific event and ROI.

    Args:
        subject_id: Participant identifier
        subject_data: Dictionary with GLM result paths
        roi_name: Name of the ROI (e.g., 'ventral_striatum')
        event_type: Event type to extract (e.g., 'reward_anticipation')
        contrast_mapping: Mapping of event types to contrast names
        config: Configuration dictionary with ROI coordinates

    Returns:
        Dictionary with beta value or None if extraction failed
    """
    try:
        contrast_name = contrast_mapping.get(event_type)
        if not contrast_name:
            logger.warning(f"No contrast mapping for event: {event_type}")
            return None

        # Determine which mask function to use
        if roi_name == 'ventral_striatum':
            mask_func = get_aal_vs_mask
            roi_coords = config.get('roi', {}).get('ventral_striatum', {})
        elif roi_name == 'orbitofrontal_cortex':
            mask_func = get_ho_ofo_mask
            roi_coords = config.get('roi', {}).get('orbitofrontal_cortex', {})
        else:
            logger.warning(f"Unknown ROI: {roi_name}")
            return None

        # Extract beta using the ROI extraction utility
        beta_value = extract_beta_from_glm_results(
            glm_results_path=subject_data['path'],
            contrast_name=contrast_name,
            mask_func=mask_func,
            roi_coords=roi_coords
        )

        if beta_value is None:
            logger.warning(f"Failed to extract beta for {subject_id}, {roi_name}, {event_type}")
            return None

        return {
            'subject_id': subject_id,
            'roi': roi_name,
            'event_type': event_type,
            'beta_value': float(beta_value),
            'success': True
        }

    except Exception as e:
        logger.error(f"Error extracting beta for {subject_id}, {roi_name}, {event_type}: {e}")
        return None

def run_beta_extraction(
    glm_output_dir: Path,
    harmonized_metadata_path: Path,
    output_csv_path: Path,
    config_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Main function to extract beta estimates for all participants, ROIs, and events.

    Args:
        glm_output_dir: Path to directory containing first-level GLM results
        harmonized_metadata_path: Path to harmonized metadata JSON
        output_csv_path: Path where to write the CSV output
        config_path: Optional path to config file

    Returns:
        List of dictionaries containing extracted beta values
    """
    logger.info(f"Starting beta extraction from: {glm_output_dir}")

    # Load configuration
    if config_path and config_path.exists():
        config = load_config(config_path)
    else:
        # Create default config
        config = {
            'roi': {
                'ventral_striatum': {'x': 10, 'y': 10, 'z': -5, 'radius': 8},
                'orbitofrontal_cortex': {'x': -5, 'y': 45, 'z': -15, 'probability': 0.3}
            }
        }

    # Load harmonized metadata to get group information
    group_mapping = {}
    if harmonized_metadata_path.exists():
        with open(harmonized_metadata_path, 'r') as f:
            metadata = json.load(f)
            for participant in metadata.get('participants', []):
                group_mapping[participant['participant_id']] = participant.get('group', 'unknown')
    else:
        logger.warning(f"Harmonized metadata not found: {harmonized_metadata_path}")

    # Load GLM results
    glm_results = load_first_level_results(glm_output_dir)
    logger.info(f"Found GLM results for {len(glm_results)} subjects")

    # Get contrast mapping
    contrast_mapping = get_event_contrast_mapping()

    # Extract betas
    all_betas = []
    for subject_id, subject_data in glm_results.items():
        for roi_name in ROIS.keys():
            for event_type in REWARD_EVENTS:
                result = extract_beta_for_event(
                    subject_id=subject_id,
                    subject_data=subject_data,
                    roi_name=roi_name,
                    event_type=event_type,
                    contrast_mapping=contrast_mapping,
                    config=config
                )
                if result:
                    # Add group information from metadata
                    result['group'] = group_mapping.get(subject_id, 'unknown')
                    result['dataset'] = group_mapping.get(f"{subject_id}_dataset", "unknown")
                    all_betas.append(result)

    # Write to CSV
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv_path, 'w', newline='') as f:
        if all_betas:
            fieldnames = ['participant_id', 'group', 'roi', 'event_type', 'beta_value']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in all_betas:
                writer.writerow({
                    'participant_id': row['subject_id'],
                    'group': row['group'],
                    'roi': row['roi'],
                    'event_type': row['event_type'],
                    'beta_value': row['beta_value']
                })

    logger.info(f"Wrote {len(all_betas)} beta estimates to {output_csv_path}")

    # Generate provenance sidecar
    provenance_data = {
        'task': 'T019_beta_extraction',
        'input_glm_dir': str(glm_output_dir),
        'input_metadata': str(harmonized_metadata_path),
        'output_csv': str(output_csv_path),
        'rois_processed': list(ROIS.keys()),
        'events_processed': REWARD_EVENTS,
        'total_estimates': len(all_betas)
    }
    generate_provenance_sidecar(output_csv_path, provenance_data)

    return all_betas

def main():
    """Command-line entry point for beta extraction."""
    parser = argparse.ArgumentParser(
        description='Extract beta estimates for reward events from first-level GLM results'
    )
    parser.add_argument(
        '--glm-output',
        type=Path,
        required=True,
        help='Path to directory containing first-level GLM results'
    )
    parser.add_argument(
        '--metadata',
        type=Path,
        required=True,
        help='Path to harmonized metadata JSON file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/results/beta_estimates.csv'),
        help='Path for output CSV file'
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('code/config.yaml'),
        help='Path to configuration file'
    )

    args = parser.parse_args()

    try:
        run_beta_extraction(
            glm_output_dir=args.glm_output,
            harmonized_metadata_path=args.metadata,
            output_csv_path=args.output,
            config_path=args.config
        )
        logger.info("Beta extraction completed successfully")
    except Exception as e:
        logger.error(f"Beta extraction failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()