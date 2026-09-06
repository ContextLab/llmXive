import argparse
import json
import logging
import os
import sys
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Execute verify_dataset.py and update research.md and config.json"
    )
    parser.add_argument(
        "--dataset-id",
        type=str,
        default="Z-Reward",
        help="Dataset ID to verify (default: Z-Reward)"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala",
        help="Project root directory"
    )
    return parser.parse_args()

def run_verification(dataset_id: str) -> dict:
    """
    Execute verify_dataset.py and capture its JSON output from stdout.
    Returns the parsed JSON result.
    """
    script_path = Path("code/verify_dataset.py")
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    cmd = [sys.executable, str(script_path), "--dataset-id", dataset_id]
    logger.info(f"Running verification command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=120
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Verification script failed with exit code {e.returncode}")
        logger.error(f"stderr: {e.stderr}")
        raise RuntimeError(f"Verification failed: {e.stderr}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Verification script timed out")

    # Parse the JSON output from stdout
    try:
        output_json = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON output from verify_dataset.py: {e}")
        logger.error(f"Raw stdout: {result.stdout}")
        raise RuntimeError(f"Invalid JSON output: {e}")

    return output_json

def update_research_md(
    project_root: Path,
    verification_result: dict
):
    """
    Update research.md with verification results.
    If source_type is 'synthetic', write synthetic notes.
    Otherwise, write real data verification details.
    """
    research_md_path = project_root / "specs" / "001-llmxive-follow-up-extending-beyond-scala" / "research.md"
    
    # Ensure directory exists
    research_md_path.parent.mkdir(parents=True, exist_ok=True)

    source_type = verification_result.get("source_type", "unknown")
    checksum = verification_result.get("checksum", "N/A")
    title_token_overlap = verification_result.get("title_token_overlap", "N/A")

    # Read existing content if file exists
    existing_content = ""
    if research_md_path.exists():
        existing_content = research_md_path.read_text(encoding="utf-8")

    # Prepare the new entry
    new_entry = f"""
### Verification Results for {verification_result.get('dataset_id', 'Unknown')}

- **Source Type**: {source_type}
- **Checksum**: {checksum}
- **Title Token Overlap**: {title_token_overlap}
"""

    if source_type == "synthetic":
        new_entry += """
- **Note**: synthetic_fallback
"""

    # Append to existing content or create new file
    final_content = existing_content.rstrip() + "\n" + new_entry

    # Write back to file
    research_md_path.write_text(final_content, encoding="utf-8")
    logger.info(f"Updated {research_md_path} with verification results")

def update_config_json(
    project_root: Path,
    verification_result: dict
):
    """
    If source_type is 'synthetic', write IS_SYNTHETIC_RUN: true to config.json.
    """
    config_path = project_root / "data" / "processed" / "config.json"
    
    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    source_type = verification_result.get("source_type", "unknown")

    config_data = {}
    if config_path.exists():
        try:
            config_data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            config_data = {}

    if source_type == "synthetic":
        config_data["IS_SYNTHETIC_RUN"] = True
        logger.info("Setting IS_SYNTHETIC_RUN: true in config.json")
    else:
        # Ensure it's false or removed if real data
        config_data["IS_SYNTHETIC_RUN"] = False

    # Atomic write (read-modify-write in one operation)
    config_path.write_text(
        json.dumps(config_data, indent=2) + "\n",
        encoding="utf-8"
    )
    logger.info(f"Updated {config_path}")

def main():
    args = parse_args()
    project_root = Path(args.project_root)

    if not project_root.exists():
        raise FileNotFoundError(f"Project root not found: {project_root}")

    try:
        # 1. Run verification
        verification_result = run_verification(args.dataset_id)
        logger.info(f"Verification result: {verification_result}")

        # 2. Update research.md
        update_research_md(project_root, verification_result)

        # 3. Update config.json (if synthetic)
        update_config_json(project_root, verification_result)

        logger.info("Task T000b completed successfully.")

    except Exception as e:
        logger.error(f"Task T000b failed: {e}")
        # Re-raise to indicate failure
        raise

if __name__ == "__main__":
    main()