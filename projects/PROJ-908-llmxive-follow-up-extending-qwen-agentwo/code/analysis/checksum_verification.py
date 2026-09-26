"""
Task T016c: Checksum Verification for Benchmark Data.

This script generates and stores the checksum for `data/raw/benchmark.json`
in the project state file under `artifact_hashes`.

It requires T016a (fetch benchmark) to be completed first.
"""
import logging
import sys
from pathlib import Path
from utils.checksums import store_checksum_in_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    project_id = "PROJ-908-llmxive-follow-up-extending-qwen-agentwo"
    artifact_path = Path("data/raw/benchmark.json")
    state_file_path = Path("state/projects/PROJ-908-llmxive-follow-up-extending-qwen-agentwo.yaml")

    if not artifact_path.exists():
        logger.error(f"Artifact not found: {artifact_path}")
        logger.error("Ensure T016a (Fetch Canonical Benchmark) has been completed successfully.")
        sys.exit(1)

    logger.info(f"Computing checksum for {artifact_path}...")
    store_checksum_in_state(project_id, artifact_path, state_file_path)
    logger.info("Checksum verification and storage completed successfully.")

if __name__ == '__main__':
    main()
