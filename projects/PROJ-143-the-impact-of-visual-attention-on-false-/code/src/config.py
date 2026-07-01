"""
Configuration management for the Visual Attention False Memory study.
Defines paths, thresholds, and model selection parameters.
"""
import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys

@dataclass(frozen=True)
class StudyPaths:
    """Configuration for all project directory paths."""
    root: str = "."
    data_raw: str = "data/raw"
    data_processed: str = "data/processed"
    data_figures: str = "figures"
    code: str = "code"
    specs: str = "specs"
    logs: str = "logs"

    def get_path(self, key: str) -> Path:
        """Resolve a relative path key to an absolute Path object."""
        if key == "root":
            return Path(self.root).resolve()
        
        base = Path(self.root).resolve()
        if key == "data_raw":
            return base / self.data_raw
        elif key == "data_processed":
            return base / self.data_processed
        elif key == "data_figures":
            return base / self.data_figures
        elif key == "code":
            return base / self.code
        elif key == "specs":
            return base / self.specs
        elif key == "logs":
            return base / self.logs
        else:
            raise ValueError(f"Unknown path key: {key}")

    def ensure_directories(self) -> None:
        """Create all required directories if they do not exist."""
        base = Path(self.root).resolve()
        dirs_to_create = [
            base / self.data_raw,
            base / self.data_processed,
            base / self.data_figures,
            base / self.logs,
        ]
        for d in dirs_to_create:
            d.mkdir(parents=True, exist_ok=True)

@dataclass(frozen=True)
class Thresholds:
    """Configuration for statistical and validation thresholds."""
    # Power analysis
    alpha: float = 0.01
    power: float = 0.80
    expected_effect_size: float = 0.30

    # False memory validation
    inconclusive_failure_rate: float = 0.10  # 10%
    min_rater_count: int = 3
    consensus_threshold: float = 0.66  # 2/3 agreement

    # Saliency validation
    auc_threshold: float = 0.70

    # Robustness
    magnitude_change_threshold: float = 0.05

    # Noise/Invalidation
    noise_correlation_threshold: float = 0.30

@dataclass(frozen=True)
class ModelSelection:
    """Configuration for model selection and hardware constraints."""
    # Saliency model
    saliency_model_name: str = "resnet18"
    saliency_target_layer: str = "layer4"
    saliency_input_size: int = 224
    use_cpu: bool = True
    use_cuda: bool = False
    quantization: str = "none"  # none, 8-bit, 4-bit

    # Alternative models for robustness
    alternative_saliency_models: List[str] = field(default_factory=lambda: ["vit_b"])

@dataclass
class StudyConfig:
    """Main configuration container."""
    paths: StudyPaths = field(default_factory=StudyPaths)
    thresholds: Thresholds = field(default_factory=Thresholds)
    model: ModelSelection = field(default_factory=ModelSelection)
    metadata: Dict[str, Any] = field(default_factory=lambda: {"version": "1.0", "updated": None})

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a serializable dictionary."""
        return {
            "paths": asdict(self.paths),
            "thresholds": asdict(self.thresholds),
            "model": asdict(self.model),
            "metadata": self.metadata
        }

    def save(self, filepath: Optional[str] = None) -> None:
        """Save configuration to a JSON file."""
        if filepath is None:
            filepath = str(self.paths.get_path("data_processed") / "config.json")
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: Optional[str] = None) -> 'StudyConfig':
        """Load configuration from a JSON file."""
        if filepath is None:
            filepath = str(Path.cwd() / "data" / "processed" / "config.json")
        
        path = Path(filepath)
        if not path.exists():
            # Return default config if file doesn't exist
            return cls()

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        config = cls()
        config.paths = StudyPaths(**data.get("paths", {}))
        config.thresholds = Thresholds(**data.get("thresholds", {}))
        config.model = ModelSelection(**data.get("model", {}))
        config.metadata = data.get("metadata", {})
        return config

# Global config instance
_global_config: Optional[StudyConfig] = None

def get_config() -> StudyConfig:
    """Get the global configuration instance, initializing if necessary."""
    global _global_config
    if _global_config is None:
        # Try to load from default location, else create default
        default_path = Path.cwd() / "data" / "processed" / "config.json"
        if default_path.exists():
            _global_config = StudyConfig.load(str(default_path))
        else:
            _global_config = StudyConfig()
            _global_config.paths.ensure_directories()
            _global_config.save()
    return _global_config

def update_config(updates: Dict[str, Any]) -> StudyConfig:
    """
    Update global configuration with provided values.
    Supports nested updates via dot notation (e.g., "thresholds.alpha").
    """
    global _global_config
    if _global_config is None:
        _global_config = get_config()

    for key, value in updates.items():
        parts = key.split('.')
        obj = _global_config
        
        # Navigate to the parent object
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                raise KeyError(f"Configuration key not found: {part}")
        
        # Set the value
        final_key = parts[-1]
        if hasattr(obj, final_key):
            setattr(obj, final_key, value)
        else:
            raise KeyError(f"Configuration key not found: {final_key}")
    
    return _global_config

def main():
    """CLI entry point for configuration management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Study Configuration Management")
    parser.add_argument('--init', action='store_true', help='Initialize default config')
    parser.add_argument('--show', action='store_true', help='Print current config')
    parser.add_argument('--update', type=str, nargs='+', help='Update config (key=value)')
    parser.add_argument('--save', action='store_true', help='Save current config')
    
    args = parser.parse_args()
    
    if args.init:
        config = StudyConfig()
        config.paths.ensure_directories()
        config.save()
        print(f"Configuration initialized and saved to {config.paths.get_path('data_processed') / 'config.json'}")
    
    if args.show:
        config = get_config()
        print(json.dumps(config.to_dict(), indent=2))
    
    if args.update:
        config = get_config()
        updates = {}
        for item in args.update:
            if '=' in item:
                k, v = item.split('=', 1)
                # Try to convert to appropriate type
                try:
                    v = int(v)
                except ValueError:
                    try:
                        v = float(v)
                    except ValueError:
                        if v.lower() == 'true': v = True
                        elif v.lower() == 'false': v = False
                        else: pass
                updates[k] = v
        update_config(updates)
        if args.save:
            config.save()
            print("Configuration updated and saved.")
        else:
            print("Configuration updated (not saved).")
    
    if not any([args.init, args.show, args.update]):
        parser.print_help()

if __name__ == "__main__":
    main()
