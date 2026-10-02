import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"Artifact not found: {file_path}")

def verify_artifacts(base_dirs: List[str], extensions: List[str] = None) -> Dict[str, Any]:
    """
    Verify that all expected artifacts exist and calculate their checksums.
    
    Args:
        base_dirs: List of base directories to scan (e.g., ['data/', 'models/'])
        extensions: List of file extensions to include (e.g., ['.csv', '.json', '.pkl'])
    
    Returns:
        Dictionary containing verification status and artifact details
    """
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success",
        "artifacts": [],
        "missing": [],
        "errors": []
    }
    
    for base_dir_str in base_dirs:
        base_path = Path(base_dir_str)
        if not base_path.exists():
            results["missing"].append(str(base_path))
            continue
        
        for root, _, files in os.walk(base_path):
            for file in files:
                file_path = Path(root) / file
                
                # Filter by extension if specified
                if extensions:
                    if file_path.suffix not in extensions:
                        continue
                
                try:
                    checksum = calculate_sha256(file_path)
                    file_size = file_path.stat().st_size
                    
                    results["artifacts"].append({
                        "path": str(file_path),
                        "size_bytes": file_size,
                        "sha256": checksum,
                        "type": file_path.suffix
                    })
                except Exception as e:
                    results["errors"].append({
                        "path": str(file_path),
                        "error": str(e)
                    })
    
    # Check for critical missing files
    critical_files = [
        "data/processed/ground_truth.csv",
        "data/processed/features.csv",
        "models/logistic_regression.pkl",
        "models/random_forest.pkl",
        "models/decision_boundary.pkl",
        "data/processed/threshold_sweep.json",
        "data/processed/model_report.json"
    ]
    
    for critical_file in critical_files:
        if not Path(critical_file).exists():
            if critical_file not in results["missing"]:
                results["missing"].append(critical_file)
    
    if results["missing"]:
        results["status"] = "failed"
        results["message"] = f"Missing {len(results['missing'])} critical artifacts"
    
    return results

def write_checksum_manifest(artifacts: List[Dict], output_path: Path) -> None:
    """Write a manifest file containing all checksums."""
    manifest = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_artifacts": len(artifacts),
        "artifacts": artifacts
    }
    
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)

def main():
    """Main entry point for artifact verification."""
    print("Starting artifact verification...")
    
    # Define directories and file types to check
    base_dirs = ["data/", "models/"]
    extensions = [".csv", ".json", ".pkl", ".parquet"]
    
    # Verify artifacts
    results = verify_artifacts(base_dirs, extensions)
    
    # Print summary
    print(f"\nVerification Status: {results['status'].upper()}")
    print(f"Total Artifacts Found: {len(results['artifacts'])}")
    print(f"Missing Artifacts: {len(results['missing'])}")
    print(f"Errors: {len(results['errors'])}")
    
    if results['missing']:
        print("\nMissing Critical Artifacts:")
        for missing in results['missing']:
            print(f"  - {missing}")
    
    if results['errors']:
        print("\nErrors During Checksum Calculation:")
        for error in results['errors']:
            print(f"  - {error['path']}: {error['error']}")
    
    # Write manifest to data/logs/checksum_manifest.json
    manifest_path = Path("data/logs/checksum_manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    if results['artifacts']:
        write_checksum_manifest(results['artifacts'], manifest_path)
        print(f"\nManifest written to: {manifest_path}")
    
    # Exit with appropriate code
    sys.exit(0 if results['status'] == 'success' else 1)

if __name__ == "__main__":
    main()
