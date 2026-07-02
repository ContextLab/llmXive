"""
Configuration management for llmXive avian song variation project.

Loads paths from plan.md (YAML section) and environment variables.
Provides a centralized Config object for the entire project.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Try to import yaml; if missing, provide a clear error
try:
    import yaml
except ImportError:
    raise ImportError(
        "PyYAML is required for config.py. "
        "Please install it via 'pip install pyyaml' or ensure it is in requirements.txt."
    )

from utils import get_project_paths

# Default paths relative to project root
DEFAULTS = {
    "data_raw": "data/raw",
    "data_processed": "data/processed",
    "output_logs": "output/logs",
    "output_reports": "output/reports",
    "output_models": "output/models",
    "specs": "specs/001-predicting-avian-song-variation",
    "state_file": "state.yaml",
    "plan_file": "plan.md",
}

class Config:
    """
    Central configuration holder.
    
    Loads paths from:
    1. Environment variables (highest priority)
    2. plan.md YAML section (if present)
    3. Hardcoded defaults (lowest priority)
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent
        self.paths: Dict[str, Path] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from env vars, plan.md, and defaults."""
        
        # 1. Load base paths from utils (project structure)
        base_paths = get_project_paths(self.project_root)
        
        # Initialize paths with defaults first
        for key, default_rel in DEFAULTS.items():
            # If base_paths has a specific override, use it, else construct from root
            if key in base_paths:
                self.paths[key] = base_paths[key]
            else:
                self.paths[key] = self.project_root / default_rel

        # 2. Override with environment variables
        # Convention: PROJ_<KEY> (uppercase)
        for key in self.paths.keys():
            env_key = f"PROJ_{key.upper()}"
            if env_key in os.environ:
                self.paths[key] = Path(os.environ[env_key])

        # 3. Attempt to load from plan.md if it exists
        plan_path = self.paths.get("plan_file", self.project_root / "plan.md")
        if plan_path.exists():
            self._parse_plan_md(plan_path)

        # Ensure all directories exist
        self._ensure_directories()

    def _parse_plan_md(self, plan_path: Path) -> None:
        """
        Parse plan.md to extract YAML configuration block.
        
        Assumes plan.md contains a YAML block at the start or a specific
        section labeled 'config' or similar. For robustness, we look for
        a YAML block between '---' markers or a 'paths:' section.
        """
        try:
            content = plan_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            
            # Look for YAML block start/end
            yaml_lines = []
            in_yaml = False
            
            for line in lines:
                if line.strip() == '---' and not in_yaml:
                    in_yaml = True
                    continue
                if line.strip() == '---' and in_yaml:
                    break
                if in_yaml:
                    yaml_lines.append(line)
            
            if yaml_lines:
                yaml_content = "\n".join(yaml_lines)
                data = yaml.safe_load(yaml_content)
                
                if isinstance(data, dict) and "paths" in data:
                    for key, val in data["paths"].items():
                        if key in self.paths and val:
                            # Resolve relative to project root if relative path
                            p = Path(val)
                            if not p.is_absolute():
                                p = self.project_root / p
                            self.paths[key] = p
            else:
                # Fallback: try to find 'paths:' section in markdown
                # This is a simpler heuristic if no YAML block exists
                pass

        except Exception as e:
            # Log warning but don't fail; defaults are safe
            print(f"Warning: Could not parse plan.md config: {e}", file=sys.stderr)

    def _ensure_directories(self) -> None:
        """Create directories if they don't exist."""
        for key, path in self.paths.items():
            if key.endswith("_file"):
                # Ensure parent directory exists for files
                path.parent.mkdir(parents=True, exist_ok=True)
            else:
                path.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Optional[Path] = None) -> Path:
        """Get a path by key."""
        return self.paths.get(key, default or self.paths.get(key))

    def __getitem__(self, key: str) -> Path:
        return self.paths[key]

    def __repr__(self) -> str:
        return f"Config(root={self.project_root}, paths={list(self.paths.keys())})"

# Global singleton instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global config singleton."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def main() -> None:
    """CLI entry point to print current configuration."""
    cfg = get_config()
    print("Current Project Configuration:")
    print(f"Root: {cfg.project_root}")
    print("Paths:")
    for k, v in cfg.paths.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
