"""
Checksum Manifest Generator for llmXive pipeline.

Generates SHA-256 checksums for all artifacts in the project tree
and updates the state manifest file.
"""
import os
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Import project root helper from existing config
# Fallback if not available in current context
try:
    from config import PROJECT_ROOT, STATE_DIR
except ImportError:
    # Define defaults if config.py doesn't export these yet
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    STATE_DIR = PROJECT_ROOT / "state"

# Directories to scan for artifacts
ARTIFACT_DIRS = [
    "code",
    "data/processed",
    "data/raw",
    "artifacts/reports",
    "artifacts/figures",
    "tests",
]

# File extensions to include
INCLUDE_EXTENSIONS = {".py", ".json", ".csv", ".png", ".txt", ".yaml", ".yml", ".md"}

# Excluded paths
EXCLUDED_PATHS = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".pytest_cache",
    "state/manifest.json",  # Don't hash the manifest itself
}

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}")

def scan_artifacts(base_dir: Path) -> List[Dict[str, Any]]:
    """Scan directory for artifacts and compute their checksums."""
    artifacts = []
    
    for rel_path_str in ARTIFACT_DIRS:
        rel_path = Path(rel_path_str)
        target_dir = base_dir / rel_path
        
        if not target_dir.exists():
            continue
        
        for root, dirs, files in os.walk(target_dir):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDED_PATHS]
            
            for file_name in files:
                file_path = Path(root) / file_name
                
                # Check extension
                if file_path.suffix.lower() not in INCLUDE_EXTENSIONS:
                    continue
                
                # Skip excluded paths
                if any(excl in file_path.parts for excl in EXCLUDED_PATHS):
                    continue
                
                try:
                    checksum = compute_file_checksum(file_path)
                    relative_path = file_path.relative_to(base_dir)
                    
                    artifacts.append({
                        "path": str(relative_path),
                        "checksum": checksum,
                        "size_bytes": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat()
                    })
                except Exception as e:
                    print(f"Warning: Could not process {file_path}: {e}", file=sys.stderr)
    
    return artifacts

def generate_manifest(artifacts: List[Dict[str, Any]], base_dir: Path) -> Dict[str, Any]:
    """Generate the complete manifest structure."""
    return {
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project_root": str(base_dir),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "metadata": {
            "scan_directories": ARTIFACT_DIRS,
            "included_extensions": list(INCLUDE_EXTENSIONS),
            "excluded_paths": list(EXCLUDED_PATHS)
        }
    }

def save_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """Save manifest to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load existing manifest if it exists."""
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def verify_artifacts(manifest: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
    """Verify current artifacts against stored manifest."""
    stored_artifacts = {a["path"]: a["checksum"] for a in manifest.get("artifacts", [])}
    current_artifacts = scan_artifacts(base_dir)
    
    verification_results = {
        "verified": True,
        "missing": [],
        "modified": [],
        "new": [],
        "total_stored": len(stored_artifacts),
        "total_current": len(current_artifacts)
    }
    
    current_map = {a["path"]: a["checksum"] for a in current_artifacts}
    
    # Check for missing or modified artifacts
    for path, stored_checksum in stored_artifacts.items():
        if path not in current_map:
            verification_results["missing"].append(path)
            verification_results["verified"] = False
        elif current_map[path] != stored_checksum:
            verification_results["modified"].append(path)
            verification_results["verified"] = False
    
    # Check for new artifacts
    for path in current_map:
        if path not in stored_artifacts:
            verification_results["new"].append(path)
    
    return verification_results

def main(args: List[str] = None) -> int:
    """Main entry point for checksum manifest generation."""
    base_dir = PROJECT_ROOT
    manifest_path = STATE_DIR / "manifest.json"
    
    # Parse command line arguments
    command = "generate"
    if args and len(args) > 1:
        command = args[1].lower()
    
    if command == "verify":
        existing_manifest = load_manifest(manifest_path)
        if not existing_manifest:
            print("Error: No existing manifest found. Run 'generate' first.", file=sys.stderr)
            return 1
        
        result = verify_artifacts(existing_manifest, base_dir)
        print(json.dumps(result, indent=2))
        return 0 if result["verified"] else 1
    
    elif command == "generate":
        print(f"Scanning artifacts in {base_dir}...")
        artifacts = scan_artifacts(base_dir)
        
        if not artifacts:
            print("Warning: No artifacts found to checksum.", file=sys.stderr)
        
        manifest = generate_manifest(artifacts, base_dir)
        save_manifest(manifest, manifest_path)
        
        print(f"Manifest generated: {manifest_path}")
        print(f"Artifacts checksummed: {manifest['artifact_count']}")
        return 0
    
    elif command == "help":
        print("Usage: python checksum_manifest.py [generate|verify|help]")
        print("  generate - Scan artifacts and create/update manifest")
        print("  verify   - Compare current state against stored manifest")
        print("  help     - Show this help message")
        return 0
    
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Use 'help' for usage information.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))
