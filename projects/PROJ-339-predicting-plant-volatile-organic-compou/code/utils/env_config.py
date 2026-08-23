"""
Environment variable management for data paths and seeds.

This module provides a robust configuration manager for the llmXive pipeline,
handling environment variables for data paths, random seeds, and other
critical runtime parameters.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load .env file if it exists (prior to any other config loading)
load_dotenv()

class EnvConfigError(Exception):
    """Raised when environment configuration is missing or invalid."""
    pass

class EnvConfig:
    """
    Manages environment variable configuration for the project.
    
    Attributes:
        data_root (Path): Root directory for all data (default: ./data)
        raw_data_dir (Path): Directory for raw data files
        processed_data_dir (Path): Directory for processed data files
        results_dir (Path): Directory for analysis results
        models_dir (Path): Directory for trained model artifacts
        seed (int): Random seed for reproducibility
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from environment variables with defaults."""
        # Data paths
        self.data_root = Path(os.getenv("DATA_ROOT", "./data"))
        self.raw_data_dir = self.data_root / "raw"
        self.processed_data_dir = self.data_root / "processed"
        self.results_dir = self.data_root / "results"
        self.models_dir = self.data_root / "models"
        
        # Random seed
        seed_str = os.getenv("RANDOM_SEED", "42")
        try:
            self.seed = int(seed_str)
        except ValueError:
            raise EnvConfigError(f"RANDOM_SEED must be an integer, got: {seed_str}")
        
        # Logging level
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Specific data file paths (optional overrides)
        self.query_log_path = Path(os.getenv("QUERY_LOG_PATH", str(self.raw_data_dir / "query_log.json")))
        self.synthetic_data_path = Path(os.getenv("SYNTHETIC_DATA_PATH", str(self.raw_data_dir / "synthetic_arabidopsis_v1.csv")))
        self.merged_dataset_path = Path(os.getenv("MERGED_DATASET_PATH", str(self.processed_data_dir / "merged_dataset.csv")))
        self.model_metrics_path = Path(os.getenv("MODEL_METRICS_PATH", str(self.results_dir / "model_metrics.json")))
        self.model_artifact_path = Path(os.getenv("MODEL_ARTIFACT_PATH", str(self.models_dir / "random_forest.pkl")))
        self.interpretation_report_path = Path(os.getenv("INTERPRETATION_REPORT_PATH", str(self.results_dir / "interpretation_report.json")))
        self.feature_importance_pvalues_path = Path(os.getenv("FEATURE_IMPORTANCE_PVALUES_PATH", str(self.results_dir / "feature_importance_pvalues.json")))
        self.shap_plot_path = Path(os.getenv("SHAP_PLOT_PATH", str(self.results_dir / "shap_summary.png")))
        self.validation_report_path = Path(os.getenv("VALIDATION_REPORT_PATH", str(self.results_dir / "data_validation_report.json")))
        self.stability_metrics_path = Path(os.getenv("STABILITY_METRICS_PATH", str(self.results_dir / "stability_metrics.json")))
        self.overlap_report_path = Path(os.getenv("OVERLAP_REPORT_PATH", str(self.results_dir / "overlap_report.json")))
        self.perf_metrics_path = Path(os.getenv("PERF_METRICS_PATH", str(self.results_dir / "perf_metrics.json")))
        
        self._config = {
            "data_root": str(self.data_root),
            "raw_data_dir": str(self.raw_data_dir),
            "processed_data_dir": str(self.processed_data_dir),
            "results_dir": str(self.results_dir),
            "models_dir": str(self.models_dir),
            "seed": self.seed,
            "log_level": self.log_level,
            "query_log_path": str(self.query_log_path),
            "synthetic_data_path": str(self.synthetic_data_path),
            "merged_dataset_path": str(self.merged_dataset_path),
            "model_metrics_path": str(self.model_metrics_path),
            "model_artifact_path": str(self.model_artifact_path),
            "interpretation_report_path": str(self.interpretation_report_path),
            "feature_importance_pvalues_path": str(self.feature_importance_pvalues_path),
            "shap_plot_path": str(self.shap_plot_path),
            "validation_report_path": str(self.validation_report_path),
            "stability_metrics_path": str(self.stability_metrics_path),
            "overlap_report_path": str(self.overlap_report_path),
            "perf_metrics_path": str(self.perf_metrics_path),
        }
    
    def validate(self) -> None:
        """
        Validate that all required directories exist and are writable.
        
        Raises:
            EnvConfigError: If any directory is missing or not writable.
        """
        required_dirs = [
            self.raw_data_dir,
            self.processed_data_dir,
            self.results_dir,
            self.models_dir,
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise EnvConfigError(f"Cannot create directory {dir_path}: {e}")
            
            if not os.access(dir_path, os.W_OK):
                raise EnvConfigError(f"Directory {dir_path} is not writable")
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary."""
        return self._config.copy()
    
    def to_json(self, indent: int = 2) -> str:
        """Return configuration as a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

# Singleton instance
_config_instance: Optional[EnvConfig] = None

def get_config() -> EnvConfig:
    """
    Get the singleton EnvConfig instance.
    
    Returns:
        EnvConfig: The global configuration instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvConfig()
    return _config_instance

def reset_config() -> None:
    """Reset the configuration singleton (useful for testing)."""
    global _config_instance
    _config_instance = None

def main() -> None:
    """
    CLI entry point to display current configuration.
    """
    config = get_config()
    print("Current Environment Configuration:")
    print(config.to_json())
    
    # Validate configuration
    try:
        config.validate()
        print("\n✓ All directories validated successfully.")
    except EnvConfigError as e:
        print(f"\n✗ Configuration validation failed: {e}")
        raise

if __name__ == "__main__":
    main()
