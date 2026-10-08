"""
Script to configure linting (ruff) and formatting (black) tools.
Creates ruff.toml and updates pyproject.toml with black configuration.
"""
import subprocess
import sys
import os
from pathlib import Path

def ensure_package_installed(package_name: str, import_name: str = None) -> None:
    """Ensure a package is installed, install it if not."""
    if import_name is None:
        import_name = package_name
    try:
        __import__(import_name)
    except ImportError:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

def create_ruff_config() -> None:
    """Create ruff.toml with the exact required configuration."""
    config_content = """line-length = 88
target-version = "py39"
select = ["E", "F", "W", "I"]
"""
    ruff_path = Path("ruff.toml")
    if ruff_path.exists():
        print(f"ruff.toml already exists at {ruff_path.absolute()}")
        # Verify content matches expected
        current_content = ruff_path.read_text()
        if current_content.strip() == config_content.strip():
            print("ruff.toml content matches expected configuration.")
            return
        else:
            print("ruff.toml exists but content differs. Overwriting.")
    ruff_path.write_text(config_content)
    print(f"Created ruff.toml at {ruff_path.absolute()}")

def create_pyproject_config() -> None:
    """Create or update pyproject.toml with [tool.black] section."""
    pyproject_path = Path("pyproject.toml")
    black_section = """
[tool.black]
line-length = 88
target-version = ['py39']
"""
    
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" in content:
            print("pyproject.toml already contains [tool.black] section.")
            # Check if line-length is correct
            if "line-length = 88" in content:
                print("Black configuration is correct.")
                return
            else:
                print("Updating black configuration in pyproject.toml...")
                # Simple replacement for line-length
                lines = content.splitlines()
                new_lines = []
                in_black = False
                for line in lines:
                    if "[tool.black]" in line:
                        in_black = True
                        new_lines.append(line)
                    elif in_black and "line-length" in line:
                        new_lines.append("line-length = 88")
                    elif in_black and "target-version" in line:
                        new_lines.append("target-version = ['py39']")
                    elif in_black and line.strip().startswith('['):
                        in_black = False
                        new_lines.append(line)
                    else:
                        new_lines.append(line)
                content = "\n".join(new_lines)
        else:
            print("Appending [tool.black] section to pyproject.toml...")
            content = content.rstrip() + black_section
    else:
        print("Creating new pyproject.toml with [tool.black] section...")
        content = f"""[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "statistical-properties-black-hole-mergers"
version = "0.1.0"
description = "Investigating the statistical properties of simulated black hole mergers"
requires-python = ">=3.9"
dependencies = [
    "numpy",
    "scipy",
    "pandas",
    "matplotlib",
    "requests",
    "tqdm",
    "pytest",
    "h5py",
    "statsmodels",
    "memory-profiler",
]
{black_section.strip()}
"""
    
    pyproject_path.write_text(content)
    print(f"Updated pyproject.toml at {pyproject_path.absolute()}")

def main() -> None:
    """Main entry point for configuring linting and formatting tools."""
    print("Configuring linting (ruff) and formatting (black) tools...")
    
    # Ensure ruff is installed
    ensure_package_installed("ruff", "ruff")
    
    # Create configuration files
    create_ruff_config()
    create_pyproject_config()
    
    print("Configuration complete.")
    print("Verification commands:")
    print("  test -f ruff.toml && test -f pyproject.toml")
    print("  grep -q 'line-length = 88' ruff.toml && grep -q 'line-length = 88' pyproject.toml")

if __name__ == "__main__":
    main()
