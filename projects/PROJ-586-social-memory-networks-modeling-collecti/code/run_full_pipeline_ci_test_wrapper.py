"""
Test wrapper to verify CI pipeline execution.

This script runs a minimal version of the pipeline to verify
that all components work correctly without running the full
expensive experiments.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from run_full_pipeline_ci import (
    get_memory_usage_mb,
    get_disk_usage_mb,
    save_results
)

def main():
    """Run minimal verification."""
    print("=== CI Pipeline Verification ===")
    
    # Test 1: Memory measurement
    print("\n1. Testing memory measurement...")
    try:
        mem = get_memory_usage_mb()
        print(f"   Current memory: {mem:.2f} MB")
        assert mem >= 0, "Memory should be non-negative"
        print("   ✓ Memory measurement works")
    except Exception as e:
        print(f"   ✗ Memory measurement failed: {e}")
        return 1
    
    # Test 2: Disk measurement
    print("\n2. Testing disk measurement...")
    try:
        disk = get_disk_usage_mb(PROJECT_ROOT)
        print(f"   Project disk usage: {disk:.2f} MB")
        assert disk >= 0, "Disk usage should be non-negative"
        print("   ✓ Disk measurement works")
    except Exception as e:
        print(f"   ✗ Disk measurement failed: {e}")
        return 1
    
    # Test 3: Save results
    print("\n3. Testing results saving...")
    try:
        test_results = {
            "test": "verification",
            "memory_mb": mem,
            "disk_mb": disk
        }
        output_path = PROJECT_ROOT / "results" / "test_verification.json"
        save_results(test_results, output_path)
        
        if output_path.exists():
            print(f"   Results saved to: {output_path}")
            print("   ✓ Results saving works")
        else:
            print("   ✗ Results file not created")
            return 1
    except Exception as e:
        print(f"   ✗ Results saving failed: {e}")
        return 1
    
    print("\n=== All verification tests passed ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())