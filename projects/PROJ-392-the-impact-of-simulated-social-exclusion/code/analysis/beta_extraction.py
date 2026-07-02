"""
Beta Estimation Extraction Module

Extracts beta estimates for 'reward anticipation' and 'reward receipt' events
from first-level GLM results for all participants.

Dependencies:
  - code/analysis/first_level_glm.py (for loading GLM results)
  - code/analysis/roi_extraction.py (for ROI context)
  - code/config/loader.py (for configuration)
  - code/data_download/harmonize_metadata.py (for participant grouping)
"""

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from project modules based on provided API surface
from analysis.first_level_glm import load_events, create_design_matrix, fit_first_level_glm, compute_contrasts, process_subject_first_level, run_first_level_glm_pipeline, save_results_summary, FirstLevelGLMError
from config.loader import get_config, get_path, get_analysis_params, get_all_dataset_ids
from data_download.harmonize_metadata import load_dataset_manifest, harmonize_participant_groups, write_unified_metadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BetaExtractionError(Exception):
    """Custom exception for beta extraction failures."""
    pass

def load_first_level_results(participant_id: str, dataset_id: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Load first-level GLM results for a specific participant.

    Args:
        participant_id: The participant identifier (e.g., 'sub-001')
        dataset_id: The dataset identifier (e.g., 'ds004738')
        config: Configuration dictionary

    Returns:
        Dictionary containing GLM results or None if not found
    """
    results_dir = Path(get_path(config, 'processed_fmri')) / dataset_id / 'first_level_results'
    participant_dir = results_dir / participant_id

    if not participant_dir.exists():
        logger.warning(f"First-level results not found for {participant_id} in {dataset_id}")
        return None

    # Look for the results summary file
    results_file = participant_dir / 'results_summary.json'
    if not results_file.exists():
        logger.warning(f"Results summary not found for {participant_id} in {dataset_id}")
        return None

    try:
        with open(results_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise BetaExtractionError(f"Failed to parse results for {participant_id}: {e}")

def extract_beta_from_results(results: Dict[str, Any], contrast_name: str, event_type: str) -> Optional[float]:
    """
    Extract beta value for a specific contrast from GLM results.

    Args:
        results: First-level GLM results dictionary
        contrast_name: Name of the contrast to extract
        event_type: Type of event (for logging)

    Returns:
        Beta value or None if contrast not found
    """
    if 'contrasts' not in results:
        logger.warning(f"No contrasts found in results for {event_type}")
        return None

    contrast_data = results['contrasts'].get(contrast_name)
    if not contrast_data:
        logger.warning(f"Contrast '{contrast_name}' not found in results for {event_type}")
        return None

    # Extract the beta estimate (typically the first value in the contrast vector)
    # The structure depends on how compute_contrasts was implemented
    if 'beta_estimate' in contrast_data:
        return float(contrast_data['beta_estimate'])
    elif 'estimate' in contrast_data:
        return float(contrast_data['estimate'])
    else:
        # Fallback: try to get from parameter estimates
        if 'parameters' in contrast_data and len(contrast_data['parameters']) > 0:
            return float(contrast_data['parameters'][0])

    logger.warning(f"Could not extract beta estimate for contrast '{contrast_name}'")
    return None

def get_roi_masks(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get ROI mask definitions from configuration.

    Returns:
        List of ROI definitions with name and path
    """
    roi_params = get_analysis_params(config, 'roi_analysis')
    rois = []

    # Default ROIs based on task description
    default_rois = [
        {'name': 'ventral_striatum', 'atlas': 'AAL'},
        {'name': 'ofc', 'atlas': 'Harvard-Oxford'}
    ]

    for roi in roi_params.get('masks', default_rois):
        rois.append(roi)

    return rois

def extract_beta_estimates(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract beta estimates for all participants, ROIs, and event types.

    Args:
        config: Configuration dictionary

    Returns:
        List of dictionaries containing extraction results
    """
    results = []
    event_types = ['reward_anticipation', 'reward_receipt']
    datasets = get_all_dataset_ids(config)

    logger.info(f"Starting beta extraction for {len(event_types)} event types across {len(datasets)} datasets")

    for dataset_id in datasets:
        # Load participant metadata for this dataset
        manifest_path = Path(get_path(config, 'behavioral')) / f"{dataset_id}_manifest.json"
        if not manifest_path.exists():
            logger.warning(f"Manifest not found for {dataset_id}, skipping")
            continue

        try:
            manifest = load_dataset_manifest(str(manifest_path))
            participants = manifest.get('participants', [])
        except Exception as e:
            logger.error(f"Failed to load manifest for {dataset_id}: {e}")
            continue

        rois = get_roi_masks(config)

        for participant in participants:
            participant_id = participant.get('participant_id')
            if not participant_id:
                continue

            # Load first-level results
            first_level_results = load_first_level_results(participant_id, dataset_id, config)
            if not first_level_results:
                continue

            for roi in rois:
                roi_name = roi['name']

                for event_type in event_types:
                    # Construct contrast name based on event type and ROI
                    # This assumes the contrast naming convention from first_level_glm
                    contrast_name = f"{event_type}_vs_baseline_{roi_name}"

                    # Also try alternative naming conventions
                    alternative_contrasts = [
                        f"{event_type}_{roi_name}",
                        f"{roi_name}_{event_type}",
                        f"{event_type}",
                        f"reward_{event_type}"
                    ]

                    beta_value = None
                    for contrast in [contrast_name] + alternative_contrasts:
                        try:
                            beta_value = extract_beta_from_results(first_level_results, contrast, event_type)
                            if beta_value is not None:
                                logger.debug(f"Found beta for {contrast} in {participant_id}")
                                break
                        except Exception as e:
                            logger.debug(f"Contrast {contrast} failed: {e}")
                            continue

                    if beta_value is not None:
                        results.append({
                            'participant_id': participant_id,
                            'group': participant.get('group', 'unknown'),
                            'dataset_id': dataset_id,
                            'roi': roi_name,
                            'event_type': event_type,
                            'beta_value': beta_value
                        })
                    else:
                        logger.warning(f"No beta extracted for {participant_id}, {roi_name}, {event_type}")

    return results

def save_beta_estimates(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save beta estimates to a CSV file.

    Args:
        results: List of extraction results
        output_path: Path to output CSV file
    """
    if not results:
        logger.warning("No results to save")
        return

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write to CSV
    fieldnames = ['participant_id', 'group', 'dataset_id', 'roi', 'event_type', 'beta_value']
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Saved {len(results)} beta estimates to {output_path}")

def main():
    """Main entry point for beta extraction."""
    parser = argparse.ArgumentParser(description='Extract beta estimates from first-level GLM results')
    parser.add_argument('--config', type=str, default='config/project_config.yaml',
                      help='Path to configuration file')
    parser.add_argument('--output', type=str, default='data/results/beta_estimates.csv',
                      help='Output path for beta estimates CSV')
    parser.add_argument('--log-level', type=str, default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      help='Logging level')

    args = parser.parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    try:
        # Load configuration
        config = get_config(args.config)

        # Extract beta estimates
        logger.info("Starting beta extraction process")
        results = extract_beta_estimates(config)

        # Save results
        save_beta_estimates(results, args.output)

        logger.info("Beta extraction completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Beta extraction failed: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
