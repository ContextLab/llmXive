"""
Setup script to create the code directory hierarchy for the llmXive project.
Creates: code/{dataset,symbolic,bes,analysis,utils}
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List

# Define the directory structure to create relative to project root
CODE_SUBDIRS = [
    "dataset",
    "symbolic",
    "bes",
    "analysis",
    "utils"
]

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes this script is run from the project root or a subdirectory.
    """
    # If run as script, __file__ is available. If imported, we need a fallback.
    if __file__ and "__file__" in globals():
        current_dir = Path(__file__).resolve().parent
        # Check if we are in code/; if so, go up one level
        if current_dir.name == "code":
            return current_dir.parent
        return current_dir
    # Fallback: assume current working directory is project root
    return Path.cwd()

def setup_code_directories(project_root: Path, verbose: bool = True) -> List[Path]:
    """
    Create the code directory hierarchy.
    
    Args:
        project_root: Path to the project root directory.
        verbose: If True, print status messages.
        
    Returns:
        List of created directory paths.
        
    Raises:
        OSError: If directories cannot be created or verified.
    """
    code_root = project_root / "code"
    created_dirs = []
    
    # Ensure code root exists
    if not code_root.exists():
        code_root.mkdir(parents=True)
        if verbose:
            print(f"Created directory: {code_root}")
    
    # Create subdirectories
    for subdir_name in CODE_SUBDIRS:
        subdir_path = code_root / subdir_name
        
        try:
            # Create directory if it doesn't exist
            if not subdir_path.exists():
                subdir_path.mkdir(parents=True)
                if verbose:
                    print(f"Created directory: {subdir_path}")
            else:
                if verbose:
                    print(f"Directory already exists: {subdir_path}")
            
            # Verify directory is writable
            test_file = subdir_path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
                created_dirs.append(subdir_path)
                if verbose:
                    print(f"Verified writable: {subdir_path}")
            except (OSError, PermissionError) as e:
                raise OSError(f"Directory {subdir_path} is not writable: {e}")
                
        except (OSError, PermissionError) as e:
            raise OSError(f"Failed to create directory {subdir_path}: {e}")
    
    if verbose:
        print(f"\nSuccessfully created {len(created_dirs)} directories under {code_root}")
    
    return created_dirs

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Setup code directory hierarchy for llmXive project."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Path to project root (default: auto-detect)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output messages"
    )
    
    args = parser.parse_args()
    verbose = not args.quiet
    
    project_root = args.project_root if args.project_root else get_project_root()
    
    try:
        created = setup_code_directories(project_root, verbose=verbose)
        # Exit with success
        return 0
    except OSError as e:
        if verbose:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
