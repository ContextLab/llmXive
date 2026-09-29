import os
import sys
from pathlib import Path

def ensure_project_dirs(project_root: Path) -> None:
    """
    Ensure standard project directories exist.
    Creates them if they don't exist.
    """
    dirs = [
        'state',
        'code',
        'data/raw',
        'data/processed',
        'data/reports',
        'data/logs',
        'tests',
        'specs',
        'config',
        'figures'
    ]
    
    for d in dirs:
        dir_path = project_root / d
        dir_path.mkdir(parents=True, exist_ok=True)

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Looks for a marker file or traverses up from the script location.
    """
    current = Path(__file__).resolve()
    
    # Traverse up to find 'state' directory which is a project marker
    while current != current.parent:
        if (current / 'state').exists():
            return current
        current = current.parent
    
    # Fallback to current working directory
    return Path.cwd()

def main():
    """
    CLI utility to ensure project directories exist.
    """
    import argparse
    parser = argparse.ArgumentParser(description='Ensure project directories exist')
    parser.add_argument('--project-root', type=str, default=None, help='Override project root')
    args = parser.parse_args()
    
    if args.project_root:
        root = Path(args.project_root)
    else:
        root = get_project_root()
        
    ensure_project_dirs(root)
    print(f"Ensured directories for: {root}")

if __name__ == '__main__':
    main()
