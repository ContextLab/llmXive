"""
Manifest generation and management for reproducibility.

This module provides functionality to generate, save, and load
reproducibility manifests containing metadata about the analysis run.
"""
import json
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.utils.logging import get_logger


logger = get_logger(__name__)


class ManifestGenerator:
    """Generates reproducibility manifests for analysis runs."""

    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        """
        Initialize the manifest generator.
        
        Args:
            project_root: Root directory of the project. Defaults to current directory.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.manifest_path = self.project_root / "results" / "manifest.json"
        self._manifest_data: Dict[str, Any] = {
            "metadata": {
                "generated_at": None,
                "project_name": "statistical-analysis-of-topic-drift",
                "version": "1.0.0"
            },
            "parameters": {},
            "data_checksums": {},
            "fetch_status": {},
            "model_results": {},
            "statistics": {},
            "sensitivity_analysis": {}
        }

    def set_generated_at(self, timestamp: Optional[datetime] = None) -> None:
        """Set the generation timestamp."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        self._manifest_data["metadata"]["generated_at"] = timestamp.isoformat()

    def add_parameter(self, key: str, value: Any) -> None:
        """Add a parameter to the manifest."""
        self._manifest_data["parameters"][key] = value
        logger.debug(f"Added parameter: {key} = {value}")

    def add_parameters(self, params: Dict[str, Any]) -> None:
        """Add multiple parameters to the manifest."""
        self._manifest_data["parameters"].update(params)
        logger.debug(f"Added parameters: {list(params.keys())}")

    def add_data_checksum(self, file_path: str, checksum: str) -> None:
        """Add a data file checksum to the manifest."""
        self._manifest_data["data_checksums"][file_path] = checksum
        logger.debug(f"Added checksum for {file_path}")

    def add_fetch_status(self, source: str, status: Dict[str, Any]) -> None:
        """Add fetch status for a data source."""
        self._manifest_data["fetch_status"][source] = status
        logger.debug(f"Added fetch status for {source}")

    def add_model_result(self, window: str, result: Dict[str, Any]) -> None:
        """Add model results for a specific time window."""
        self._manifest_data["model_results"][window] = result
        logger.debug(f"Added model results for window {window}")

    def add_statistic(self, key: str, value: Any) -> None:
        """Add a computed statistic to the manifest."""
        self._manifest_data["statistics"][key] = value
        logger.debug(f"Added statistic: {key}")

    def add_sensitivity_result(self, threshold: float, inconsistency_rate: float) -> None:
        """Add sensitivity analysis result."""
        if "sensitivity_thresholds" not in self._manifest_data:
            self._manifest_data["sensitivity_analysis"]["thresholds"] = []
            self._manifest_data["sensitivity_analysis"]["inconsistency_rates"] = []
        
        self._manifest_data["sensitivity_analysis"]["thresholds"].append(threshold)
        self._manifest_data["sensitivity_analysis"]["inconsistency_rates"].append(inconsistency_rate)
        logger.debug(f"Added sensitivity result: threshold={threshold}, rate={inconsistency_rate}")

    def compute_file_checksum(self, file_path: Union[str, Path]) -> str:
        """
        Compute SHA256 checksum of a file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Hexadecimal SHA256 checksum string.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()

    def generate_manifest(self) -> Dict[str, Any]:
        """
        Generate the final manifest dictionary.
        
        Returns:
            Complete manifest dictionary ready for serialization.
        """
        self.set_generated_at()
        return self._manifest_data.copy()

    def save_manifest(self, path: Optional[Union[str, Path]] = None) -> None:
        """
        Save the manifest to a JSON file.
        
        Args:
            path: Optional custom path. Defaults to results/manifest.json.
        """
        output_path = Path(path) if path else self.manifest_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        manifest = self.generate_manifest()
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, default=str)
        
        logger.info(f"Manifest saved to {output_path}")

    def load_manifest(self, path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Load an existing manifest from a JSON file.
        
        Args:
            path: Optional custom path. Defaults to results/manifest.json.
            
        Returns:
            Loaded manifest dictionary.
        """
        input_path = Path(path) if path else self.manifest_path
        
        if not input_path.exists():
            logger.warning(f"Manifest file not found: {input_path}. Creating new manifest.")
            return self.generate_manifest()
        
        with open(input_path, "r", encoding="utf-8") as f:
            loaded_manifest = json.load(f)
        
        # Merge with current structure to ensure all fields exist
        self._manifest_data.update(loaded_manifest)
        logger.info(f"Manifest loaded from {input_path}")
        
        return self._manifest_data


def generate_reproducibility_manifest(
    project_root: Optional[Union[str, Path]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    data_files: Optional[List[Path]] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate a reproducibility manifest.
    
    Args:
        project_root: Root directory of the project.
        parameters: Dictionary of parameters to include.
        data_files: List of data file paths to checksum.
        
    Returns:
        Generated manifest dictionary.
    """
    generator = ManifestGenerator(project_root)
    
    if parameters:
        generator.add_parameters(parameters)
    
    if data_files:
        for file_path in data_files:
            try:
                checksum = generator.compute_file_checksum(file_path)
                generator.add_data_checksum(str(file_path), checksum)
            except FileNotFoundError as e:
                logger.warning(f"Could not checksum {file_path}: {e}")
    
    return generator.generate_manifest()


def save_reproducibility_manifest(
    manifest: Dict[str, Any],
    output_path: Union[str, Path]
) -> None:
    """
    Save a manifest dictionary to a JSON file.
    
    Args:
        manifest: Manifest dictionary to save.
        output_path: Path where the manifest should be saved.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)
    
    logger.info(f"Manifest saved to {output_path}")


def load_reproducibility_manifest(
    manifest_path: Union[str, Path]
) -> Dict[str, Any]:
    """
    Load a manifest from a JSON file.
    
    Args:
        manifest_path: Path to the manifest file.
        
    Returns:
        Loaded manifest dictionary.
    """
    manifest_path = Path(manifest_path)
    
    if not manifest_path.exists():
        logger.warning(f"Manifest not found at {manifest_path}. Returning empty manifest.")
        return {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "project_name": "statistical-analysis-of-topic-drift",
                "version": "1.0.0"
            },
            "parameters": {},
            "data_checksums": {},
            "fetch_status": {},
            "model_results": {},
            "statistics": {},
            "sensitivity_analysis": {}
        }
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)