"""
Extract metadata for all Python source files in the project.

Computes:
  - file_age: Days since last modification (from git log)
  - file_size: Size in bytes
  - cyclomatic_complexity: From radon

Outputs to: data/metadata/file_metadata.csv
"""
import os
import csv
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
OUTPUT_FILE = DATA_METADATA_DIR / "file_metadata.csv"

# Ensure output directory exists
DATA_METADATA_DIR.mkdir(parents=True, exist_ok=True)

def get_file_age_git(file_path: Path) -> Optional[float]:
    """Get file age in days from git log."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ai", str(file_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            date_str = result.stdout.strip().split()[0]  # YYYY-MM-DD
            last_modified = datetime.strptime(date_str, "%Y-%m-%d")
            age_days = (datetime.now() - last_modified).days
            return float(age_days)
    except (subprocess.CalledProcessError, ValueError, IndexError):
        pass
    return None

def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return file_path.stat().st_size

def get_cyclomatic_complexity(file_path: Path) -> Optional[float]:
    """Get cyclomatic complexity using radon."""
    try:
        import radon.metrics
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        # radon.metrics.h_visit returns a list of functions with their complexities
        results = list(radon.metrics.h_visit(source))
        if results:
            # Return the sum of complexities for all functions/classes in the file
            total_complexity = sum(func.complexity for func in results)
            return float(total_complexity)
        return 0.0
    except ImportError:
        print("Warning: radon not installed. Skipping cyclomatic complexity.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Warning: Could not compute complexity for {file_path}: {e}", file=sys.stderr)
        return None

def find_python_files(directory: Path) -> List[Path]:
    """Find all .py files in the given directory recursively."""
    return list(directory.rglob("*.py"))

def extract_metadata() -> List[Dict[str, Any]]:
    """Extract metadata for all Python files in the code directory."""
    python_files = find_python_files(CODE_DIR)
    records = []

    for file_path in python_files:
        relative_path = file_path.relative_to(PROJECT_ROOT)
        
        age = get_file_age_git(file_path)
        size = get_file_size(file_path)
        complexity = get_cyclomatic_complexity(file_path)

        records.append({
            "file_path": str(relative_path),
            "file_age": age,
            "file_size": size,
            "cyclomatic_complexity": complexity
        })

    return records

def save_to_csv(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Save records to a CSV file."""
    if not records:
        print("No records to save.")
        return

    fieldnames = ["file_path", "file_age", "file_size", "cyclomatic_complexity"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def main():
    """Main entry point."""
    print(f"Scanning Python files in {CODE_DIR}...")
    records = extract_metadata()
    print(f"Extracted metadata for {len(records)} files.")
    
    save_to_csv(records, OUTPUT_FILE)
    print(f"Metadata saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
