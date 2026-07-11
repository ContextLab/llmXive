import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path if running from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.hash_artifacts import hash_file, hash_directory, save_hashes, load_hashes
from utils.logging_utils import setup_logging, get_logger

logger = setup_logging()
logger = get_logger(__name__)

# Define the artifacts to hash based on the completed tasks and project structure
ARTIFACT_GROUPS = {
    "data_prep": [
        "code/data_prep/download_defects4j.py",
        "code/data_prep/generate_summaries.py",
        "code/data_prep/generate_summaries_real_llm.py",
        "code/data_prep/setup_data_directories.py",
    ],
    "analysis": [
        "code/analysis/bootstrap_utils.py",
        "code/analysis/correction_utils.py",
        "code/analysis/run_statistics.py",
    ],
    "utils": [
        "code/utils/hash_artifacts.py",
        "code/utils/config_manager.py",
        "code/utils/models.py",
        "code/utils/logging_utils.py",
        "code/utils/interaction_logger.py",
        "code/utils/anonymize_logs.py",
        "code/utils/assignment_generator.py",
        "code/utils/latency_calibrator.py",
        "code/utils/secure_consent_storage.py",
        "code/utils/generate_baseline_results.py",
        "code/utils/generate_reproducibility_package.py",
        "code/utils/startup_runner.py",
    ],
    "tests": [
        "code/tests/test_assignment_generator.py",
        "code/tests/test_bootstrap_utils.py",
        "code/tests/test_latency_calibrator.py",
        "code/tests/test_reproducibility.py",
        "code/tests/test_setup_data_directories.py",
        "code/tests/test_setup_project_structure.py",
        "code/tests/test_statistics.py",
    ],
    "setup": [
        "code/setup_project_structure.py",
    ],
    "data_outputs": [
        "data/analysis_results/results.csv",
        "data/analysis_results/sensitivity_analysis.csv",
        "data/analysis_results/outlier_flags.json",
        "data/analysis_results/baseline_results.json",
        "data/interaction_logs/anonymized_logs.csv",
        "data/reproducibility_package_v1.0.tar.gz",
    ],
    "docs": [
        "README.md",
    ],
    "ci": [
        ".github/workflows/test_reproducibility.yml",
    ],
}

def collect_artifacts() -> List[str]:
    """Collect all artifact paths relative to project root."""
    artifacts = []
    for group, files in ARTIFACT_GROUPS.items():
        for file_rel in files:
            full_path = project_root / file_rel
            if full_path.exists():
                artifacts.append(file_rel)
            else:
                logger.warning(f"Artifact not found, skipping: {full_path}")
    return artifacts

def generate_hashes(artifacts: List[str]) -> Dict[str, str]:
    """Generate SHA-256 hashes for a list of artifacts."""
    hashes = {}
    for rel_path in artifacts:
        full_path = project_root / rel_path
        if full_path.is_file():
            hashes[rel_path] = hash_file(full_path)
        elif full_path.is_dir():
            hashes[rel_path] = hash_directory(full_path)
        else:
            logger.error(f"Path exists but is not a file or dir: {full_path}")
    return hashes

def main():
    """Main entry point to update artifact_hashes.yaml."""
    state_dir = project_root / "state" / "projects" / "PROJ-140-evaluating-the-efficacy-of-code-summariz"
    state_dir.mkdir(parents=True, exist_ok=True)
    output_file = state_dir / "artifact_hashes.yaml"

    logger.info(f"Collecting artifacts from {project_root}...")
    artifacts = collect_artifacts()
    
    if not artifacts:
        logger.error("No artifacts found to hash. Check ARTIFACT_GROUPS definition.")
        sys.exit(1)

    logger.info(f"Found {len(artifacts)} artifacts. Generating hashes...")
    hashes = generate_hashes(artifacts)

    metadata = {
        "project_id": "PROJ-140-evaluating-the-efficacy-of-code-summariz",
        "task_id": "T032",
        "description": "Final artifact hashes for reproducibility package",
        "artifact_count": len(hashes),
        "hashes": hashes
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Successfully updated {output_file}")
    print(f"Updated {output_file} with {len(hashes)} artifact hashes.")

if __name__ == "__main__":
    main()
