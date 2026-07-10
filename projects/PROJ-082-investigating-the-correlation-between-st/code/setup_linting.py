import subprocess
import sys
from pathlib import Path
import json

def install_tools():
    """Install linting and formatting tools."""
    tools = ['ruff', 'black']
    for tool in tools:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', tool])
            print(f"Installed {tool}")
        except subprocess.CalledProcessError:
            print(f"Failed to install {tool}")

def ensure_config_file():
    """Ensure configuration files for linting exist."""
    project_root = Path(__file__).resolve().parent.parent
    
    ruff_config = project_root / ".ruff.toml"
    black_config = project_root / ".black.toml"
    
    if not ruff_config.exists():
        with open(ruff_config, 'w') as f:
            f.write('[lint]\nselect = ["E", "F", "W"]\n')
        print(f"Created {ruff_config}")
    
    if not black_config.exists():
        with open(black_config, 'w') as f:
            f.write('[tool.black]\nline-length = 88\n')
        print(f"Created {black_config}")

def main():
    install_tools()
    ensure_config_file()
    print("Linting and formatting setup complete.")

if __name__ == "__main__":
    main()