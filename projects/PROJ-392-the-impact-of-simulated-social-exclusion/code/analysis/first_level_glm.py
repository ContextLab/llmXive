import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from nilearn import image
from nilearn.glm.first_level import FirstLevelModel
from nilearn.glm.contrasts import compute_contrast
from nilearn.interfaces.bids import get_bids_files
from nilearn._utils import logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger.logger.setLevel(logging.WARNING)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed-fmri"
DATA_RESULTS = PROJECT_ROOT / "data" / "results"
DATA_BEHAVIORAL = PROJECT_ROOT / "data" / "behavioral"
HARMONIZED_METADATA = DATA_BEHAVIORAL / "harmonized_metadata.json"

# ROI coordinates (MNI space) - Ventral Striatum (AAL) and OFC (Harvard-Oxford)
# Approximate centers based on standard atlases
ROI_COORDS = {
    "vs": {"x": 0, "y": 10, "z": -8},  # Ventral Striatum
    "ofo": {"x": 0, "y": 50, "z": -10} # Orbitofrontal Cortex
}

# Task conditions to model
CONDITIONS = {
    "exclusion": ["exclusion", "social_exclusion"],
    "inclusion": ["inclusion", "social_inclusion"],
    "reward_anticipation": ["anticipation", "reward_cue"],
    "reward_receipt": ["receipt", "reward_outcome"]
}

def load_harmonized_metadata() -> Dict[str, Any]:
    """Load the harmonized metadata from T014."""
    if not HARMONIZED_METADATA.exists():
        raise FileNotFoundError(
            f"Harmonized metadata not found at {HARMONIZED_METADATA}. "
            "Please ensure T014 (harmonize_datasets.py) has been completed."
        )
    
    with open(HARMONIZED_METADATA, 'r') as f:
        return json.load(f)

def get_preprocessed_files(participant_id: str, dataset_id: str) -> List[Path]:
    """Find preprocessed NIfTI files for a specific participant."""
    search_path = DATA_PROCESSED / dataset_id / "sub-" + participant_id
    
    if not search_path.exists():
        logging.warning(f"No preprocessed files found for {dataset_id}/{participant_id}")
        return []
    
    # Look for space-MNI_desc-preproc_bold.nii.gz files
    files = list(search_path.rglob("space-MNI_desc-preproc_bold.nii.gz"))
    return files

def get_events_file(participant_id: str, dataset_id: str) -> Optional[Path]:
    """Find the events TSV file for a specific participant."""
    search_path = DATA_PROCESSED / dataset_id / "sub-" + participant_id / "func"
    
    if not search_path.exists():
        return None
    
    # Look for task-*_events.tsv files
    files = list(search_path.glob("task-*_events.tsv"))
    if files:
        return files[0]
    return None

def create_first_level_model(
    hrf_model: str = "spm",
    drift_model: str = "cosine",
    high_pass: float = 0.01,
    noise_model: str = "ar1",
    standardize: bool = True,
    signal_scaling: Tuple[int, int] = (0, 2),
    smoothing_fwhm: Optional[float] = None,
    memory: str = "nilearn_cache",
    verbose: int = 0
) -> FirstLevelModel:
    """
    Create a FirstLevelModel with autoregressive pre-whitening.
    
    Args:
        hrf_model: HRF model to use ('spm', 'spm-t', 'glover', 'spm-glover')
        drift_model: Drift model ('cosine', 'polynomial', None)
        high_pass: High-pass filter cutoff frequency
        noise_model: Noise model ('ols', 'ar1', 'ar1+whitened')
        standardize: Whether to standardize signals
        signal_scaling: Scaling dimensions (0=tr, 1=space, 2=both)
        smoothing_fwhm: Spatial smoothing FWHM (mm)
        memory: Memory location for caching
        verbose: Verbosity level
        
    Returns:
        Configured FirstLevelModel instance
    """
    return FirstLevelModel(
        hrf_model=hrf_model,
        drift_model=drift_model,
        high_pass=high_pass,
        noise_model=noise_model,  # ar1 for autoregressive pre-whitening
        standardize=standardize,
        signal_scaling=signal_scaling,
        smoothing_fwhm=smoothing_fwhm,
        memory=memory,
        verbose=verbose
    )

def run_first_level_glm(
    participant_id: str,
    dataset_id: str,
    output_dir: Path,
    model_kwargs: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run first-level GLM analysis for a single participant.
    
    Args:
        participant_id: Participant identifier (e.g., '01')
        dataset_id: Dataset identifier (e.g., 'ds000246')
        output_dir: Directory to save results
        model_kwargs: Additional kwargs for FirstLevelModel
        
    Returns:
        Dictionary containing paths to results and metadata
    """
    if model_kwargs is None:
        model_kwargs = {
            "noise_model": "ar1",
            "hrf_model": "spm",
            "drift_model": "cosine",
            "high_pass": 0.01,
            "standardize": True,
            "signal_scaling": (0, 2),
            "verbose": 1
        }
    
    # Get preprocessed files
    func_files = get_preprocessed_files(participant_id, dataset_id)
    if not func_files:
        return {"status": "skipped", "reason": "No preprocessed files found"}
    
    # Get events file
    events_file = get_events_file(participant_id, dataset_id)
    if not events_file:
        return {"status": "skipped", "reason": "No events file found"}
    
    logging.info(f"Running first-level GLM for {dataset_id}/{participant_id}")
    
    # Create model
    model = create_first_level_model(**model_kwargs)
    
    try:
        # Fit the model
        model = model.fit(
            func_files,
            events_files=events_file
        )
        
        # Define contrasts
        # For social exclusion/inclusion tasks
        contrasts = {
            "exclusion_vs_inclusion": ["exclusion", "inclusion"],
            "inclusion_vs_exclusion": ["inclusion", "exclusion"],
            # For reward tasks
            "reward_anticipation_vs_baseline": ["reward_anticipation"],
            "reward_receipt_vs_baseline": ["reward_receipt"]
        }
        
        results = {}
        for contrast_name, contrast_def in contrasts.items():
            try:
                z_map = model.compute_contrast(
                    contrast_def,
                    output_type='z'
                )
                
                # Save contrast map
                output_path = output_dir / f"sub-{participant_id}_{contrast_name}_zmap.nii.gz"
                z_map.to_filename(output_path)
                
                results[contrast_name] = {
                    "status": "success",
                    "path": str(output_path)
                }
                
            except Exception as e:
                logging.warning(f"Failed to compute contrast {contrast_name}: {e}")
                results[contrast_name] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        # Save model metadata
        metadata = {
            "participant_id": participant_id,
            "dataset_id": dataset_id,
            "func_files": [str(f) for f in func_files],
            "events_file": str(events_file),
            "model_parameters": model_kwargs,
            "contrast_results": results,
            "timestamp": time.time()
        }
        
        metadata_path = output_dir / f"sub-{participant_id}_first_level_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            "status": "success",
            "metadata_path": str(metadata_path),
            "results": results
        }
        
    except Exception as e:
        logging.error(f"First-level GLM failed for {participant_id}: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }

def run_first_level_analysis_batch(
    metadata: Dict[str, Any],
    output_dir: Optional[Path] = None,
    model_kwargs: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Run first-level GLM for all participants in the harmonized metadata.
    
    Args:
        metadata: Harmonized metadata dictionary from T014
        output_dir: Directory to save results (defaults to data/results/first_level)
        model_kwargs: Additional kwargs for FirstLevelModel
        
    Returns:
        List of results dictionaries for each participant
    """
    if output_dir is None:
        output_dir = DATA_RESULTS / "first_level"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    participants = metadata.get("participants", [])
    
    logging.info(f"Starting first-level analysis for {len(participants)} participants")
    
    for i, participant in enumerate(participants):
        pid = participant["participant_id"]
        dataset_id = participant["dataset_id"]
        
        logging.info(f"Processing participant {i+1}/{len(participants)}: {dataset_id}/{pid}")
        
        result = run_first_level_glm(
            participant_id=pid,
            dataset_id=dataset_id,
            output_dir=output_dir,
            model_kwargs=model_kwargs
        )
        
        results.append(result)
        
        # Log progress
        if result["status"] == "success":
            logging.info(f"  ✓ Completed {pid}")
        else:
            logging.warning(f"  ✗ Failed {pid}: {result.get('reason', result.get('error', 'Unknown error'))}")
    
    # Save summary
    summary = {
        "total_participants": len(participants),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "results": results
    }
    
    summary_path = output_dir / "first_level_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logging.info(f"First-level analysis complete: {summary['successful']}/{summary['total_participants']} successful")
    
    return results

def main():
    """Main entry point for first-level GLM execution."""
    parser = argparse.ArgumentParser(
        description="Run first-level GLM analysis with autoregressive pre-whitening"
    )
    parser.add_argument(
        "--model-config",
        type=str,
        help="Path to JSON file with model parameters"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load harmonized metadata
    logging.info("Loading harmonized metadata...")
    try:
        metadata = load_harmonized_metadata()
    except FileNotFoundError as e:
        logging.error(str(e))
        sys.exit(1)
    
    # Load model config if provided
    model_kwargs = None
    if args.model_config:
        config_path = Path(args.model_config)
        if config_path.exists():
            with open(config_path, 'r') as f:
                model_kwargs = json.load(f)
            logging.info(f"Loaded model configuration from {config_path}")
    
    # Run analysis
    output_dir = Path(args.output_dir) if args.output_dir else None
    results = run_first_level_analysis_batch(
        metadata=metadata,
        output_dir=output_dir,
        model_kwargs=model_kwargs
    )
    
    # Exit with error code if any failures
    failed_count = sum(1 for r in results if r["status"] == "failed")
    if failed_count > 0:
        logging.warning(f"{failed_count} participants failed to process")
        # Don't exit with error - partial success is acceptable

if __name__ == "__main__":
    main()
