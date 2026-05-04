#!/usr/bin/env python3
"""
T156: Verify 3 UCI datasets exist in data/raw/

Required datasets:
- Electricity (from UCI)
- Traffic (from UCI)
- Synthetic Control Chart (from UCI)

This script checks for the presence of required datasets and reports status.
Exit code 0 = all datasets found, 1 = some datasets missing.
"""

import os
import sys
from pathlib import Path

def main():
    # Project root is parent of scripts directory
    project_root = Path(__file__).parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    
    # Required datasets with possible file names (based on download_datasets.py conventions)
    required_datasets = {
        "Electricity": [
            "electricity.csv",
            "Electricity.csv",
            "UCI_Electricity.csv",
            "electricity.csv.gz",
        ],
        "Traffic": [
            "traffic.csv",
            "Traffic.csv",
            "UCI_Traffic.csv",
            "traffic.csv.gz",
        ],
        "Synthetic Control Chart": [
            "synthetic_control_chart.csv",
            "synthetic_control.csv",
            "SCC.csv",
            "synthetic_control_chart.csv.gz",
        ],
    }
    
    print("=" * 70)
    print("T156: UCI Dataset Verification")
    print("=" * 70)
    print(f"Project root: {project_root}")
    print(f"Data directory: {data_raw_dir}")
    print()
    
    # Check if data directory exists
    if not data_raw_dir.exists():
        print(f"❌ ERROR: Data directory does not exist: {data_raw_dir}")
        print("   Please run T007 to create data directory structure first.")
        print("=" * 70)
        sys.exit(1)
    
    all_found = True
    found_datasets = []
    missing_datasets = []
    
    for dataset_name, possible_names in required_datasets.items():
        found = False
        for name in possible_names:
            file_path = data_raw_dir / name
            if file_path.exists():
                file_size = file_path.stat().st_size
                file_size_mb = file_size / (1024 * 1024)
                print(f"✅ {dataset_name:25s}: {name:35s} ({file_size_mb:.2f} MB)")
                found = True
                found_datasets.append((dataset_name, name, file_size))
                break
        
        if not found:
            print(f"❌ {dataset_name:25s}: NOT FOUND")
            print(f"   Tried: {', '.join(possible_names)}")
            missing_datasets.append(dataset_name)
            all_found = False
    
    print()
    print("=" * 70)
    print(f"Summary: {len(found_datasets)} found, {len(missing_datasets)} missing")
    print("=" * 70)
    
    if all_found:
        print("✅ ALL REQUIRED DATASETS VERIFIED")
        print()
        print("Datasets ready for T158 (checksum recording) and T125 (evaluation).")
        print("=" * 70)
        sys.exit(0)
    else:
        print("❌ SOME DATASETS MISSING")
        print()
        print("Missing datasets:")
        for name in missing_datasets:
            print(f"  - {name}")
        print()
        print("To download missing datasets, run:")
        print("  python code/scripts/download_all_datasets.py")
        print()
        print("Or download individually:")
        print("  python code/scripts/download_synthetic_control.py")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
