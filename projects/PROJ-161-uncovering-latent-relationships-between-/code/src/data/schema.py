from typing import TypedDict, Required, Optional

class DataVersion(TypedDict, total=False):
    """Schema for the data version file."""
    source_url: Required[str]
    checksum_sha256: Required[str]
    timestamp: Required[str]

class DataVersionFile(TypedDict):
    """TypedDict for a single data version entry."""
    source_url: str
    checksum_sha256: str
    timestamp: str
