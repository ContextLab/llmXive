"""
Checksum utility for data integrity management.
"""
import hashlib
import json
import os
from typing import Any, Dict, Optional
from pathlib import Path


class ChecksumManager:
    """
    Manages SHA-256 checksums for data artifacts.
    """

    def __init__(self, checksum_file: str = "data/checksums.json"):
        self.checksum_file = Path(checksum_file)
        self.checksums: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load existing checksums from disk."""
        if self.checksum_file.exists():
            with open(self.checksum_file, "r") as f:
                self.checksums = json.load(f)
        else:
            self.checksums = {}

    def save(self) -> None:
        """Save checksums to disk."""
        self.checksum_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.checksum_file, "w") as f:
            json.dump(self.checksums, f, indent=2)

    def compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def register(self, file_path: str, hash_value: Optional[str] = None) -> str:
        """
        Register a file's checksum.
        
        Args:
            file_path: Path to the file.
            hash_value: Optional pre-computed hash. If None, computed from file.
        
        Returns:
            The computed hash.
        """
        if hash_value is None:
            hash_value = self.compute_file_hash(file_path)
        
        self.checksums[file_path] = hash_value
        self.save()
        return hash_value

    def verify(self, file_path: str) -> bool:
        """Verify a file's checksum against stored value."""
        if file_path not in self.checksums:
            return False
        
        current_hash = self.compute_file_hash(file_path)
        return current_hash == self.checksums[file_path]

    def clear(self) -> None:
        """Clear all stored checksums."""
        self.checksums = {}
        if self.checksum_file.exists():
            os.remove(self.checksum_file)