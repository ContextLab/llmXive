"""
Script to bundle the llmXive project into a reproducibility package.
This script creates a zip archive containing:
- src/ (source code)
- src/config/defaults.yaml
- scripts/run_full_suite.sh
- docs/README.md
- requirements.txt
- tests/ (test suite)
- data/ (processed results if available)
"""
import os
import sys
import zipfile
import shutil
import argparse
from pathlib import Path
from datetime import datetime

def create_reproducibility_package(output_path: str = "reproducibility_package.zip"):
    """
    Create a zip archive containing all necessary files for reproducing the experiment.
    
    Args:
        output_path: Path to the output zip file.
    
    Returns:
        None
    """
    # Define the files and directories to include
    project_root = Path(__file__).parent.parent
    include_patterns = [
        "src/",
        "src/config/defaults.yaml",
        "scripts/run_full_suite.sh",
        "docs/README.md",
        "requirements.txt",
        "tests/",
        "data/processed/",
        "logs/",
        "state/",
        ".gitignore",
        "README.md"
    ]

    # Check if output file exists and remove it
    output_file = project_root / output_path
    if output_file.exists():
        print(f"Removing existing package: {output_file}")
        output_file.unlink()

    # Create the zip file
    print(f"Creating reproducibility package: {output_file}")
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for pattern in include_patterns:
            pattern_path = project_root / pattern
            
            if pattern_path.is_file():
                # Add single file
                arcname = pattern
                zipf.write(pattern_path, arcname)
                print(f"  Added: {arcname}")
            
            elif pattern_path.is_dir():
                # Add directory recursively
                for file_path in pattern_path.rglob('*'):
                    if file_path.is_file():
                        arcname = str(file_path.relative_to(project_root))
                        zipf.write(file_path, arcname)
                        print(f"  Added: {arcname}")
            else:
                print(f"  Warning: Pattern not found: {pattern}")

    # Verify the package
    print(f"\nPackage created successfully: {output_file}")
    print(f"Package size: {output_file.stat().st_size / (1024 * 1024):.2f} MB")
    
    # List contents
    print("\nPackage contents:")
    with zipfile.ZipFile(output_file, 'r') as zipf:
        for name in sorted(zipf.namelist()):
            print(f"  {name}")

    return True

def main():
    parser = argparse.ArgumentParser(
        description="Create a reproducibility package for the llmXive project."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reproducibility_package.zip",
        help="Output path for the zip file (default: reproducibility_package.zip)"
    )
    
    args = parser.parse_args()
    
    try:
        success = create_reproducibility_package(args.output)
        if success:
            print("\n✓ Reproducibility package created successfully!")
            print("\nTo verify the package:")
            print("  1. Extract the package: unzip reproducibility_package.zip")
            print("  2. Navigate to the extracted directory")
            print("  3. Run: bash scripts/run_full_suite.sh")
            print("  4. Verify that all expected output files are generated")
            sys.exit(0)
        else:
            print("\n✗ Failed to create reproducibility package")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error creating reproducibility package: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
