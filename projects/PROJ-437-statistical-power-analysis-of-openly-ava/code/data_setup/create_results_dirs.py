"""
Module to create the results directory structure for the statistical power analysis project.

This module implements task T001d: Create directory `results/`, `results/paper/`.
"""
import os
import sys
from pathlib import Path

# Ensure the parent code directory is in the path for imports if running as script
if __name__ == "__main__":
    code_root = Path(__file__).resolve().parent.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))

def create_results_directories(base_path: Optional[Path] = None) -> dict:
    """
    Create the required results directory structure.
    
    Creates:
      - results/
      - results/paper/
    
    Args:
        base_path: Optional base path. If None, uses the project root 
                   (parent of the code directory).
    
    Returns:
        dict: A dictionary containing the paths of created directories.
    """
    if base_path is None:
        # Default to project root: parent of the 'code' directory
        current_file = Path(__file__).resolve()
        code_dir = current_file.parent
        base_path = code_dir.parent
    
    results_root = base_path / "results"
    paper_dir = results_root / "paper"
    
    created_dirs = []
    
    # Create results root
    if not results_root.exists():
        results_root.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(results_root))
        print(f"Created directory: {results_root}")
    else:
        print(f"Directory already exists: {results_root}")
    
    # Create results/paper
    if not paper_dir.exists():
        paper_dir.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(paper_dir))
        print(f"Created directory: {paper_dir}")
    else:
        print(f"Directory already exists: {paper_dir}")
    
    return {
        "results_root": str(results_root),
        "paper_dir": str(paper_dir),
        "created": created_dirs,
        "status": "success"
    }

def main():
    """Main entry point for creating results directories."""
    print("Creating results directory structure...")
    try:
        result = create_results_directories()
        print(f"Status: {result['status']}")
        print(f"Created directories: {', '.join(result['created'])}")
        return 0
    except Exception as e:
        print(f"Error creating directories: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())