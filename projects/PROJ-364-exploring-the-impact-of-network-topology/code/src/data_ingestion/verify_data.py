"""
Data Availability Verification Module (T012a).

This module checks for the existence of paired real datasets (defect coords + thermal conductivity)
versus unpaired aggregate data. It generates a status flag in `state/data_status.json` to trigger
synthetic fallback or population-level analysis if real paired data is missing.

It also resolves Plan vs Spec contradictions by logging specific warnings if the "no data"
assumption conflicts with the "assume data" assumption.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Import from existing project API surface
from src.logging_config import get_data_ingestion_logger
from src.config import get_config
from src.utils.checksum import compute_file_sha256


# Expected file patterns for paired data
# We assume paired data exists if we find a coordinate file (CSV/Parquet) AND a thermal property file
# in the same directory or with matching stems in `data/raw/`.
COORD_EXTENSIONS = {'.csv', '.parquet', '.txt'}
THERMAL_EXTENSIONS = {'.csv', '.parquet', '.json', '.txt'}
THERMAL_KEYWORDS = ['thermal', 'conductivity', 'k_value', 'temperature']


def _scan_directory_for_pairs(data_dir: Path) -> Tuple[bool, bool, List[str]]:
    """
    Scans the data directory for paired and unpaired datasets.

    Returns:
        Tuple[has_paired, has_unpaired, issues]:
            has_paired: True if at least one paired dataset (coords + thermal) is found.
            has_unpaired: True if aggregate/unpaired thermal data is found without coords.
            issues: List of warning strings describing mismatches or contradictions.
    """
    has_paired = False
    has_unpaired = False
    issues = []

    if not data_dir.exists():
        issues.append(f"Data directory {data_dir} does not exist.")
        return has_paired, has_unpaired, issues

    # Collect all potential data files
    all_files = list(data_dir.rglob('*'))
    coord_files = [f for f in all_files if f.suffix.lower() in COORD_EXTENSIONS]
    thermal_files = [f for f in all_files if f.suffix.lower() in THERMAL_EXTENSIONS]

    # Heuristic for pairing:
    # 1. Files with matching stems (e.g., 'sample_01_coords.csv' and 'sample_01_thermal.csv')
    # 2. Or files in the same directory with relevant keywords in names

    paired_stems = set()
    thermal_stems = set()
    coord_stems = set()

    for f in coord_files:
        stem = f.stem
        # Normalize stem by removing common suffixes like '_coords'
        clean_stem = stem.replace('_coords', '').replace('_defects', '').replace('_positions', '')
        coord_stems.add(clean_stem)

    for f in thermal_files:
        stem = f.stem
        is_thermal = any(kw in stem.lower() for kw in THERMAL_KEYWORDS)
        if is_thermal:
            clean_stem = stem.replace('_thermal', '').replace('_conductivity', '').replace('_k', '')
            thermal_stems.add(clean_stem)
        else:
            # If it's a thermal file but doesn't match keywords, check if it's in a thermal-specific dir
            if 'thermal' in str(f).lower():
                thermal_stems.add(stem)

    # Check for matches
    common_stems = coord_stems.intersection(thermal_stems)
    if common_stems:
        has_paired = True

    # Check for unpaired thermal data (thermal files that didn't match any coord file)
    unpaired_thermal = thermal_stems - common_stems
    if unpaired_thermal:
        has_unpaired = True
        issues.append(f"Found unpaired thermal data for stems: {list(unpaired_thermal)[:5]}...")

    # Check for unpaired coords (coords without thermal)
    unpaired_coords = coord_stems - thermal_stems
    if unpaired_coords:
        issues.append(f"Found defect coordinates without matching thermal data for stems: {list(unpaired_coords)[:5]}...")

    return has_paired, has_unpaired, issues


def check_data_availability(data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Checks for the existence of paired real datasets vs unpaired aggregate data.

    Args:
        data_dir: Optional path to the data directory. If None, uses config.

    Returns:
        Dict with keys:
            - has_real_data (bool)
            - is_unpaired (bool)
            - fallback_mode (str): 'none', 'synthetic', or 'population'
            - issues (List[str])
    """
    logger = get_data_ingestion_logger()
    config = get_config()

    if data_dir is None:
        # Default to project root data/raw if config doesn't specify
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        data_dir = project_root / 'data' / 'raw'
        if not data_dir.exists():
            # Try to find it relative to config
            if 'data' in config and 'raw_dir' in config['data']:
                data_dir = Path(config['data']['raw_dir'])
            else:
                data_dir = project_root / 'data' / 'raw'

    logger.info(f"Checking data availability in: {data_dir}")

    has_paired, has_unpaired, issues = _scan_directory_for_pairs(data_dir)

    # Determine fallback mode based on findings
    fallback_mode = 'none'
    is_unpaired = False

    if has_paired:
        logger.info("Real paired data detected. Proceeding with standard analysis.")
    elif has_unpaired:
        logger.warning("No paired data found. Only unpaired aggregate thermal data detected.")
        is_unpaired = True
        fallback_mode = 'population'
        issues.append("Plan vs Spec Contradiction: Spec assumes paired data, but only unpaired aggregate data found. Routing to population-level analysis (T031d).")
    else:
        logger.warning("No real data found (neither paired nor unpaired).")
        fallback_mode = 'synthetic'
        issues.append("Plan vs Spec Contradiction: Plan assumes 'no data' requires synthetic fallback, but Spec assumes data exists. Fallback mode: synthetic generation for pipeline validation only.")

    return {
        'has_real_data': has_paired or has_unpaired,
        'has_paired': has_paired,
        'is_unpaired': is_unpaired,
        'fallback_mode': fallback_mode,
        'issues': issues,
        'data_directory': str(data_dir)
    }


def write_status(status: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Writes the data status to `state/data_status.json`.

    Args:
        status: The status dictionary from check_data_availability.
        output_path: Optional path to the status file. Defaults to project_root/state/data_status.json.

    Returns:
        Path to the written file.
    """
    if output_path is None:
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        output_path = project_root / 'state' / 'data_status.json'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Add timestamp and checksum for auditability
    import time
    status['timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if os.path.exists(output_path):
        # Preserve previous checksum if available
        status['previous_checksum'] = compute_file_sha256(output_path)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)

    logger = get_data_ingestion_logger()
    logger.info(f"Data status written to {output_path}")
    return output_path


def verify_and_save(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main entry point for T012a. Checks data availability and saves the status.

    Args:
        output_path: Optional path for the status file.

    Returns:
        The status dictionary.
    """
    status = check_data_availability()
    write_status(status, output_path)
    return status
