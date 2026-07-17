import os
import sys
from pathlib import Path

def main():
    """
    Create the directory: specs/001-llmxive-followup/contracts/
    This task corresponds to T001f in the project tasks.md.
    """
    base_path = Path.cwd()
    target_dir = base_path / "specs" / "001-llmxive-followup" / "contracts"

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"Successfully created directory: {target_dir}")
        
        # Create a .gitkeep file to ensure the directory is tracked by git
        # even if it is initially empty.
        gitkeep = target_dir / ".gitkeep"
        gitkeep.write_text("# Contracts directory for llmXive follow-up project\n")
        print(f"Created placeholder file: {gitkeep}")
        
        return 0
    except PermissionError:
        print(f"Error: Permission denied creating directory {target_dir}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error creating directory {target_dir}: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())