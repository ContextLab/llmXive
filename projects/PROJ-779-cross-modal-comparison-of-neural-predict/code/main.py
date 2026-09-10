"""
Main orchestration script for the cross-modal neural prediction error pipeline.
Handles the execution flow, data integrity checks, and constitution compliance.
"""
import sys
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_config, ensure_directories, STATE_PROJECT_FILE
from code.utils.logger import get_logger, configure_logging
from code.validation.reliability import main as run_reliability_check
from code.analysis.source import run_sensitivity_analysis, main as run_source_analysis
from code.analysis.stats import main as run_stats_analysis
from code.analysis.metrics import main as run_metrics_extraction
from code.data.preprocess import main as run_preprocessing
from code.data.download import main as run_download

logger = get_logger(__name__)

class ConstitutionViolationError(Exception):
    """Raised when a constitutional amendment required for execution is not ratified."""
    pass

class DataIntegrityError(Exception):
    """Raised when data artifact checksums do not match recorded values."""
    pass

def load_json_result(path: Path) -> Dict[str, Any]:
    """Load a JSON result file."""
    if not path.exists():
        raise FileNotFoundError(f"Result file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def verify_data_integrity(config: Dict[str, Any]) -> None:
    """
    Verify that processed data artifacts match checksums recorded in the state file.
    Raises DataIntegrityError on mismatch.
    """
    state_path = Path(config['output_paths']['state_project'])
    if not state_path.exists():
        logger.warning(f"State file not found at {state_path}. Skipping integrity check.")
        return

    try:
        import yaml
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f) or {}
    except ImportError:
        logger.warning("PyYAML not installed. Skipping state file parsing.")
        return
    except Exception as e:
        logger.warning(f"Could not parse state file: {e}")
        return

    artifact_hashes = state_data.get('artifact_hashes', {})
    cleaned_data_path = Path(config['output_paths']['cleaned_data'])

    if cleaned_data_path.exists() and 'ds000246' in artifact_hashes:
        # Compute SHA256 of the cleaned data file
        sha256_hash = hashlib.sha256()
        try:
            with open(cleaned_data_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            computed_hash = sha256_hash.hexdigest()
            recorded_hash = artifact_hashes['ds000246']
            
            if computed_hash != recorded_hash:
                raise DataIntegrityError(
                    f"Data integrity check failed for cleaned_data.fif. "
                    f"Computed: {computed_hash}, Recorded: {recorded_hash}"
                )
            logger.info("Data integrity check passed.")
        except FileNotFoundError:
            logger.warning("Cleaned data file not found for integrity check.")

def check_constitution_compliance(config: Dict[str, Any]) -> None:
    """
    Check if the required constitutional amendment (T055b) is ratified.
    If not ratified, raises ConstitutionViolationError to halt the pipeline.
    """
    state_path = Path(config['output_paths']['state_project'])
    ratified = False

    if state_path.exists():
        try:
            import yaml
            with open(state_path, 'r') as f:
                state_data = yaml.safe_load(f) or {}
            
            # Check for the specific flag
            ratified = state_data.get('amendment_ratified', False)
        except Exception as e:
            logger.warning(f"Could not verify amendment status: {e}")
    else:
        logger.warning(f"State file {state_path} not found. Assuming amendment not ratified.")

    if not ratified:
        logger.error("CONSTITUTION VIOLATION: Amendment VII (T055b) is not ratified.")
        logger.error("Pipeline execution is halted per Constitution Principle VII.")
        raise ConstitutionViolationError(
            "Amendment VII (Split-Half Reliability as Proxy) is not ratified. "
            "Pipeline execution halted. Please review and ratify the amendment in "
            f"docs/constitution-amendment-vii.md and update {state_path}."
        )
    
    logger.info("Constitution compliance check passed.")

def classify_latency(metrics: Dict[str, Any], threshold_ms: float = 50.0) -> Dict[str, Any]:
    """
    Classify latency difference against the 50ms threshold (SC-001).
    """
    result = {"classification": "unknown", "delta_ms": None}
    
    aud_lat = metrics.get('auditory', {}).get('peak_latency_ms')
    vis_lat = metrics.get('visual', {}).get('peak_latency_ms')
    
    if aud_lat is not None and vis_lat is not None:
        delta = abs(aud_lat - vis_lat)
        result['delta_ms'] = delta
        if delta < threshold_ms:
            result['classification'] = "domain_general"
        else:
            result['classification'] = "modality_specific"
    
    return result

def classify_source_overlap(tost_p: float, dice: float, tost_threshold: float = 0.05, dice_threshold: float = 0.6) -> str:
    """
    Classify source overlap based on TOST p-value and Dice coefficient.
    """
    if tost_p < tost_threshold and dice > dice_threshold:
        return "Equivalence Supported"
    else:
        return "Difference Detected"

def generate_manifest(config: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a manifest of the run."""
    return {
        "config": config,
        "results_summary": results,
        "timestamp": "2023-10-27T12:00:00Z" # Placeholder, use datetime in real impl
    }

def run_download_preprocess(config: Dict[str, Any]) -> None:
    """Run the download and preprocessing stage."""
    logger.info("Stage: Download & Preprocess")
    run_download(config)
    run_preprocessing(config)

def run_extract_metrics(config: Dict[str, Any]) -> None:
    """Run the metrics extraction stage."""
    logger.info("Stage: Extract Metrics")
    run_metrics_extraction(config)

def run_localize_sources(config: Dict[str, Any]) -> None:
    """Run the source localization stage."""
    logger.info("Stage: Localize Sources")
    run_source_analysis(config)

def run_statistical_analysis(config: Dict[str, Any]) -> None:
    """Run the statistical analysis stage."""
    logger.info("Stage: Statistical Analysis")
    run_stats_analysis(config)
    run_reliability_check(config)

def run_full_pipeline(config: Dict[str, Any]) -> None:
    """Run the full analysis pipeline."""
    ensure_directories()
    
    # 1. Constitution Check
    check_constitution_compliance(config)
    
    # 2. Data Integrity Check
    verify_data_integrity(config)
    
    # 3. Run Stages
    run_download_preprocess(config)
    run_extract_metrics(config)
    run_localize_sources(config)
    run_statistical_analysis(config)
    
    logger.info("Pipeline completed successfully.")

def run_orchestration(stage: str, config: Dict[str, Any]) -> None:
    """Run a specific stage of the pipeline."""
    ensure_directories()
    
    if stage == "download_preprocess":
        run_download_preprocess(config)
    elif stage == "extract_metrics":
        run_extract_metrics(config)
    elif stage == "localize_sources":
        run_localize_sources(config)
    elif stage == "statistical_analysis":
        run_statistical_analysis(config)
    elif stage == "full_run":
        run_full_pipeline(config)
    else:
        raise ValueError(f"Unknown stage: {stage}")

def main():
    """Entry point for the pipeline."""
    configure_logging()
    config = get_config()
    
    # Simple CLI argument parsing
    stage = "full_run"
    if len(sys.argv) > 1:
        stage = sys.argv[1]
    
    try:
        run_orchestration(stage, config)
    except ConstitutionViolationError as e:
        logger.error(str(e))
        sys.exit(1)
    except DataIntegrityError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()