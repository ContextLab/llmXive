import os
from pathlib import Path
from typing import Dict, Any

def get_config() -> Dict[str, Any]:
    """
    Returns the project configuration dictionary.
    This function centralizes all paths, seeds, and hyperparameters.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    config = {
        "project_root": str(project_root),
        "data_raw": str(project_root / "data" / "raw"),
        "data_derived": str(project_root / "data" / "derived"),
        "data_validation": str(project_root / "data" / "validation"),
        "code_path": str(project_root / "code"),
        "derived_path": str(project_root / "data" / "derived"),  # Explicitly added for analysis.py
        
        # Random seeds for reproducibility
        "random_seed": 42,
        "np_seed": 42,
        
        # Hyperparameters
        "thresholds": [0.40, 0.45, 0.50, 0.55, 0.60],
        "distortion_count": 10,
        "snr_range": (-20, 20),
        "rt60_range": (0.1, 1.5),
        
        # ASR and Embedding models
        "asr_model": "whisper-tiny",
        "embedding_model": "all-MiniLM-L6-v2",
        
        # Resource limits
        "max_workers": 4,
        "batch_size": 16,
    }
    
    return config
