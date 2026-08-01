"""
Reproducibility Package Generator

Generates a self-contained tarball for OSF publication containing:
- Analysis scripts
- Anonymized interaction logs
- Analysis results
- README documentation

Explicitly excludes sensitive data (consent forms) per Constitution Principle VI.
"""
import os
import sys
import tarfile
import json
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_utils import get_logger

logger = get_logger(__name__)

# Configuration
PACKAGE_NAME = "reproducibility_package_v1.0"
OUTPUT_DIR = PROJECT_ROOT / "data"
OUTPUT_FILE = OUTPUT_DIR / f"{PACKAGE_NAME}.tar.gz"

# Inclusion patterns (relative to project root)
INCLUDE_PATTERNS = [
    "code/analysis/run_statistics.py",
    "code/analysis/bootstrap_utils.py",
    "code/analysis/correction_utils.py",
    "code/analysis/config.py",
    "code/utils/config_manager.py",
    "code/utils/logging_utils.py",
    "code/utils/hash_artifacts.py",
    "code/utils/models.py",
    "data/analysis_results/results.csv",
    "data/analysis_results/sensitivity_analysis.csv",
    "data/analysis_results/outlier_flags.json",
    "data/interaction_logs/anonymized_logs.csv",
    "README.md",
    "requirements.txt",
    "LICENSE",
]

# Exclusion patterns (explicitly excluded for security/compliance)
EXCLUDE_PATTERNS = [
    "data/consent/",
    "data/interaction_logs/raw_logs.csv",
    "data/interaction_logs/anonymization_mapping.json",
    ".env",
    "__pycache__",
    "*.pyc",
    ".git",
    ".github",
    "state/",
]

def should_exclude(file_path: str) -> bool:
    """
    Determine if a file should be excluded from the package.
    
    Args:
        file_path: Relative path from project root
        
    Returns:
        True if file should be excluded, False otherwise
    """
    # Check against explicit exclusions
    for exclude_pattern in EXCLUDE_PATTERNS:
        if file_path.startswith(exclude_pattern) or file_path == exclude_pattern.rstrip('/'):
            return True
    
    # Check for sensitive file extensions/names
    if file_path.endswith('.env'):
        return True
    if 'consent' in file_path.lower():
        return True
    if 'raw_logs' in file_path:
        return True
    
    return False

def create_reproducibility_package() -> str:
    """
    Create the reproducibility package tarball.
    
    Returns:
        Path to the created tarball
    """
    logger.info(f"Starting reproducibility package generation: {OUTPUT_FILE}")
    
    # Verify required input files exist
    required_files = [
        "data/analysis_results/results.csv",
        "data/interaction_logs/anonymized_logs.csv",
        "README.md",
        "requirements.txt"
    ]
    
    missing_files = []
    for req_file in required_files:
        if not (PROJECT_ROOT / req_file).exists():
            missing_files.append(req_file)
    
    if missing_files:
        raise FileNotFoundError(
            f"Required files missing for reproducibility package: {missing_files}. "
            "Please ensure analysis has been run and README/requirements.txt exist."
        )
    
    # Create a temporary directory to stage files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        staging_dir = temp_path / PACKAGE_NAME
        staging_dir.mkdir()
        
        logger.info(f"Staging files in: {staging_dir}")
        
        # Copy included files to staging directory
        files_copied = 0
        for include_pattern in INCLUDE_PATTERNS:
            src_path = PROJECT_ROOT / include_pattern
            
            if not src_path.exists():
                logger.warning(f"Skipping missing file: {include_pattern}")
                continue
            
            if should_exclude(include_pattern):
                logger.warning(f"Excluding file despite inclusion pattern: {include_pattern}")
                continue
            
            # Calculate relative path within the package
            rel_path = src_path.relative_to(PROJECT_ROOT)
            dest_path = staging_dir / rel_path
            
            # Create parent directories
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            if src_path.is_file():
                shutil.copy2(src_path, dest_path)
                files_copied += 1
                logger.debug(f"Copied: {include_pattern}")
            elif src_path.is_dir():
                # Copy directory recursively
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
                # Count files in directory
                for _ in dest_path.rglob("*"):
                    files_copied += 1
                logger.debug(f"Copied directory: {include_pattern}")
        
        if files_copied == 0:
            raise RuntimeError("No files were copied to the staging directory. Check patterns.")
        
        logger.info(f"Staged {files_copied} files in {staging_dir}")
        
        # Create manifest
        manifest = {
            "package_name": PACKAGE_NAME,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "project_id": "PROJ-140-evaluating-the-efficacy-of-code-summariz",
            "included_files": [
                str(p.relative_to(staging_dir)) 
                for p in staging_dir.rglob("*") if p.is_file()
            ],
            "excluded_patterns": EXCLUDE_PATTERNS,
            "version": "1.0"
        }
        
        manifest_path = staging_dir / "MANIFEST.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Created manifest: {manifest_path}")
        
        # Create tarball
        logger.info(f"Creating tarball: {OUTPUT_FILE}")
        
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        with tarfile.open(OUTPUT_FILE, "w:gz") as tar:
            tar.add(staging_dir, arcname=PACKAGE_NAME)
        
        logger.info(f"Successfully created reproducibility package: {OUTPUT_FILE}")
        
        # Verify tarball
        with tarfile.open(OUTPUT_FILE, "r:gz") as tar:
            members = tar.getnames()
            logger.info(f"Package contains {len(members)} entries")
            
            # Verify sensitive data is excluded
            sensitive_found = []
            for member in members:
                if should_exclude(member):
                    sensitive_found.append(member)
            
            if sensitive_found:
                raise RuntimeError(
                    f"SECURITY ERROR: Sensitive files found in package: {sensitive_found}"
                )
            
            logger.info("Verification passed: No sensitive data in package")
        
        return str(OUTPUT_FILE)

def main():
    """Main entry point for the reproducibility package generator."""
    try:
        package_path = create_reproducibility_package()
        logger.info(f"Reproducibility package created successfully: {package_path}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Missing required files: {e}")
        return 1
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during package generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
