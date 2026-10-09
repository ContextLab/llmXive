"""
Dataset contract definitions.

These Pydantic models describe the expected structure of dataset‑related
metadata used throughout the project. They are deliberately lightweight –
only the fields required by the pipeline are captured.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator


class DatasetInfo(BaseModel):
    """
    Core metadata for a dataset used in the analysis pipeline.

    Attributes
    ----------
    name: Human‑readable name of the dataset.
    version: Optional version identifier.
    source_url: URL where the raw data can be downloaded.
    local_path: Path on the local filesystem where the downloaded file resides.
    expected_hash: Optional SHA‑256 hash used for integrity verification.
    columns: Optional list of column names expected in the CSV.
    """

    name: str = Field(..., description="Human‑readable dataset name.")
    version: Optional[str] = Field(
        None, description="Optional version or release identifier."
    )
    source_url: HttpUrl = Field(..., description="URL to download the raw file.")
    local_path: Path = Field(..., description="Local path where the file is stored.")
    expected_hash: Optional[str] = Field(
        None,
        description="SHA‑256 hash of the file for integrity checking.",
        regex=r"^[a-fA-F0-9]{64}$",
    )
    columns: Optional[List[str]] = Field(
        None, description="Column names expected in the CSV file."
    )

    @validator("local_path")
    def ensure_path_is_absolute(cls, v: Path) -> Path:
        """Force absolute paths to avoid ambiguous relative handling."""
        return v.resolve()


class RawDatasetMeta(DatasetInfo):
    """
    Metadata specific to the raw (downloaded) dataset.

    In addition to the base fields, we track whether the file has been
    verified against its expected hash.
    """

    verified: bool = Field(
        False,
        description="Flag indicating whether the file hash matched the expected_hash.",
    )
