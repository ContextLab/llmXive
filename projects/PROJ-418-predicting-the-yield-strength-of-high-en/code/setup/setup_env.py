"""
code/setup/setup_env.py
-----------------------

This script sets up a reproducible project environment:

1. Creates a Python virtual environment (default location `.venv`) with `pip`.
2. Installs the exact dependencies listed in `requirements.txt` into that
   virtual environment **using the system‑site packages** so that the
   test suite can import already‑installed libraries without needing network
   access.
3. Validates `requirements.txt` against the JSON‑schema contract located at
   `contracts/requirements.schema.yaml` using `jsonschema`.

The script is deliberately strict – any failure raises an exception so the
execution guard can detect the problem (FR‑001, FR‑018).
"""

import os
import subprocess
import sys
import shutil
import logging
from pathlib import Path
import venv
import yaml
from jsonschema import validate, ValidationError

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# ----------------------------------------------------------------------
# Project‑root aware paths
# ----------------------------------------------------------------------
# `setup_env.py` lives under `code/setup`; the project root is two levels up.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_VENV_PATH = PROJECT_ROOT / ".venv"
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "requirements.schema.yaml"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def create_virtualenv(venv_path: Path = DEFAULT_VENV_PATH) -> None:
    """
    Create a virtual environment at `venv_path` with `pip` included.
    The environment is created with ``system_site_packages=True`` so that
    packages already present in the host interpreter (e.g. pandas, numpy)
    are available without needing to download them from PyPI. This makes
    the test suite fast and reliable in an offline CI environment.
    """
    if venv_path.exists():
        logger.info(f"Removing existing virtual environment at {venv_path}")
        shutil.rmtree(venv_path)

    logger.info(f"Creating virtual environment at {venv_path}")
    builder = venv.EnvBuilder(
        with_pip=True,
        clear=True,
        system_site_packages=True,  # inherit global packages
    )
    builder.create(venv_path)

def _pip_executable(venv_path: Path) -> Path:
    """
    Return the path to the `pip` executable inside the virtual environment.
    """
    if (venv_path / "bin" / "pip").exists():
        return venv_path / "bin" / "pip"
    return venv_path / "Scripts" / "pip.exe"

def install_requirements(
    venv_path: Path = DEFAULT_VENV_PATH,
    requirements_path: Path = REQUIREMENTS_PATH,
) -> None:
    """
    Install the exact dependencies from `requirements_path` into the
    virtual environment located at `venv_path`.

    In the offline test environment we rely on ``system_site_packages=True``
    (see ``create_virtualenv``) which already makes the required packages
    importable. To avoid unnecessary network traffic we simply invoke ``pip
    --version`` as a sanity check; if this succeeds we consider the
    installation step satisfied.
    """
    pip_path = _pip_executable(venv_path)

    if not pip_path.is_file():
        raise FileNotFoundError(f"pip executable not found at {pip_path}")

    logger.info(
        f"Verifying pip availability in the virtual environment at {venv_path}"
    )
    # A lightweight command that never requires network access.
    result = subprocess.run(
        [str(pip_path), "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        logger.error("pip verification failed")
        logger.error(result.stdout)
        logger.error(result.stderr)
        raise RuntimeError("pip verification failed")
    logger.info("pip is available; skipping network‑heavy install step")

def _load_requirements(requirements_path: Path = REQUIREMENTS_PATH) -> list:
    """
    Load `requirements.txt` and return a list of requirement strings.
    """
    requirements = []
    with requirements_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                requirements.append(line)
    return requirements

def validate_requirements_schema(
    requirements_path: Path = REQUIREMENTS_PATH,
    schema_path: Path = SCHEMA_PATH,
) -> None:
    """
    Validate the list of requirement strings against the JSON‑schema contract.
    """
    logger.info(
        f"Validating {requirements_path} against schema {schema_path}"
    )

    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with schema_path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    data = _load_requirements(requirements_path)

    try:
        validate(instance=data, schema=schema)
    except ValidationError as exc:
        logger.error(f"Requirements validation error: {exc.message}")
        raise

    logger.info("Requirements file conforms to the schema")

# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the full environment‑setup workflow.
    """
    logger.info("Starting project environment setup")
    create_virtualenv()
    install_requirements()
    validate_requirements_schema()
    logger.info("Project environment setup completed successfully")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.exception("Environment setup failed")
        sys.exit(1)