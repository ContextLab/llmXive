import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
from config import Config

class TraceLoader:
    """Loads trace data from JSON files."""
    
    def __init__(self, base_dir: Optional[str] = None):
        self.config = Config()
        self.base_dir = Path(base_dir) if base_dir else self.config.data_raw_dir
    
    def load_single(self, file_path: str) -> Dict[str, Any]:
        """Load a single trace file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_all(self, directory: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """Load all trace files from a directory."""
        target_dir = Path(directory) if directory else self.base_dir
        
        if not target_dir.exists():
            raise FileNotFoundError(f"Directory not found: {target_dir}")
        
        for file_path in target_dir.glob("session_*.json"):
            yield self.load_single(str(file_path))
    
    def load_as_list(self, directory: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load all traces as a list."""
        return list(self.load_all(directory))

class MetricsLoader:
    """Loads metrics data from CSV files."""
    
    def __init__(self, base_dir: Optional[str] = None):
        self.config = Config()
        self.base_dir = Path(base_dir) if base_dir else self.config.data_processed_dir
    
    def load(self, file_path: str) -> List[Dict[str, Any]]:
        """Load metrics from a CSV file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def load_feature_matrix(self) -> List[Dict[str, Any]]:
        """Load the feature matrix from the standard location."""
        file_path = self.base_dir / "feature_matrix.csv"
        return self.load(str(file_path))
