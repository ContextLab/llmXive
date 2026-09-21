"""
Setup script to create and verify the data directory hierarchy.
This script creates data/raw and data/processed directories and verifies
they exist and are writable.
"""
import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Tuple

def setup_data_directories(base_dir: Path) -> Tuple[bool, List[str]]:
    """
    Create the required data directory hierarchy and verify writability.
    
    Args:
        base_dir: The project root directory path.
        
    Returns:
        Tuple of (success: bool, messages: List[str])
    """
    messages = []
    success = True
    
    # Define the required directories
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    required_dirs = [data_dir, raw_dir, processed_dir]
    
    # Create directories
    for dir_path in required_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            messages.append(f"Created directory: {dir_path}")
        except PermissionError:
            messages.append(f"ERROR: Permission denied creating {dir_path}")
            success = False
        except OSError as e:
            messages.append(f"ERROR: Failed to create {dir_path}: {e}")
            success = False
    
    # Verify directories exist and are writable
    for dir_path in required_dirs:
        if not dir_path.exists():
            messages.append(f"ERROR: Directory does not exist after creation: {dir_path}")
            success = False
            continue
        
        if not dir_path.is_dir():
            messages.append(f"ERROR: Path is not a directory: {dir_path}")
            success = False
            continue
        
        # Test writability by creating a temporary file
        test_file = dir_path / ".write_test"
        try:
            with open(test_file, 'w') as f:
                f.write("write_test")
            with open(test_file, 'r') as f:
                content = f.read()
            if content != "write_test":
                messages.append(f"ERROR: Write/read test failed for {dir_path}")
                success = False
            else:
                messages.append(f"Verified writable: {dir_path}")
            # Clean up test file
            test_file.unlink()
        except PermissionError:
            messages.append(f"ERROR: Directory is not writable: {dir_path}")
            success = False
        except OSError as e:
            messages.append(f"ERROR: Failed write test for {dir_path}: {e}")
            success = False
    
    return success, messages

def main():
    """Main entry point for the setup script."""
    parser = argparse.ArgumentParser(
        description="Setup data directory hierarchy for the project."
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to write a JSON status report"
    )
    
    args = parser.parse_args()
    base_dir = Path(args.base_dir).resolve()
    
    print(f"Setting up data directories in: {base_dir}")
    success, messages = setup_data_directories(base_dir)
    
    for msg in messages:
        print(msg)
    
    if success:
        print("\n✓ Data directory setup completed successfully.")
    else:
        print("\n✗ Data directory setup encountered errors.")
        sys.exit(1)
    
    # Write output report if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "success": success,
            "base_dir": str(base_dir),
            "directories": [
                str(base_dir / "data"),
                str(base_dir / "data" / "raw"),
                str(base_dir / "data" / "processed")
            ],
            "messages": messages
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nStatus report written to: {output_path}")

if __name__ == "__main__":
    main()
