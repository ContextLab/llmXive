"""
Schema definitions for project data artifacts.

This module defines the expected structure for data versioning and other
critical data files used in the llmXive pipeline.
"""
from typing import TypedDict, Required


class DataVersion(TypedDict, total=False):
    """
    Schema for data_version.json.

    Tracks the provenance and integrity of downloaded datasets.
    Used by T007b to log download metadata.

    Attributes:
        source_url: The URL from which the data was downloaded.
        checksum_sha256: The SHA256 hash of the downloaded file content.
        timestamp: ISO 8601 formatted timestamp of the download.
    """
    source_url: Required[str]
    checksum_sha256: Required[str]
    timestamp: Required[str]
