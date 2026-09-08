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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
        description='Populate research.md and config.json with verification results.'
    )
    parser.add_argument(
        '--dataset-id',
        type=str,
        default='Z-Reward',
        help='Dataset ID to verify.'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.7,
        help='Verification threshold.'
    )
    parser.add_argument(
        '--algorithm',
        type=str,
        default='cosine-tfidf',
        help='Verification algorithm.'
    )
    parser.add_argument(
        '--project-root',
        type=str,
        default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala',
        help='Root directory of the project.'
    )
    return parser.parse_args()

def run_verification(dataset_id, threshold, algorithm):
    """
    Executes the reference-validator command and returns the JSON output.
    Raises RuntimeError if the command fails or returns invalid JSON.
    """
    cmd = [
        'reference-validator',
        '--dataset-id', dataset_id,
        '--threshold', str(threshold),
        '--algorithm', algorithm
    ]

    logger.info(f"Running verification command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            error_msg = f"Command failed with exit code {result.returncode}. stderr: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        output = result.stdout.strip()
        if not output:
            raise RuntimeError("Command produced no output.")

        try:
            data = json.loads(output)
            logger.info(f"Verification successful: {data}")
            return data
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Output is not valid JSON: {output}") from e

    except FileNotFoundError:
        raise RuntimeError("reference-validator command not found.")

def update_research_md(research_md_path, verification_data):
    """
    Updates research.md with verification results.
    Reads the file, finds the verified_datasets section, and updates the entry for the dataset.
    """
    if not research_md_path.exists():
        raise FileNotFoundError(f"research.md not found at {research_md_path}")

    content = research_md_path.read_text()
    
    # Simple logic to inject/update the verified_datasets section based on the task description
    # The task description implies a YAML structure. We will ensure the keys exist.
    # Since we cannot parse YAML reliably without a library in a simple script, 
    # and the task implies a specific structure, we will construct the block.
    
    # Check if verified_datasets key exists
    if 'verified_datasets:' not in content:
        logger.warning("verified_datasets key not found in research.md. Appending section.")
        content += "\nverified_datasets:\n"

    # We will replace the content of the first entry under verified_datasets if it matches the dataset_id
    # or append a new one if it doesn't exist.
    # Given the strict requirement, we will reconstruct the specific block for the dataset.
    
    import re
    
    # Pattern to find the block for z-reward (case insensitive for key)
    # We assume the structure: - dataset_id: "z-reward" ...
    dataset_entry_pattern = r'(\s*-\s*dataset_id:\s*["\']?z-reward["\']?.*?)(?=\s*-\s*dataset_id:|\Z)'
    
    # Prepare the new entry content
    new_entry = f"""  - dataset_id: "z-reward"
    title_token_overlap: {verification_data.get('title_token_overlap', 0)}
    checksum: "{verification_data.get('checksum', '')}"
    verification_date: "2023-10-27" # Placeholder or derived from timestamp
    source_type: "{verification_data.get('source_type', '')}"
"""

    # If we find an existing block, replace it. If not, append.
    # Note: This is a text-based replacement. For robustness, a YAML parser is preferred, 
    # but we stick to standard lib where possible.
    match = re.search(dataset_entry_pattern, content, re.DOTALL | re.IGNORECASE)
    
    if match:
        logger.info(f"Updating existing entry for z-reward in {research_md_path}")
        # Replace the matched block with the new entry
        new_content = content[:match.start()] + new_entry + content[match.end():]
    else:
        logger.info(f"Appending new entry for z-reward in {research_md_path}")
        # Ensure there is a newline before appending if needed
        if not content.endswith('\n'):
            content += '\n'
        new_content = content + new_entry

    research_md_path.write_text(new_content)
    logger.info(f"Updated {research_md_path}")

def update_config_json(config_path, verification_data, project_root):
    """
    Updates config.json with IS_SYNTHETIC_RUN flag if source_type is 'synthetic'.
    Also checks for lineage_report.json existence as per SC-004.
    """
    lineage_report_path = Path(project_root) / "data/processed/lineage_report.json"
    
    # Check SC-004: Verify lineage report existence if synthetic
    if verification_data.get('source_type') == 'synthetic':
        if not lineage_report_path.exists():
            raise RuntimeError(
                "SC-004 Violation: source_type is 'synthetic' but data/processed/lineage_report.json does not exist. "
                "Cannot write IS_SYNTHETIC_RUN flag."
            )
        logger.info("SC-004 check passed: lineage_report.json exists.")
    else:
        if lineage_report_path.exists():
            logger.info("Lineage report exists, but source_type is not synthetic. No flag needed.")
        else:
            logger.info("No lineage report found, and source_type is not synthetic. No action needed for config.")

    # Only write to config.json if source_type is synthetic
    if verification_data.get('source_type') == 'synthetic':
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_data = {"IS_SYNTHETIC_RUN": True}
        config_path.write_text(json.dumps(config_data, indent=2))
        logger.info(f"Updated {config_path} with IS_SYNTHETIC_RUN: true")
    else:
        logger.info("Source type is not synthetic. Not updating config.json with synthetic flag.")

def main():
    args = parse_args()
    project_root = Path(args.project_root)
    research_md_path = project_root / "specs/001-llmxive-follow-up-extending-beyond-scala/research.md"
    config_path = project_root / "data/processed/config.json"

    try:
        # 1. Run verification
        verification_data = run_verification(args.dataset_id, args.threshold, args.algorithm)

        # 2. Update research.md
        update_research_md(research_md_path, verification_data)

        # 3. Update config.json (only if synthetic)
        update_config_json(config_path, verification_data, project_root)

        logger.info("Task T000b completed successfully.")

    except RuntimeError as e:
        logger.error(f"Task T000b failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()