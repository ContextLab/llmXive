import os
import sys
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any

# Ensure parent is in path for relative imports if run as script
_parent = Path(__file__).resolve().parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

from config import ensure_directories

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants based on project structure
STIMULI_DIR = Path("data/interim/stimuli")
ERROR_LOG_PATH = Path("data/interim/generation_errors.log")
MANIFEST_PATH = Path("data/interim/stimuli_manifest.json")

def load_error_log() -> List[Dict[str, Any]]:
    """
    Reads the generation_errors.log file and returns a list of error records.
    Each record is expected to be a JSON object per line.
    """
    errors = []
    if not ERROR_LOG_PATH.exists():
        logger.warning(f"Error log not found at {ERROR_LOG_PATH}. Proceeding with empty error list.")
        return errors

    with open(ERROR_LOG_PATH, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                errors.append(record)
            except json.JSONDecodeError:
                logger.warning(f"Skipping invalid JSON line {line_num} in error log: {line[:50]}...")
    return errors

def extract_metadata_from_filename(filename: str) -> Dict[str, Any]:
    """
    Parses the stimulus filename to extract metadata.
    Expected format: emotion_{emotion}_flanker_{count}_eccentricity_{val}.png
    Returns a dict with emotion, flanker_count, eccentricity, and original filename.
    """
    # Regex pattern to match the expected filename structure
    # Adjust if the actual naming convention in stimulus_gen.py differs slightly
    pattern = r"emotion_(?P<emotion>[\w]+)_flanker_(?P<count>\d+)_eccentricity_(?P<ecc>[\d.]+)\.png"
    match = re.match(pattern, filename)

    if not match:
        # Fallback or strict failure depending on requirements.
        # Here we return None to indicate it cannot be parsed,
        # but the main loop will handle logging.
        return None

    return {
        "filename": filename,
        "emotion": match.group('emotion'),
        "flanker_count": int(match.group('count')),
        "eccentricity": float(match.group('ecc'))
    }

def get_stimuli_files() -> List[Path]:
    """
    Returns a list of Path objects for all .png images in the stimuli directory.
    """
    if not STIMULI_DIR.exists():
        logger.error(f"Stimuli directory not found: {STIMULI_DIR}")
        return []
    
    files = list(STIMULI_DIR.glob("*.png"))
    # Also check for jpg if necessary, but spec implies png
    if not files:
        files = list(STIMULI_DIR.glob("*.jpg"))
    
    return sorted(files)

def generate_manifest() -> Dict[str, Any]:
    """
    Generates the complete stimuli manifest by:
    1. Scanning data/interim/stimuli for images.
    2. Extracting metadata from filenames.
    3. Cross-referencing with data/interim/generation_errors.log to mark status.
    4. Validating that every image has a corresponding entry with exact values.
    
    Returns a dictionary representing the manifest.
    """
    ensure_directories()
    
    error_logs = load_error_log()
    # Create a lookup for errors by a key (e.g., filename or a generated ID)
    # Since the error log likely contains the attempted parameters, we map by filename if present,
    # or by a combination of parameters if filename wasn't generated.
    # Assuming the error log contains 'filename' or 'params' that match our scan.
    error_lookup = {}
    for err in error_logs:
        key = err.get('filename') or err.get('params', {}).get('filename')
        if key:
            error_lookup[key] = err
    
    stimuli_files = get_stimuli_files()
    manifest_entries = []
    missing_metadata = []
    
    for file_path in stimuli_files:
        filename = file_path.name
        metadata = extract_metadata_from_filename(filename)
        
        if metadata is None:
            logger.warning(f"Could not extract metadata from filename: {filename}")
            missing_metadata.append(filename)
            continue
        
        # Check if this file was logged as an error (e.g. overlap detected but maybe saved?)
        # The task says: "Reading generation_errors.log to update 'status' fields for excluded items"
        # If an item is in the error log, it might be excluded.
        # However, if the file EXISTS in the directory, it was likely generated successfully.
        # We check the error log to see if there's a specific exclusion reason attached to this specific run.
        # If the error log says "Excluded due to overlap", and the file exists, it might be a discrepancy.
        # We assume: If file exists, it is valid. If error log exists for it, we record the warning/exclusion context if any.
        
        status = "valid"
        exclusion_reason = None
        
        if filename in error_lookup:
            err_record = error_lookup[filename]
            # If the error log indicates the item was excluded, we mark it.
            # But if the file exists, it implies it wasn't excluded from the disk output.
            # Let's assume the error log records attempts that FAILED to generate.
            # If the file exists, we might have a stale log or a partial generation.
            # For the manifest, we prioritize the existence of the file.
            # We add a note if the error log contains a warning associated with it.
            if err_record.get('status') == 'excluded':
                # This is a conflict: File exists but log says excluded.
                # We mark it as 'warning' and include the reason.
                status = "warning"
                exclusion_reason = err_record.get('reason', 'Unknown reason')
                logger.warning(f"File {filename} exists but marked as excluded in error log: {exclusion_reason}")
            else:
                status = "valid"
        
        entry = {
            "file_path": str(file_path.relative_to(Path.cwd())),
            "filename": filename,
            "emotion": metadata['emotion'],
            "flanker_count": metadata['flanker_count'],
            "eccentricity": metadata['eccentricity'],
            "status": status,
            "exclusion_reason": exclusion_reason
        }
        manifest_entries.append(entry)
    
    # Validation: Ensure every image has an entry
    # We already iterated over all images, so if we got here, we have entries for all parseable ones.
    # If there are unparseable filenames, we logged them.
    
    manifest = {
        "version": "1.0",
        "generated_at": str(Path.cwd().absolute()), # Or use datetime
        "total_stimuli": len(manifest_entries),
        "total_excluded": len([e for e in manifest_entries if e['status'] == 'excluded']),
        "stimuli": manifest_entries,
        "validation_notes": {
            "unparseable_filenames": missing_metadata,
            "error_log_path": str(ERROR_LOG_PATH),
            "stimuli_dir": str(STIMULI_DIR)
        }
    }
    
    return manifest

def main():
    """
    CLI entry point to generate the stimuli manifest.
    """
    logger.info("Starting stimuli manifest generation...")
    
    try:
        manifest = generate_manifest()
        
        # Write to disk
        with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Manifest generated successfully: {MANIFEST_PATH}")
        logger.info(f"Total stimuli recorded: {manifest['total_stimuli']}")
        
        if manifest['validation_notes']['unparseable_filenames']:
            logger.warning(f"Found {len(manifest['validation_notes']['unparseable_filenames'])} files with unparseable filenames.")
            
    except Exception as e:
        logger.error(f"Failed to generate manifest: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()