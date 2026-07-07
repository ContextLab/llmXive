import subprocess
import sys
import os
from code.utils.logging import pipeline_logger


def check_command(command: str) -> bool:
    """
    Check if a command is available in the system PATH.
    
    Args:
        command: The command to check (e.g., 'flake8', 'black')
        
    Returns:
        True if the command is available, False otherwise.
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


def install_tool(tool_name: str) -> bool:
    """
    Install a Python tool using pip.
    
    Args:
        tool_name: The name of the tool to install (e.g., 'flake8', 'black')
        
    Returns:
        True if installation was successful, False otherwise.
    """
    try:
        pipeline_logger.info(f"Installing {tool_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", tool_name])
        pipeline_logger.info(f"{tool_name} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        pipeline_logger.error(f"Failed to install {tool_name}: {e}")
        return False


def main():
    """
    Main function to configure linting (flake8/black) and formatting tools.
    
    This function checks if flake8 and black are installed. If not, it installs them.
    It also creates configuration files for these tools if they don't exist.
    """
    tools = ["flake8", "black"]
    
    for tool in tools:
        if not check_command(tool):
            pipeline_logger.warning(f"{tool} not found. Attempting to install...")
            if not install_tool(tool):
                pipeline_logger.error(f"Could not install {tool}. Please install manually.")
                sys.exit(1)
        else:
            pipeline_logger.info(f"{tool} is already installed.")
    
    # Create .flake8 configuration if it doesn't exist
    flake8_config_path = ".flake8"
    if not os.path.exists(flake8_config_path):
        pipeline_logger.info(f"Creating {flake8_config_path}...")
        with open(flake8_config_path, "w") as f:
            f.write("""[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist
ignore = E203, E266, W503
max-complexity = 10
""")
        pipeline_logger.info(f"{flake8_config_path} created.")
    else:
        pipeline_logger.info(f"{flake8_config_path} already exists.")
    
    # Create pyproject.toml for Black configuration if it doesn't exist
    pyproject_path = "pyproject.toml"
    if not os.path.exists(pyproject_path):
        pipeline_logger.info(f"Creating {pyproject_path}...")
        with open(pyproject_path, "w") as f:
            f.write("""[tool.black]
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
""")
        pipeline_logger.info(f"{pyproject_path} created.")
    else:
        pipeline_logger.info(f"{pyproject_path} already exists.")
    
    pipeline_logger.info("Linting and formatting tools configured successfully.")


if __name__ == "__main__":
    main()