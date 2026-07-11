"""
Environment configuration management for random seeds and model paths.

This module provides a centralized configuration class to manage:
- Random seeds for reproducibility (numpy, torch, random)
- Model paths for CPU-optimized diffusion models
- Directory paths for data and outputs
- Simulation and generation parameters

Usage:
    config = Config.load()
    config.set_seed(42)
    model_path = config.model_paths['lcm_model']
"""

import os
import random
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
import json

# Try to import torch and numpy, but handle gracefully if not installed yet
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class Config:
    """Centralized configuration manager for the llmXive pipeline."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize configuration with project root."""
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        
        self.project_root = Path(project_root).resolve()
        self._data = self._load_defaults()
        
    def _load_defaults(self) -> Dict[str, Any]:
        """Load default configuration values."""
        return {
            # Random seeds
            'random_seed': 42,
            'torch_seed': 42,
            'numpy_seed': 42,
            'deterministic': False,
            
            # Model paths
            'model_paths': {
                'lcm_model': 'latent-consistency/lcm-lora-sdv1-5',
                'yolo_model': 'yolov8n.pt',
            },
            
            # Directory paths (relative to project root)
            'paths': {
                'data_raw': 'data/raw',
                'data_derived': 'data/derived',
                'data_processed': 'data/processed',
                'physics_constraints': 'data/derived/physics_constraints',
                'prompts': 'data/derived/prompts',
                'generated_images': 'data/derived/generated_images',
                'evaluation_results': 'data/derived/evaluation_results',
                'state': 'state/projects',
                'specs': 'specs/001-llmxive-followup',
                'code_simulation': 'code/simulation',
                'code_generation': 'code/generation',
                'code_evaluation': 'code/evaluation',
                'code_analysis': 'code/analysis',
                'code_utils': 'code/utils',
                'tests_contract': 'tests/contract',
                'tests_integration': 'tests/integration',
                'tests_unit': 'tests/unit',
            },
            
            # Simulation parameters
            'simulation': {
                'resolution': (512, 512),
                'time_step': 0.016,  # ~60 FPS
                'iterations': 10,
                'max_objects': 50,
            },
            
            # Generation parameters
            'generation': {
                'num_inference_steps': 4,
                'guidance_scale': 1.0,
                'num_candidates': 5,  # For SSIM selection
                'batch_size': 1,
                'max_retries': 3,
            },
            
            # Evaluation parameters
            'evaluation': {
                'confidence_threshold': 0.7,
                'iou_threshold': 0.5,
                'y_offset_threshold': 5,  # pixels
                'min_cell_count': 5,  # For Fisher's Exact Test switch
            },
            
            # Statistical parameters
            'statistics': {
                'alpha': 0.05,
                'power_target': 0.8,
                'effect_size': 0.2,
                'contradiction_rate_threshold': 0.05,  # 5%
            },
            
            # Dataset parameters
            'dataset': {
                'source': 'coco-captions',
                'split': 'train',
                'target_size': 100,  # N=100 scope
                'validation_size': 20,
            }
        }
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'Config':
        """
        Load configuration from a YAML/JSON file or create default.
        
        Args:
            config_path: Path to config file. If None, uses default.
        
        Returns:
            Config instance with loaded or default values.
        """
        config = cls()
        
        if config_path:
            config_path = Path(config_path)
            if config_path.exists():
                config._load_from_file(config_path)
        
        return config
    
    def _load_from_file(self, config_path: Path) -> None:
        """Load configuration from a file."""
        with open(config_path, 'r') as f:
            if config_path.suffix in ['.json']:
                loaded = json.load(f)
            elif config_path.suffix in ['.yaml', '.yml']:
                try:
                    import yaml
                    loaded = yaml.safe_load(f)
                except ImportError:
                    raise ImportError("PyYAML is required to load YAML config files")
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
        
        # Deep update the loaded config
        self._deep_update(self._data, loaded)
    
    def _deep_update(self, base: Dict, update: Dict) -> None:
        """Recursively update a dictionary with another dictionary."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dotted key path."""
        keys = key.split('.')
        value = self._data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value by dotted key path."""
        keys = key.split('.')
        target = self._data
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
    
    def set_seed(self, seed: Optional[int] = None) -> None:
        """
        Set random seeds for reproducibility across all libraries.
        
        Args:
            seed: The seed value. If None, uses config value.
        """
        if seed is None:
            seed = self.get('random_seed', 42)
        
        # Set Python's random seed
        random.seed(seed)
        
        # Set numpy seed
        if HAS_NUMPY:
            np.random.seed(seed)
            self.set('numpy_seed', seed)
        
        # Set torch seed
        if HAS_TORCH:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(seed)
                torch.cuda.manual_seed_all(seed)
            self.set('torch_seed', seed)
        
        # Set deterministic behavior if configured
        if self.get('deterministic', False):
            if HAS_TORCH:
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
        
        self.set('random_seed', seed)
    
    def get_path(self, path_key: str) -> Path:
        """
        Get an absolute path for a configuration key.
        
        Args:
            path_key: Key in the 'paths' configuration (e.g., 'data_raw')
        
        Returns:
            Absolute Path object.
        """
        relative = self.get(f'paths.{path_key}', '')
        return self.project_root / relative
    
    def ensure_paths_exist(self) -> List[Path]:
        """
        Ensure all configured paths exist on disk.
        
        Returns:
            List of created paths.
        """
        created = []
        for path_key in self.get('paths', {}).keys():
            path = self.get_path(path_key)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                created.append(path)
        return created
    
    def get_model_path(self, model_name: str) -> str:
        """
        Get the model identifier/path for a named model.
        
        Args:
            model_name: Name of the model (e.g., 'lcm_model')
        
        Returns:
            Model identifier string.
        """
        return self.get(f'model_paths.{model_name}', '')
    
    def save(self, config_path: str) -> None:
        """
        Save current configuration to a file.
        
        Args:
            config_path: Path to save the config file.
        """
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(self._data, f, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return a copy of the configuration dictionary."""
        import copy
        return copy.deepcopy(self._data)
    
    def __repr__(self) -> str:
        return f"Config(project_root={self.project_root}, seed={self.get('random_seed')})"
    
    def __str__(self) -> str:
        return json.dumps(self._data, indent=2)


def main():
    """CLI entry point for configuration management."""
    import argparse
    
    parser = argparse.ArgumentParser(description='llmXive Configuration Manager')
    parser.add_argument('--config', '-c', type=str, help='Path to config file')
    parser.add_argument('--set-seed', type=int, help='Set random seed')
    parser.add_argument('--ensure-paths', action='store_true', help='Create all configured directories')
    parser.add_argument('--save', type=str, help='Save config to file')
    parser.add_argument('--show', action='store_true', help='Show current config')
    
    args = parser.parse_args()
    
    config = Config.load(args.config)
    
    if args.set_seed is not None:
        config.set_seed(args.set_seed)
        print(f"Seed set to: {args.set_seed}")
    
    if args.ensure_paths:
        created = config.ensure_paths_exist()
        print(f"Ensured {len(created)} paths exist:")
        for p in created:
            print(f"  - {p}")
    
    if args.save:
        config.save(args.save)
        print(f"Config saved to: {args.save}")
    
    if args.show or not any([args.set_seed, args.ensure_paths, args.save]):
        print("Current Configuration:")
        print(config)
    
    return config


if __name__ == '__main__':
    main()
