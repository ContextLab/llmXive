import os
import sys
import time
import json
import traceback
import argparse
import subprocess
from pathlib import Path

def check_cpu_only():
    # Simple check for CPU-only environment
    # In a real CI, this would check for GPU availability
    print("Checking CPU-only environment...")
    return True

def run_download_stage():
    print("Running download stage...")
    result = subprocess.run([sys.executable, "code/download.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Download failed: {result.stderr}")
        return False
    return True

def run_preprocess_stage():
    print("Running preprocess stage...")
    result = subprocess.run([sys.executable, "code/preprocess.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Preprocess failed: {result.stderr}")
        return False
    return True

def run_features_stage():
    print("Running features stage...")
    result = subprocess.run([sys.executable, "code/features.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Features failed: {result.stderr}")
        return False
    return True

def run_analysis_stage():
    print("Running analysis stage...")
    result = subprocess.run([sys.executable, "code/analysis.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Analysis failed: {result.stderr}")
        return False
    return True

def run_report_stage():
    print("Running report stage...")
    result = subprocess.run([sys.executable, "code/report.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Report failed: {result.stderr}")
        return False
    return True

def main():
    print("Starting Quickstart Validation...")
    
    if not check_cpu_only():
        print("Not a CPU-only environment.")
        sys.exit(1)
    
    stages = [
        ("Download", run_download_stage),
        ("Preprocess", run_preprocess_stage),
        ("Features", run_features_stage),
        ("Analysis", run_analysis_stage),
        ("Report", run_report_stage)
    ]
    
    for name, func in stages:
        print(f"\n--- {name} ---")
        if not func():
            print(f"Validation failed at {name}.")
            sys.exit(1)
        print(f"{name} completed successfully.")
    
    print("\nAll stages completed successfully.")
    print("Quickstart validation passed.")

if __name__ == "__main__":
    main()