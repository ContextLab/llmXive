import os
import json
import logging
import sys
import hashlib
import yaml
from typing import Dict, List, Any, Optional, Set
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/data_loader.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_DIR = Path('data/raw')
STATE_DIR = Path('state')
ARTIFACT_HASHES_FILE = STATE_DIR / 'artifact_hashes.yaml'
SCHEMA_FILE = Path('contracts/dataset.schema.yaml')

# Expected domain values based on spec
VALID_DOMAINS: Set[str] = {'medical', 'office', 'education', 'household'}

# Expected role format (simplified regex check)
# Roles should be non-empty strings, typically single words or simple phrases
VALID_ROLE_PATTERN = r'^[a-zA-Z0-9_\s]+$'

def ensure_dirs():
    """Ensure required directories exist."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def load_schema(schema_path: Path = SCHEMA_FILE) -> Dict[str, Any]:
    """Load the dataset schema from YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a single file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_hash(dir_path: Path) -> str:
    """Compute SHA256 hash of all files in a directory (deterministic order)."""
    sha256_hash = hashlib.sha256()
    files = sorted(dir_path.glob('*'))
    for file_path in files:
        if file_path.is_file():
          # Include relative path in hash to detect file moves
          relative_path = file_path.relative_to(dir_path).as_posix().encode('utf-8')
          sha256_hash.update(relative_path)
          sha256_hash.update(compute_file_hash(file_path).encode('utf-8'))
    return sha256_hash.hexdigest()

def validate_checksum() -> bool:
    """
    Validate the checksum of raw data against state/artifact_hashes.yaml.
    
    Returns:
        bool: True if checksum matches or if it's the first run (no checksum file).
        
    Raises:
        ValueError: If checksum file exists but data doesn't match.
    """
    if not ARTIFACT_HASHES_FILE.exists():
        logger.info("First run detected: Checksum file missing. Proceeding without verification.")
        return True
    
    try:
        with open(ARTIFACT_HASHES_FILE, 'r') as f:
            state_data = yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load artifact_hashes.yaml: {e}. Proceeding without verification.")
        return True
    
    if 'gatemem_test' not in state_data:
        logger.info("First run detected: Checksum file missing gatemem_test key. Proceeding without verification.")
        return True
    
    stored_hash = state_data['gatemem_test']
    
    if not RAW_DATA_DIR.exists() or not any(RAW_DATA_DIR.iterdir()):
        logger.warning("Raw data directory is empty. Cannot verify checksum.")
        return False
    
    current_hash = compute_directory_hash(RAW_DATA_DIR)
    
    if current_hash != stored_hash:
        error_msg = "Checksum mismatch. Data integrity compromised."
        logger.error(error_msg)
        logger.error(f"Expected: {stored_hash}")
        logger.error(f"Actual: {current_hash}")
        raise ValueError(error_msg)
    
    logger.info("Checksum verification passed.")
    return True

def parse_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse a JSONL file into a list of episode dictionaries.
    
    Args:
        file_path: Path to the JSONL file.
        
    Returns:
        List of episode dictionaries.
        
    Note:
        Malformed JSON lines are logged and skipped (recoverable).
    """
    episodes = []
    
    if not file_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                episode = json.loads(line)
                episodes.append(episode)
            except json.JSONDecodeError as e:
                logger.warning(f"Malformed JSON at line {line_num} in {file_path.name}: {e}. Skipping line.")
                continue
    
    return episodes

def extract_fields(episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Explicitly extract and load required fields from episodes.
    
    Args:
        episodes: List of raw episode dictionaries.
        
    Returns:
        List of episodes with only required fields.
        
    Raises:
        ValueError: If any required field is missing from an episode.
    """
    REQUIRED_FIELDS = ['outcome', 'predictors', 'covariates', 'leak-target', 'roles', 'domains']
    extracted = []
    
    for i, episode in enumerate(episodes):
        missing_fields = [field for field in REQUIRED_FIELDS if field not in episode]
        
        if missing_fields:
            error_msg = f"Episode {i} is missing required fields: {missing_fields}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        extracted.append({
            'outcome': episode['outcome'],
            'predictors': episode['predictors'],
            'covariates': episode['covariates'],
            'leak-target': episode['leak-target'],
            'roles': episode['roles'],
            'domains': episode['domains']
        })
    
    return extracted

def validate_episode(episode: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate an episode against the dataset schema and semantic constraints.
    
    This function performs:
    1. Schema validation (presence and type of required fields)
    2. Semantic validation (domain values, role format)
    3. Checksum verification (if checksum file exists)
    
    Args:
        episode: The episode dictionary to validate.
        schema: Optional pre-loaded schema. If None, it will be loaded.
        
    Returns:
        bool: True if the episode is valid.
        
    Raises:
        ValueError: If the episode fails validation or checksum mismatch.
    """
    # 1. Checksum Verification (Runtime)
    # This is done once per batch/episode processing, not per individual episode
    # to avoid redundant I/O. We assume the caller has already verified or will verify.
    # However, per task requirements, we check here if the file exists and matches.
    # We do this check only once per call sequence, but since this is a function,
    # we check every time to ensure data integrity before processing.
    # Optimization: In a real pipeline, this would be moved to the top-level loader.
    # For this task, we implement the check as specified.
    validate_checksum()
    
    # 2. Load Schema if not provided
    if schema is None:
        schema = load_schema()
    
    # 3. Schema Validation
    required_keys = ['leak-target', 'roles', 'domains', 'outcome', 'predictors', 'covariates']
    for key in required_keys:
        if key not in episode:
            logger.error(f"Validation error: Missing required field '{key}' in episode.")
            return False
    
    # Type validation based on schema (simplified)
    # Assuming schema defines types as strings like 'string', 'list', 'dict'
    type_map = {
        'leak-target': str,
        'roles': (list, str), # Could be list of roles or single string
        'domains': (list, str),
        'outcome': (dict, str),
        'predictors': (dict, list),
        'covariates': (dict, list)
    }
    
    for key, expected_type in type_map.items():
        if not isinstance(episode[key], expected_type):
            logger.error(f"Validation error: Field '{key}' has wrong type. Expected {expected_type}, got {type(episode[key])}.")
            return False

    # 4. Semantic Validation
    # Validate 'domains'
    if isinstance(episode['domains'], list):
        domains = episode['domains']
    else:
        domains = [episode['domains']]
    
    for domain in domains:
        if domain not in VALID_DOMAINS:
            logger.error(f"Validation error: Invalid domain '{domain}'. Expected one of {VALID_DOMAINS}.")
            return False
    
    # Validate 'roles'
    if isinstance(episode['roles'], list):
        roles = episode['roles']
    else:
        roles = [episode['roles']]
    
    import re
    for role in roles:
        if not isinstance(role, str) or not re.match(VALID_ROLE_PATTERN, role):
            logger.error(f"Validation error: Invalid role format '{role}'. Roles must be alphanumeric/underscore/space.")
            return False
    
    return True

def run_data_loader_pipeline() -> List[Dict[str, Any]]:
    """
    Run the full data loading and validation pipeline.
    
    Returns:
        List of validated episodes.
    """
    ensure_dirs()
    
    # Load schema
    schema = load_schema()
    
    # Find all JSONL files in raw data directory
    jsonl_files = list(RAW_DATA_DIR.glob('*.jsonl'))
    
    if not jsonl_files:
        logger.warning("No JSONL files found in data/raw/.")
        return []
    
    all_episodes = []
    
    for file_path in jsonl_files:
        logger.info(f"Processing file: {file_path}")
        try:
            episodes = parse_jsonl(file_path)
            extracted = extract_fields(episodes)
            
            # Validate each episode
            valid_episodes = []
            for episode in extracted:
                if validate_episode(episode, schema):
                    valid_episodes.append(episode)
                else:
                    logger.warning(f"Skipping invalid episode from {file_path.name}")
            
            all_episodes.extend(valid_episodes)
            logger.info(f"Loaded and validated {len(valid_episodes)} episodes from {file_path.name}")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            continue
    
    return all_episodes

def get_dataset_statistics(episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate basic statistics about the loaded dataset.
    
    Args:
        episodes: List of validated episodes.
        
    Returns:
        Dictionary with statistics.
    """
    if not episodes:
        return {'total_episodes': 0, 'domains': {}, 'roles': {}}
    
    domain_counts = {}
    role_counts = {}
    
    for episode in episodes:
        # Count domains
        domains = episode['domains']
        if isinstance(domains, list):
            for d in domains:
                domain_counts[d] = domain_counts.get(d, 0) + 1
        else:
            domain_counts[domains] = domain_counts.get(domains, 0) + 1
        
        # Count roles
        roles = episode['roles']
        if isinstance(roles, list):
            for r in roles:
                role_counts[r] = role_counts.get(r, 0) + 1
        else:
            role_counts[roles] = role_counts.get(roles, 0) + 1
    
    return {
        'total_episodes': len(episodes),
        'domains': domain_counts,
        'roles': role_counts
    }

def main():
    """Main entry point for data loader."""
    logger.info("Starting data loader pipeline...")
    
    try:
        episodes = run_data_loader_pipeline()
        stats = get_dataset_statistics(episodes)
        
        logger.info(f"Pipeline completed. Total valid episodes: {stats['total_episodes']}")
        logger.info(f"Domain distribution: {stats['domains']}")
        logger.info(f"Role distribution: {stats['roles']}")
        
        # Save statistics
        stats_file = Path('data/processed/dataset_statistics.json')
        stats_file.parent.mkdir(parents=True, exist_ok=True)
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Statistics saved to {stats_file}")
        
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
