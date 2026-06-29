#!/usr/bin/env python3
"""
T001c - Create project directory structure for glass-forming alloy research.

This script creates the required directory hierarchy for the project:
- data/ (with raw/, derived/, samples/ subdirectories)
- results/ (with shap_plots/ subdirectory)
- logs/
- state/
- contracts/

Run as: python scripts/setup_directories.py
"""
import os
import sys
from pathlib import Path
from datetime import datetime

def create_directory_structure():
    """Create all required project directories."""
    # Define all directories to create (relative to project root)
    directories = [
        "data",
        "data/raw",
        "data/derived",
        "data/samples",
        "results",
        "results/shap_plots",
        "logs",
        "state",
        "contracts",
    ]
    
    project_root = Path(__file__).resolve().parent.parent
    created_count = 0
    skipped_count = 0
    
    print(f"[T001c] Directory setup starting at: {datetime.now().isoformat()}")
    print(f"[T001c] Project root: {project_root}")
    print(f"[T001c] Creating {len(directories)} directories...")
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  [SKIP] {dir_path} (already exists)")
            skipped_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATED] {dir_path}")
            created_count += 1
    
    print(f"[T001c] Summary: {created_count} created, {skipped_count} skipped")
    print(f"[T001c] Directory setup complete at: {datetime.now().isoformat()}")
    
    return created_count, skipped_count

def verify_directories():
    """Verify all required directories exist after creation."""
    directories = [
        "data",
        "data/raw",
        "data/derived",
        "data/samples",
        "results",
        "results/shap_plots",
        "logs",
        "state",
        "contracts",
    ]
    
    project_root = Path(__file__).resolve().parent.parent
    missing = []
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing.append(dir_path)
    
    if missing:
        print(f"[ERROR] Missing directories: {missing}")
        return False
    
    print("[VERIFY] All required directories exist.")
    return True

if __name__ == "__main__":
    created, skipped = create_directory_structure()
    if verify_directories():
        print("[SUCCESS] T001c directory structure verified.")
        sys.exit(0)
    else:
        print("[FAILURE] T001c directory structure verification failed.")
        sys.exit(1)
