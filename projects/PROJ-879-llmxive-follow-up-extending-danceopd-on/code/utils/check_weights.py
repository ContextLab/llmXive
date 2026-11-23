import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from utils.config import get_config, get_path

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")

def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return file_path.stat().st_size

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load manifest file if it exists."""
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            return json.load(f)
    return {}

def verify_file(file_path: Path, expected_hash: str) -> Tuple[bool, str]:
    """Verify a file against its expected hash."""
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    try:
        actual_hash = calculate_sha256(file_path)
        if actual_hash == expected_hash:
            return True, "OK"
        return False, f"Hash mismatch: expected {expected_hash}, got {actual_hash}"
    except Exception as e:
        return False, f"Error verifying file: {str(e)}"

def verify_ground_truth(manifest: Dict[str, Any]) -> bool:
    """Verify ground truth files exist and match manifest."""
    if "ground_truth" not in manifest:
        return False
    
    gt_files = manifest["ground_truth"]
    for file_name, expected_hash in gt_files.items():
        file_path = get_path("data/raw") / file_name
        if not file_path.exists():
            print(f"WARNING: Ground truth file not found: {file_path}")
            return False
        valid, msg = verify_file(file_path, expected_hash)
        if not valid:
            print(f"WARNING: Ground truth verification failed for {file_name}: {msg}")
            return False
    return True

def initialize_manifest(manifest_path: Path, weight_paths: Optional[Dict[str, Path]] = None) -> Dict[str, Any]:
    """
    Initialize manifest with existing weight files if present.
    
    Args:
        manifest_path: Path to the manifest file to create/update
        weight_paths: Optional dict mapping weight types to file paths.
                     If None, uses default paths from config.
                     
    Returns:
        The initialized manifest dictionary.
    """
    config = get_config()
    project_root = get_project_root()
    
    # Default weight paths if not provided
    if weight_paths is None:
        weight_paths = {
            "teacher_weights": Path(config.get("TEACHER_WEIGHTS_PATH", "models/teacher_weights.pth")),
            "expert_fields": Path(config.get("EXPERT_FIELDS_PATH", "models/expert_fields/")),
        }
    
    manifest = {
        "version": "1.0",
        "created": None,
        "updated": None,
        "weights": {},
        "ground_truth": {}
    }
    
    # Initialize with existing weight files if present
    for weight_type, path in weight_paths.items():
        # Resolve relative to project root if not absolute
        if not path.is_absolute():
            full_path = project_root / path
        else:
            full_path = path
        
        if full_path.exists():
            if full_path.is_file():
                # Single file
                try:
                    file_hash = calculate_sha256(full_path)
                    file_size = get_file_size(full_path)
                    manifest["weights"][weight_type] = {
                        "path": str(full_path),
                        "hash": file_hash,
                        "size": file_size,
                        "exists": True
                    }
                    print(f"Initialized manifest entry for {weight_type}: {full_path.name}")
                except Exception as e:
                    print(f"WARNING: Could not process {weight_type}: {str(e)}")
                    manifest["weights"][weight_type] = {
                        "path": str(full_path),
                        "exists": False,
                        "error": str(e)
                    }
            elif full_path.is_dir():
                # Directory - scan for files
                manifest["weights"][weight_type] = {
                    "path": str(full_path),
                    "type": "directory",
                    "files": {}
                }
                for file_path in full_path.rglob("*"):
                    if file_path.is_file() and file_path.suffix in [".pth", ".pt", ".bin"]:
                        try:
                            file_hash = calculate_sha256(file_path)
                            file_size = get_file_size(file_path)
                            rel_path = str(file_path.relative_to(project_root))
                            manifest["weights"][weight_type]["files"][rel_path] = {
                                "hash": file_hash,
                                "size": file_size,
                                "exists": True
                            }
                            print(f"Initialized manifest entry for {weight_type}: {rel_path}")
                        except Exception as e:
                            print(f"WARNING: Could not process {file_path}: {str(e)}")
        else:
            manifest["weights"][weight_type] = {
                "path": str(full_path),
                "exists": False,
                "note": "File not found - will be initialized when available"
            }
            print(f"WARNING: {weight_type} not found at {full_path}")
    
    # Check for ground truth files
    gt_dir = project_root / "data" / "raw"
    if gt_dir.exists():
        for file_path in gt_dir.glob("*.parquet"):
            if "teacher_ground_truth" in file_path.name or "ground_truth" in file_path.name:
                try:
                    file_hash = calculate_sha256(file_path)
                    file_size = get_file_size(file_path)
                    rel_path = str(file_path.relative_to(project_root))
                    manifest["ground_truth"][file_path.name] = file_hash
                    print(f"Initialized manifest entry for ground truth: {rel_path}")
                except Exception as e:
                    print(f"WARNING: Could not process ground truth {file_path}: {str(e)}")
    
    # Add metadata
    from datetime import datetime
    now = datetime.now().isoformat()
    manifest["created"] = now
    manifest["updated"] = now
    
    # Save manifest
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Manifest initialized at {manifest_path}")
    return manifest

def main():
    """Main entry point for weight checking and manifest initialization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check weights and initialize manifest")
    parser.add_argument("--path", type=str, default=None,
                      help="Path to weights directory or file. If not provided, uses config defaults.")
    parser.add_argument("--manifest", type=str, 
                      default="data/raw/weights_manifest.json",
                      help="Path to manifest file (default: data/raw/weights_manifest.json)")
    parser.add_argument("--init", action="store_true",
                      help="Initialize manifest with existing weights")
    parser.add_argument("--verify", action="store_true",
                      help="Verify existing manifest against files")
    
    args = parser.parse_args()
    
    project_root = get_project_root()
    manifest_path = project_root / args.manifest
    
    # Load existing manifest
    manifest = load_manifest(manifest_path)
    
    if args.init:
        # Initialize manifest with existing weight files
        weight_paths = None
        if args.path:
            path = Path(args.path)
            if path.is_file():
                weight_paths = {"teacher_weights": path}
            elif path.is_dir():
                weight_paths = {"teacher_weights": path}
        
        manifest = initialize_manifest(manifest_path, weight_paths)
        print("Manifest initialization complete.")
        return 0
    
    if args.verify:
        if not manifest_path.exists():
            print(f"ERROR: Manifest not found at {manifest_path}")
            return 1
        
        # Verify files in manifest
        all_valid = True
        for weight_type, weight_info in manifest.get("weights", {}).items():
            if isinstance(weight_info, dict) and weight_info.get("exists", False):
                if "files" in weight_info:
                    # Directory case
                    for rel_path, file_info in weight_info["files"].items():
                        if file_info.get("exists", False):
                            file_path = project_root / rel_path
                            if file_path.exists():
                                valid, msg = verify_file(file_path, file_info["hash"])
                                if not valid:
                                    print(f"VERIFICATION FAILED: {rel_path} - {msg}")
                                    all_valid = False
                            else:
                                print(f"FILE MISSING: {rel_path}")
                                all_valid = False
                else:
                    # Single file case
                    file_path = project_root / Path(weight_info["path"])
                    if file_path.exists():
                        valid, msg = verify_file(file_path, weight_info["hash"])
                        if not valid:
                            print(f"VERIFICATION FAILED: {weight_type} - {msg}")
                            all_valid = False
                    else:
                        print(f"FILE MISSING: {weight_type} ({weight_info['path']})")
                        all_valid = False
        
        # Verify ground truth
        if manifest.get("ground_truth"):
            if not verify_ground_truth(manifest):
                all_valid = False
        
        if all_valid:
            print("All verifications passed.")
            return 0
        else:
            print("Some verifications failed.")
            return 1
    
    # Default: just show current manifest status
    if manifest_path.exists():
        print(f"Manifest exists at {manifest_path}")
        print(f"Contents: {json.dumps(manifest, indent=2)}")
    else:
        print(f"Manifest not found at {manifest_path}")
        print("Use --init to initialize with existing weights")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())