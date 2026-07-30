import os
import sys
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/interim/manifest_generation.log')
    ]
)
logger = logging.getLogger(__name__)

def load_error_log(error_log_path: Path) -> Dict[str, str]:
    """
    Load the generation error log to identify excluded items.
    Returns a dictionary mapping stimulus IDs to exclusion reasons.
    """
    excluded_items = {}
    if not error_log_path.exists():
        logger.warning(f"Error log not found at {error_log_path}. No exclusions recorded.")
        return excluded_items

    with open(error_log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Expected format: "ERROR: <stimulus_id> - <reason>" or similar
            # We parse based on common log patterns from stimulus_gen.py
            if "ERROR" in line or "excluded" in line.lower():
                # Heuristic parsing: extract ID and reason
                # Assuming format: "ERROR: <id> - <reason>"
                parts = line.split(" - ", 1)
                if len(parts) == 2:
                    # Clean up the first part to get the ID
                    id_part = parts[0].replace("ERROR:", "").replace("ERROR: ", "").strip()
                    # If the ID part contains more structure, try to extract the actual ID
                    # e.g., "ERROR: stimulus_001_anger_3flank_10ecc" -> "stimulus_001_anger_3flank_10ecc"
                    # For simplicity, we assume the ID is the last word before " - " or the whole first part if it looks like an ID
                    if id_part.startswith("stimulus_"):
                        stimulus_id = id_part
                    else:
                        # Fallback: try to extract a stimulus_... pattern
                        match = re.search(r'stimulus_\w+', id_part)
                        if match:
                            stimulus_id = match.group(0)
                        else:
                            stimulus_id = id_part # Fallback to the whole string
                    
                    reason = parts[1].strip()
                    excluded_items[stimulus_id] = reason
                    logger.debug(f"Found excluded item: {stimulus_id} -> {reason}")
    return excluded_items

def extract_metadata_from_filename(filename: str) -> Optional[Dict[str, Any]]:
    """
    Extract metadata (emotion, flanker_count, eccentricity) from the stimulus filename.
    Expected filename pattern: stimulus_{id}_{emotion}_{flankers}flank_{ecc}ecc.png (example)
    Adjust regex based on actual naming convention from stimulus_gen.py
    """
    # Pattern based on typical generation: stimulus_<id>_<emotion>_<flankers>flank_<ecc>ecc.png
    # We need to be flexible. Let's assume the filename contains these keywords.
    # A robust pattern might be:
    # stimulus_(?P<id>\w+)_(?P<emotion>\w+)_(?P<flankers>\d+)flank_(?P<ecc>\d+)ecc\.png
    pattern = r'stimulus_(?P<id>[\w-]+)_(?P<emotion>[\w-]+)_(?P<flankers>\d+)flank_(?P<ecc>\d+)ecc\.png'
    match = re.match(pattern, filename)
    
    if match:
        return {
            'filename': filename,
            'id': match.group('id'),
            'emotion': match.group('emotion'),
            'flanker_count': int(match.group('flankers')),
            'eccentricity': int(match.group('ecc')),
            'status': 'generated' # Default status
        }
    
    # Fallback pattern if naming is different (e.g., just numbers)
    pattern_fallback = r'stimulus_(?P<id>[\w-]+)_(?P<emotion>[\w-]+)_(?P<flankers>\d+)_(?P<ecc>\d+)\.png'
    match_fallback = re.match(pattern_fallback, filename)
    if match_fallback:
        return {
            'filename': filename,
            'id': match_fallback.group('id'),
            'emotion': match_fallback.group('emotion'),
            'flanker_count': int(match_fallback.group('flankers')),
            'eccentricity': int(match_fallback.group('ecc')),
            'status': 'generated'
        }

    logger.warning(f"Could not parse metadata from filename: {filename}")
    return None

def get_stimuli_files(stimuli_dir: Path) -> List[Path]:
    """
    Get all image files from the stimuli directory.
    """
    if not stimuli_dir.exists():
        raise FileNotFoundError(f"Stimuli directory not found: {stimuli_dir}")
    
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    files = []
    for ext in image_extensions:
        files.extend(stimuli_dir.glob(f"*{ext}"))
        files.extend(stimuli_dir.glob(f"*{ext.upper()}"))
    
    return sorted(files)

def generate_manifest(stimuli_dir: Path, error_log_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Generate the stimuli manifest JSON file.
    1. Read error log to get excluded items.
    2. Scan stimuli directory for generated images.
    3. Extract metadata from filenames.
    4. Validate that every image has an entry.
    5. Update status for excluded items if they somehow appear (or log if missing).
    6. Write the manifest.
    """
    logger.info(f"Generating manifest for stimuli in {stimuli_dir}")
    logger.info(f"Reading error log from {error_log_path}")

    # Load excluded items
    excluded_items = load_error_log(error_log_path)
    logger.info(f"Found {len(excluded_items)} excluded items in error log.")

    # Get all stimulus files
    stimuli_files = get_stimuli_files(stimuli_dir)
    logger.info(f"Found {len(stimuli_files)} stimulus images.")

    manifest_entries = []
    missing_entries = []

    for file_path in stimuli_files:
        filename = file_path.name
        metadata = extract_metadata_from_filename(filename)
        
        if not metadata:
            missing_entries.append(filename)
            logger.warning(f"Skipping {filename}: Could not extract metadata.")
            continue

        # Check if this item was excluded (shouldn't happen if generation is correct, but for robustness)
        if metadata['id'] in excluded_items:
            metadata['status'] = 'excluded'
            metadata['exclusion_reason'] = excluded_items[metadata['id']]
            logger.warning(f"Found image for excluded item {metadata['id']}. Marking as excluded.")
        else:
            metadata['status'] = 'generated'

        # Ensure relative path for the manifest
        metadata['file_path'] = str(file_path.relative_to(stimuli_dir.parent))
        
        manifest_entries.append(metadata)

    # Log any missing metadata
    if missing_entries:
        logger.error(f"Failed to parse metadata for {len(missing_entries)} files: {missing_entries}")

    # Validate completeness: Every image should have an entry
    parsed_ids = {entry['id'] for entry in manifest_entries if entry['status'] == 'generated'}
    # Note: We don't expect excluded items to be in the directory, but if they are, they are handled.
    
    logger.info(f"Manifest generated with {len(manifest_entries)} entries.")
    logger.info(f"  - Generated: {len([e for e in manifest_entries if e['status'] == 'generated'])}")
    logger.info(f"  - Excluded: {len([e for e in manifest_entries if e['status'] == 'excluded'])}")

    # Create the final manifest structure
    manifest = {
        "version": "1.0",
        "generated_at": str(Path(output_path).parent), # Or a timestamp
        "total_items": len(manifest_entries),
        "stimuli": manifest_entries
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Manifest written to {output_path}")
    return manifest

def main():
    """
    Entry point for generating the stimuli manifest.
    """
    # Define paths relative to project root
    # Assuming the script is run from the project root or code/
    project_root = Path(__file__).resolve().parent.parent.parent
    
    stimuli_dir = project_root / "data" / "interim" / "stimuli"
    error_log_path = project_root / "data" / "interim" / "generation_errors.log"
    output_path = project_root / "data" / "interim" / "stimuli_manifest.json"

    # Check prerequisites
    if not stimuli_dir.exists():
        logger.error(f"Stimuli directory does not exist: {stimuli_dir}")
        logger.error("Please ensure T013 (stimulus_gen.py) has been run successfully.")
        sys.exit(1)

    if not error_log_path.exists():
        logger.warning(f"Error log does not exist: {error_log_path}. Proceeding with empty exclusion list.")

    try:
        generate_manifest(stimuli_dir, error_log_path, output_path)
        logger.info("T014 completed successfully.")
    except Exception as e:
        logger.error(f"Failed to generate manifest: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
