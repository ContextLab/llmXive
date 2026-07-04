import subprocess
import sys
import os
from code.utils.logging import pipeline_logger

def check_command(command: str) -> bool:
    """
    Check if a command is available in the system PATH.
    
    Args:
        command: The command name to check (e.g., 'flake8', 'black')
        
    Returns:
        True if the command exists, False otherwise
    """
    try:
        subprocess.run(
            [command, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tool(tool: str) -> bool:
    """
    Install a Python tool using pip.
    
    Args:
        tool: The pip package name to install
        
    Returns:
        True if installation succeeded, False otherwise
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", tool],
            check=True,
            capture_output=True,
            text=True
        )
        pipeline_logger.info(f"Successfully installed {tool}")
        return True
    except subprocess.CalledProcessError as e:
        pipeline_logger.error(f"Failed to install {tool}: {e.stderr}")
        return False

def main():
    """
    Main entry point for linting setup.
    Checks for flake8 and black, installs them if missing,
    and generates configuration files.
    """
    pipeline_logger.info("Starting linting configuration setup...")
    
    # Define required tools
    tools = [
        {"name": "flake8", "package": "flake8"},
        {"name": "black", "package": "black"}
    ]
    
    all_installed = True
    
    for tool in tools:
        tool_name = tool["name"]
        package_name = tool["package"]
        
        if check_command(tool_name):
            pipeline_logger.info(f"{tool_name} is already installed.")
        else:
            pipeline_logger.warning(f"{tool_name} not found. Installing...")
            if install_tool(package_name):
                if check_command(tool_name):
                    pipeline_logger.info(f"{tool_name} installed successfully.")
                else:
                    pipeline_logger.error(f"{tool_name} installation verification failed.")
                    all_installed = False
            else:
                pipeline_logger.error(f"Failed to install {tool_name}.")
                all_installed = False
    
    if not all_installed:
        pipeline_logger.error("Linting setup failed due to missing tools.")
        sys.exit(1)
    
    # Generate configuration files
    config_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(config_dir))
    
    # Create setup.cfg for flake8
    flake8_config_path = os.path.join(project_root, "setup.cfg")
    flake8_config = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    .venv,
    build,
    dist,
    *.egg-info
max-complexity = 10
"""
    
    if not os.path.exists(flake8_config_path):
        with open(flake8_config_path, "w") as f:
            f.write(flake8_config)
        pipeline_logger.info(f"Created flake8 configuration at {flake8_config_path}")
    else:
        pipeline_logger.info(f"Flake8 configuration already exists at {flake8_config_path}")
    
    # Create pyproject.toml for black if it doesn't exist
    pyproject_path = os.path.join(project_root, "pyproject.toml")
    
    black_config = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.venv
  | build
  | dist
  | \\.egg-info
)/
'''
"""
    
    if os.path.exists(pyproject_path):
        # Read existing file and check if black config exists
        with open(pyproject_path, "r") as f:
            content = f.read()
        
        if "[tool.black]" not in content:
            with open(pyproject_path, "a") as f:
                f.write("\n" + black_config)
            pipeline_logger.info(f"Appended black configuration to {pyproject_path}")
        else:
            pipeline_logger.info(f"Black configuration already exists in {pyproject_path}")
    else:
        with open(pyproject_path, "w") as f:
            f.write(black_config)
        pipeline_logger.info(f"Created pyproject.toml with black configuration at {pyproject_path}")
    
    pipeline_logger.info("Linting configuration setup completed successfully.")

if __name__ == "__main__":
    main()