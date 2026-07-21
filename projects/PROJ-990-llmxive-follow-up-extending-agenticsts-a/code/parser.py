import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_DIR = Path("data/raw")
CHECKSUM_FILE = Path("data/raw/.checksums.json")
MIN_FILE_SIZE = 0  # Must be non-empty, so > 0 bytes
REQUIRED_EXTENSIONS = ['.json', '.jsonl', '.log']

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute SHA256 checksum of a file.
    Reads file in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute checksum for {file_path}: {e}")
        raise

def load_existing_checksums() -> Dict[str, str]:
    """
    Load previously stored checksums from disk.
    Returns empty dict if file doesn't exist.
    """
    if not CHECKSUM_FILE.exists():
        return {}
    try:
        with open(CHECKSUM_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load checksums file: {e}. Starting fresh.")
        return {}

def save_checksums(checksums: Dict[str, str]) -> None:
    """
    Save checksums to disk.
    """
    try:
        CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CHECKSUM_FILE, 'w') as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Saved checksums to {CHECKSUM_FILE}")
    except IOError as e:
        logger.error(f"Failed to save checksums: {e}")
        raise

def validate_data_source() -> List[Path]:
    """
    Validate that data/raw/ contains non-empty, checksum-verified trajectory files.
    
    Returns:
        List[Path]: List of validated file paths.
        
    Raises:
        FileNotFoundError: If no trajectory files are found.
        ValueError: If files are empty or checksums don't match.
    """
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"Raw data directory not found: {RAW_DATA_DIR}")
    
    # Find all potential trajectory files
    trajectory_files = []
    for ext in REQUIRED_EXTENSIONS:
        trajectory_files.extend(RAW_DATA_DIR.glob(f"*{ext}"))
    
    if not trajectory_files:
        raise FileNotFoundError(
            f"No trajectory files found in {RAW_DATA_DIR}. "
            f"Expected files with extensions: {REQUIRED_EXTENSIONS}"
        )
    
    # Filter non-empty files
    non_empty_files = [f for f in trajectory_files if f.stat().st_size > 0]
    
    if not non_empty_files:
        raise ValueError(
            f"All files in {RAW_DATA_DIR} are empty. "
            "Trajectory files must contain data."
        )
    
    # Load existing checksums
    stored_checksums = load_existing_checksums()
    validated_files = []
    new_checksums = {}
    
    for file_path in non_empty_files:
        relative_path = str(file_path)
        current_checksum = compute_file_checksum(file_path)
        
        if relative_path in stored_checksums:
            if stored_checksums[relative_path] == current_checksum:
                logger.info(f"Checksum verified: {file_path.name}")
                validated_files.append(file_path)
            else:
                raise ValueError(
                    f"Checksum mismatch for {file_path.name}. "
                    "File may have been corrupted or modified. "
                    "Please restore the original file or re-download the dataset."
                )
        else:
            # First time seeing this file - store its checksum
            logger.info(f"Storing checksum for new file: {file_path.name}")
            validated_files.append(file_path)
        
        new_checksums[relative_path] = current_checksum
    
    # Save updated checksums
    save_checksums(new_checksums)
    
    logger.info(f"Validated {len(validated_files)} trajectory files.")
    return validated_files

def parse_turn_data(turn_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a single turn's data from trajectory log.
    
    Args:
        turn_json: Dictionary containing turn data
        
    Returns:
        Dictionary with parsed turn metrics
    """
    try:
        return {
            'turn_id': turn_json.get('turn_id', -1),
            'health': turn_json.get('health', 0),
            'threat_level': turn_json.get('threat_level', 0),
            'deck_size': turn_json.get('deck_size', 0),
            'legal_moves': turn_json.get('legal_moves', []),
            'selected_move': turn_json.get('selected_move', None),
            'entropy': turn_json.get('entropy', None),
            'token_count': turn_json.get('token_count', 0),
            'retrieved_layers': turn_json.get('retrieved_layers', [])
        }
    except Exception as e:
        logger.error(f"Error parsing turn data: {e}")
        raise

def extract_metrics_from_trajectory(trajectory_path: Path) -> List[Dict[str, Any]]:
    """
    Extract metrics from a single trajectory file.
    
    Args:
        trajectory_path: Path to trajectory file
        
    Returns:
        List of dictionaries containing turn-level metrics
    """
    metrics = []
    
    try:
        if trajectory_path.suffix == '.jsonl':
            with open(trajectory_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        turn_data = json.loads(line.strip())
                        parsed = parse_turn_data(turn_data)
                        parsed['source_file'] = trajectory_path.name
                        parsed['line_num'] = line_num
                        metrics.append(parsed)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON at {trajectory_path}:{line_num}: {e}")
                        continue
        elif trajectory_path.suffix == '.json':
            with open(trajectory_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for idx, turn_data in enumerate(data):
                        parsed = parse_turn_data(turn_data)
                        parsed['source_file'] = trajectory_path.name
                        parsed['turn_idx'] = idx
                        metrics.append(parsed)
                elif isinstance(data, dict):
                    parsed = parse_turn_data(data)
                    parsed['source_file'] = trajectory_path.name
                    metrics.append(parsed)
        elif trajectory_path.suffix == '.log':
            # Simple log parsing - each line is a JSON object
            with open(trajectory_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        turn_data = json.loads(line.strip())
                        parsed = parse_turn_data(turn_data)
                        parsed['source_file'] = trajectory_path.name
                        parsed['line_num'] = line_num
                        metrics.append(parsed)
                    except json.JSONDecodeError:
                        continue
        else:
            logger.warning(f"Unsupported file format: {trajectory_path.suffix}")
            
    except Exception as e:
        logger.error(f"Failed to extract metrics from {trajectory_path}: {e}")
        raise
    
    return metrics

def parse_trajectories(input_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Main entry point: Validate data source and parse all trajectory files.
    
    This function performs:
    1. Validates that data/raw/ contains non-empty, checksum-verified files
    2. Extracts metrics from all validated trajectory files
    3. Returns a consolidated DataFrame
    
    Args:
        input_dir: Optional directory to parse (defaults to data/raw)
        
    Returns:
        pd.DataFrame: Consolidated metrics with columns:
            - turn_id, health, threat_level, deck_size
            - legal_moves (list), selected_move
            - entropy, token_count, retrieved_layers (list)
            - source_file, line_num/turn_idx
    
    Raises:
        FileNotFoundError: If no valid trajectory files found
        ValueError: If files are empty or corrupted
    """
    target_dir = input_dir if input_dir else RAW_DATA_DIR
    
    logger.info(f"Starting trajectory parsing from {target_dir}")
    
    # STEP 1: Validate data source (T034 requirement)
    validated_files = validate_data_source()
    
    logger.info(f"Found {len(validated_files)} validated trajectory files")
    
    all_metrics = []
    
    # STEP 2: Extract metrics from all validated files
    for file_path in validated_files:
        logger.info(f"Processing {file_path.name}")
        try:
            file_metrics = extract_metrics_from_trajectory(file_path)
            all_metrics.extend(file_metrics)
            logger.info(f"  Extracted {len(file_metrics)} turns from {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            # Continue with other files rather than failing completely
            continue
    
    if not all_metrics:
        raise ValueError(
            "No valid metrics extracted from trajectory files. "
            "Check file formats and content."
        )
    
    # STEP 3: Create DataFrame
    df = pd.DataFrame(all_metrics)
    
    # Ensure legal_moves is stored as JSON string for CSV compatibility
    if 'legal_moves' in df.columns:
        df['legal_moves'] = df['legal_moves'].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else str(x)
        )
    
    if 'retrieved_layers' in df.columns:
        df['retrieved_layers'] = df['retrieved_layers'].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else str(x)
        )
    
    logger.info(f"Successfully parsed {len(df)} turns from {len(validated_files)} files")
    
    return df

def main():
    """
    Command-line entry point for trajectory parsing.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Parse trajectory logs from data/raw/')
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='data/processed/metrics_with_moves.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        default=None,
        help='Input directory (default: data/raw/)'
    )
    
    args = parser.parse_args()
    
    try:
        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Parse trajectories
        df = parse_trajectories(
            input_dir=Path(args.input_dir) if args.input_dir else None
        )
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Saved parsed metrics to {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Data source error: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during parsing: {e}")
        raise

if __name__ == '__main__':
    main()