"""
Setup script to configure linting (flake8, pylint) and formatting (black) tools.
Creates necessary configuration files in the project root.
"""
import subprocess
import sys
from pathlib import Path

def check_black():
    """Check if Black is installed."""
    try:
        subprocess.run(["black", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_flake8():
    """Check if Flake8 is installed."""
    try:
        subprocess.run(["flake8", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_pylint():
    """Check if Pylint is installed."""
    try:
        subprocess.run(["pylint", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    """Main entry point for linting setup."""
    project_root = Path(__file__).parent.parent
    print(f"Configuring linting and formatting tools for project at: {project_root}")

    # Check for required tools
    tools = {
        "black": check_black,
        "flake8": check_flake8,
        "pylint": check_pylint,
    }

    missing_tools = []
    for tool_name, check_func in tools.items():
        if not check_func():
            missing_tools.append(tool_name)

    if missing_tools:
        print(f"Missing tools: {', '.join(missing_tools)}")
        print("Installing missing tools...")
        install_cmd = [sys.executable, "-m", "pip", "install"] + missing_tools
        subprocess.run(install_cmd, check=True)
        print("Tools installed successfully.")

    # Create configuration files
    setup_black(project_root)
    setup_flake8(project_root)
    setup_pylint(project_root)

    print("Linting and formatting configuration complete.")

def setup_black(project_root: Path):
    """Create Black configuration file."""
    pyproject_path = project_root / "pyproject.toml"
    
    black_config = """[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
"""
    
    if not pyproject_path.exists():
        # Create pyproject.toml with Black config
        with open(pyproject_path, "w") as f:
            f.write(black_config)
        print(f"Created {pyproject_path} with Black configuration")
    else:
        # Check if Black config already exists
        with open(pyproject_path, "r") as f:
            content = f.read()
            if "[tool.black]" not in content:
                with open(pyproject_path, "a") as f:
                    f.write("\n" + black_config)
                print(f"Added Black configuration to {pyproject_path}")
            else:
                print(f"Black configuration already exists in {pyproject_path}")

def setup_flake8(project_root: Path):
    """Create Flake8 configuration file."""
    setup_cfg_path = project_root / "setup.cfg"
    
    flake8_config = """[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist
ignore = E203, E266, E501, W503
max-complexity = 10
select = B,C,E,F,W,T4,B9
"""
    
    if not setup_cfg_path.exists():
        with open(setup_cfg_path, "w") as f:
            f.write(flake8_config)
        print(f"Created {setup_cfg_path} with Flake8 configuration")
    else:
        with open(setup_cfg_path, "r") as f:
            content = f.read()
            if "[flake8]" not in content:
                with open(setup_cfg_path, "a") as f:
                    f.write("\n" + flake8_config)
                print(f"Added Flake8 configuration to {setup_cfg_path}")
            else:
                print(f"Flake8 configuration already exists in {setup_cfg_path}")

def setup_pylint(project_root: Path):
    """Create Pylint configuration file."""
    pylintrc_path = project_root / "pylintrc"
    
    if not pylintrc_path.exists():
        # Generate default pylint config and then modify it
        subprocess.run([sys.executable, "-m", "pylint", "--generate-rcfile"], 
                     stdout=open(pylintrc_path, "w"), check=False)
        
        # Modify the generated config to match our needs
        with open(pylintrc_path, "r") as f:
            content = f.read()
        
        # Update max-line-length
        content = content.replace("max-line-length = 100", "max-line-length = 88")
        
        # Disable specific checks that conflict with Black
        disable_checks = [
            "C0301", # line-too-long (handled by Black)
            "C0326", # bad-whitespace (handled by Black)
            "C0330", # bad-continuation (handled by Black)
            "E1136", # unsubscriptable-object (common false positive)
        ]
        
        for check in disable_checks:
            content = content.replace(f"disable =\n    {check},", f"disable =\n    {check},")
            if f"    {check}," not in content:
                # Add to disable list
                content = content.replace("disable =", f"disable =\n    {check},")
        
        with open(pylintrc_path, "w") as f:
            f.write(content)
        
        print(f"Created {pylintrc_path} with Pylint configuration")
    else:
        print(f"Pylint configuration already exists at {pylintrc_path}")

if __name__ == "__main__":
    main()