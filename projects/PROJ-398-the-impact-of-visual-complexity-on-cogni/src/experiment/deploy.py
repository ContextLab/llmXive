"""
src/experiment/deploy.py
-------------------------

This module provides a tiny helper for launching the Streamlit pilot
interface locally and persisting a small JSON file that contains the
access URL.  The implementation is deliberately lightweight – it does
**not** start a production‑grade server, but it is sufficient for the
unit‑tests that mock out the subprocess call and verify that the
deployment information is written correctly.

Public API
----------
* ``ensure_streamlit_config`` – make sure a ``.streamlit`` directory
  with a minimal ``config.toml`` exists.
* ``build_deployment_info`` – create a dictionary containing the
  local URL based on the chosen port.
* ``write_deployment_info`` – dump the deployment dictionary as JSON
  to a user‑specified path.
* ``parse_arguments`` – command‑line argument parser.
* ``start_streamlit_server`` – launch ``streamlit run`` as a subprocess.
* ``main`` – orchestrates the whole flow.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict

__all__ = [
    "ensure_streamlit_config",
    "build_deployment_info",
    "write_deployment_info",
    "parse_arguments",
    "start_streamlit_server",
    "main",
]


def ensure_streamlit_config(project_root: Path = Path.cwd()) -> Path:
    """
    Ensure a ``.streamlit/config.toml`` file exists.

    The configuration forces Streamlit into headless mode so that it can be
    started from a non‑interactive environment (e.g. CI or the test suite).

    Parameters
    ----------
    project_root: Path
        Root directory of the project (defaults to the current working
        directory).

    Returns
    ----------
    Path
        Path to the written ``config.toml`` file.
    """
    config_dir = project_root / ".streamlit"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = config_dir / "config.toml"
    if not config_path.is_file():
        # Minimal configuration – headless mode is sufficient for the tests.
        config_content = "[server]\nheadless = true\n"
        config_path.write_text(config_content, encoding="utf-8")
    return config_path


def build_deployment_info(port: int) -> Dict[str, str]:
    """
    Construct a dictionary containing the URL where the Streamlit app can be reached.

    Parameters
    ----------
    port: int
        Port on which the Streamlit server will listen.

    Returns
    ----------
    dict
        ``{\"url\": \"http://localhost:<port>\"}``
    """
    return {"url": f"http://localhost:{port}"}


def write_deployment_info(info: Dict[str, str], output_path: Path) -> None:
    """
    Write the deployment information to a JSON file.

    Parameters
    ----------
    info: dict
        Deployment dictionary (as returned by :func:`build_deployment_info`).
    output_path: Path
        Destination file.  Parent directories are created automatically.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(info, indent=2), encoding="utf-8")


def parse_arguments(argv: list | None = None) -> argparse.Namespace:
    """
    Parse command‑line arguments for the deployment script.

    Supported arguments
    -------------------
    ``--port`` (int, default: 8501)
        Port for the Streamlit server.

    ``--output`` (path, default: ``deployment_info.json``)
        File where the deployment URL will be stored.
    """
    parser = argparse.ArgumentParser(
        description="Deploy the Streamlit pilot interface locally."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port on which to run the Streamlit server (default: 8501).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("deployment_info.json"),
        help="Path to write deployment information JSON (default: deployment_info.json).",
    )
    return parser.parse_args(argv)


def start_streamlit_server(port: int) -> subprocess.Popen:
    """
    Launch the Streamlit pilot interface as a subprocess.

    The function starts ``streamlit run src/experiment/pilot_interface.py`` with
    the requested port and forces headless mode.  The returned ``Popen`` object
    can be used by callers to terminate the process if needed.

    Parameters
    ----------
    port: int
        Port on which to start the server.

    Returns
    -------
    subprocess.Popen
        The subprocess handling the Streamlit server.
    """
    command = [
        "streamlit",
        "run",
        "src/experiment/pilot_interface.py",
        "--server.port",
        str(port),
        "--server.headless",
        "true",
    ]
    # ``stdout`` and ``stderr`` are piped so that the test suite can mock them.
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Give the server a moment to start – the real app may need a few seconds.
    # In the test environment this pause is negligible because the subprocess is mocked.
    time.sleep(1)
    return process


def main(argv: list | None = None) -> int:
    """
    Entry‑point for the deployment script.

    The steps are:
    1. Parse command‑line arguments.
    2. Ensure a minimal Streamlit configuration exists.
    3. Start the Streamlit server.
    4. Write a JSON file containing the local access URL.
    5. Print the URL to ``stdout`` for user convenience.

    Returns
    -------
    int
        Exit status (0 for success, non‑zero for failure).
    """
    args = parse_arguments(argv)

    # 1. Prepare Streamlit configuration.
    ensure_streamlit_config()

    # 2. Start the server.
    try:
        process = start_streamlit_server(args.port)
    except FileNotFoundError as exc:
        # ``streamlit`` executable not found – propagate a clear error.
        sys.stderr.write(f"Error launching Streamlit: {exc}\\n")
        return 1

    # 3. Build and persist deployment information.
    info = build_deployment_info(args.port)
    write_deployment_info(info, args.output)

    # 4. Inform the user.
    print(f"Streamlit app deployed at {info['url']}")

    # The process is left running; the caller (or the test harness) can decide
    # when to terminate it.  Returning ``0`` signals successful deployment.
    return 0


if __name__ == "__main__":
    sys.exit(main())