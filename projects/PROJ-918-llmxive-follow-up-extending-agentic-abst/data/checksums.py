"""
Checksum management for data integrity verification.

This module provides utilities to generate, save, load, and verify
SHA-256 checksums for files in the data directories.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Constants
CHECKSUM_FILE_NAME = "checksums.json"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the hash of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default: sha256).
        
    Returns:
        Hexadecimal hash string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is unsupported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_checksums(directory: Optional[Path] = None) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory recursively.
    
    Args:
        directory: Directory to scan. Defaults to DATA_DIR.
        
    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    target_dir = directory if directory else DATA_DIR
    checksums = {}
    
    if not target_dir.exists():
        raise FileNotFoundError(f"Directory not found: {target_dir}")
        
    for root, _, files in os.walk(target_dir):
        # Skip hidden files and .gitkeep
        files = [f for f in files if not f.startswith(".") and f != ".gitkeep"]
        for filename in files:
            file_path = Path(root) / filename
            try:
                rel_path = file_path.relative_to(DATA_DIR)
                checksum = calculate_file_hash(file_path)
                checksums[str(rel_path)] = checksum
            except ValueError:
                # Skip files outside the data directory if any
                continue
                
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Optional[Path] = None) -> Path:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary of checksums.
        output_path: Path to the output file. Defaults to DATA_DIR/checksums.json.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = DATA_DIR / CHECKSUM_FILE_NAME
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)
        
    return output_path

def load_checksums(input_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        input_path: Path to the input file. Defaults to DATA_DIR/checksums.json.
        
    Returns:
        Dictionary of checksums.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if input_path is None:
        input_path = DATA_DIR / CHECKSUM_FILE_NAME
        
    if not input_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {input_path}")
        
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)

def verify_checksums(checksums: Optional[Dict[str, str]] = None) -> Tuple[bool, List[str]]:
    """
    Verify the integrity of files against stored checksums.
    
    Args:
        checksums: Optional dictionary of expected checksums. If None, loads from file.
        
    Returns:
        Tuple of (all_valid: bool, failed_files: List[str]).
    """
    if checksums is None:
        try:
            checksums = load_checksums()
        except FileNotFoundError:
            return False, ["Checksum file not found. Run 'generate_checksums' first."]
    
    failed_files = []
    for rel_path, expected_hash in checksums.items():
        file_path = DATA_DIR / rel_path
        if not file_path.exists():
            failed_files.append(f"{rel_path} (missing)")
            continue
        
        try:
            actual_hash = calculate_file_hash(file_path)
            if actual_hash != expected_hash:
                failed_files.append(f"{rel_path} (hash mismatch)")
        except Exception as e:
            failed_files.append(f"{rel_path} (error: {str(e)})")
            
    return len(failed_files) == 0, failed_files

def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage data checksums.")
    parser.add_argument("command", choices=["generate", "verify"], help="Action to perform")
    parser.add_argument("--output", type=str, help="Output path for checksums (for generate)")
    parser.add_argument("--directory", type=str, help="Directory to scan (for generate)")
    
    args = parser.parse_args()
    
    if args.command == "generate":
        target_dir = Path(args.directory) if args.directory else None
        try:
            checksums = generate_checksums(target_dir)
            output_path = Path(args.output) if args.output else None
            saved_path = save_checksums(checksums, output_path)
            print(f"Generated {len(checksums)} checksums. Saved to: {saved_path}")
        except Exception as e:
            print(f"Error generating checksums: {e}", file=sys.stderr)
            sys.exit(1)
            
    elif args.command == "verify":
        try:
            is_valid, failed = verify_checksums()
            if is_valid:
                print("All checksums verified successfully.")
            else:
                print("Verification failed for the following files:")
                for f in failed:
                    print(f"  - {f}")
                sys.exit(1)
        except Exception as e:
            print(f"Error verifying checksums: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
