import os
from pathlib import Path
from typing import Optional, Dict, Any

class Config:
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            # Default to current working directory if no root provided
            self.project_root = Path.cwd()
        else:
            self.project_root = project_root
        
        # Define base directories relative to project root
        self.data_dir = self.project_root / "data"
        self.code_dir = self.project_root / "code"
        self.tests_dir = self.project_root / "tests"
        self.docs_dir = self.project_root / "docs"
        
        # Sub-directories
        self.stimuli_dir = self.data_dir / "stimuli"
        self.stimuli_metadata_dir = self.data_dir / "stimuli_metadata"
        self.responses_dir = self.data_dir / "responses"
        self.processed_dir = self.data_dir / "processed"
        self.ethics_dir = self.data_dir / "ethics"
        self.logs_dir = self.data_dir / "logs"
        self.figures_dir = self.project_root / "figures"
        
        # Code sub-directories
        self.code_data_dir = self.code_dir / "data"
        self.code_stimuli_dir = self.code_dir / "stimuli"
        self.code_participants_dir = self.code_dir / "participants"
        self.code_analysis_dir = self.code_dir / "analysis"
        
        # Test sub-directories
        self.tests_unit_dir = self.tests_dir / "unit"
        self.tests_integration_dir = self.tests_dir / "integration"
        self.tests_contract_dir = self.tests_dir / "contract"
        
        # Docs sub-directories
        self.docs_ethics_dir = self.docs_dir / "ethics"

# Global config instance (lazy initialization)
_config: Optional[Config] = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config

def get_project_root() -> Path:
    return get_config().project_root

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
    return get_logs_dir() / "error.log"

def get_manipulation_error_log_path() -> Path:
    return get_logs_dir() / "manipulation_errors.log"

def ensure_directories():
    """Ensure all required directories exist."""
    config = get_config()
    dirs_to_create = [
        config.stimuli_dir,
        config.stimuli_metadata_dir,
        config.responses_dir,
        config.processed_dir,
        config.ethics_dir,
        config.logs_dir,
        config.figures_dir,
        config.code_data_dir,
        config.code_stimuli_dir,
        config.code_participants_dir,
        config.code_analysis_dir,
        config.tests_unit_dir,
        config.tests_integration_dir,
        config.tests_contract_dir,
        config.docs_ethics_dir
    ]
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)

def get_dataset_source() -> str:
    return os.getenv("DATASET_SOURCE", "mock")

def get_alpha_level() -> float:
    return float(os.getenv("ALPHA_LEVEL", 0.05))

def get_power_target() -> float:
    return float(os.getenv("POWER_TARGET", 0.80))

def get_effect_size() -> float:
    return float(os.getenv("EFFECT_SIZE", 0.25))
