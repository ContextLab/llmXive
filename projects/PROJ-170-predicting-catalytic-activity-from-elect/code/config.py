import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, List

# Global configuration cache
_config_cache: Optional[Dict[str, Any]] = None

def get_project_root() -> Path:
    """
    Returns the root path of the project.
    Assumes the code is run from the repository root or that 'code' is a subdirectory.
    """
    current_file = Path(__file__).resolve()
    # Navigate up one level from code/ to project root
    return current_file.parent

def get_data_path() -> Path:
    """Returns the path to the data directory."""
    return get_project_root() / "data"

def get_output_path() -> Path:
    """Returns the path to the outputs directory."""
    return get_project_root() / "outputs"

class Configuration:
    """
    Simple configuration holder.
    Loads paths from environment variables if present, otherwise uses defaults.
    """
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
        # Allow environment variable overrides for paths
        self.data_path = Path(os.getenv("LLMXIVE_DATA_PATH", str(project_root / "data")))
        self.outputs_path = Path(os.getenv("LLMXIVE_OUTPUTS_PATH", str(project_root / "outputs")))
        self.code_path = Path(os.getenv("LLMXIVE_CODE_PATH", str(project_root / "code")))
        self.tests_path = Path(os.getenv("LLMXIVE_TESTS_PATH", str(project_root / "tests")))
        self.state_path = Path(os.getenv("LLMXIVE_STATE_PATH", str(project_root / "state")))
        self.models_path = Path(os.getenv("LLMXIVE_MODELS_PATH", str(project_root / "code" / "models")))
        
        # Ensure required directories exist (soft creation for config loading)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create base directories if they don't exist to prevent runtime errors."""
        for path in [self.data_path, self.outputs_path, self.state_path, self.models_path]:
            path.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, str]:
        """Return configuration as a dictionary of strings."""
        return {
            "project_root": str(self.project_root),
            "data_path": str(self.data_path),
            "outputs_path": str(self.outputs_path),
            "code_path": str(self.code_path),
            "tests_path": str(self.tests_path),
            "state_path": str(self.state_path),
            "models_path": str(self.models_path),
        }

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to a JSON file."""
        save_path = path or (self.outputs_path / "config_snapshot.json")
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

def get_config() -> Configuration:
    """Returns a Configuration instance."""
    return Configuration(get_project_root())

def main():
    """Entry point for config verification and demonstration."""
    config = get_config()
    
    print(f"Project Root: {config.project_root}")
    print(f"Data Path: {config.data_path}")
    print(f"Output Path: {config.outputs_path}")
    print(f"Models Path: {config.models_path}")
    
    # Verify paths exist
    missing = [p for p in [config.data_path, config.outputs_path] if not p.exists()]
    if missing:
        print(f"Warning: Missing directories: {missing}")
    else:
        print("All base directories exist.")
        
    print("Configuration loaded successfully.")

if __name__ == "__main__":
    main()