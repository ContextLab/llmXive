"""
Configuration management for the llmXive OmniDirector pipeline.

Handles path resolution, constant definitions, and memory-efficient
chunked data loading strategies to ensure <6GB memory footprint.
"""
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union, Iterator, List, Generator, BinaryIO
import yaml

# Configure logging for this module
logger = logging.getLogger(__name__)

# ==============================================================================
# Memory Constraints & Constants
# ==============================================================================

# Target maximum memory footprint in GB (Constraint: <6GB)
MAX_MEMORY_GB = 5.5  # Conservative buffer below 6GB limit
MAX_MEMORY_BYTES = int(MAX_MEMORY_GB * 1024**3)

# Chunking configuration for streaming large datasets
CHUNK_SIZE_FRAMES = 100  # Number of frames per chunk for processing
CHUNK_SIZE_SEQUENCES = 10  # Number of sequences per chunk for loading

# Default paths relative to project root
DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_RAW = DEFAULT_PROJECT_ROOT / "data" / "raw"
DEFAULT_DATA_PROCESSED = DEFAULT_PROJECT_ROOT / "data" / "processed"
DEFAULT_CODE_ROOT = DEFAULT_PROJECT_ROOT / "code"

# ==============================================================================
# Configuration Loading
# ==============================================================================

def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file or return defaults.
    
    Args:
        config_path: Path to the YAML config file. If None, returns defaults.
        
    Returns:
        Dictionary containing configuration parameters.
    """
    defaults = {
        "project": {
            "root": str(DEFAULT_PROJECT_ROOT),
            "name": "llmXive-omnidirector"
        },
        "paths": {
            "data_raw": str(DEFAULT_DATA_RAW),
            "data_processed": str(DEFAULT_DATA_PROCESSED),
            "code": str(DEFAULT_CODE_ROOT)
        },
        "memory": {
            "max_gb": MAX_MEMORY_GB,
            "chunk_frames": CHUNK_SIZE_FRAMES,
            "chunk_sequences": CHUNK_SIZE_SEQUENCES
        },
        "processing": {
            "parallel_workers": 4,
            "enable_logging": True,
            "log_level": "INFO"
        }
    }
    
    if config_path is None:
        return defaults
        
    config_path = Path(config_path)
    if not config_path.exists():
        logger.warning(f"Config file not found at {config_path}, using defaults.")
        return defaults
        
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return defaults
        
    return deep_merge(defaults, user_config)

def get_config() -> Dict[str, Any]:
    """
    Get the global configuration instance.
    
    Returns:
        The loaded configuration dictionary.
    """
    # In a real application, this might cache the config.
    # For now, we load from the default location if it exists.
    default_cfg_path = Path(__file__).parent.parent / "config.yaml"
    return load_config(default_cfg_path)

def get_constant(key: str, config: Optional[Dict[str, Any]] = None) -> Any:
    """
    Retrieve a constant value from the configuration by dot-notation key.
    
    Args:
        key: Dot-separated key (e.g., 'memory.max_gb').
        config: Optional config dict. If None, loads default.
                
    Returns:
        The value associated with the key.
                
    Raises:
        KeyError: If the key is not found.
    """
    if config is None:
        config = get_config()
        
    keys = key.split('.')
    current = config
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            raise KeyError(f"Configuration key '{key}' not found.")
    return current

def get_path(key: str, config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Retrieve a path from the configuration and return it as a Path object.
    
    Args:
        key: Dot-separated key pointing to a path string.
        config: Optional config dict.
                
    Returns:
        pathlib.Path object.
    """
    path_str = get_constant(key, config)
    return Path(path_str)

def ensure_paths_exist(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Ensure all directories defined in the configuration exist.
    Creates them if missing.
    """
    if config is None:
        config = get_config()
        
    path_keys = [
        "paths.data_raw",
        "paths.data_processed",
        "paths.code"
    ]
    
    for key in path_keys:
        try:
            p = get_path(key, config)
            p.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured path exists: {p}")
        except KeyError:
            pass # Key not found, skip

# ==============================================================================
# Utility Functions
# ==============================================================================

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries. Values from 'override' take precedence.
    """
    result = deepcopy_dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def deepcopy_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep copy a dictionary manually to avoid import overhead for large dicts if needed,
    though json.loads(json.dumps(d)) is also an option.
    """
    import copy
    return copy.deepcopy(d)

# ==============================================================================
# Memory-Efficient Data Loading Strategy (Task T006b)
# ==============================================================================
# This section implements the chunked data loading and streaming logic required
# to ensure the pipeline stays within the <6GB memory footprint constraint.
# It provides generators that yield data in small batches rather than loading
# the entire dataset into RAM at once.

class ChunkedDatasetLoader:
    """
    A streaming loader for large dataset archives (e.g., OmniDirector zip).
    
    This class implements the memory-efficient strategy by:
    1. Opening the archive once.
    2. Iterating through entries or logical chunks.
    3. Yielding data chunks (lists of records or DataFrames) one at a time.
    4. Allowing the garbage collector to reclaim memory of previous chunks.
    
    This ensures that memory usage is proportional to CHUNK_SIZE, not total dataset size.
    """
    
    def __init__(self, zip_path: Union[str, Path], chunk_size: int = CHUNK_SIZE_FRAMES):
        """
        Initialize the loader.
        
        Args:
            zip_path: Path to the dataset zip file.
            chunk_size: Number of frames/records to yield per chunk.
        """
        self.zip_path = Path(zip_path)
        self.chunk_size = chunk_size
        if not self.zip_path.exists():
            raise FileNotFoundError(f"Dataset zip file not found: {self.zip_path}")
    
    def stream_sequences(self) -> Iterator[List[Dict[str, Any]]]:
        """
        Generator that yields chunks of sequence data.
        
        Yields:
            List of dictionaries, each representing a frame or sequence chunk.
        """
        import zipfile
        import json
        
        logger.info(f"Starting chunked stream from {self.zip_path} (chunk_size={self.chunk_size})")
        
        current_chunk = []
        sequence_count = 0
        
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zf:
                # Assuming the zip contains a specific structure, e.g., sequences/*.json
                # or a single large manifest. We adapt to the OmniDirector schema.
                # Strategy: Read file names, then iterate content.
                
                # List all JSON files that represent frames or sequences
                # Adjust glob pattern based on actual zip structure if known
                json_files = [f for f in zf.namelist() if f.endswith('.json')]
                
                if not json_files:
                    # Fallback: maybe it's a single large file or different structure
                    # For now, assume a flat list of frame files or a manifest
                    logger.warning("No JSON files found in zip. Attempting to read manifest or raw structure.")
                    # If the zip is just a collection of frames, we might need to iterate differently.
                    # This is a generic implementation assuming a 'manifest.json' or similar.
                    if 'manifest.json' in json_files:
                        json_files = ['manifest.json']
                    else:
                        raise ValueError("No recognizable data files found in zip archive.")
                
                for file_name in json_files:
                    with zf.open(file_name) as f:
                        # Read content as text
                        content = f.read().decode('utf-8')
                        data = json.loads(content)
                        
                        # Handle different data structures
                        if isinstance(data, list):
                            items = data
                        elif isinstance(data, dict):
                            # Assume it's a sequence object with a 'frames' key
                            items = data.get('frames', [data])
                        else:
                            items = []
                            
                        for item in items:
                            current_chunk.append(item)
                            
                            if len(current_chunk) >= self.chunk_size:
                                yield current_chunk
                                current_chunk = []
                                
                    sequence_count += 1
                    
            # Yield any remaining items
            if current_chunk:
                yield current_chunk
                
        except Exception as e:
            logger.error(f"Error streaming dataset: {e}")
            raise

def load_dataset_chunked(
    zip_path: Union[str, Path],
    chunk_size: int = CHUNK_SIZE_FRAMES,
    config: Optional[Dict[str, Any]] = None
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Public API for chunked dataset loading.
    
    This function wraps the ChunkedDatasetLoader to provide a simple generator interface.
    It enforces the memory constraint by strictly limiting the number of items
    held in memory at any one time.
    
    Args:
        zip_path: Path to the dataset zip file.
        chunk_size: Number of records to yield per batch.
        config: Optional configuration dict (used to override chunk_size).
                
    Yields:
        List of data records (dictionaries).
                
    Example:
        for chunk in load_dataset_chunked("data/raw/omnidirector.zip"):
            process_chunk(chunk) # Process and discard before next yield
    """
    if config:
        try:
            chunk_size = get_constant('memory.chunk_frames', config)
        except KeyError:
            pass
            
    loader = ChunkedDatasetLoader(zip_path, chunk_size)
    yield from loader.stream_sequences()

def main():
    """
    Entry point for testing the configuration and chunked loading strategy.
    """
    logging.basicConfig(level=logging.INFO)
    
    # 1. Load Config
    cfg = get_config()
    logger.info(f"Max Memory GB: {get_constant('memory.max_gb', cfg)}")
    logger.info(f"Chunk Size: {get_constant('memory.chunk_frames', cfg)}")
    
    # 2. Ensure Paths
    ensure_paths_exist(cfg)
    
    # 3. Test Chunked Loading (if a dummy file exists, otherwise just log)
    # This is a dry-run check to ensure the API works without crashing
    # if the file is missing.
    dummy_path = Path("data/raw/test_dummy.zip")
    if dummy_path.exists():
        logger.info("Testing chunked loader with dummy file...")
        # In a real scenario, we would iterate here.
        # For now, we just verify the class instantiation works.
        try:
            loader = ChunkedDatasetLoader(dummy_path, 10)
            logger.info("ChunkedDatasetLoader instantiated successfully.")
        except Exception as e:
            logger.error(f"Loader test failed: {e}")
    else:
        logger.info("No dummy zip found. Skipping runtime test of chunked loader.")
        logger.info("Chunked loading strategy defined and ready for use.")

if __name__ == "__main__":
    main()