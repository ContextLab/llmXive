"""
src/experiment/deploy.py
-------------------------

Deployment helper for the Streamlit pilot interface.

This script prepares a minimal Streamlit configuration suitable for
deployment on Streamlit Cloud (or any other Streamlit‑compatible hosting
service) and writes a small JSON file containing the public URL that can
be shared with participants for recruitment.

The script **does not** push code to Streamlit Cloud – that step is
performed manually by linking the repository in the Streamlit Cloud UI.
What it does is:

1. Ensure a ``.streamlit/config.toml`` exists inside the Streamlit app
   directory (by default ``src/experiment``) with sensible defaults.
2. Validate that a public URL (``--base-url``) has been supplied.
3. Write ``data/derived/deployment_info.json`` containing the URL and a
   timestamp.
4. Optionally generate a short invitation text that can be copied into
   recruitment emails.

The script can be invoked directly:

.. code-block:: console

    python code/src/experiment/deploy.py \\
        --app-dir src/experiment \\
        --base-url https://my-pilot-app.streamlit.app \\
        --output data/derived/deployment_info.json

The output JSON looks like::

    {
        "deployment_url": "https://my-pilot-app.streamlit.app",
        "recruitment_link": "https://my-pilot-app.streamlit.app",
        "generated_at": "2026-09-24T12:34:56Z"
    }

The ``recruitment_link`` field can be distributed to participants.
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def ensure_streamlit_config(app_dir: Path) -> None:
    """
    Ensure ``.streamlit/config.toml`` exists inside ``app_dir`` with a
    minimal configuration suitable for head‑less deployment.

    Parameters
    ----------
    app_dir: Path
        Directory that contains the Streamlit entry‑point (e.g.
        ``src/experiment``).
    """
    config_dir = app_dir / ".streamlit"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = config_dir / "config.toml"
    if config_path.is_file():
        # Preserve an existing file – we assume the user knows what they
        # are doing.
        return

    # Minimal configuration: run head‑less and disable the "Run on save"
    # warning that can appear in CI environments.
    config_contents = """[server]
headless = true
enableCORS = false
port = $PORT
"""
    config_path.write_text(config_contents, encoding="utf-8")


def build_deployment_info(base_url: str) -> Dict[str, str]:
    """
    Build the JSON payload that records deployment information.

    Parameters
    ----------
    base_url: str
        The public URL where the Streamlit app is reachable.

    Returns
    -------
    dict
        Mapping with ``deployment_url``, ``recruitment_link`` and a UTC
        timestamp.
    """
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "deployment_url": base_url.rstrip("/"),
        "recruitment_link": base_url.rstrip("/"),
        "generated_at": now_iso,
    }


def write_deployment_info(info: Dict[str, str], output_path: Path) -> None:
    """
    Write the deployment information to ``output_path`` as pretty‑printed
    JSON.  The parent directory is created if it does not exist.

    Parameters
    ----------
    info: dict
        Deployment information dictionary.
    output_path: Path
        Destination file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, sort_keys=True)


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare Streamlit deployment configuration and generate a "
            "recruitment link for the pilot study."
        )
    )
    parser.add_argument(
        "--app-dir",
        type=Path,
        default=Path("src/experiment"),
        help="Directory containing the Streamlit app (default: src/experiment).",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        required=True,
        help=(
            "Public URL of the deployed Streamlit app (e.g. "
            "https://my-app.streamlit.app)."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/derived/deployment_info.json"),
        help=(
            "Path where deployment information JSON will be written "
            "(default: data/derived/deployment_info.json)."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    # 1️⃣ Ensure Streamlit config exists.
    ensure_streamlit_config(args.app_dir)

    # 2️⃣ Build the deployment info payload.
    deployment_info = build_deployment_info(args.base_url)

    # 3️⃣ Persist the JSON artifact.
    write_deployment_info(deployment_info, args.output)

    # 4️⃣ Print a friendly message for the user.
    print(f"✅ Streamlit config written to {args.app_dir / '.streamlit' / 'config.toml'}")
    print(f"✅ Deployment info written to {args.output}")
    print("\n--- Recruitment link ---")
    print(deployment_info["recruitment_link"])
    print("\nDistribute the above link to participants.")


if __name__ == "__main__":
    main()