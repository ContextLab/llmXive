import os
import subprocess
import sys
import logging
import tomlkit

logger = logging.getLogger(__name__)

def write_ruff_toml():
    """Write the ruff configuration to pyproject.toml."""
    ruff_config = {
        "tool": {
            "ruff": {
                "line-length": 88,
                "target-version": "py311",
                "select": [
                    "E",  # pycodestyle errors
                    "W",  # pycodestyle warnings
                    "F",  # pyflakes
                    "I",  # isort
                    "C",  # flake8-comprehensions
                    "B",  # flake8-bugbear
                    "UP", # pyupgrade
                ],
                "ignore": [
                    "E501", # line too long (handled by black)
                    "B008", # do not perform function calls in argument defaults
                    "C901", # too complex
                ],
                "exclude": [
                    ".git",
                    "__pycache__",
                    "data",
                    "state",
                    "build",
                    "dist",
                ],
                "per-file-ignores": {
                    "__init__.py": ["F401", "F403"],
                },
            }
        }
    }

    # Check if pyproject.toml exists
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml", "r") as f:
            content = f.read()
        doc = tomlkit.parse(content)
    else:
        doc = tomlkit.document()

    # Merge or set tool.ruff
    if "tool" not in doc:
        doc["tool"] = tomlkit.table()
    doc["tool"]["ruff"] = tomlkit.table()

    # Update specific settings
    ruff_table = doc["tool"]["ruff"]
    for key, value in ruff_config["tool"]["ruff"].items():
        ruff_table[key] = value

    with open("pyproject.toml", "w") as f:
        f.write(tomlkit.dumps(doc))

    logger.info("Ruff configuration written to pyproject.toml")

def write_black_toml():
    """Write the black configuration to pyproject.toml."""
    black_config = {
        "tool": {
            "black": {
                "line-length": 88,
                "target-version": ["py311"],
                "exclude": r"/(\.git|__pycache__|data|state|build|dist)/",
            }
        }
    }

    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml", "r") as f:
            content = f.read()
        doc = tomlkit.parse(content)
    else:
        doc = tomlkit.document()

    if "tool" not in doc:
        doc["tool"] = tomlkit.table()
    if "black" not in doc["tool"]:
        doc["tool"]["black"] = tomlkit.table()

    for key, value in black_config["tool"]["black"].items():
        doc["tool"]["black"][key] = value

    with open("pyproject.toml", "w") as f:
        f.write(tomlkit.dumps(doc))

    logger.info("Black configuration written to pyproject.toml")

def install_tools():
    """Install ruff and black if not present."""
    tools = ["ruff", "black"]
    for tool in tools:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", tool])
            logger.info(f"{tool} installed successfully.")
        except subprocess.CalledProcessError:
            logger.warning(f"Failed to install {tool}. Please install manually.")

def run_lint_check():
    """Run ruff lint check."""
    try:
        result = subprocess.run(
            ["ruff", "check", "code/"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        logger.info("Lint check passed.")
        return True
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)
        logger.error("Lint check failed.")
        return False

def run_format_check():
    """Run black format check."""
    try:
        result = subprocess.run(
            ["black", "--check", "code/"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        logger.info("Format check passed.")
        return True
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)
        logger.error("Format check failed.")
        return False

def run_format_fix():
    """Run black format fix."""
    try:
        result = subprocess.run(
            ["black", "code/"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        logger.info("Format fix applied.")
        return True
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)
        logger.error("Format fix failed.")
        return False

def main():
    """Main entry point for configuring linting and formatting."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    logger.info("Configuring linting and formatting tools...")
    install_tools()
    write_ruff_toml()
    write_black_toml()
    logger.info("Configuration complete.")

    # Optional: Run checks immediately to verify
    logger.info("Running initial lint and format checks...")
    run_lint_check()
    run_format_check()

if __name__ == "__main__":
    main()
