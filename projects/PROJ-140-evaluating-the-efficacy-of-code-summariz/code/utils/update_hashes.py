"""
T032: Hash Generation
Generates artifact_hashes.yaml for the reproducibility package.

This script scans the project for critical artifacts (code, data results, configs)
and computes SHA-256 hashes for versioning and integrity verification.
It outputs the hashes to state/projects/PROJ-140-evaluating-the-efficacy-of-code-summariz/artifact_hashes.yaml.

Dependencies:
- code/utils/hash_artifacts.py (for hash_file, hash_directory, save_hashes)
"""
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path if running from subdirectory
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.hash_artifacts import hash_file, hash_directory, save_hashes
from utils.logging_utils import get_logger

logger = get_logger(__name__)

# Define the project state directory
PROJECT_ID = "PROJ-140-evaluating-the-efficacy-of-code-summariz"
STATE_DIR = project_root / "state" / "projects" / PROJECT_ID
HASH_OUTPUT_FILE = STATE_DIR / "artifact_hashes.yaml"

# Define the artifacts to hash
# These are the critical files that must be versioned for reproducibility
ARTIFACT_PATTERNS = [
    # Code modules
    "code/**/*.py",
    # Configuration
    "requirements.txt",
    ".env.example", # If exists, otherwise skip
    # Data results (generated)
    "data/analysis_results/results.csv",
    "data/analysis_results/final_report.md",
    "data/analysis_results/sensitivity_analysis.csv",
    "data/analysis_results/sensitivity_analysis_report.md",
    "data/interaction_logs/anonymized_logs.csv",
    "data/interaction_logs/cleaned_logs.csv",
    "data/interaction_logs/missing_ground_truth.json",
    "data/interaction_logs/outlier_flags.json",
    # Summaries
    "data/summaries/llm_summaries_sim.csv",
    "data/summaries/rule_summaries.csv",
    # CI/CD
    ".github/workflows/test_reproducibility.yml",
    # Docs
    "docs/README.md",
    "docs/api.md",
    "docs/quickstart.md",
]

def collect_artifacts(base_path: Path, patterns: List[str]) -> List[Path]:
    """
    Collects all files matching the given glob patterns relative to base_path.
    """
    artifacts = []
    for pattern in patterns:
        # Handle optional files (e.g., .env.example might not exist)
        if not pattern.startswith(".env") and not (base_path / pattern).exists():
            # Check if it's a directory pattern or a specific file
            # If it's a specific file that doesn't exist, skip it
            if "*" not in pattern:
                continue
        
        # Use rglob for recursive patterns
        if "**" in pattern:
            # rglob is safer for recursive matching
            files = list(base_path.rglob(pattern.replace("**/", "")))
            # Filter out directories if rglob picks them up (though rglob usually respects file patterns)
            files = [f for f in files if f.is_file()]
            artifacts.extend(files)
        else:
            # Simple glob
            matched = list(base_path.glob(pattern))
            artifacts.extend([f for f in matched if f.is_file()])
    
    # Remove duplicates and sort
    unique_artifacts = sorted(list(set(artifacts)))
    return unique_artifacts

def generate_hashes_for_project() -> Dict[str, Any]:
    """
    Scans the project, hashes all artifacts, and returns a dictionary of hashes.
    """
    logger.info(f"Starting hash generation for project: {PROJECT_ID}")
    
    if not STATE_DIR.exists():
        logger.warning(f"State directory does not exist: {STATE_DIR}. Creating it.")
        STATE_DIR.mkdir(parents=True, exist_ok=True)

    artifacts = collect_artifacts(project_root, ARTIFACT_PATTERNS)
    
    if not artifacts:
        logger.warning("No artifacts found to hash. Check patterns.")
        return {}

    hashes = {}
    for artifact in artifacts:
        rel_path = artifact.relative_to(project_root)
        logger.info(f"Hashing: {rel_path}")
        
        try:
            file_hash = hash_file(artifact)
            hashes[str(rel_path)] = file_hash
        except Exception as e:
            logger.error(f"Failed to hash {rel_path}: {e}")
            # Continue with other files

    return hashes

def main():
    """
    Main entry point for T032.
    Generates the artifact_hashes.yaml file.
    """
    logger.info("Executing T032: Hash Generation")
    
    hashes = generate_hashes_for_project()
    
    if not hashes:
        logger.error("No hashes generated. Aborting.")
        sys.exit(1)

    # Prepare the data structure for YAML
    output_data = {
        "project_id": PROJECT_ID,
        "generated_at": datetime.now().isoformat(),
        "artifacts": hashes
    }

    # Ensure output directory exists
    if not HASH_OUTPUT_FILE.parent.exists():
        HASH_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Save to YAML
    try:
        with open(HASH_OUTPUT_FILE, 'w') as f:
            yaml.dump(output_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Successfully saved hashes to {HASH_OUTPUT_FILE}")
        
        # Verify the file was created
        if HASH_OUTPUT_FILE.exists():
            logger.info("Verification: artifact_hashes.yaml exists.")
        else:
            logger.error("Verification failed: artifact_hashes.yaml does not exist.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to write hashes to file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
