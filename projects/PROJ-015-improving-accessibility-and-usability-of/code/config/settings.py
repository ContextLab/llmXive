import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json
import logging

from utils.logger import get_logger

logger = get_logger(__name__)

class Settings:
    """
    Centralized configuration management for the study.
    
    Loads configuration from environment variables and optional JSON config files.
    Validates critical parameters and provides typed accessors.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.project_root = Path(__file__).parent.parent.parent
        self._config_path = config_path
        
        # Initialize default values
        self.seed = 42
        self.data_raw_dir = self.project_root / "data" / "raw"
        self.data_processed_dir = self.project_root / "data" / "processed"
        self.log_level = "INFO"
        self.max_sessions = 100
        self.sus_imputation_threshold = 1
        self.explanation_engagement_enabled = True
        self.interface_sequence = ["traditional", "explainable"]
        self.xai_algorithm = "rule_based"  # Options: rule_based, shap, lime
        self.statistical_test = "anova"
        self.correction_method = "holm_bonferroni"
        self.min_participants = 30
        self.timeout_seconds = 3600
        
        # Load configuration
        self._load_from_env()
        if config_path:
            self._load_from_file(config_path)
        
        # Validate and ensure directories exist
        self._validate_and_setup()
    
    def _load_from_env(self) -> None:
        """Load settings from environment variables."""
        if os.getenv("STUDY_SEED"):
            try:
                self.seed = int(os.getenv("STUDY_SEED"))
            except ValueError:
                logger.warning(f"Invalid STUDY_SEED value, using default: {self.seed}")
        
        if os.getenv("LOG_LEVEL"):
            self.log_level = os.getenv("LOG_LEVEL").upper()
        
        if os.getenv("MAX_SESSIONS"):
            try:
                self.max_sessions = int(os.getenv("MAX_SESSIONS"))
            except ValueError:
                logger.warning(f"Invalid MAX_SESSIONS value, using default: {self.max_sessions}")
        
        if os.getenv("SUS_IMPUTATION_THRESHOLD"):
            try:
                self.sus_imputation_threshold = int(os.getenv("SUS_IMPUTATION_THRESHOLD"))
            except ValueError:
                logger.warning(f"Invalid SUS_IMPUTATION_THRESHOLD, using default: {self.sus_imputation_threshold}")
        
        if os.getenv("EXPLANATION_ENGAGEMENT_ENABLED"):
            val = os.getenv("EXPLANATION_ENGAGEMENT_ENABLED").lower()
            self.explanation_engagement_enabled = val in ("true", "1", "yes")
        
        if os.getenv("XAI_ALGORITHM"):
            allowed = ["rule_based", "shap", "lime"]
            val = os.getenv("XAI_ALGORITHM").lower()
            if val in allowed:
                self.xai_algorithm = val
            else:
                logger.warning(f"Invalid XAI_ALGORITHM '{val}', using default: {self.xai_algorithm}")
        
        if os.getenv("STATISTICAL_TEST"):
            val = os.getenv("STATISTICAL_TEST").lower()
            if val in ["anova", "ttest", "wilcoxon"]:
                self.statistical_test = val
        
        if os.getenv("CORRECTION_METHOD"):
            val = os.getenv("CORRECTION_METHOD").lower()
            if val in ["holm_bonferroni", "bonferroni", "fdr"]:
                self.correction_method = val
        
        if os.getenv("MIN_PARTICIPANTS"):
            try:
                self.min_participants = int(os.getenv("MIN_PARTICIPANTS"))
            except ValueError:
                logger.warning(f"Invalid MIN_PARTICIPANTS, using default: {self.min_participants}")
        
        if os.getenv("INTERFACE_SEQUENCE"):
            # Expecting comma-separated list like "traditional,explainable"
            val = os.getenv("INTERFACE_SEQUENCE")
            if val:
                self.interface_sequence = [s.strip() for s in val.split(",")]
        
        # Override paths if set
        if os.getenv("DATA_RAW_DIR"):
            self.data_raw_dir = Path(os.getenv("DATA_RAW_DIR"))
        
        if os.getenv("DATA_PROCESSED_DIR"):
            self.data_processed_dir = Path(os.getenv("DATA_PROCESSED_DIR"))
    
    def _load_from_file(self, config_path: Union[str, Path]) -> None:
        """Load settings from a JSON configuration file."""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_file}, using defaults and env vars")
            return
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Update settings from file
            if "seed" in config:
                self.seed = int(config["seed"])
            if "max_sessions" in config:
                self.max_sessions = int(config["max_sessions"])
            if "sus_imputation_threshold" in config:
                self.sus_imputation_threshold = int(config["sus_imputation_threshold"])
            if "explanation_engagement_enabled" in config:
                self.explanation_engagement_enabled = bool(config["explanation_engagement_enabled"])
            if "xai_algorithm" in config:
                self.xai_algorithm = str(config["xai_algorithm"])
            if "statistical_test" in config:
                self.statistical_test = str(config["statistical_test"])
            if "correction_method" in config:
                self.correction_method = str(config["correction_method"])
            if "min_participants" in config:
                self.min_participants = int(config["min_participants"])
            if "timeout_seconds" in config:
                self.timeout_seconds = int(config["timeout_seconds"])
            if "interface_sequence" in config and isinstance(config["interface_sequence"], list):
                self.interface_sequence = [str(s) for s in config["interface_sequence"]]
            
            # Path overrides
            if "data_raw_dir" in config:
                self.data_raw_dir = Path(config["data_raw_dir"])
            if "data_processed_dir" in config:
                self.data_processed_dir = Path(config["data_processed_dir"])
            
            logger.info(f"Loaded configuration from {config_file}")
        
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error(f"Error parsing config file {config_file}: {e}")
    
    def _validate_and_setup(self) -> None:
        """Validate settings and create necessary directories."""
        # Validate seed
        if not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError(f"Invalid seed value: {self.seed}")
        
        # Validate directories
        for dir_path in [self.data_raw_dir, self.data_processed_dir]:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created directory: {dir_path}")
                except OSError as e:
                    raise RuntimeError(f"Failed to create directory {dir_path}: {e}")
            elif not dir_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {dir_path}")
        
        # Validate xai_algorithm
        if self.xai_algorithm not in ["rule_based", "shap", "lime"]:
            logger.warning(f"Unsupported XAI algorithm: {self.xai_algorithm}, defaulting to rule_based")
            self.xai_algorithm = "rule_based"
        
        # Set log level
        try:
            logging.getLogger().setLevel(self.log_level)
        except ValueError:
            logger.warning(f"Invalid log level: {self.log_level}, using INFO")
            logging.getLogger().setLevel("INFO")
    
    def get_raw_data_path(self) -> Path:
        """Return the path to the raw data directory."""
        return self.data_raw_dir
    
    def get_processed_data_path(self) -> Path:
        """Return the path to the processed data directory."""
        return self.data_processed_dir
    
    def to_dict(self) -> Dict[str, Any]:
        """Export settings to a dictionary."""
        return {
            "project_root": str(self.project_root),
            "data_raw_dir": str(self.data_raw_dir),
            "data_processed_dir": str(self.data_processed_dir),
            "seed": self.seed,
            "log_level": self.log_level,
            "max_sessions": self.max_sessions,
            "sus_imputation_threshold": self.sus_imputation_threshold,
            "explanation_engagement_enabled": self.explanation_engagement_enabled,
            "interface_sequence": self.interface_sequence,
            "xai_algorithm": self.xai_algorithm,
            "statistical_test": self.statistical_test,
            "correction_method": self.correction_method,
            "min_participants": self.min_participants,
            "timeout_seconds": self.timeout_seconds,
        }
    
    def __repr__(self) -> str:
        return f"Settings(seed={self.seed}, xai={self.xai_algorithm}, log_level={self.log_level})"

# Singleton instance
_settings_instance: Optional[Settings] = None

def get_settings(config_path: Optional[Union[str, Path]] = None) -> Settings:
    """
    Get the singleton Settings instance.
    
    Args:
        config_path: Optional path to a JSON config file to override defaults.
    
    Returns:
        Settings instance.
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings(config_path)
    return _settings_instance

def reset_settings() -> None:
    """Reset the settings singleton (useful for testing)."""
    global _settings_instance
    _settings_instance = None

def main() -> None:
    """Main entry point for testing the settings module."""
    settings = get_settings()
    print("Current Settings:")
    for key, value in settings.to_dict().items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()