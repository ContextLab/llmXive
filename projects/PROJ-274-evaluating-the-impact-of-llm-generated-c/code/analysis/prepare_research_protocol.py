import os
import hashlib
import sys
from pathlib import Path
from utils.setup_paths import ensure_project_dirs

def generate_research_content():
    """
    Reads the research.md file, calculates its SHA256 hash,
    updates the file with the hash in the Sign-off section,
    and writes the hash to state/research_protocol.sha256.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    research_file = project_root / "specs" / "001-evaluating-the-impact-of-llm-generated-c" / "research.md"
    state_dir = project_root / "state"
    hash_file = state_dir / "research_protocol.sha256"

    # Ensure state directory exists
    ensure_project_dirs(state_dir)

    if not research_file.exists():
        raise FileNotFoundError(f"Research protocol file not found: {research_file}")

    # Read current content
    with open(research_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Calculate hash of current content
    current_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

    # Update the content to include the hash in the Sign-off section
    # We look for the placeholder 'Hash: `PENDING_GENERATION`' and replace it
    updated_content = content.replace('Hash: `PENDING_GENERATION`', f'Hash: `{current_hash}`')

    # Write updated content back to the file
    with open(research_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    # Write the hash to the state file
    with open(hash_file, 'w', encoding='utf-8') as f:
        f.write(current_hash)

    print(f"Research protocol updated. Hash: {current_hash}")
    print(f"Hash saved to: {hash_file}")
    return current_hash

def main():
    try:
        generate_research_content()
        sys.exit(0)
    except Exception as e:
        print(f"Error generating research protocol: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
