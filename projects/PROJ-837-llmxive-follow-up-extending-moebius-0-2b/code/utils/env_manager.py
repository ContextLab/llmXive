"""
Environment manager for dataset paths and artifact hash tracking.

Provides utilities for:
- Path validation and creation
- Artifact hash computation and verification
- Dataset configuration management
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from config_env import (
    get_env_config, 
    ensure_env_paths_exist, 
    verify_dataset, 
    register_artifact,
    get_data_path,
    get_datasets_path,
    get_annotations_path,
    get_results_path
)
from utils.logger import get_logger

logger = get_logger(__name__)

class EnvManager:
    """Manages environment configuration and artifact tracking."""
    
    def __init__(self):
        ensure_env_paths_exist()
        self.config = get_env_config()
        self.logger = logger

    def setup_dataset_paths(self, dataset_configs: Dict[str, Dict[str, Any]]):
        """
        Setup paths for multiple datasets.
        
        Args:
            dataset_configs: Dict mapping dataset name to config with 'path' and 'expected_hash'
        """
        results = {}
        for name, config in dataset_configs.items():
            path = Path(config['path'])
            expected_hash = config.get('expected_hash')
            
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Verify or register
            if path.exists():
                is_valid, error = verify_dataset(name, path)
                if is_valid:
                    results[name] = {"status": "verified", "path": str(path)}
                    self.logger.info(f"Dataset '{name}' verified: {path}")
                else:
                    results[name] = {"status": "invalid", "error": error, "path": str(path)}
                    self.logger.warning(f"Dataset '{name}' verification failed: {error}")
            else:
                results[name] = {"status": "missing", "path": str(path)}
                self.logger.info(f"Dataset '{name}' not yet downloaded: {path}")
        
        return results

    def compute_and_register_hash(self, name: str, path: Path, 
                                 metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Compute hash for a file and register it.
        
        Args:
            name: Artifact name
            path: Path to the file
            metadata: Optional metadata to store with the hash
        
        Returns:
            The computed hash string
        """
        if not path.exists():
            raise FileNotFoundError(f"Cannot compute hash for non-existent file: {path}")
        
        hash_value = self.config._compute_file_hash(path)
        self.config.register_artifact(name, path, hash_value, metadata)
        self.logger.info(f"Registered artifact '{name}' with hash {hash_value[:16]}...")
        return hash_value

    def verify_all_artifacts(self) -> Dict[str, bool]:
        """
        Verify all registered artifacts.
        
        Returns:
            Dict mapping artifact name to verification status
        """
        results = {}
        for name, info in self.config._dataset_registry.items():
            path = Path(info['path'])
            is_valid = self.config.verify_artifact(name, path)
            results[name] = is_valid
            status = "OK" if is_valid else "FAILED"
            self.logger.debug(f"Artifact '{name}': {status}")
        
        return results

    def get_artifact_report(self) -> Dict[str, Any]:
        """
        Generate a report of all registered artifacts.
        
        Returns:
            Dict with artifact details and verification status
        """
        report = {
            "mode": self.config.mode,
            "total_artifacts": len(self.config._dataset_registry),
            "artifacts": {}
        }
        
        for name, info in self.config._dataset_registry.items():
            path = Path(info['path'])
            is_valid = self.config.verify_artifact(name, path)
            report["artifacts"][name] = {
                "path": str(path),
                "hash": info['hash'],
                "exists": path.exists(),
                "verified": is_valid,
                "mode": info.get('mode'),
                "metadata": info.get('metadata', {})
            }
        
        return report

    def save_env_state(self, output_path: Optional[Path] = None):
        """
        Save current environment state to a JSON file.
        
        Args:
            output_path: Optional path for the state file (defaults to results/env_state.json)
        """
        if output_path is None:
            output_path = get_results_path() / "env_state.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            "config_summary": get_env_config_summary(),
            "artifacts": self.config._dataset_registry,
            "timestamp": "now"  # Would use datetime.now().isoformat() in real impl
        }
        
        with open(output_path, 'w') as f:
            json.dump(state, f, indent=2)
        
        self.logger.info(f"Environment state saved to {output_path}")
        return output_path

def get_env_manager() -> EnvManager:
    """Get or create the global EnvManager instance."""
    if not hasattr(get_env_manager, '_instance'):
        get_env_manager._instance = EnvManager()
    return get_env_manager._instance

def setup_environment(dataset_configs: Optional[Dict[str, Dict[str, Any]]] = None):
    """
    Setup the environment and optionally register datasets.
    
    Args:
        dataset_configs: Optional dict of dataset configurations
    """
    manager = get_env_manager()
    ensure_env_paths_exist()
    
    if dataset_configs:
        return manager.setup_dataset_paths(dataset_configs)
    
    return {"status": "initialized", "message": "Environment paths created"}

def verify_environment() -> Tuple[bool, Dict[str, Any]]:
    """
    Verify the entire environment setup.
    
    Returns:
        Tuple of (is_valid, report_dict)
    """
    manager = get_env_manager()
    report = manager.get_artifact_report()
    
    # Check if all critical paths exist
    critical_paths = [
        get_data_path(),
        get_datasets_path(),
        get_annotations_path(),
        get_results_path()
    ]
    
    paths_exist = all(p.exists() for p in critical_paths)
    
    # Check if all registered artifacts are valid
    if report["artifacts"]:
        all_valid = all(
            info.get("verified", False) 
            for info in report["artifacts"].values()
        )
    else:
        all_valid = True  # No artifacts registered yet is OK
    
    is_valid = paths_exist and all_valid
    
    return is_valid, report
