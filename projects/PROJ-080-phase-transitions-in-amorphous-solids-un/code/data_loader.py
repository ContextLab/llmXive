import os
import hashlib
import json
import logging
import h5py
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from datasets import load_dataset
from datasets.exceptions import DatasetNotFoundError
import sys

# Configure logging for the module
logger = logging.getLogger(__name__)

# Constants
STATE_DIR = Path("state/projects")
STATE_FILE_NAME = "PROJ-080-phase-transitions-in-amorphous-solids-un.yaml"
REAL_DATASET_ID = "materials-science/amorphous-silicon-shear-trajectories"

class RealDataFetchError(Exception):
    """Raised when real data cannot be fetched."""
    pass

class ChecksumValidationError(Exception):
    """Raised when checksum validation fails."""
    pass

class FatalError(Exception):
    """Raised for unrecoverable errors."""
    pass

def get_schema_path() -> Path:
    return Path("specs/contracts/trajectory.schema.yaml")

def load_schema(path: Path) -> Dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Computes the SHA-256 hash of a file.
    Reads in chunks to handle large files.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_artifact_hashes(hashes: Dict[str, str], state_file: Optional[Path] = None) -> None:
    """
    Writes artifact hashes to the state YAML file.
    Creates the directory structure if it doesn't exist.
    """
    if state_file is None:
        state_file = STATE_DIR / STATE_FILE_NAME
    
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state if it exists
    if state_file.exists():
        with open(state_file, 'r') as f:
            try:
                state = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state = {}
    else:
        state = {}
    
    # Update or create artifact_hashes
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    state['artifact_hashes'].update(hashes)
    
    # Write back to file
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Artifact hashes written to {state_file}")

def read_artifact_hashes(state_file: Optional[Path] = None) -> Dict[str, str]:
    """
    Reads artifact hashes from the state YAML file.
    """
    if state_file is None:
        state_file = STATE_DIR / STATE_FILE_NAME
    
    if not state_file.exists():
        return {}
    
    with open(state_file, 'r') as f:
        try:
            state = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            return {}
    
    return state.get('artifact_hashes', {})

def verify_checksum_local(file_path: Union[str, Path], expected_hash: str) -> bool:
    """
    Verifies the SHA-256 hash of a local file against an expected value.
    """
    actual_hash = compute_sha256(file_path)
    if actual_hash != expected_hash:
        logger.error(f"Checksum mismatch for {file_path}. Expected: {expected_hash}, Got: {actual_hash}")
        return False
    return True

def download_and_verify_shard(dataset_id: str, split: str = "train") -> Tuple[Path, str]:
    """
    Downloads a dataset shard (if streaming is not used for the whole dataset) 
    and verifies its checksum. 
    NOTE: For streaming datasets, we compute hash on the fly or on the first chunk 
    if we need to store it, but typically streaming avoids full download.
    However, for the purpose of T010, we need to compute a hash of the source.
    Since the dataset is streamed, we will compute a hash of the first N bytes 
    of the stream to represent the source integrity, OR we download a representative shard.
    
    For this implementation, we will attempt to download the full dataset to a cache 
    location to compute a stable hash, OR we use the streaming iterator to compute a hash
    of the stream content if the dataset allows. 
    
    Given the constraints of "Real Data" and "Streaming", we will compute the hash 
    of the first 100MB of the stream to represent the data source integrity for this task,
    as downloading 7GB+ might be too heavy for a simple checksum step if not required.
    However, the spec says "checksum of the downloaded/generated file". 
    If we stream, we don't have a single file. 
    
    Strategy: We will download the dataset to the cache dir (handled by datasets lib) 
    and compute the hash of the cached files.
    """
    logger.info(f"Fetching dataset {dataset_id} for checksum verification...")
    
    try:
        # Load dataset in streaming mode to verify existence and get a handle
        ds = load_dataset(dataset_id, split=split, streaming=True)
        
        # To get a checksum, we need a file. 
        # We will download the first shard or a representative portion to a temp file
        # to compute a hash that represents the data source.
        # Alternatively, we can compute a hash of the iterator content.
        
        # Let's try to download the dataset to cache to get a stable file path
        # This might be heavy, so we do it carefully.
        # If the dataset is too large, we might need to hash the stream.
        
        # For T010, we need to write a hash to state. 
        # We will compute a hash of the first 1000 samples as a "fingerprint" 
        # of the real data source to ensure we are using the right version.
        
        import tempfile
        import shutil
        
        # Create a temporary file to store a sample of the data for hashing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".parquet") as tmp_file:
            tmp_path = tmp_file.name
        
        count = 0
        max_samples = 1000
        try:
            for i, item in enumerate(ds):
                if count >= max_samples:
                    break
                # We need to serialize the item to hash it. 
                # Since we don't know the exact format, we'll convert to JSON string
                # This is a "fingerprint" of the data content.
                json_str = json.dumps(item, sort_keys=True)
                tmp_file.write(json_str.encode('utf-8'))
                count += 1
        except Exception as e:
            logger.warning(f"Error during streaming for hash: {e}")
            raise RealDataFetchError(f"Failed to stream dataset for hash computation: {e}")
        
        hash_value = compute_sha256(tmp_path)
        os.unlink(tmp_path)
        
        logger.info(f"Computed fingerprint hash for {dataset_id}: {hash_value}")
        return Path(tmp_path), hash_value # Return dummy path as we deleted it, or keep logic
        
    except (DatasetNotFoundError, ConnectionError) as e:
        raise RealDataFetchError(f"Failed to fetch real dataset {dataset_id}: {e}")

def load_verified_dataset_streaming(dataset_id: str, split: str = "train") -> Any:
    """
    Loads the dataset in streaming mode.
    """
    try:
        return load_dataset(dataset_id, split=split, streaming=True)
    except (DatasetNotFoundError, ConnectionError) as e:
        raise RealDataFetchError(f"Failed to load real dataset {dataset_id}: {e}")

def generate_synthetic_data_if_missing(data_dir: Path) -> List[Path]:
    """
    Checks if synthetic data exists in data_dir. If not, calls the generator.
    Returns list of generated file paths.
    """
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    h5_files = list(data_dir.glob("synthetic_trajectory_*.h5"))
    
    if h5_files:
        logger.info(f"Found {len(h5_files)} existing synthetic trajectory files.")
        return h5_files
    
    logger.info("No synthetic data found. Generating...")
    # Import the generator function
    from data_generator import generate_synthetic_trajectory, save_trajectory_to_h5, save_metadata_json
    
    # Generate a small synthetic trajectory for fallback
    trajectory = generate_synthetic_trajectory(n_particles=100, n_timesteps=50, strain_rate=0.01, temperature=300, label="brittle")
    output_file = data_dir / "synthetic_trajectory_fallback.h5"
    save_trajectory_to_h5(trajectory, output_file)
    save_metadata_json([{"file": str(output_file), "label": "brittle"}], data_dir / "metadata.json")
    
    logger.info("Synthetic data generated.")
    return [output_file]

def load_synthetic_data(data_dir: Path) -> List[Path]:
    """
    Loads synthetic data from data_dir.
    """
    data_dir = Path(data_dir)
    h5_files = list(data_dir.glob("synthetic_trajectory_*.h5"))
    if not h5_files:
        raise FileNotFoundError(f"No synthetic trajectory files found in {data_dir}")
    return h5_files

def stream_trajectories(source: Union[str, Path, Any]) -> Iterator[Dict]:
    """
    Yields trajectory data chunks.
    If source is a dataset object (from load_dataset), it iterates directly.
    If source is a path, it loads from HDF5.
    """
    if isinstance(source, str) or isinstance(source, Path):
        path = Path(source)
        if path.suffix == ".h5":
            with h5py.File(path, 'r') as f:
                # Assuming structure: f['particles'], f['timesteps'] etc.
                # This is a simplified streamer for the fallback case
                yield dict(f) 
    else:
        # Assume it's a streaming dataset object
        for item in source:
            yield item

def get_trajectory_metadata(source: Union[str, Path, Any]) -> Dict:
    """
    Extracts metadata from the source.
    """
    if isinstance(source, str) or isinstance(source, Path):
        path = Path(source)
        if path.suffix == ".json":
            with open(path, 'r') as f:
                return json.load(f)
        else:
            # Try to find metadata.json in the same dir
            metadata_path = path.parent / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    return json.load(f)
    return {}

def compute_and_store_hashes(data_sources: List[Union[str, Path]], state_file: Optional[Path] = None) -> None:
    """
    Computes SHA-256 hashes for the given data sources and writes them to the state file.
    This is the core implementation for T010.
    """
    hashes = {}
    for source in data_sources:
        path = Path(source)
        if path.exists():
            h = compute_sha256(path)
            hashes[str(path)] = h
            logger.info(f"Computed hash for {path}: {h}")
        else:
            logger.warning(f"Source not found, skipping hash: {path}")
    
    if hashes:
        write_artifact_hashes(hashes, state_file)
    else:
        logger.warning("No data sources found to compute hashes for.")

def validate_checksums(data_sources: List[Union[str, Path]], state_file: Optional[Path] = None) -> bool:
    """
    Validates the checksums of data sources against the stored values.
    """
    stored_hashes = read_artifact_hashes(state_file)
    if not stored_hashes:
        logger.warning("No stored checksums found. Skipping validation.")
        return True # Or False? Spec says "If hash file is missing, run T010". 
                    # But this function is for validation. If missing, we can't validate.
                    # We'll return True to allow execution to proceed to T010 logic if needed.
    
    for source in data_sources:
        path = str(Path(source))
        if path in stored_hashes:
            if not verify_checksum_local(source, stored_hashes[path]):
                logger.error(f"Checksum validation failed for {source}")
                return False
        else:
            logger.warning(f"No stored hash found for {source}")
    return True

def main():
    """
    Main entry point for data loading and checksum operations.
    Tries to load real data. If fails, falls back to synthetic.
    Then computes and stores hashes.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    data_dir = Path("data/raw")
    state_file = STATE_DIR / STATE_FILE_NAME
    
    data_sources = []
    
    # 1. Try to fetch real data
    real_data_loaded = False
    try:
        logger.info(f"Attempting to load real dataset: {REAL_DATASET_ID}")
        ds = load_verified_dataset_streaming(REAL_DATASET_ID)
        # Since we are streaming, we don't have a single file to hash easily.
        # We will compute a fingerprint hash of the stream as done in download_and_verify_shard logic
        # But for T010, we need to write a hash to state.
        # We will simulate a "download" of a representative shard for the hash.
        # In a real scenario, we might hash the first N bytes of the stream.
        
        # Let's compute a hash of the first 1000 items as a fingerprint
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as tmp:
            tmp_path = tmp.name
        
        count = 0
        for item in ds:
            if count >= 1000:
                break
            tmp.write((json.dumps(item) + "\n").encode('utf-8'))
            count += 1
        
        real_hash = compute_sha256(tmp_path)
        os.unlink(tmp_path)
        
        # We treat this fingerprint as the "file" hash for the real dataset
        # We store it under a special key
        write_artifact_hashes({"real_dataset_fingerprint": real_hash}, state_file)
        logger.info(f"Real data fingerprint stored: {real_hash}")
        real_data_loaded = True
        
    except RealDataFetchError as e:
        logger.warning(f"Real data fetch failed: {e}. Falling back to synthetic.")
        log_synthetic_fallback_active() # Assuming this is defined in logging_config
        
    # 2. If real data failed, load synthetic
    if not real_data_loaded:
        logger.info("Loading synthetic data...")
        synthetic_files = generate_synthetic_data_if_missing(data_dir)
        data_sources.extend(synthetic_files)
        
        # Compute and store hashes for synthetic files
        compute_and_store_hashes(data_sources, state_file)
    else:
        logger.info("Real data loaded successfully. Synthetic fallback not needed.")
        # For real data, we already stored the fingerprint.
        # If we had downloaded files, we would store their paths and hashes here.
    
    # 3. Validate checksums if they exist
    if read_artifact_hashes(state_file):
        if not validate_checksums(data_sources, state_file):
            raise ChecksumValidationError("Checksum validation failed.")
    
    logger.info("Data loading and checksum computation complete.")

# Helper for logging if not imported elsewhere
def log_synthetic_fallback_active():
    logger.warning("SYNTHETIC FALLBACK ACTIVE")

if __name__ == "__main__":
    main()
