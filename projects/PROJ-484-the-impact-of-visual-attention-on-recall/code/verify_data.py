import os
import sys
import json
import yaml
import logging
import argparse
from pathlib import Path

# Import local utilities
from logging_config import setup_logging

# ----------------------------------------------------------------------
# Helper Functions (unchanged from original implementation)
# ----------------------------------------------------------------------
def load_json_file(filepath):
    """Load a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def load_yaml_file(filepath):
    """Load a YAML file."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def find_bids_sidecars(directory):
    """
    Find BIDS sidecar files (JSON/YAML) in the given directory.
    Returns a list of file paths.
    """
    sidecars = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json') or file.endswith('.yaml') or file.endswith('.yml'):
                sidecars.append(os.path.join(root, file))
    return sidecars

def extract_columns_from_sidecar(filepath):
    """
    Extract column information from a BIDS sidecar file.
    Returns a dict of columns to their types/metadata.
    """
    if filepath.endswith('.json'):
        data = load_json_file(filepath)
    else:
        data = load_yaml_file(filepath)
    return data.get('Columns', {})

def extract_geometry_metadata(sidecar_data):
    """
    Extract geometry metadata from a sidecar dictionary.
    Expected keys: screen_width_px, viewing_distance_mm, sampling_rate_hz
    Returns a dict with these values (if present).
    """
    geometry = {}
    # Direct keys
    for key in ('screen_width_px', 'viewing_distance_mm', 'sampling_rate_hz'):
        if key in sidecar_data:
            geometry[key] = float(sidecar_data[key])
    return geometry

def calculate_ivt_threshold(screen_width_px, viewing_distance_mm, sampling_rate_hz, deg=0.5):
    """
    Calculate I-VT threshold given geometry.
    This function mirrors the one used elsewhere in the pipeline.
    """
    # Convert viewing distance to cm for consistency with typical FOV calculations
    viewing_distance_cm = viewing_distance_mm / 10.0
    # Assume a horizontal field of view of ~55 degrees (as used elsewhere)
    fov_deg = 55.0
    pixels_per_degree = screen_width_px / fov_deg
    threshold = (deg * pixels_per_degree) / sampling_rate_hz
    return threshold

def verify_temporal_load(events_data, stimulus_duration_ms):
    """
    Verify that stimulus duration matches expected temporal load.
    Placeholder implementation – actual logic lives elsewhere.
    """
    # This function is retained for compatibility but not used in this task.
    return True

def load_verified_sources(source_path=None):
    """
    Load verified sources configuration.
    Checks for 'verified_sources_hypothetical.json' first, then
    'verified_sources.json' in the same directory as this script.
    Returns a list of source dictionaries.
    """
    sources = []
    project_root = Path(__file__).parent

    # Hypothetical sources
    hypothetical_path = project_root / "verified_sources_hypothetical.json"
    if hypothetical_path.exists():
        try:
            with open(hypothetical_path, 'r') as f:
                data = json.load(f)
                sources.extend(data.get('sources', []))
        except Exception as e:
            logging.warning(f"Could not load hypothetical sources: {e}")

    # Verified sources
    verified_path = project_root / "verified_sources.json"
    if verified_path.exists():
        try:
            with open(verified_path, 'r') as f:
                data = json.load(f)
                sources.extend(data.get('sources', []))
        except Exception as e:
            logging.warning(f"Could not load verified sources: {e}")

    return sources

# ----------------------------------------------------------------------
# Geometry Calibration Logic (new for T071)
# ----------------------------------------------------------------------
def _load_default_geometry():
    """
    Load default geometry values from config.yaml.
    Expected keys in config.yaml:
      default_screen_width_px
      default_viewing_distance_mm
      default_sampling_rate_hz
    Returns a dict with the three geometry parameters.
    """
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.is_file():
        raise FileNotFoundError(f"Default geometry config not found at {config_path}")
    cfg = load_yaml_file(config_path)
    defaults = {
        'screen_width_px': float(cfg.get('default_screen_width_px', 1920)),
        'viewing_distance_mm': float(cfg.get('default_viewing_distance_mm', 600)),
        'sampling_rate_hz': float(cfg.get('default_sampling_rate_hz', 1000))
    }
    return defaults

def _extract_geometry_from_dataset(data_dir):
    """
    Attempt to extract geometry metadata from the BIDS dataset.
    Looks for sidecar files (JSON/YAML) that contain the required fields.
    Returns a dict (may be empty if nothing found).
    """
    geometry = {}
    sidecar_files = find_bids_sidecars(data_dir)
    for sc_path in sidecar_files:
        try:
            if sc_path.endswith('.json'):
                sc_data = load_json_file(sc_path)
            else:
                sc_data = load_yaml_file(sc_path)
            geom = extract_geometry_metadata(sc_data)
            geometry.update(geom)
        except Exception:
            # Ignore malformed sidecars – continue searching
            continue
    return geometry

def main():
    """
    Entry point for geometry calibration verification.
    Performs the strict check required by task T071.
    """
    parser = argparse.ArgumentParser(
        description="Verify geometry calibration for visual attention dataset"
    )
    parser.add_argument(
        "--dataset-id",
        default="ds001435",
        help="Identifier of the dataset to verify (matches entries in verified sources)"
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Root directory of the BIDS dataset. If omitted, uses DATA_PATH environment variable."
    )
    args = parser.parse_args()

    logger = setup_logging("verify_data")
    logger.info(f"Starting geometry verification for dataset: {args.dataset_id}")

    # Resolve data directory
    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        # Fall back to config's data path
        from config import get_data_path
        data_dir = Path(get_data_path()) / "raw" / args.dataset_id

    if not data_dir.is_dir():
        logger.error(f"Data directory not found: {data_dir}")
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    # Load verified sources and determine if this dataset is marked as hypothetical
    sources = load_verified_sources()
    source_info = next((s for s in sources if s.get('id') == args.dataset_id), None)
    is_hypothetical = source_info is not None and source_info.get('status') == 'hypothetical'

    # ------------------------------------------------------------------
    # Extract geometry from the dataset
    # ------------------------------------------------------------------
    geometry = _extract_geometry_from_dataset(str(data_dir))

    required_keys = ('screen_width_px', 'viewing_distance_mm', 'sampling_rate_hz')
    missing_keys = [k for k in required_keys if k not in geometry or geometry[k] is None]

    if missing_keys:
        if is_hypothetical:
            # Load defaults from config.yaml and log a warning
            logger.warning(
                f"Missing geometry fields {missing_keys} for hypothetical dataset. "
                "Loading defaults from config.yaml."
            )
            defaults = _load_default_geometry()
            geometry.update(defaults)
        else:
            # Strict mode – fail loudly
            missing_str = ", ".join(missing_keys)
            error_msg = "ERROR: Cannot calibrate I-VT threshold without screen geometry."
            logger.error(error_msg + f" Missing fields: {missing_str}")
            raise RuntimeError(error_msg)

    # At this point we have a complete geometry dict
    logger.info(f"Geometry calibration successful: {geometry}")

    # Optionally calculate the I-VT threshold (not required for the task but useful)
    try:
        ivt_thr = calculate_ivt_threshold(
            screen_width_px=geometry['screen_width_px'],
            viewing_distance_mm=geometry['viewing_distance_mm'],
            sampling_rate_hz=geometry['sampling_rate_hz']
        )
        logger.info(f"Calculated I-VT threshold (px/frame): {ivt_thr:.4f}")
    except Exception as e:
        logger.warning(f"Failed to calculate I-VT threshold: {e}")

    logger.info("Geometry verification completed without errors.")
    # Exit cleanly
    sys.exit(0)

if __name__ == "__main__":
    main()
