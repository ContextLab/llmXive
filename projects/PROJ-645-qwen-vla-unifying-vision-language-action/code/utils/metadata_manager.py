"""
Metadata management utilities for dataset versioning and checksums.

This module provides functions to:
- Load and parse metadata.yaml
- Update dataset entries with checksums and row counts
- Validate metadata structure
- Generate reports on dataset status
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

from datetime import datetime

# Project root relative path
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
METADATA_FILE = DATA_DIR / "metadata.yaml"

class MetadataManager:
    """Manager for dataset metadata operations."""
    
    def __init__(self, metadata_path: Optional[Path] = None):
        """
        Initialize the metadata manager.
        
        Args:
            metadata_path: Path to metadata.yaml. Defaults to data/metadata.yaml.
        """
        self.metadata_path = metadata_path or METADATA_FILE
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from YAML file."""
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_path}")
        
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def save_metadata(self) -> None:
        """Save current metadata state to file."""
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                self.metadata,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                indent=2
            )
    
    def get_dataset(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a dataset entry by name.
        
        Args:
            name: The name of the dataset (e.g., 'filtered_open_x_embodiment')
        
        Returns:
            Dataset entry dict or None if not found.
        """
        for dataset in self.metadata.get('datasets', []):
            if dataset.get('name') == name:
                return dataset
        return None
    
    def update_dataset(
        self,
        name: str,
        checksum: Optional[str] = None,
        row_count: Optional[int] = None,
        version: Optional[str] = None,
        status: Optional[str] = None
    ) -> bool:
        """
        Update a dataset entry with new information.
        
        Args:
            name: Dataset name
            checksum: SHA256 checksum (optional)
            row_count: Number of rows (optional)
            version: Version string (optional)
            status: Status string (optional)
        
        Returns:
            True if update was successful, False if dataset not found.
        """
        dataset = self.get_dataset(name)
        if dataset is None:
            return False
        
        if checksum is not None:
            dataset['checksum'] = checksum
        if row_count is not None:
            dataset['row_count'] = row_count
        if version is not None:
            dataset['version'] = version
        if status is not None:
            dataset['status'] = status
        
        self.save_metadata()
        return True
    
    def compute_file_checksum(self, file_path: Path) -> str:
        """
        Compute SHA256 checksum of a file.
        
        Args:
            file_path: Path to the file.
        
        Returns:
            Hex digest of the SHA256 hash.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def count_parquet_rows(self, file_path: Path) -> int:
        """
        Count rows in a Parquet file.
        
        Args:
            file_path: Path to the Parquet file.
        
        Returns:
            Number of rows in the file.
        """
        try:
            import pandas as pd
            df = pd.read_parquet(file_path)
            return len(df)
        except ImportError:
            raise ImportError("pandas is required to count Parquet rows. Install with: pip install pandas pyarrow")
        except Exception as e:
            raise RuntimeError(f"Failed to count rows in {file_path}: {e}")
    
    def verify_and_update_dataset(self, name: str) -> Dict[str, Any]:
        """
        Verify a dataset file and update metadata with checksum and row count.
        
        Args:
            name: Dataset name to verify.
        
        Returns:
            Updated dataset entry.
        """
        dataset = self.get_dataset(name)
        if dataset is None:
            raise ValueError(f"Dataset not found: {name}")
        
        file_path = PROJECT_ROOT / dataset['path']
        
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        # Compute checksum
        checksum = self.compute_file_checksum(file_path)
        
        # Count rows
        row_count = self.count_parquet_rows(file_path)
        
        # Update metadata
        self.update_dataset(
            name=name,
            checksum=checksum,
            row_count=row_count,
            version=dataset.get('version', '1.0.0'),
            status='verified'
        )
        
        return self.get_dataset(name)
    
    def get_all_datasets(self) -> List[Dict[str, Any]]:
        """Get all dataset entries."""
        return self.metadata.get('datasets', [])
    
    def get_pending_datasets(self) -> List[Dict[str, Any]]:
        """Get all datasets with pending status."""
        return [
            ds for ds in self.metadata.get('datasets', [])
            if ds.get('status') == 'pending_download'
        ]
    
    def get_verified_datasets(self) -> List[Dict[str, Any]]:
        """Get all datasets with verified status."""
        return [
            ds for ds in self.metadata.get('datasets', [])
            if ds.get('status') == 'verified'
        ]
    
    def generate_report(self) -> str:
        """Generate a human-readable report of all datasets."""
        lines = [
            "Dataset Metadata Report",
            "=" * 50,
            f"Metadata Version: {self.metadata.get('metadata_version')}",
            f"Dataset Name: {self.metadata.get('dataset_name')}",
            f"Version: {self.metadata.get('version')}",
            f"Created: {self.metadata.get('created_at')}",
            "",
            "Datasets:"
        ]
        
        for dataset in self.metadata.get('datasets', []):
            lines.append(f"  - {dataset['name']}")
            lines.append(f"      Path: {dataset['path']}")
            lines.append(f"      Format: {dataset['format']}")
            lines.append(f"      Status: {dataset.get('status', 'unknown')}")
            lines.append(f"      Version: {dataset.get('version', 'pending')}")
            if dataset.get('checksum') != 'pending':
                lines.append(f"      Checksum: {dataset['checksum'][:16]}...")
            lines.append(f"      Rows: {dataset.get('row_count', 0)}")
            lines.append(f"      Description: {dataset.get('description', 'N/A')}")
            lines.append("")
        
        return "\n".join(lines)

def main():
    """CLI entry point for metadata management."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python metadata_manager.py <command> [args]")
        print("Commands:")
        print("  list              - List all datasets")
        print("  pending           - List pending datasets")
        print("  verified          - List verified datasets")
        print("  verify <name>     - Verify and update a dataset")
        print("  report            - Generate full report")
        sys.exit(1)
    
    command = sys.argv[1]
    manager = MetadataManager()
    
    if command == "list":
        for ds in manager.get_all_datasets():
            print(f"- {ds['name']} ({ds.get('status', 'unknown')})")
    elif command == "pending":
        for ds in manager.get_pending_datasets():
            print(f"- {ds['name']}")
    elif command == "verified":
        for ds in manager.get_verified_datasets():
            print(f"- {ds['name']}")
    elif command == "verify":
        if len(sys.argv) < 3:
            print("Usage: python metadata_manager.py verify <dataset_name>")
            sys.exit(1)
        name = sys.argv[2]
        try:
            updated = manager.verify_and_update_dataset(name)
            print(f"Verified: {updated['name']}")
            print(f"  Checksum: {updated['checksum'][:16]}...")
            print(f"  Rows: {updated['row_count']}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    elif command == "report":
        print(manager.generate_report())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
