"""
Main entry point for Parameter Estimation and Statistical Analysis.

Orchestrates:
1. Running Bilby/Dynesty (via run_bilby.py)
2. Orchestrate Statistical Analysis (via compare_posteriors.py)
3. Calculating Delta_Bias (via baseline comparison)
4. Generating final bias report.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from src.utils.logging import get_logger, log_step_start, log_step_complete, log_step_error
from src.utils.config import get_project_root, ensure_dir, set_seed
from src.pe.run_bilby import run_bilby_pe
from src.pe.compare_posteriors import orchestrate_statistical_analysis, save_results
from src.data.validation_logic import validate_injection

logger = get_logger(__name__)


def load_validated_events() -> List[Dict[str, Any]]:
    """Load list of valid events from data/interim/valid_events.json."""
    project_root = get_project_root()
    valid_events_path = project_root / "data" / "interim" / "valid_events.json"
    
    if not valid_events_path.exists():
        raise FileNotFoundError(f"Valid events file not found: {valid_events_path}")
    
    with open(valid_events_path, 'r') as f:
        data = json.load(f)
    
    return data.get('event_ids', [])


def get_event_paths(event_id: str) -> Dict[str, str]:
    """Construct paths for an event's data."""
    project_root = get_project_root()
    base = project_root / "data" / "processed" / event_id
    
    return {
        "original": str(base / "original_posterior.json"),
        "compressed": {
            "quantization_8bit": str(base / "compressed" / "quantization" / "8bit" / "posterior.json"),
            "quantization_4bit": str(base / "compressed" / "quantization" / "4bit" / "posterior.json"),
            "jpeg2000_50": str(base / "compressed" / "jpeg2000" / "50" / "posterior.json"),
            # Add other levels as needed
        }
    }


def run_pe_for_event(event_id: str):
    """Run Bilby PE for original and compressed data for a single event."""
    log_step_start("PE", f"Running PE for event {event_id}")
    
    try:
        # Paths
        paths = get_event_paths(event_id)
        
        # Run Bilby for original
        # Note: This assumes the waveform data exists at expected locations
        # and run_bilby_pe handles loading it.
        # In a real pipeline, we might pass the waveform path explicitly.
        run_bilby_pe(event_id=event_id, is_compressed=False, output_path=paths["original"])
        
        # Run Bilby for compressed variants
        for level, comp_path in paths["compressed"].items():
            # Ensure directory exists
            ensure_dir(Path(comp_path))
            run_bilby_pe(event_id=event_id, is_compressed=True, level=level, output_path=comp_path)
            
        log_step_complete("PE", f"PE completed for event {event_id}")
    except Exception as e:
        log_step_error("PE", f"PE failed for event {event_id}: {e}")
        raise


def run_statistical_analysis_for_event(event_id: str):
    """Run statistical analysis (t-tests, CI overlap) for a single event."""
    log_step_start("Stats", f"Running stats for event {event_id}")
    
    try:
        paths = get_event_paths(event_id)
        
        # Check if original posterior exists
        if not Path(paths["original"]).exists():
            logger.error(f"Original posterior not found for {event_id}. Skipping stats.")
            return
        
        # Filter compressed paths that exist
        existing_compressed = {
            k: v for k, v in paths["compressed"].items() if Path(v).exists()
        }
        
        if not existing_compressed:
            logger.warning(f"No compressed posteriors found for {event_id}. Skipping stats.")
            return
        
        results = orchestrate_statistical_analysis(
            event_id=event_id,
            original_posterior_path=paths["original"],
            compressed_posterior_paths=existing_compressed
        )
        
        save_results(results, str(Path(paths["original"]).parent.parent))
        
        log_step_complete("Stats", f"Stats completed for event {event_id}")
    except Exception as e:
        log_step_error("Stats", f"Stats failed for event {event_id}: {e}")
        raise


def main():
    """Main entry point for the PE pipeline."""
    project_root = get_project_root()
    set_seed(42) # Pin seed for reproducibility
    
    logger.info("Starting Parameter Estimation Pipeline")
    
    try:
        # 1. Load valid events
        event_ids = load_validated_events()
        logger.info(f"Found {len(event_ids)} valid events.")
        
        if len(event_ids) < 5:
            logger.warning(f"Only {len(event_ids)} events found. Proceeding anyway.")
        
        # 2. Run PE for each event
        for event_id in event_ids:
            run_pe_for_event(event_id)
        
        # 3. Run Statistical Analysis for each event
        for event_id in event_ids:
            run_statistical_analysis_for_event(event_id)
        
        logger.info("PE Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"PE Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()