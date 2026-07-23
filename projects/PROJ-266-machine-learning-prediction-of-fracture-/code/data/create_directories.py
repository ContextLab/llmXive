import os
import sys

def main():
    """
    Create the required data directory structure for the project.
    
    Creates:
      - data/
      - data/raw/
      - data/processed/
      - data/explainability/
    """
    base_dir = "data"
    subdirs = ["raw", "processed", "explainability"]
    
    directories = [base_dir] + [os.path.join(base_dir, d) for d in subdirs]
    
    created = []
    failed = []
    
    for dir_path in directories:
        try:
            os.makedirs(dir_path, exist_ok=True)
            created.append(dir_path)
            print(f"Created directory: {dir_path}")
        except OSError as e:
            failed.append((dir_path, str(e)))
            print(f"Failed to create directory {dir_path}: {e}", file=sys.stderr)
    
    if failed:
        print(f"\nWarning: {len(failed)} directory creation(s) failed.", file=sys.stderr)
        return 1
    
    print(f"\nSuccessfully created {len(created)} directory(ies).")
    return 0

if __name__ == "__main__":
    sys.exit(main())