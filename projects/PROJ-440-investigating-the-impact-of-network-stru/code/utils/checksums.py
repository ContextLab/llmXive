import hashlib
import os
import json
from typing import Dict, List, Optional
from pathlib import Path

def compute_file_checksum(file_path: str) -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        str: Hexadecimal checksum string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_checksum_file(data_dir: str, output_path: str):
    """
    Generate a checksum file for all files in the data directory.
    
    Args:
        data_dir: Path to the data directory.
        output_path: Path to save the checksum file.
    """
    checksums = {}
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.gitkeep'):
                continue
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, data_dir)
            checksums[relative_path] = compute_file_checksum(file_path)
    
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    print(f"Checksums generated and saved to {output_path}")

def verify_checksums(checksum_file: str, data_dir: str) -> bool:
    """
    Verify checksums of files against a checksum file.
    
    Args:
        checksum_file: Path to the checksum file.
        data_dir: Path to the data directory.
        
    Returns:
        bool: True if all checksums match, False otherwise.
    """
    with open(checksum_file, 'r') as f:
        checksums = json.load(f)
    
    all_valid = True
    for relative_path, expected_checksum in checksums.items():
        file_path = os.path.join(data_dir, relative_path)
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            all_valid = False
            continue
        
        actual_checksum = compute_file_checksum(file_path)
        if actual_checksum != expected_checksum:
            print(f"Checksum mismatch for {file_path}")
            all_valid = False
    
    return all_valid

def verify_single_file(file_path: str, expected_checksum: str) -> bool:
    """
    Verify the checksum of a single file.
    
    Args:
        file_path: Path to the file.
        expected_checksum: Expected checksum.
        
    Returns:
        bool: True if checksum matches, False otherwise.
    """
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum == expected_checksum

def setup_data_directories(base_path: str):
    """
    Create the required data subdirectories.
    
    Args:
        base_path: Base path for the data directory.
    """
    directories = ["raw", "processed", "analysis"]
    for dir_name in directories:
        dir_path = os.path.join(base_path, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")

def register_artifacts(state_path: str, checksum_file: str, data_dir: str):
    """
    Register the current checksum state into the project state file.
    
    Args:
        state_path: Path to the project state YAML file.
        checksum_file: Path to the generated checksum JSON file.
        data_dir: Path to the data directory (for relative path context).
    """
    import yaml
    from datetime import datetime
    
    # Load existing state or create new
    state_data = {}
    if os.path.exists(state_path):
        try:
            with open(state_path, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        except Exception:
            state_data = {}
    
    # Load checksums
    if not os.path.exists(checksum_file):
        raise FileNotFoundError(f"Checksum file not found: {checksum_file}")
    
    with open(checksum_file, 'r') as f:
        current_checksums = json.load(f)
    
    # Update state
    state_data['last_checksum_run'] = datetime.now().isoformat()
    state_data['data_checksums'] = current_checksums
    state_data['data_directory'] = str(Path(data_dir).resolve())
    
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"Artifacts registered in {state_path}")

def main():
    """
    Main entry point for CLI usage.
    
    Usage:
        python code/utils/checksums.py --update
        python code/utils/checksums.py --verify
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage data checksums for the project.")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Generate new checksums for all files in data/ and register in state/"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify current data files against the last registered checksums"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Path to the data directory (default: data)"
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default="state/projects/PROJ-440-investigating-the-impact-of-network-stru.yaml",
        help="Path to the project state file (default: state/projects/PROJ-440-investigating-the-impact-of-network-stru.yaml)"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data_dir):
        print(f"Error: Data directory not found: {args.data_dir}")
        sys.exit(1)
    
    checksum_file = os.path.join(args.data_dir, ".checksums.json")
    
    if args.update:
        print(f"Generating checksums for {args.data_dir}...")
        generate_checksum_file(args.data_dir, checksum_file)
        print("Registering artifacts in state...")
        register_artifacts(args.state_file, checksum_file, args.data_dir)
        print("Update complete.")
    
    elif args.verify:
        if not os.path.exists(checksum_file):
            print(f"Error: Checksum file not found: {checksum_file}")
            print("Run with --update first to generate checksums.")
            sys.exit(1)
        
        print(f"Verifying checksums for {args.data_dir}...")
        is_valid = verify_checksums(checksum_file, args.data_dir)
        if is_valid:
            print("All checksums verified successfully.")
        else:
            print("Verification failed: some files are missing or modified.")
            sys.exit(1)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
