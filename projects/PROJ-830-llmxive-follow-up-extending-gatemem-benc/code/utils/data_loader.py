import os
import json
import logging
import sys
import hashlib
import yaml
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datasets import load_dataset

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
VALID_DOMAINS = {'medical', 'office', 'education', 'household'}
CHECKSUM_FILE = Path('state/artifact_hashes.yaml')
RAW_DATA_FILE = Path('data/raw/gatemem_test.jsonl')
SCHEMA_FILE = Path('contracts/dataset.schema.yaml')

def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the dataset schema from YAML."""
    if schema_path is None:
        schema_path = SCHEMA_FILE
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_checksum(raw_data_path: Optional[Path] = None, checksum_file_path: Optional[Path] = None) -> bool:
    """
    Verify the SHA-256 checksum of the raw data file against the stored checksum.
    
    Args:
        raw_data_path: Path to the raw data file (default: data/raw/gatemem_test.jsonl)
        checksum_file_path: Path to the checksum file (default: state/artifact_hashes.yaml)
        
    Returns:
        True if checksum matches, False otherwise.
        
    Raises:
        FileNotFoundError: If checksum file is missing.
        ValueError: If checksum mismatch.
    """
    if raw_data_path is None:
        raw_data_path = RAW_DATA_FILE
    if checksum_file_path is None:
        checksum_file_path = CHECKSUM_FILE

    # Check if checksum file exists
    if not checksum_file_path.exists():
        raise FileNotFoundError("Checksum file missing. Data integrity cannot be verified. Aborting.")

    # Check if raw data file exists
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data file missing: {raw_data_path}")

    # Load stored checksum
    with open(checksum_file_path, 'r') as f:
        checksum_data = yaml.safe_load(f)

    if 'gatemem_test' not in checksum_data:
        raise FileNotFoundError("Checksum file missing. Data integrity cannot be verified. Aborting.")

    stored_checksum = checksum_data['gatemem_test'].get('sha256')
    if not stored_checksum:
        raise ValueError("Checksum file exists but 'gatemem_test' entry is malformed.")

    # Compute current checksum
    sha256_hash = hashlib.sha256()
    with open(raw_data_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    computed_checksum = sha256_hash.hexdigest()

    if stored_checksum != computed_checksum:
        raise ValueError("Checksum mismatch. Data integrity compromised.")

    logger.info(f"Checksum verification passed for {raw_data_path}")
    return True

def validate_episode(
    episode: Dict[str, Any],
    schema: Optional[Dict[str, Any]] = None,
    validate_checksum: bool = True
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate a single episode against the dataset schema and perform semantic checks.
    
    This function:
    1. Validates presence of required fields (outcome, predictors, covariates, leak-target)
    2. Performs semantic validation (domain values, roles format)
    3. Verifies checksum of raw data file if validate_checksum is True
    
    Args:
        episode: The episode dictionary to validate.
        schema: The dataset schema (optional, will load if not provided).
        validate_checksum: Whether to verify the raw data checksum (default: True).
        
    Returns:
        A tuple of (validated_episode, list_of_warnings).
        The validated_episode will have a 'valid' key set to True or False.
        
    Raises:
        FileNotFoundError: If checksum file is missing and validate_checksum is True.
        ValueError: If checksum mismatch or required fields are missing.
    """
    warnings = []
    
    # Load schema if not provided
    if schema is None:
        schema = load_schema()
    
    # Checksum verification (performed once per call, not per episode, but required before processing)
    if validate_checksum:
        try:
            validate_checksum()
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Checksum verification failed: {e}")
            raise
    
    # Required fields from schema
    required_fields = ['outcome', 'predictors', 'covariates', 'leak-target']
    
    # Check presence of required fields
    missing_fields = []
    for field in required_fields:
        if field not in episode or episode[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Episode missing required fields: {missing_fields}")
    
    # Semantic validation for 'domain'
    domain = episode.get('covariates', {}).get('domain')
    if domain:
        if domain not in VALID_DOMAINS:
            warnings.append(f"Invalid domain value: {domain}. Expected one of {VALID_DOMAINS}")
            episode['valid'] = False
        else:
            episode['valid'] = True
    else:
        # If domain is missing, we can't validate it, but we don't fail the episode yet
        # unless the schema requires it. We'll flag it as a warning.
        warnings.append("Missing 'domain' in covariates. Cannot perform semantic validation.")
        episode['valid'] = False
    
    # Semantic validation for 'roles'
    roles = episode.get('roles', [])
    if roles and not isinstance(roles, list):
        warnings.append(f"Invalid roles format: expected list, got {type(roles)}")
        episode['valid'] = False
    elif roles:
        # Check if roles are strings
        non_string_roles = [r for r in roles if not isinstance(r, str)]
        if non_string_roles:
            warnings.append(f"Roles contain non-string values: {non_string_roles}")
            episode['valid'] = False
        else:
            # Basic format check: roles should not be empty strings
            empty_roles = [r for r in roles if not r.strip()]
            if empty_roles:
                warnings.append("Roles contain empty strings")
                episode['valid'] = False
            else:
                if 'valid' not in episode:
                    episode['valid'] = True
    
    # Log anomalies if any
    if warnings:
        for warning in warnings:
            logger.warning(f"Episode {episode.get('episode_id', 'unknown')}: {warning}")
    
    return episode, warnings

def fetch_dataset(
    config: str = 'default',
    split: str = 'test',
    streaming: bool = True
) -> Any:
    """
    Fetch the GateMem dataset from HuggingFace.
    
    Args:
        config: Dataset configuration name (default: 'default')
        split: Dataset split to load (default: 'test')
        streaming: Whether to stream the dataset (default: True)
        
    Returns:
        The loaded dataset.
        
    Raises:
        ConnectionError: If the dataset fetch fails.
    """
    try:
        logger.info(f"Fetching GateMem dataset (config={config}, split={split}, streaming={streaming})")
        dataset = load_dataset(
            'gatekeeper/gatemem',
            config=config,
            split=split,
            streaming=streaming
        )
        logger.info("Dataset fetched successfully")
        return dataset
    except Exception as e:
        logger.error(f"Critical: Real Data Fetch Failed: {e}")
        raise ConnectionError(f"Failed to fetch dataset: {e}")

def parse_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse a JSONL file into a list of episode dictionaries.
    
    Args:
        file_path: Path to the JSONL file.
        
    Returns:
        List of episode dictionaries.
    """
    episodes = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                episode = json.loads(line)
                episodes.append(episode)
            except json.JSONDecodeError as e:
                logger.warning(f"Malformed JSON at line {line_num}: {e}. Skipping line.")
    return episodes

def extract_fields(episode: Dict[str, Any]) -> Dict[str, Any]:
    """
    Explicitly extract and load required fields from an episode.
    
    Args:
        episode: The episode dictionary.
        
    Returns:
        A dictionary with the extracted fields.
        
    Raises:
        ValueError: If any required field is missing.
    """
    required_fields = ['outcome', 'predictors', 'covariates', 'leak-target', 'roles', 'domains']
    extracted = {}
    
    for field in required_fields:
        if field not in episode:
            raise ValueError(f"Required field '{field}' missing from episode")
        extracted[field] = episode[field]
    
    return extracted

def ensure_dirs() -> None:
    """Ensure all required directories exist."""
    directories = [
        'data/raw',
        'data/processed',
        'data/samples',
        'state',
        'logs',
        'contracts',
        'tests'
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {directory}")

def run_data_loader_pipeline() -> Dict[str, Any]:
    """
    Run the full data loading pipeline.
    
    Returns:
        A dictionary with pipeline results.
    """
    ensure_dirs()
    
    # Fetch dataset
    try:
        dataset = fetch_dataset()
    except ConnectionError as e:
        return {'success': False, 'error': str(e)}
    
    # Validate checksum if file exists
    if RAW_DATA_FILE.exists():
        try:
            validate_checksum()
        except (FileNotFoundError, ValueError) as e:
            return {'success': False, 'error': f"Checksum validation failed: {e}"}
    
    return {'success': True, 'dataset': dataset}

def get_dataset_statistics(dataset: Any) -> Dict[str, Any]:
    """
    Get basic statistics about the dataset.
    
    Args:
        dataset: The dataset object.
        
    Returns:
        A dictionary with statistics.
    """
    stats = {
        'num_episodes': 0,
        'domains': set(),
        'has_leak_target': False,
        'has_outcome': False
    }
    
    # If streaming, we need to iterate
    if hasattr(dataset, '__iter__'):
        for episode in dataset:
            stats['num_episodes'] += 1
            if 'leak-target' in episode:
                stats['has_leak_target'] = True
            if 'outcome' in episode:
                stats['has_outcome'] = True
            if 'covariates' in episode and 'domain' in episode['covariates']:
                stats['domains'].add(episode['covariates']['domain'])
    
    stats['domains'] = list(stats['domains'])
    return stats

def main() -> None:
    """Main entry point for the data loader."""
    logger.info("Starting data loader pipeline")
    result = run_data_loader_pipeline()
    
    if result['success']:
        logger.info("Data loader pipeline completed successfully")
        dataset = result.get('dataset')
        if dataset:
            stats = get_dataset_statistics(dataset)
            logger.info(f"Dataset statistics: {stats}")
    else:
        logger.error(f"Data loader pipeline failed: {result.get('error')}")
        sys.exit(1)

if __name__ == '__main__':
    main()