import argparse
import json
import logging
import os
import sys
import subprocess
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
        description='Populate research.md with dataset verification results.'
    )
    parser.add_argument(
        '--dataset-id',
        type=str,
        default='Z-Reward',
        help='The dataset ID to verify.'
    )
    parser.add_argument(
        '--verify-script',
        type=str,
        default='code/verify_dataset.py',
        help='Path to the verification script.'
    )
    parser.add_argument(
        '--research-md',
        type=str,
        default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-follow-up-extending-beyond-scala/research.md',
        help='Path to the research.md file.'
    )
    return parser.parse_args()

def run_verification(dataset_id, verify_script):
    """Run the verification script and capture JSON output."""
    cmd = [sys.executable, verify_script, '--dataset-id', dataset_id]
    logger.info(f"Running verification: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=300
        )
        
        # The script should output JSON to stdout
        output = result.stdout.strip()
        if not output:
            raise ValueError("Verification script produced no output.")
        
        try:
            verification_data = json.loads(output)
            return verification_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON output: {output}")
            raise e
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Verification script failed with return code {e.returncode}")
        logger.error(f"Stderr: {e.stderr}")
        raise e
    except FileNotFoundError:
        logger.error(f"Verification script not found at {verify_script}")
        raise

def update_research_md(research_path, verification_data):
    """Update research.md with the verification results."""
    path = Path(research_path)
    if not path.exists():
        raise FileNotFoundError(f"Research file not found: {research_path}")

    # Read existing content
    content = path.read_text(encoding='utf-8')
    
    # Determine source type
    source_type = verification_data.get('source_type', 'unknown')
    is_synthetic = source_type == 'synthetic'
    
    # Prepare the entry to add
    # Format: - dataset_id: Z-Reward
    #   title_token_overlap: <float>
    #   checksum: <str>
    #   verification_date: <ISO8601>
    #   source_type: <str>
    
    import datetime
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    entry_lines = [
        f"- dataset_id: {verification_data.get('dataset_id', 'Z-Reward')}",
        f"  title_token_overlap: {verification_data.get('title_token_overlap', 0.0)}",
        f"  checksum: {verification_data.get('checksum', 'N/A')}",
        f"  verification_date: {now_iso}",
        f"  source_type: {source_type}"
    ]
    
    if is_synthetic:
        entry_lines.append("  note: synthetic_fallback")
        # We need to ensure IS_SYNTHETIC_RUN: true is in the file
        # We'll add it near the top or as a global flag if not present
        if "IS_SYNTHETIC_RUN: true" not in content:
            # Insert at the beginning if not found, or after the header
            if content.startswith("---"):
                # Assuming YAML frontmatter or similar, insert after
                lines = content.split('\n')
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.strip() == "---":
                        insert_idx = i + 1
                lines.insert(insert_idx, "IS_SYNTHETIC_RUN: true")
                content = '\n'.join(lines)
            else:
                content = "IS_SYNTHETIC_RUN: true\n\n" + content

    # Find the 'verified_datasets' section and append
    # Simple approach: append to the end of the file if 'verified_datasets' exists
    # Or find the list and append.
    
    lines = content.split('\n')
    new_lines = []
    in_verified_datasets = False
    appended = False
    
    for line in lines:
        new_lines.append(line)
        if line.strip() == "verified_datasets:":
            in_verified_datasets = True
            continue
        
        if in_verified_datasets and not appended:
            # Check if this line is a new list item starting with "- "
            # or if we are at the end of the list (indented less or new section)
            # For safety, we'll just append the new entry after the last existing entry
            # But since we don't know where the list ends, let's just append at the end of the file
            # if we can't find a better spot, but the prompt says "append/ensure"
            # A robust way is to find the last line that starts with "  " inside the list
            pass

    # Simpler strategy: Append the new entry to the end of the file under the section
    # We need to ensure we are inside the list.
    # Let's reconstruct the file to ensure correct YAML structure.
    
    # Find the index of "verified_datasets:"
    start_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == "verified_datasets:":
            start_idx = i
            break
    
    if start_idx == -1:
        raise ValueError("Could not find 'verified_datasets' key in research.md")
    
    # Find the end of the list (next top-level key or end of file)
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            if not line.startswith('#'): # Skip comments
                end_idx = i
                break
    
    # Insert the new entry before end_idx
    # We need to insert the entry lines.
    # The entry should be indented correctly.
    # The list items usually start with "- " at the indentation of the list.
    # The parent key "verified_datasets:" is usually at 0 indent.
    # So list items should be indented by 2 spaces? Or 1 space?
    # Looking at the template: " - dataset_id: string" (2 spaces before dash)
    # Let's assume 2 spaces for the dash.
    
    entry_text = '\n'.join(entry_lines)
    
    # Insert at end_idx
    new_content_lines = lines[:end_idx] + [entry_text] + lines[end_idx:]
    new_content = '\n'.join(new_content_lines)
    
    # Write back
    path.write_text(new_content, encoding='utf-8')
    logger.info(f"Successfully updated {research_path} with verification results.")

def main():
    args = parse_args()
    
    try:
        # 1. Run verification
        verification_data = run_verification(args.dataset_id, args.verify_script)
        
        # 2. Update research.md
        update_research_md(args.research_md, verification_data)
        
        logger.info("Task T000b completed successfully.")
        
    except Exception as e:
        logger.error(f"Task T000b failed: {e}")
        # Re-raise to fail loudly
        raise

if __name__ == '__main__':
    main()