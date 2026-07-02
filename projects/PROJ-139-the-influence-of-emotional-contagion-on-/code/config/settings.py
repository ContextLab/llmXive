import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# Configure logging for the config module
logger = logging.getLogger(__name__)

@dataclass
class APIKeys:
    """Container for API keys required by the project."""
    pushshift_api_key: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: str = "llmXive-emotional-contagion:1.0"
    
    def __post_init__(self):
        # Validate critical keys if present but empty
        if self.pushshift_api_key is not None and self.pushshift_api_key.strip() == "":
            logger.warning("pushshift_api_key is set but empty")
        if self.reddit_client_id is not None and self.reddit_client_id.strip() == "":
            logger.warning("reddit_client_id is set but empty")
        if self.reddit_client_secret is not None and self.reddit_client_secret.strip() == "":
            logger.warning("reddit_client_secret is set but empty")

@dataclass
class DatasetPaths:
    """Container for dataset paths."""
    raw_dir: Path = field(default_factory=lambda: Path("data/raw"))
    processed_dir: Path = field(default_factory=lambda: Path("data/processed"))
    annotations_file: Path = field(default_factory=lambda: Path("data/raw/annotations.json"))
    exclusions_log: Path = field(default_factory=lambda: Path("data/processed/exclusions.log"))
    vader_validation_report: Path = field(default_factory=lambda: Path("data/processed/vader_validation_report.json"))
    valid_threads_file: Path = field(default_factory=lambda: Path("data/processed/valid_threads.csv"))
    sensitivity_analysis_file: Path = field(default_factory=lambda: Path("data/processed/sensitivity_analysis.csv"))
    final_report: Path = field(default_factory=lambda: Path("docs/paper.md"))
    
    def __post_init__(self):
        # Ensure paths are Path objects
        if isinstance(self.raw_dir, str):
            self.raw_dir = Path(self.raw_dir)
        if isinstance(self.processed_dir, str):
            self.processed_dir = Path(self.processed_dir)
        if isinstance(self.annotations_file, str):
            self.annotations_file = Path(self.annotations_file)
        if isinstance(self.exclusions_log, str):
            self.exclusions_log = Path(self.exclusions_log)
        if isinstance(self.vader_validation_report, str):
            self.vader_validation_report = Path(self.vader_validation_report)
        if isinstance(self.valid_threads_file, str):
            self.valid_threads_file = Path(self.valid_threads_file)
        if isinstance(self.sensitivity_analysis_file, str):
            self.sensitivity_analysis_file = Path(self.sensitivity_analysis_file)
        if isinstance(self.final_report, str):
            self.final_report = Path(self.final_report)

        # Ensure directories exist
        for path_attr in ['raw_dir', 'processed_dir']:
            dir_path = getattr(self, path_attr)
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {dir_path}")

@dataclass
class Config:
    """Main configuration container."""
    api_keys: APIKeys = field(default_factory=APIKeys)
    dataset_paths: DatasetPaths = field(default_factory=DatasetPaths)
    debug_mode: bool = False
    random_seed: int = 42
    max_threads: int = 500
    min_replies_for_contagion: int = 5
    min_seeds_for_thread: int = 3
    sentiment_threshold: float = 0.05
    kappa_threshold: float = 0.6
    
    def __post_init__(self):
        if not isinstance(self.api_keys, APIKeys):
            self.api_keys = APIKeys(**self.api_keys) if isinstance(self.api_keys, dict) else APIKeys()
        if not isinstance(self.dataset_paths, DatasetPaths):
            self.dataset_paths = DatasetPaths(**self.dataset_paths) if isinstance(self.dataset_paths, dict) else DatasetPaths()

def load_config_from_env() -> Config:
    """Load configuration from environment variables."""
    api_keys = APIKeys(
        pushshift_api_key=os.getenv("PUSHSHIFT_API_KEY"),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "llmXive-emotional-contagion:1.0")
    )
    
    dataset_paths = DatasetPaths(
        raw_dir=Path(os.getenv("RAW_DATA_DIR", "data/raw")),
        processed_dir=Path(os.getenv("PROCESSED_DATA_DIR", "data/processed")),
        annotations_file=Path(os.getenv("ANNOTATIONS_FILE", "data/raw/annotations.json")),
        exclusions_log=Path(os.getenv("EXCLUSIONS_LOG", "data/processed/exclusions.log")),
        vader_validation_report=Path(os.getenv("VADER_VALIDATION_REPORT", "data/processed/vader_validation_report.json")),
        valid_threads_file=Path(os.getenv("VALID_THREADS_FILE", "data/processed/valid_threads.csv")),
        sensitivity_analysis_file=Path(os.getenv("SENSITIVITY_ANALYSIS_FILE", "data/processed/sensitivity_analysis.csv")),
        final_report=Path(os.getenv("FINAL_REPORT", "docs/paper.md"))
    )
    
    config = Config(
        api_keys=api_keys,
        dataset_paths=dataset_paths,
        debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true",
        random_seed=int(os.getenv("RANDOM_SEED", "42")),
        max_threads=int(os.getenv("MAX_THREADS", "500")),
        min_replies_for_contagion=int(os.getenv("MIN_REPLIES_FOR_CONTAGION", "5")),
        min_seeds_for_thread=int(os.getenv("MIN_SEEDS_FOR_THREAD", "3")),
        sentiment_threshold=float(os.getenv("SENTIMENT_THRESHOLD", "0.05")),
        kappa_threshold=float(os.getenv("KAPPA_THRESHOLD", "0.6"))
    )
    
    logger.info("Configuration loaded from environment variables")
    return config

def load_config_from_file(config_path: str = "config/config.json") -> Config:
    """Load configuration from a JSON file."""
    config_path = Path(config_path)
    
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}. Using defaults.")
        return Config()
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        api_keys_data = config_data.get('api_keys', {})
        dataset_paths_data = config_data.get('dataset_paths', {})
        
        api_keys = APIKeys(**api_keys_data) if api_keys_data else APIKeys()
        dataset_paths = DatasetPaths(**dataset_paths_data) if dataset_paths_data else DatasetPaths()
        
        config = Config(
            api_keys=api_keys,
            dataset_paths=dataset_paths,
            debug_mode=config_data.get('debug_mode', False),
            random_seed=config_data.get('random_seed', 42),
            max_threads=config_data.get('max_threads', 500),
            min_replies_for_contagion=config_data.get('min_replies_for_contagion', 5),
            min_seeds_for_thread=config_data.get('min_seeds_for_thread', 3),
            sentiment_threshold=config_data.get('sentiment_threshold', 0.05),
            kappa_threshold=config_data.get('kappa_threshold', 0.6)
        )
        
        logger.info(f"Configuration loaded from file: {config_path}")
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse config file {config_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load config from file {config_path}: {e}")
        raise

_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance, loading from environment if not set."""
    global _config
    if _config is None:
        _config = load_config_from_env()
    return _config

def load_config_from_env():
    """Alias for load_config_from_env to match API surface."""
    return load_config_from_env()

def load_config_from_file(config_path: str = "config/config.json") -> Config:
    """Alias for load_config_from_file to match API surface."""
    return load_config_from_file(config_path)
