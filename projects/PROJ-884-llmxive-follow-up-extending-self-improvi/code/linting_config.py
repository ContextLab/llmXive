"""
Linting and formatting configuration management for the llmXive project.

This module provides utilities to create and manage configuration files
for Black and Flake8, ensuring consistent code style across the project.
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional


def create_black_config_file(config_path: Optional[Path] = None) -> Path:
    """
    Create a pyproject.toml file with Black configuration if it doesn't exist
    or update it if it does.
    
    Args:
        config_path: Optional path to the config file. Defaults to project root.
        
    Returns:
        Path to the created/updated configuration file.
    """
    if config_path is None:
        config_path = Path.cwd() / "pyproject.toml"
        
    black_config = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 88
"""
    
    # Check if file exists
    if config_path.exists():
        content = config_path.read_text()
        if "[tool.black]" in content:
            # Update existing config
            lines = content.split('\n')
            in_black_section = False
            new_lines = []
            skip_until_next_section = False
            
            for i, line in enumerate(lines):
                if line.strip().startswith('[tool.black]'):
                    in_black_section = True
                    new_lines.append(line)
                    continue
                elif in_black_section and line.strip().startswith('['):
                    in_black_section = False
                    skip_until_next_section = False
                    new_lines.append(line)
                elif in_black_section:
                    # Skip existing black config lines
                    continue
                else:
                    new_lines.append(line)
            
            # Insert black config before isort if it exists, or at end
            insert_pos = len(new_lines)
            for i, line in enumerate(new_lines):
                if line.strip().startswith('[tool.isort]'):
                    insert_pos = i
                    break
            
            final_content = '\n'.join(new_lines[:insert_pos]) + '\n' + black_config + '\n'.join(new_lines[insert_pos:])
            config_path.write_text(final_content)
        else:
            # Append to existing file
            config_path.write_text(content + '\n' + black_config)
    else:
        # Create new file
        config_path.write_text(black_config)
        
    return config_path


def create_flake8_config_file(config_path: Optional[Path] = None) -> Path:
    """
    Create a .flake8 file with Flake8 configuration.
    
    Args:
        config_path: Optional path to the config file. Defaults to project root.
        
    Returns:
        Path to the created configuration file.
    """
    if config_path is None:
        config_path = Path.cwd() / ".flake8"
        
    flake8_config = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info,
    .venv,
    venv
per-file-ignores =
    __init__.py: F401
"""
    
    config_path.write_text(flake8_config)
    return config_path


def run_black_check(path: Optional[Path] = None, check_only: bool = True) -> Tuple[bool, str]:
    """
    Run Black on the specified path.
    
    Args:
        path: Path to check. Defaults to current directory.
        check_only: If True, only check formatting (don't modify files).
        
    Returns:
        Tuple of (success, message)
    """
    if path is None:
        path = Path.cwd()
        
    cmd = [sys.executable, "-m", "black"]
    if check_only:
        cmd.append("--check")
    cmd.append("--diff")
    cmd.append(str(path))
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return True, "All files are formatted correctly."
        else:
            return False, f"Black formatting issues found:\n{result.stdout}\n{result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "Black check timed out."
    except FileNotFoundError:
        return False, "Black is not installed. Run: pip install black"
    except Exception as e:
        return False, f"Error running Black: {str(e)}"


def run_flake8_check(path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Run Flake8 on the specified path.
    
    Args:
        path: Path to check. Defaults to current directory.
        
    Returns:
        Tuple of (success, message)
    """
    if path is None:
        path = Path.cwd()
        
    cmd = [sys.executable, "-m", "flake8", str(path)]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return True, "All files pass Flake8 checks."
        else:
            return False, f"Flake8 issues found:\n{result.stdout}\n{result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "Flake8 check timed out."
    except FileNotFoundError:
        return False, "Flake8 is not installed. Run: pip install flake8"
    except Exception as e:
        return False, f"Error running Flake8: {str(e)}"


def setup_linting(project_root: Optional[Path] = None) -> Tuple[Path, Path]:
    """
    Set up linting configuration files for the project.
    
    Args:
        project_root: Optional path to project root. Defaults to current directory.
        
    Returns:
        Tuple of (black_config_path, flake8_config_path)
    """
    if project_root is None:
        project_root = Path.cwd()
        
    os.chdir(project_root)
    
    black_config = create_black_config_file()
    flake8_config = create_flake8_config_file()
    
    return black_config, flake8_config


def main():
    """Main entry point for linting configuration setup and checks."""
    print("Setting up linting configuration...")
    
    black_config, flake8_config = setup_linting()
    print(f"Created Black config: {black_config}")
    print(f"Created Flake8 config: {flake8_config}")
    
    print("\nRunning Black check...")
    success, message = run_black_check()
    print(message)
    
    print("\nRunning Flake8 check...")
    success, message = run_flake8_check()
    print(message)
    
    if success:
        print("\n✓ All linting checks passed!")
    else:
        print("\n✗ Some linting checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()