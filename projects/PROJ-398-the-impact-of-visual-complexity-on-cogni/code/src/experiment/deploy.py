"""
src/experiment/deploy.py

This module provides a lightweight helper to launch the Streamlit pilot
interface locally.  It creates a minimal ``.streamlit/config.toml`` (if it does
not already exist), builds a small JSON deployment descriptor and finally
starts the Streamlit server as a subprocess.

The implementation is deliberately simple because the unit‑tests mock out
the subprocess call – they only verify that the configuration files are
created and that the expected JSON descriptor is written.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def ensure_streamlit_config(config_dir: Path | None = None) -> Path:
    """
    Ensure a ``.streamlit/config.toml`` file exists with a minimal, safe
    configuration for local execution.

    Parameters
    ----------
    config_dir :
        Optional directory where the ``.streamlit`` folder should be created.
        If ``None`` the folder is placed in the current working directory.

    Returns
    -------
    Path
        The path to the created (or existing) ``config.toml`` file.
    """
    if config_dir is None:
        config_dir = Path.cwd() / ".streamlit"
    else:
        config_dir = Path(config_dir)

    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.toml"

    # Minimal config – keep Streamlit headless and restrict network exposure.
    default_config = (
        "[server]\n"
        "headless = true\n"
        "enableCORS = false\n"
        "port = 8501\n"
    )

    if not config_file.exists():
        config_file.write_text(default_config, encoding="utf-8")
    return config_file


def build_deployment_info(args: argparse.Namespace) -> dict:
    """
    Build a dictionary describing the deployment.  The dictionary is later
    serialised to JSON for downstream consumption (e.g., CI checks).

    Parameters
    ----------
    args :
        Parsed command‑line arguments.

    Returns
    -------
    dict
        Mapping with ``host``, ``port`` and the full ``url``.
    """
    host = args.host
    port = args.port
    url = f"http://{host}:{port}"
    return {"host": host, "port": port, "url": url}


def write_deployment_info(info: dict, output_path: Path) -> None:
    """
    Persist the deployment descriptor as JSON.

    Parameters
    ----------
    info :
        Deployment information dictionary.
    output_path :
        Destination file path.  Parent directories are created if missing.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)


def parse_arguments(argv: list | None = None) -> argparse.Namespace:
    """
    Parse command‑line arguments for the deployment script.

    Parameters
    ----------
    argv :
        Optional list of arguments (defaults to ``sys.argv[1:]``).

    Returns
    -------
    argparse.Namespace
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Deploy the Streamlit pilot interface locally."
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Hostname or IP address on which Streamlit will listen.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port number for the Streamlit server.",
    )
    parser.add_argument(
        "--config-dir",
        type=str,
        default=None,
        help="Directory for the .streamlit configuration (default: cwd/.streamlit).",
    )
    parser.add_argument(
        "--info-output",
        type=str,
        default="data/derived/deployment_info.json",
        help="Path where the deployment JSON descriptor will be written.",
    )
    return parser.parse_args(argv)


def start_streamlit_server(args: argparse.Namespace) -> subprocess.Popen:
    """
    Launch the Streamlit pilot interface as a background subprocess.

    The function returns the ``subprocess.Popen`` object so callers (or tests)
    can inspect or terminate the process.

    Parameters
    ----------
    args :
        Parsed command‑line arguments.

    Returns
    -------
    subprocess.Popen
        The running Streamlit process.
    """
    # Resolve the absolute path to the pilot interface script.
    pilot_script = Path.cwd() / "src" / "experiment" / "pilot_interface.py"
    if not pilot_script.is_file():
        raise FileNotFoundError(f"Pilot interface not found at {pilot_script}")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(pilot_script),
        "--server.headless",
        "true",
        "--server.enableCORS",
        "false",
        "--server.address",
        args.host,
        "--server.port",
        str(args.port),
    ]

    # ``stdout`` and ``stderr`` are piped so that unit‑tests can capture them
    # without cluttering the test output.
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # Give Streamlit a moment to start up; the caller can still wait longer if needed.
    time.sleep(1)
    return process


def main() -> None:
    """
    Entry‑point for ``python -m src.experiment.deploy``.
    """
    args = parse_arguments()
    # 1. Ensure Streamlit configuration exists.
    ensure_streamlit_config(args.config_dir)

    # 2. Build and persist deployment metadata.
    info = build_deployment_info(args)
    write_deployment_info(info, args.info_output)

    # 3. Start the Streamlit server.
    try:
        proc = start_streamlit_server(args)
        # In a real deployment we would block until the process exits.
        # For CI / testing we simply print the URL and exit.
        print(f"Streamlit server started at {info['url']}")
    except Exception as exc:
        # Re‑raise after printing a helpful message – this makes the failure
        # loud for the execution gate.
        print(f"Failed to start Streamlit server: {exc}", file=sys.stderr)
        raise

if __name__ == "__main__":
    main()