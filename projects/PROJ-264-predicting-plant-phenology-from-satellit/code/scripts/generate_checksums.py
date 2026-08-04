"""
CLI Script to generate and verify checksums for data directories.

Usage:
    python -m scripts.generate_checksums generate
    python -m scripts.generate_checksums verify
"""
import sys
from pathlib import Path
from src.data.checksums import generate_checksums_for_directories, verify_all_checksums
from src.lib.utils import setup_logging

def main() -> int:
    """Main entry point for the checksum script."""
    setup_logging()
    
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.generate_checksums <generate|verify>")
        return 1
    
    command = sys.argv[1]
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    
    if not data_dir.exists():
        print(f"Error: Data directory not found at {data_dir}")
        return 1
    
    sub_dirs = ["raw", "processed"]
    exclude_patterns = ["*.pyc", "__pycache__", "*.log", ".git", ".DS_Store"]
    
    try:
        if command == "generate":
            output_path = generate_checksums_for_directories(
                data_dir,
                sub_dirs,
                exclude_patterns=exclude_patterns
            )
            print(f"Checksums generated successfully at: {output_path}")
            return 0
        
        elif command == "verify":
            success = verify_all_checksums(
                data_dir,
                sub_dirs,
                exclude_patterns=exclude_patterns
            )
            if success:
                print("Verification successful: All checksums match.")
                return 0
            else:
                print("Verification failed: Some checksums do not match.")
                return 1
        else:
            print(f"Unknown command: {command}. Use 'generate' or 'verify'.")
            return 1
            
    except Exception as e:
        print(f"Error during execution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
