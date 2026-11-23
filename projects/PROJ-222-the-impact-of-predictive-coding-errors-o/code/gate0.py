"""
Gate 0: Data Discovery & Validation.
This module is kept for backward compatibility but logic is now in download.py (T012).
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_data_dir

class DataNotFoundError(Exception):
    """Raised when no valid datasets are found."""
    pass

def parse_verified_datasets_block(readme_path: Path) -> List[Dict[str, Any]]:
    """Parse the 'Verified datasets' block from data/README.md."""
    if not readme_path.exists():
        return []
    
    content = readme_path.read_text()
    lines = content.split('\n')
    
    datasets = []
    in_block = False
    current_dataset = {}
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('## Verified datasets'):
            in_block = True
            continue
        
        if in_block:
            if stripped.startswith('## ') or stripped.startswith('#'):
                break
            if not stripped:
                continue
            
            if stripped.startswith('- id:'):
                if current_dataset:
                    datasets.append(current_dataset)
                current_dataset = {'id': int(stripped.split(':')[1].strip())}
            elif stripped.startswith('source:'):
                current_dataset['source'] = stripped.split(':')[1].strip()
            elif stripped.startswith('type:'):
                current_dataset['type'] = stripped.split(':')[1].strip()
    
    if current_dataset:
        datasets.append(current_dataset)
    
    return datasets

def validate_gate0(readme_path: Path) -> bool:
    """
    Validate that at least one dataset is listed and valid.
    Returns True if valid, False otherwise.
    """
    datasets = parse_verified_datasets_block(readme_path)
    return len(datasets) > 0

def update_readme_with_gate_status(readme_path: Path, status: str):
    """Update README with gate status."""
    # Implementation for updating README
    pass

def main():
    """Main entry point for Gate 0."""
    data_dir = get_data_dir()
    readme_path = data_dir / "README.md"
    
    if not validate_gate0(readme_path):
        raise DataNotFoundError("No datasets found in data/README.md.")
    
    print("Gate 0 passed.")

if __name__ == "__main__":
    main()
