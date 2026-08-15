import os
import sys
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure project root is in path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_error_log(error_log_path: Path) -> List[Dict[str, Any]]:
    """
    Load the generation error log to identify excluded items.
    Returns a list of dictionaries with error details.
    """
    if not error_log_path.exists():
        logger.warning(f"Error log not found at {error_log_path}. No exclusions to record.")
        return []
    
    exclusions = []
    try:
        with open(error_log_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    # Assuming log format is JSON or parseable key-value
                    # If it's a raw log line, we might need regex, but let's assume JSON for structured logging
                    if line.startswith('{'):
                        exclusions.append(json.loads(line))
                    else:
                        # Fallback for non-JSON log lines if necessary, though T013 should log JSON
                        logger.debug(f"Skipping unparseable error log line: {line}")
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse error log line as JSON: {line}")
    except Exception as e:
        logger.error(f"Failed to read error log {error_log_path}: {e}")
    
    return exclusions

def extract_metadata_from_filename(filename: str) -> Optional[Dict[str, Any]]:
    """
    Extract emotion, flanker count, and eccentricity from the stimulus filename.
    Expected pattern: stimulus_emotion_flankers_{n}_eccentricity_{e}.png (example)
    Adjust regex based on actual naming convention in T013.
    """
    # Pattern assumption based on T013 requirements:
    # We need to capture: emotion, flanker_count, eccentricity
    # Example: stimulus_angry_5flankers_10deg.png -> emotion=angry, flankers=5, eccentricity=10
    # Let's make it robust to variations like 'flankers' or 'f', 'deg' or 'ecc'
    
    # Generic pattern to capture numbers and text before/after known keywords
    # Assuming format: ..._emotion_{val}_flankers_{n}_eccentricity_{e}...
    pattern = r".*_(?P<emotion>[a-z]+).*flanker[s]?\s*[=:]\s*(?P<flankers>\d+).*eccentricity[=:]\s*(?P<eccentricity>[\d.]+).*"
    # Simpler pattern if filename is strict: stimulus_{emotion}_flankers_{n}_eccentricity_{e}.png
    strict_pattern = r"stimulus_(?P<emotion>[a-z_]+)_flankers_(?P<flankers>\d+)_eccentricity_(?P<eccentricity>[\d.]+)\.png"
    
    match = re.match(strict_pattern, filename)
    if match:
        return {
            "emotion": match.group('emotion'),
            "flanker_count": int(match.group('flankers')),
            "eccentricity": float(match.group('eccentricity'))
        }
    
    # Fallback to looser pattern if strict fails
    match = re.search(pattern, filename)
    if match:
        return {
            "emotion": match.group('emotion'),
            "flanker_count": int(match.group('flankers')),
            "eccentricity": float(match.group('eccentricity'))
        }
    
    return None

def get_stimuli_files(stimuli_dir: Path) -> List[Path]:
    """
    Scan the stimuli directory for generated image files.
    """
    if not stimuli_dir.exists():
        logger.error(f"Stimuli directory not found: {stimuli_dir}")
        return []
    
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp'}
    files = [
        f for f in stimuli_dir.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    logger.info(f"Found {len(files)} stimulus images in {stimuli_dir}")
    return sorted(files)

def generate_manifest(
    stimuli_dir: Path,
    error_log_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate the stimuli_manifest.json.
    
    1. Reads error log to identify excluded items (if any were tracked by filename).
    2. Scans stimuli_dir for images.
    3. Extracts metadata from filenames.
    4. Validates that every image has a corresponding entry with exact parameters.
    5. Writes the manifest to output_path.
    """
    # Load exclusions from error log
    exclusions = load_error_log(error_log_path)
    excluded_filenames = {exc.get('filename', '') for exc in exclusions if 'filename' in exc}
    
    # Get all image files
    image_files = get_stimuli_files(stimuli_dir)
    
    manifest_entries = []
    missing_metadata = []
    
    for img_path in image_files:
        filename = img_path.name
        metadata = extract_metadata_from_filename(filename)
        
        if metadata is None:
            logger.warning(f"Could not extract metadata from filename: {filename}")
            missing_metadata.append(filename)
            continue
        
        # Check if this file was logged as excluded (shouldn't happen if T013 works correctly)
        if filename in excluded_filenames:
            logger.warning(f"File {filename} found in stimuli dir but marked as excluded in error log.")
            # We still include it in the manifest but mark status as 'excluded' or 'error'
            metadata['status'] = 'excluded'
            metadata['exclusion_reason'] = next(
                (exc.get('reason', 'Unknown') for exc in exclusions if exc.get('filename') == filename),
                'Unknown'
            )
        else:
            metadata['status'] = 'generated'
        
        # Construct relative path for manifest
        rel_path = str(img_path.relative_to(stimuli_dir.parent)) # e.g., interim/stimuli/filename.png
        
        entry = {
            "file_path": rel_path,
            "filename": filename,
            "emotion": metadata['emotion'],
            "flanker_count": metadata['flanker_count'],
            "eccentricity": metadata['eccentricity'],
            "status": metadata['status'],
            "metadata_source": "filename"
        }
        
        if 'exclusion_reason' in metadata:
            entry['exclusion_reason'] = metadata['exclusion_reason']
        
        manifest_entries.append(entry)
    
    if missing_metadata:
        logger.error(f"Found {len(missing_metadata)} files with unparseable filenames: {missing_metadata[:5]}...")
    
    manifest = {
        "version": "1.0",
        "generated_at": str(Path(__file__).resolve()), # Or timestamp
        "stimuli_dir": str(stimuli_dir),
        "total_stimuli": len(manifest_entries),
        "total_excluded": len([e for e in manifest_entries if e['status'] == 'excluded']),
        "entries": manifest_entries
    }
    
    # Ensure output directory exists
    ensure_directories([output_path.parent])
    
    # Write manifest
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest generated with {len(manifest_entries)} entries at {output_path}")
    return manifest

def main():
    """
    CLI entry point for generating the stimuli manifest.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate stimuli manifest from generated images and error logs.")
    parser.add_argument(
        "--stimuli-dir",
        type=str,
        default="data/interim/stimuli",
        help="Path to the directory containing generated stimulus images."
    )
    parser.add_argument(
        "--error-log",
        type=str,
        default="data/interim/generation_errors.log",
        help="Path to the generation error log file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/interim/stimuli_manifest.json",
        help="Path for the output manifest JSON file."
    )
    
    args = parser.parse_args()
    
    stimuli_dir = Path(args.stimuli_dir)
    error_log_path = Path(args.error_log)
    output_path = Path(args.output)
    
    if not stimuli_dir.exists():
        logger.critical(f"Stimuli directory does not exist: {stimuli_dir}. Run T013 first.")
        sys.exit(1)
    
    manifest = generate_manifest(stimuli_dir, error_log_path, output_path)
    
    # Basic validation log
    total = manifest['total_stimuli']
    excluded = manifest['total_excluded']
    logger.info(f"Summary: {total} total entries, {excluded} excluded.")
    
    if total == 0:
        logger.warning("Manifest is empty. Check if stimuli were generated correctly.")

if __name__ == "__main__":
    main()
