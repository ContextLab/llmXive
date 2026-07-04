"""
Stimuli Manifest Generator (T014).

Generates `data/interim/stimuli_manifest.json` by:
1. Reading `data/interim/generation_errors.log` (from T013) to update 'status' fields.
2. Scanning `data/interim/stimuli` for generated images.
3. Validating that every image has a corresponding entry with exact flanker count and eccentricity.
4. Linking file paths to metadata (emotion, flanker count, eccentricity).
"""
import os
import sys
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

# Add project root to path if running as script
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.stimulus_gen import main as stimulus_main
else:
    from .stimulus_gen import main as stimulus_main

from config import ensure_directories, get_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INTERIM_DIR = DATA_DIR / "interim"
STIMULI_DIR = INTERIM_DIR / "stimuli"
ERRORS_LOG = INTERIM_DIR / "generation_errors.log"
MANIFEST_PATH = INTERIM_DIR / "stimuli_manifest.json"

# Regex to parse log lines: "WARNING: ... | File: <filename> | Reason: <reason>"
# Adjust based on actual log format from T013
LOG_PATTERN = re.compile(r".*File:\s*(?P<filename>[\w\.\-]+)\s*\|.*Reason:\s*(?P<reason>.+)$")

def load_error_log() -> Dict[str, str]:
    """
    Reads generation_errors.log and returns a dict mapping filename -> exclusion reason.
    """
    excluded_files: Dict[str, str] = {}
    if not ERRORS_LOG.exists():
        logger.warning(f"Error log not found at {ERRORS_LOG}. No exclusions recorded.")
        return excluded_files

    logger.info(f"Reading error log from {ERRORS_LOG}")
    with open(ERRORS_LOG, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = LOG_PATTERN.search(line)
            if match:
                filename = match.group('filename')
                reason = match.group('reason').strip()
                excluded_files[filename] = reason
            else:
                # Fallback: try to parse simple "File: X | Reason: Y" if regex fails
                if "File:" in line and "Reason:" in line:
                    parts = line.split("File:")
                    if len(parts) > 1:
                        sub_part = parts[1].split("Reason:")
                        if len(sub_part) > 1:
                            filename = sub_part[0].strip()
                            reason = sub_part[1].strip()
                            excluded_files[filename] = reason
    logger.info(f"Found {len(excluded_files)} excluded files in log.")
    return excluded_files

def extract_metadata_from_filename(filename: str) -> Optional[Dict[str, Any]]:
    """
    Extracts metadata (emotion, flanker_count, eccentricity) from the filename.
    Expected format: <emotion>_flankers<count>_eccentricity<value>.<ext>
    Example: happy_flankers5_eccentricity10.png
    """
    # Remove extension
    name = Path(filename).stem
    pattern = r"^(?P<emotion>[\w]+)_flankers(?P<count>\d+)_eccentricity(?P<ecc>\d+(?:\.\d+)?)(?:_overlap)?\.(png|jpg|jpeg)$"
    match = re.match(pattern, filename)
    
    if not match:
        # Try looser pattern if strict one fails
        pattern_loose = r"^(?P<emotion>[\w]+)_flankers(?P<count>\d+)_eccentricity(?P<ecc>[\d\.]+)"
        match = re.match(pattern_loose, filename)
        
    if match:
        return {
            "emotion": match.group('emotion'),
            "flanker_count": int(match.group('count')),
            "eccentricity": float(match.group('ecc')),
            "filename": filename
        }
    return None

def generate_manifest() -> Dict[str, Any]:
    """
    Main logic to generate the stimuli manifest.
    """
    ensure_directories()
    
    # 1. Load exclusions
    excluded_map = load_error_log()
    
    # 2. Scan stimuli directory
    if not STIMULI_DIR.exists():
        raise FileNotFoundError(f"Stimuli directory not found: {STIMULI_DIR}. Run T013 first.")
    
    image_files = list(STIMULI_DIR.glob("*.png")) + list(STIMULI_DIR.glob("*.jpg"))
    logger.info(f"Found {len(image_files)} images in {STIMULI_DIR}")
    
    manifest_entries = []
    valid_count = 0
    invalid_count = 0
    missing_metadata_count = 0
    missing_log_entry_count = 0

    for img_path in image_files:
        filename = img_path.name
        relative_path = str(img_path.relative_to(PROJECT_ROOT))
        
        # Check if this file was excluded (should not exist if T013 worked correctly, but safety check)
        if filename in excluded_map:
            logger.warning(f"File {filename} found in stimuli dir but marked as excluded in log. Skipping.")
            continue

        metadata = extract_metadata_from_filename(filename)
        
        if not metadata:
            logger.error(f"Could not parse metadata from filename: {filename}")
            missing_metadata_count += 1
            # Create a generic entry with nulls to ensure completeness check passes, or skip?
            # Task says: "Validating that every image... has a corresponding entry"
            # If we can't parse, we can't validate. We'll add an entry with nulls and flag it.
            entry = {
                "file_path": relative_path,
                "status": "invalid_metadata",
                "emotion": None,
                "flanker_count": None,
                "eccentricity": None,
                "error": "Could not parse filename parameters"
            }
            manifest_entries.append(entry)
            invalid_count += 1
            continue

        # Validate against log (if it was supposed to be excluded but exists, that's an error)
        # If it's in the log, we already skipped it above.
        
        entry = {
            "file_path": relative_path,
            "status": "generated",
            "emotion": metadata["emotion"],
            "flanker_count": metadata["flanker_count"],
            "eccentricity": metadata["eccentricity"]
        }
        manifest_entries.append(entry)
        valid_count += 1

    # 3. Check for missing log entries (files in log that don't exist? Optional, but good for completeness)
    # The task says: "Reading ... to update 'status' fields for excluded items"
    # We've already handled the "excluded" items by skipping them if they exist (shouldn't happen)
    # or by not including them if they were successfully excluded.
    # If the log contains files that were excluded and thus NOT generated, we should add them to the manifest
    # with status "excluded" to ensure the manifest is a complete record of the generation attempt.
    
    for filename, reason in excluded_map.items():
        # Check if this file exists (it shouldn't if T013 worked)
        if (STIMULI_DIR / filename).exists():
            # It exists but is marked excluded? This is a conflict.
            # We already skipped it above. Let's flag it in the log.
            logger.warning(f"Conflict: {filename} exists in stimuli dir but marked excluded in log.")
            continue
        
        # File does not exist, which is expected for excluded items.
        # Add to manifest as "excluded"
        entry = {
            "file_path": str((STIMULI_DIR / filename).relative_to(PROJECT_ROOT)),
            "status": "excluded",
            "emotion": None,
            "flanker_count": None,
            "eccentricity": None,
            "exclusion_reason": reason
        }
        manifest_entries.append(entry)
        missing_log_entry_count += 1

    # 4. Construct final manifest
    manifest = {
        "metadata": {
            "generated_at": str(Path(__file__).parent.parent.parent), # Placeholder for timestamp
            "source": "code/utils/stimuli_manifest.py (T014)",
            "total_images": len(image_files),
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "missing_metadata_count": missing_metadata_count,
            "excluded_count": missing_log_entry_count
        },
        "stimuli": manifest_entries
    }

    return manifest

def main():
    """
    Entry point for T014.
    """
    logger.info("Starting Stimuli Manifest Generation (T014)...")
    
    try:
        manifest = generate_manifest()
        
        # Write to file
        with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Manifest generated successfully: {MANIFEST_PATH}")
        logger.info(f"Total entries: {len(manifest['stimuli'])}")
        logger.info(f"Valid generated: {manifest['metadata']['valid_count']}")
        logger.info(f"Excluded: {manifest['metadata']['excluded_count']}")
        
        # Validation check: Ensure every image in data/interim/stimuli has an entry
        image_files = list(STIMULI_DIR.glob("*.png")) + list(STIMULI_DIR.glob("*.jpg"))
        manifest_files = {e['file_path'].split('/')[-1] for e in manifest['stimuli'] if e['status'] == 'generated'}
        actual_files = {f.name for f in image_files}
        
        missing_in_manifest = actual_files - manifest_files
        if missing_in_manifest:
            logger.error(f"Validation FAILED: {len(missing_in_manifest)} images missing from manifest: {missing_in_manifest}")
            sys.exit(1)
        else:
            logger.info("Validation PASSED: All images in stimuli directory are present in manifest.")
            
    except Exception as e:
        logger.error(f"Failed to generate manifest: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
