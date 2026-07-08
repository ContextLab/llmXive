import os
from pathlib import Path
from typing import Optional, Dict, Any

_config: Optional['Config'] = None

class Config:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.data_dir = self.project_root / "data"
        self.stimuli_dir = self.data_dir / "stimuli"
        self.stimuli_metadata_dir = self.data_dir / "stimuli_metadata"
        self.responses_dir = self.data_dir / "responses"
        self.processed_dir = self.data_dir / "processed"
        self.ethics_dir = self.data_dir / "ethics"
        self.logs_dir = self.data_dir / "logs"
        self.figures_dir = self.data_dir / "figures"
        self.code_dir = self.project_root / "code"
        self.tests_dir = self.project_root / "tests"
        
        # Ensure directories exist
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure all required directories exist."""
        dirs = [
            self.data_dir,
            self.stimuli_dir,
            self.stimuli_metadata_dir,
            self.responses_dir,
            self.processed_dir,
            self.ethics_dir,
            self.logs_dir,
            self.figures_dir,
            self.code_dir,
            self.tests_dir
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

def get_project_root() -> Path:
    """Get the project root directory."""
    global _config
    if _config is None:
        # Assume project root is the parent of 'code' directory
        # This might need adjustment based on actual deployment
        _config = Config(Path(__file__).resolve().parent.parent)
    return _config.project_root

def get_config() -> Config:
    """Get the global config object."""
    global _config
    if _config is None:
        _config = Config(get_project_root())
    return _config

def get_data_dir() -> Path:
    return get_config().data_dir

def get_stimuli_dir() -> Path:
    return get_config().stimuli_dir

def get_stimuli_metadata_dir() -> Path:
    return get_config().stimuli_metadata_dir

def get_responses_dir() -> Path:
    return get_config().responses_dir

def get_processed_dir() -> Path:
    return get_config().processed_dir

def get_ethics_dir() -> Path:
    return get_config().ethics_dir

def get_logs_dir() -> Path:
    return get_config().logs_dir

def get_figures_dir() -> Path:
    return get_config().figures_dir

def get_code_dir() -> Path:
    return get_config().code_dir

def get_tests_dir() -> Path:
    return get_config().tests_dir

def get_log_level() -> str:
    return os.getenv("LOG_LEVEL", "INFO")

def get_log_file_path() -> Path:
    return get_logs_dir() / "app.log"

def get_error_log_file_path() -> Path:
    return get_logs_dir() / "errors.log"

def get_manipulation_error_log_path() -> Path:
    return get_logs_dir() / "manipulation_errors.log"

def get_dataset_source() -> str:
    return os.getenv("DATASET_SOURCE", "mock")

def get_alpha_level() -> float:
    return float(os.getenv("ALPHA_LEVEL", 0.05))

def get_power_target() -> float:
    return float(os.getenv("POWER_TARGET", 0.80))

def get_effect_size() -> float:
    return float(os.getenv("EFFECT_SIZE", 0.25))
