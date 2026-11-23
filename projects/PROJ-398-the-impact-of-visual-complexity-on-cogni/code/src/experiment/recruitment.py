"""
Recruitment State Manager
==========================

This module provides utilities to manage participant IDs for the pilot study
and to generate static invitation templates that can be sent to participants.

The state is persisted in a JSON file under the ``state/`` directory at the
repository root.  The JSON structure is simple:

.. code-block:: json
    
    {
        "participants": [
            "participant_001",
            "participant_002",
            ...
        ]
    }

The module can be used programmatically or via a tiny CLI.
"""

import argparse
import json
import uuid
from pathlib import Path
from typing import Dict, List

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# Path to the JSON file that stores the recruitment state.
# The directory ``state`` is created on demand.
STATE_FILE: Path = Path("state") / "recruitment_state.json"

# Directory where invitation files are written.
DEFAULT_INVITATION_DIR: Path = Path("data") / "processed" / "invitations"

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def ensure_state_dir() -> None:
    """Make sure the parent directory for ``STATE_FILE`` exists."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_state() -> Dict[str, List[str]]:
    """
    Load the recruitment state from ``STATE_FILE``.

    Returns
    -------
    dict
        A dictionary with a single key ``\"participants\"`` mapping to a list of
        participant IDs.  If the file does not exist, an empty state is returned.
    """
    ensure_state_dir()
    if not STATE_FILE.is_file():
        return {"participants": []}
    with STATE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state: Dict[str, List[str]]) -> None:
    """Persist ``state`` to ``STATE_FILE``."""
    ensure_state_dir()
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)

# --------------------------------------------------------------------------- #
# Core public API
# --------------------------------------------------------------------------- #

def register_participant() -> str:
    """
    Generate a new unique participant identifier, store it in the state file,
    and return the identifier.

    The identifier is a UUID4 string prefixed with ``\"participant_\"`` to keep it
    human‑readable.

    Returns
    -------
    str
        The newly created participant identifier.
    """
    state = load_state()
    new_id = f"participant_{uuid.uuid4().hex[:8]}"  # short but unique
    state["participants"].append(new_id)
    save_state(state)
    return new_id

def generate_invitation_template(
    participant_id: str,
    output_dir: Path = DEFAULT_INVITATION_DIR,
    invitation_template: str | None = None,
) -> Path:
    """
    Create a static invitation file for ``participant_id``.

    Parameters
    ----------
    participant_id: str
        The identifier of the participant for whom the invitation is generated.
    output_dir: pathlib.Path, optional
        Directory where the invitation file will be written.  Defaults to
        ``data/processed/invitations``.
    invitation_template: str, optional
        A custom template string.  If omitted, a built‑in simple template is used.
        The template may contain ``{participant_id}`` which will be replaced.

    Returns
    -------
    pathlib.Path
        Path to the written invitation file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    if invitation_template is None:
        invitation_template = (
            "Dear Participant,\n\n"
            "You are invited to take part in our visual complexity pilot study.\n"
            "Please visit the following URL to begin:\n\n"
            "https://example.com/pilot?pid={participant_id}\n\n"
            "Thank you for your contribution!\n"
        )
    content = invitation_template.format(participant_id=participant_id)
    invitation_path = output_dir / f"{participant_id}_invitation.txt"
    invitation_path.write_text(content, encoding="utf-8")
    return invitation_path

# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recruitment State Manager – generate participant IDs and invitation files."
    )
    parser.add_argument(
        "--new",
        action="store_true",
        help="Create a new participant ID and write an invitation file.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all registered participant IDs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_INVITATION_DIR,
        help="Directory where invitation files are written (default: %(default)s).",
    )
    return parser.parse_args()


def main() -> None:
    """Command‑line interface for the recruitment manager."""
    args = _parse_args()

    if args.list:
        state = load_state()
        for pid in state.get("participants", []):
            print(pid)
        return

    if args.new:
        pid = register_participant()
        invitation_path = generate_invitation_template(pid, args.output_dir)
        print(f"Created participant ID: {pid}")
        print(f"Invitation written to: {invitation_path}")
        return

    # If no flags were provided, show help.
    _parse_args().print_help()


if __name__ == "__main__":
    main()