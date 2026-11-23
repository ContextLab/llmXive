"""
T072: Artifact Verification Script.

Verifies that all expected output files exist and contain valid data.
Updates state/projects/PROJ-393...yaml with artifact hashes.
"""
import json
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import yaml
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to code/
PROJECT_ROOT = Path(__file__).parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-393-predicting-the-influence-of-composition-.yaml"

# Expected artifacts
EXPECTED_ARTIFACTS = {
    "data/raw/manual_curated.csv": {
        "type": "csv",
        "required": True
    },
    "data/processed/alloys_raw.csv": {
        "type": "csv",
        "required": True
    },
    "data/processed/alloys_features.csv": {
        "type": "csv",
        "required": True
    },
    "data/processed/model_metrics.json": {
        "type": "json",
        "required": True
    },
    "docs/reports/final_report.md": {
        "type": "md",
        "required": True
    },
    "docs/reports/statistical_limitations.md": {
        "type": "md",
        "required": True
    },
    "docs/reports/microstructure_note.md": {
        "type": "md",
        "required": True
    },
    "docs/reports/data_scarcity_warning.md": {
        "type": "md",
        "required": False  # Only if N < 50
    }
}

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return ""

def validate_csv(file_path: Path) -> bool:
    """Validate that a CSV file is readable and has content."""
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            logger.warning(f"CSV file {file_path} is empty but exists.")
            return True  # Empty is valid per T027/T032
        logger.info(f"CSV {file_path} has {len(df)} rows and {len(df.columns)} columns.")
        return True
    except Exception as e:
        logger.error(f"Invalid CSV {file_path}: {e}")
        return False

def validate_json(file_path: Path) -> bool:
    """Validate that a JSON file is readable."""
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        logger.info(f"JSON {file_path} is valid.")
        return True
    except Exception as e:
        logger.error(f"Invalid JSON {file_path}: {e}")
        return False

def validate_md(file_path: Path) -> bool:
    """Validate that a Markdown file exists and is not empty."""
    try:
        if not file_path.exists():
            return False
        size = file_path.stat().st_size
        if size == 0:
            logger.warning(f"Markdown file {file_path} is empty.")
            return False
        logger.info(f"Markdown {file_path} exists ({size} bytes).")
        return True
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return False

def update_state_file(artifacts_status: Dict[str, Any]) -> bool:
    """Update the state YAML file with artifact hashes and status."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        
        state_data = {
            "project_id": "PROJ-393-predicting-the-influence-of-composition-",
            "verification_timestamp": None,  # Will be set by caller if needed
            "artifacts": artifacts_status
        }
        
        # If state file exists, load and merge
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                existing_state = yaml.safe_load(f) or {}
                # Merge artifacts
                if "artifacts" in existing_state:
                    existing_state["artifacts"].update(artifacts_status["artifacts"])
                    state_data = existing_state
        
        with open(STATE_FILE, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False)
        
        logger.info(f"State file updated at {STATE_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to update state file: {e}")
        return False

def main():
    logger.info("Starting artifact verification for T072...")
    
    artifacts_status = {
        "artifacts": {},
        "summary": {
            "total": len(EXPECTED_ARTIFACTS),
            "present": 0,
            "missing": 0,
            "invalid": 0
        }
    }
    
    all_valid = True
    
    for relative_path, spec in EXPECTED_ARTIFACTS.items():
        full_path = PROJECT_ROOT / relative_path
        artifact_info = {
            "path": relative_path,
            "exists": False,
            "valid": False,
            "hash": None,
            "details": None
        }
        
        if not full_path.exists():
            if spec["required"]:
                logger.error(f"MISSING (Required): {relative_path}")
                artifacts_status["summary"]["missing"] += 1
                all_valid = False
            else:
                logger.info(f"MISSING (Optional): {relative_path}")
                artifacts_status["summary"]["missing"] += 1
            artifacts_status["artifacts"][relative_path] = artifact_info
            continue
        
        artifact_info["exists"] = True
        artifact_info["hash"] = calculate_file_hash(full_path)
        artifacts_status["summary"]["present"] += 1
        
        # Validate content
        is_valid = False
        if spec["type"] == "csv":
            is_valid = validate_csv(full_path)
        elif spec["type"] == "json":
            is_valid = validate_json(full_path)
        elif spec["type"] == "md":
            is_valid = validate_md(full_path)
        
        artifact_info["valid"] = is_valid
        artifact_info["details"] = f"Type: {spec['type']}, Hash: {artifact_info['hash'][:16]}..."
        
        if is_valid:
            logger.info(f"VALID: {relative_path}")
        else:
            logger.error(f"INVALID: {relative_path}")
            artifacts_status["summary"]["invalid"] += 1
            all_valid = False
        
        artifacts_status["artifacts"][relative_path] = artifact_info
    
    # Update state file
    if not update_state_file(artifacts_status):
        logger.error("Failed to update state file.")
        all_valid = False
    
    # Final summary
    logger.info("=" * 50)
    logger.info(f"Verification Summary:")
    logger.info(f"  Total Expected: {artifacts_status['summary']['total']}")
    logger.info(f"  Present: {artifacts_status['summary']['present']}")
    logger.info(f"  Missing: {artifacts_status['summary']['missing']}")
    logger.info(f"  Invalid: {artifacts_status['summary']['invalid']}")
    logger.info("=" * 50)
    
    if all_valid and artifacts_status["summary"]["missing"] == 0:
        logger.info("T072 VERIFICATION PASSED: All required artifacts present and valid.")
        return 0
    else:
        logger.warning("T072 VERIFICATION FAILED: Some artifacts missing or invalid.")
        return 1

if __name__ == "__main__":
    sys.exit(main())