import sys
from pathlib import Path
from data_loader import load_datasets

def main():
    """
    Entry point for running the data loader script.
    Fetches datasets defined in data/manifests/datasets.yaml,
    validates them, saves to data/raw/, and generates checksums.
    """
    project_root = Path(__file__).parent.parent
    manifest_path = project_root / "data" / "manifests" / "datasets.yaml"
    data_raw_dir = project_root / "data" / "raw"
    checksums_path = project_root / "data" / "manifests" / "checksums.json"

    if not manifest_path.exists():
        print(f"Error: Manifest not found at {manifest_path}")
        sys.exit(1)

    print("Starting data loader...")
    load_datasets(
        manifest_path=str(manifest_path),
        data_raw_dir=str(data_raw_dir),
        checksums_path=str(checksums_path)
    )
    print("Data loader completed.")

if __name__ == "__main__":
    main()
