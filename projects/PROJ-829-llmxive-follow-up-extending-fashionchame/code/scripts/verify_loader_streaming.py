"""
Verification script for T007: DeepFashion2 Streaming Loader.

This script runs the loader to verify it yields a sufficient volume of records
without OOM, as required by the task description.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.data.loader import load_deepfashion2_streaming, load_config

def main():
    print("=" * 60)
    print("T007 VERIFICATION: DeepFashion2 Streaming Loader")
    print("=" * 60)
    
    try:
        config = load_config()
        print(f"Config loaded from: {config.get('config_path')}")
    except FileNotFoundError as e:
        print(f"Config error: {e}")
        # Continue anyway if we can load the dataset directly
    
    print("\nStarting streaming verification...")
    print("Target: Yield 100 records without OOM.")
    
    count = 0
    target_count = 100
    sample_record = None
    
    try:
        stream = load_deepfashion2_streaming(split="train", streaming=True)
        
        for sample in stream:
            count += 1
            if count == 1:
                sample_record = sample
            if count % 20 == 0:
                print(f"  Progress: {count} records yielded...")
            if count >= target_count:
                break
        
        if count >= target_count:
            print(f"\n✓ SUCCESS: Yielded {count} records.")
            print("  Streaming loader is functional.")
            
            # Print a snippet of the first record structure (excluding large binary blobs)
            if sample_record:
                print("\n  Sample record keys (excluding images if present):")
                keys = [k for k in sample_record.keys() if not k.startswith("image")]
                print(f"    {keys}")
            
            return 0
        else:
            print(f"\n✗ FAILURE: Only yielded {count} records before stream ended.")
            return 1
            
    except RuntimeError as e:
        print(f"\n✗ CRITICAL ERROR: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())