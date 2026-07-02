"""
Data Manifest Schema and Loader.

This module defines the schema for data_manifest.yaml and provides
functions to load, validate, and access manifest data.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from config import get_path, load_config
from utils.exceptions import PipelineException


MANIFEST_SCHEMA = {
    "required": ["version", "source_type", "datasets"],
    "fields": {
        "version": str,
        "source_type": str,  # 'REAL' or 'SIMULATED'
        "description": str,
        "datasets": list,
        "created_at": str,
        "metadata": dict
    },
    "dataset_schema": {
        "required": ["name", "path", "type"],
        "fields": {
            "name": str,
            "path": str,
            "type": str,  # 'SNP', 'METABOLITE', 'PHENOTYPE'
            "format": str,
            "description": str,
            "checksum": str
        }
    }
}


class ManifestLoader:
    """Loads and validates the data manifest file."""

    def __init__(self, manifest_path: Optional[Path] = None):
        """
        Initialize the manifest loader.

        Args:
            manifest_path: Optional path to the manifest file. If not provided,
                           uses the default path from config.
        """
        if manifest_path is None:
            self.path = get_path("data/data_manifest.yaml")
        else:
            self.path = manifest_path

        self.data: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """
        Load the manifest file from disk.

        Returns:
            The manifest data as a dictionary.

        Raises:
            PipelineException: If the file cannot be read or is invalid.
        """
        if not self.path.exists():
            raise PipelineException(
                code="MANIFEST_NOT_FOUND",
                message=f"Manifest file not found at {self.path}",
                details={"path": str(self.path)}
            )

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise PipelineException(
                code="MANIFEST_PARSE_ERROR",
                message="Failed to parse manifest YAML",
                details={"error": str(e), "path": str(self.path)}
            )

        self._validate()
        return self.data

    def _validate(self) -> None:
        """
        Validate the manifest against the schema.

        Raises:
            PipelineException: If validation fails.
        """
        if not self.data:
            raise PipelineException(
                code="MANIFEST_EMPTY",
                message="Manifest file is empty"
            )

        # Check required top-level fields
        for field in MANIFEST_SCHEMA["required"]:
            if field not in self.data:
                raise PipelineException(
                    code="MANIFEST_MISSING_FIELD",
                    message=f"Required field '{field}' is missing from manifest",
                    details={"missing_field": field}
                )

        # Validate field types
        for field, expected_type in MANIFEST_SCHEMA["fields"].items():
            if field in self.data and not isinstance(self.data[field], expected_type):
                raise PipelineException(
                    code="MANIFEST_INVALID_TYPE",
                    message=f"Field '{field}' has invalid type",
                    details={
                        "expected": expected_type.__name__,
                        "actual": type(self.data[field]).__name__
                    }
                )

        # Validate datasets
        if "datasets" in self.data and isinstance(self.data["datasets"], list):
            for idx, dataset in enumerate(self.data["datasets"]):
                if not isinstance(dataset, dict):
                    raise PipelineException(
                        code="MANIFEST_INVALID_DATASET",
                        message=f"Dataset at index {idx} is not a dictionary",
                        details={"index": idx}
                    )

                # Check required dataset fields
                for field in MANIFEST_SCHEMA["dataset_schema"]["required"]:
                    if field not in dataset:
                        raise PipelineException(
                            code="MANIFEST_MISSING_DATASET_FIELD",
                            message=f"Dataset at index {idx} missing required field '{field}'",
                            details={"index": idx, "field": field}
                        )

                # Validate dataset field types
                for field, expected_type in MANIFEST_SCHEMA["dataset_schema"]["fields"].items():
                    if field in dataset and not isinstance(dataset[field], expected_type):
                        raise PipelineException(
                            code="MANIFEST_INVALID_DATASET_TYPE",
                            message=f"Dataset at index {idx} field '{field}' has invalid type",
                            details={
                                "index": idx,
                                "field": field,
                                "expected": expected_type.__name__,
                                "actual": type(dataset[field]).__name__
                            }
                        )

    def get_source_type(self) -> str:
        """
        Get the source type from the manifest.

        Returns:
            The source type string ('REAL' or 'SIMULATED').
        """
        if not self.data:
            self.load()
        return self.data.get("source_type", "UNKNOWN")

    def get_datasets(self) -> List[Dict[str, Any]]:
        """
        Get the list of datasets from the manifest.

        Returns:
            List of dataset dictionaries.
        """
        if not self.data:
            self.load()
        return self.data.get("datasets", [])

    def get_dataset_by_type(self, dataset_type: str) -> Optional[Dict[str, Any]]:
        """
        Get a dataset by its type (SNP, METABOLITE, PHENOTYPE).

        Args:
            dataset_type: The type of dataset to retrieve.

        Returns:
            The dataset dictionary or None if not found.
        """
        datasets = self.get_datasets()
        for dataset in datasets:
            if dataset.get("type") == dataset_type:
                return dataset
        return None

    def get_dataset_path(self, dataset_type: str) -> Optional[Path]:
        """
        Get the resolved path for a dataset by type.

        Args:
            dataset_type: The type of dataset to retrieve.

        Returns:
            The resolved Path object or None if not found.
        """
        dataset = self.get_dataset_by_type(dataset_type)
        if dataset and "path" in dataset:
            base_dir = self.path.parent
            return base_dir / dataset["path"]
        return None


def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Convenience function to load and return the manifest data.

    Args:
        manifest_path: Optional path to the manifest file.

    Returns:
        The manifest data as a dictionary.
    """
    loader = ManifestLoader(manifest_path)
    return loader.load()


def get_manifest_source_type(manifest_path: Optional[Path] = None) -> str:
    """
    Convenience function to get the source type from the manifest.

    Args:
        manifest_path: Optional path to the manifest file.

    Returns:
        The source type string.
    """
    loader = ManifestLoader(manifest_path)
    loader.load()
    return loader.get_source_type()
