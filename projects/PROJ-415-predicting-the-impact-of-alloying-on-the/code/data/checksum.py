import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from config import DATA_DIR


def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def generate_checksums(data_dir: Optional[Path] = None) -> Dict[str, str]:
    """
    Generate checksums for all files in the data directory.
    
    Args:
        data_dir: Path to data directory. Defaults to DATA_DIR from config.
        
    Returns:
        Dictionary mapping relative file paths to their SHA256 checksums.
    """
    if data_dir is None:
        data_dir = DATA_DIR
        
    checksums = {}
    
    for root, _, files in os.walk(data_dir):
        for file in files:
            file_path = Path(root) / file
            relative_path = file_path.relative_to(data_dir)
            checksums[str(relative_path)] = compute_sha256(str(file_path))
            
    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Optional[Path] = None) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary of checksums to save.
        output_path: Path to output file. Defaults to data/artifacts/checksums.json.
    """
    if output_path is None:
        output_path = DATA_DIR / "artifacts" / "checksums.json"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)


def load_checksums(input_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        input_path: Path to input file. Defaults to data/artifacts/checksums.json.
        
    Returns:
        Dictionary of loaded checksums.
        
    Raises:
        FileNotFoundError: If the checksum file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if input_path is None:
        input_path = DATA_DIR / "artifacts" / "checksums.json"
        
    if not input_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {input_path}")
        
    with open(input_path, "r") as f:
        return json.load(f)


def verify_checksums(data_dir: Optional[Path] = None, 
                    checksums_path: Optional[Path] = None) -> Dict[str, bool]:
    """
    Verify all files against stored checksums.
    
    Args:
        data_dir: Path to data directory. Defaults to DATA_DIR from config.
        checksums_path: Path to checksums file. Defaults to data/artifacts/checksums.json.
        
    Returns:
        Dictionary mapping file paths to verification status (True = valid).
    """
    if data_dir is None:
        data_dir = DATA_DIR
    if checksums_path is None:
        checksums_path = DATA_DIR / "artifacts" / "checksums.json"
        
    stored_checksums = load_checksums(checksums_path)
    verification_results = {}
    
    for relative_path, expected_checksum in stored_checksums.items():
        file_path = data_dir / relative_path
        
        if not file_path.exists():
            verification_results[relative_path] = False
            continue
            
        actual_checksum = compute_sha256(str(file_path))
        verification_results[relative_path] = (actual_checksum == expected_checksum)
        
    return verification_results


def main() -> None:
    """
    Main function to generate and save checksums for the data directory.
    This is the entry point for the checksum generation script.
    """
    print(f"Generating checksums for data directory: {DATA_DIR}")
    
    # Ensure artifacts directory exists
    artifacts_dir = DATA_DIR / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate checksums
    checksums = generate_checksums(DATA_DIR)
    
    if not checksums:
        print("No files found in data directory to checksum.")
        return
        
    print(f"Generated checksums for {len(checksums)} files:")
    for path, checksum in checksums.items():
        print(f"  {path}: {checksum[:16]}...")
        
    # Save checksums
    output_path = DATA_DIR / "artifacts" / "checksums.json"
    save_checksums(checksums, output_path)
    print(f"\nChecksums saved to: {output_path}")
    
    # Verify checksums immediately after saving
    print("\nVerifying checksums...")
    verification_results = verify_checksums(DATA_DIR, output_path)
    
    all_valid = all(verification_results.values())
    if all_valid:
        print("All files verified successfully!")
    else:
        failed_files = [path for path, valid in verification_results.items() if not valid]
        print(f"Verification failed for {len(failed_files)} files:")
        for path in failed_files:
            print(f"  - {path}")


if __name__ == "__main__":
    main()
