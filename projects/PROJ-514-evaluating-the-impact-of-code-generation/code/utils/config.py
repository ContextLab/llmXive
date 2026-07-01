import os
from pathlib import Path
from typing import Optional, Dict, Any

# Project Root Detection
def get_project_root() -> Path:
    """Returns the absolute path to the project root."""
    current = Path(__file__).resolve()
    # Traverse up until we find a marker or hit root
    while current != current.parent:
        if (current / "code").exists() and (current / "data").exists():
            return current
        current = current.parent
    # Fallback: assume current working directory is root if structure found
    return Path.cwd()

def get_config() -> Dict[str, Any]:
    """
    Returns a dictionary of configuration values.
    Loads from environment variables or defaults.
    """
    project_root = get_project_root()
    
    return {
        "project_root": project_root,
        "data_dir": project_root / "data",
        "code_dir": project_root / "code",
        "reports_dir": project_root / "reports",
        "raw_human_dir": project_root / "data" / "raw" / "human_samples",
        "raw_llm_dir": project_root / "data" / "raw" / "llm_samples",
        "intermediate_dir": project_root / "data" / "intermediate",
        "processed_dir": project_root / "data" / "processed",
        
        # Seeds
        "random_seed": int(os.getenv("RANDOM_SEED", "42")),
        
        # Timeouts & Limits
        "api_timeout": int(os.getenv("API_TIMEOUT", "30")),
        "max_retries": int(os.getenv("MAX_RETRIES", "3")),
        "pmd_timeout_seconds": int(os.getenv("PMD_TIMEOUT_SECONDS", "120")),
        
        # API Keys (optional, for LLM)
        "hf_api_key": os.getenv("HF_API_KEY", ""),
        
        # Thresholds
        "validation_threshold": 0.95, # 95% valid required
    }
