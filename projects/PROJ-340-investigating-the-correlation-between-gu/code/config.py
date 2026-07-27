"""
Configuration management for the project.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.data_dir = base_dir / "data"
        self.code_dir = base_dir / "code"
        
    def get_required_variables_path(self) -> Path:
        return self.data_dir / "config" / "required_variables.yaml"
        
    def get_output_schema_path(self) -> Path:
        return self.base_dir / "specs" / "001-gut-microbiome-sleep-architecture" / "contracts" / "output.schema.yaml"

def get_config() -> Config:
    base = Path(__file__).parent.parent
    return Config(base)

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    if config_path is None:
        config_path = get_config().get_required_variables_path()
    if not config_path.exists():
        return {}
    # Basic loader for YAML-like or JSON config if needed
    # For now, returning empty dict as specific loader is in ingest
    return {}