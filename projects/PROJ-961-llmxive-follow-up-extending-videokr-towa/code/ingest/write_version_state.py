import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union
from utils.config import get_project_root, get_path, ensure_dir, get_config
from utils.versioning import write_project_state_yaml

def write_state_file(project_id: str, artifacts: Dict[str, str], output_path: Optional[Union[str, Path]] = None) -> None:
    """Write the project state file."""
    write_project_state_yaml(project_id, artifacts, output_path)

def main() -> None:
    """Main entry point for writing state."""
    pass
