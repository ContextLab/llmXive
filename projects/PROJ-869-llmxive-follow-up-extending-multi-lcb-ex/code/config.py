import os
import json
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class Config:
    """Project configuration management."""
    root_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    code_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "code")
    
    # Dataset paths
    raw_data_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "raw")
    processed_data_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "processed")
    
    # Output paths for specific tasks
    initial_pool_path: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "initial_pool.json")
    filtered_tasks_path: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "filtered_tasks.json")
    final_tasks_path: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "final_tasks_enriched.json")
    blind_baseline_logs_path: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "blind_baseline_logs.json")
    
    # Model paths
    model_path: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "models" / "model.gguf")
    
    # Random seed
    seed: int = 42

    def __post_init__(self):
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)

config = Config()

def get_path(relative_path: str) -> Path:
    """
    Resolves a relative path to an absolute path within the project structure.
    Handles common output paths for tasks.
    """
    # Map common task output names to config paths
    path_mapping = {
        "initial_pool.json": config.initial_pool_path,
        "filtered_tasks.json": config.filtered_tasks_path,
        "final_tasks_enriched.json": config.final_tasks_path,
        "blind_baseline_logs.json": config.blind_baseline_logs_path,
        "data/initial_pool.json": config.initial_pool_path,
        "data/filtered_tasks.json": config.filtered_tasks_path,
        "data/final_tasks_enriched.json": config.final_tasks_path,
        "data/blind_baseline_logs.json": config.blind_baseline_logs_path,
    }
    
    if relative_path in path_mapping:
        return path_mapping[relative_path]
    
    # Default to data directory if not explicitly mapped
    if relative_path.startswith("data/"):
        return config.data_dir / relative_path
    
    return config.root_dir / relative_path
