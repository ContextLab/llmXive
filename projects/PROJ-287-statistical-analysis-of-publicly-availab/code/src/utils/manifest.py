"""
Manifest generation and management for reproducibility.

This module provides functionality to generate, save, load, and validate
reproducibility manifests for the topic drift analysis pipeline.
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
    """
    Generates reproducibility manifests for the analysis pipeline.

    A manifest captures all parameters, data checksums, and environmental
    conditions required to reproduce a specific analysis run.
    """

    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        """
        Initialize the manifest generator.

        Args:
            project_root: Root directory of the project. Defaults to current directory.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.manifest_path = self.project_root / "results" / "manifest.json"
        logger.info(f"Manifest generator initialized with root: {self.project_root}")

    def _calculate_file_checksum(self, file_path: Union[str, Path]) -> str:
        """
        Calculate SHA256 checksum of a file.

        Args:
            file_path: Path to the file.

        Returns:
            Hex digest of the SHA256 hash.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        checksum = sha256_hash.hexdigest()
        logger.debug(f"Calculated checksum for {file_path}: {checksum}")
        return checksum

    def _calculate_directory_checksum(self, dir_path: Union[str, Path]) -> str:
        """
        Calculate a combined checksum for all files in a directory.

        Args:
            dir_path: Path to the directory.

        Returns:
            Hex digest of the combined SHA256 hash.
        """
        dir_path = Path(dir_path)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        combined_hash = hashlib.sha256()
        # Sort files for deterministic ordering
        files = sorted(dir_path.rglob("*"))

        for file_path in files:
            if file_path.is_file():
                # Include relative path in the hash
                rel_path = str(file_path.relative_to(dir_path))
                combined_hash.update(rel_path.encode('utf-8'))

                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        combined_hash.update(chunk)

        return combined_hash.hexdigest()

    def generate_manifest(
        self,
        parameters: Dict[str, Any],
        data_checksums: Optional[Dict[str, str]] = None,
        environment_info: Optional[Dict[str, Any]] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a reproducibility manifest.

        Args:
            parameters: Dictionary of analysis parameters used.
        data_checksums: Dictionary mapping data file paths to their checksums.
        environment_info: Dictionary of environment information (Python version, etc.).
        additional_metadata: Any additional metadata to include.

        Returns:
            Complete manifest dictionary.
        """
        logger.info("Generating reproducibility manifest")

        # Ensure results directory exists
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

        manifest = {
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "project_root": str(self.project_root),
            "parameters": parameters,
            "data_checksums": data_checksums or {},
            "environment": environment_info or {},
            "metadata": additional_metadata or {},
            "status": "in_progress"
        }

        # Calculate checksum for the manifest itself (placeholder)
        # This will be updated when the manifest is saved
        manifest["self_checksum"] = None

        logger.info(f"Manifest generated with {len(manifest['parameters'])} parameters")
        return manifest

    def update_manifest(
        self,
        manifest: Dict[str, Any],
        status: Optional[str] = None,
        data_checksums: Optional[Dict[str, str]] = None,
        results_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing manifest with new information.

        Args:
            manifest: Existing manifest dictionary.
        status: New status value.
        data_checksums: Updated or additional data checksums.
        results_info: Information about generated results.

        Returns:
            Updated manifest dictionary.
        """
        logger.info("Updating manifest")

        if status:
            manifest["status"] = status
            logger.info(f"Manifest status updated to: {status}")

        if data_checksums:
            manifest["data_checksums"].update(data_checksums)
            logger.info(f"Added {len(data_checksums)} data checksums to manifest")

        if results_info:
            manifest["results"] = results_info
            logger.info("Added results information to manifest")

        return manifest

    def calculate_manifest_checksum(self, manifest: Dict[str, Any]) -> str:
        """
        Calculate the checksum of a manifest (excluding its own checksum field).

        Args:
            manifest: Manifest dictionary.

        Returns:
            Hex digest of the manifest's SHA256 hash.
        """
        # Create a copy to avoid modifying the original
        manifest_copy = manifest.copy()
        manifest_copy.pop("self_checksum", None)

        # Sort keys for deterministic serialization
        manifest_json = json.dumps(manifest_copy, sort_keys=True, default=str)
        checksum = hashlib.sha256(manifest_json.encode('utf-8')).hexdigest()

        logger.debug(f"Calculated manifest checksum: {checksum}")
        return checksum

    def save_manifest(self, manifest: Dict[str, Any], output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Save the manifest to a JSON file.

        Args:
            manifest: Manifest dictionary to save.
        output_path: Optional custom output path.

        Returns:
            Path to the saved manifest file.
        """
        output_path = Path(output_path) if output_path else self.manifest_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate and set the manifest checksum
        manifest["self_checksum"] = self.calculate_manifest_checksum(manifest)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, default=str)

        logger.info(f"Manifest saved to: {output_path}")
        return output_path

    def load_manifest(self, input_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Load a manifest from a JSON file.

        Args:
            input_path: Optional custom input path.

        Returns:
            Loaded manifest dictionary.

        Raises:
            FileNotFoundError: If the manifest file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        input_path = Path(input_path) if input_path else self.manifest_path

        if not input_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {input_path}")

        with open(input_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        logger.info(f"Manifest loaded from: {input_path}")
        return manifest

    def validate_manifest(self, manifest: Dict[str, Any]) -> bool:
        """
        Validate a manifest's integrity and completeness.

        Args:
            manifest: Manifest dictionary to validate.

        Returns:
            True if valid, False otherwise.
        """
        logger.info("Validating manifest")

        # Check required fields
        required_fields = ["version", "generated_at", "project_root", "parameters"]
        for field in required_fields:
            if field not in manifest:
                logger.error(f"Missing required field: {field}")
                return False

        # Verify self-checksum if present
        if "self_checksum" in manifest:
            stored_checksum = manifest["self_checksum"]
            calculated_checksum = self.calculate_manifest_checksum(manifest)

            if stored_checksum != calculated_checksum:
                logger.error("Manifest checksum validation failed")
                return False

        logger.info("Manifest validation successful")
        return True


def generate_reproducibility_manifest(
    parameters: Dict[str, Any],
    data_files: Optional[List[Union[str, Path]]] = None,
    environment_info: Optional[Dict[str, Any]] = None,
    project_root: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate a reproducibility manifest.

    Args:
        parameters: Analysis parameters.
        data_files: List of data file paths to include checksums for.
        environment_info: Environment information.
        project_root: Project root directory.

    Returns:
        Generated manifest dictionary.
    """
    generator = ManifestGenerator(project_root)

    # Calculate data checksums
    data_checksums = {}
    if data_files:
        for file_path in data_files:
            try:
                checksum = generator._calculate_file_checksum(file_path)
                data_checksums[str(file_path)] = checksum
            except FileNotFoundError as e:
                logger.warning(f"Could not calculate checksum for {file_path}: {e}")

    return generator.generate_manifest(
        parameters=parameters,
        data_checksums=data_checksums,
        environment_info=environment_info
    )


def save_reproducibility_manifest(
    manifest: Dict[str, Any],
    output_path: Optional[Union[str, Path]] = None,
    project_root: Optional[Union[str, Path]] = None
) -> Path:
    """
    Convenience function to save a reproducibility manifest.

    Args:
        manifest: Manifest dictionary to save.
        output_path: Optional custom output path.
        project_root: Project root directory (for default path).

    Returns:
        Path to the saved manifest file.
    """
    generator = ManifestGenerator(project_root)
    return generator.save_manifest(manifest, output_path)


def load_reproducibility_manifest(
    input_path: Optional[Union[str, Path]] = None,
    project_root: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Convenience function to load a reproducibility manifest.

    Args:
        input_path: Optional custom input path.
        project_root: Project root directory (for default path).

    Returns:
        Loaded manifest dictionary.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    generator = ManifestGenerator(project_root)
    return generator.load_manifest(input_path)
