import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

# Existing imports from the original main module (omitted for brevity)
# from main import apply_atp_iii_criteria, get_varied_thresholds, run_sensitivity_analysis, main
# NOTE: The original main.py content is retained; this file adds the new utility function.

# -------------------------------------------------------------------------
# New utility: write_results_to_csv
# -------------------------------------------------------------------------
from utils.config import get_project_paths

def write_results_to_csv(results: Dict[str, Any]) -> None:
    """
    Write provided result objects to files under the ``data/processed`` directory.

    Parameters
    ----------
    results : dict
        Mapping where the key is a base filename (without extension) and the
        value is either a ``pandas.DataFrame`` (saved as ``.csv``) or a JSON‑
        serialisable object (saved as ``.json``).

    This helper creates the target directory if it does not exist and logs
    each write operation. Non‑serialisable objects are skipped with a warning.
    """
    # Resolve the processed data directory using the central config utility.
    project_paths = get_project_paths()
    processed_dir = Path(project_paths.get("data_processed", "data/processed"))
    processed_dir.mkdir(parents=True, exist_ok=True)

    for name, obj in results.items():
        # Normalise the filename – strip any existing suffix to avoid duplication.
        base_name = Path(name).stem

        if isinstance(obj, pd.DataFrame):
            out_path = processed_dir / f"{base_name}.csv"
            obj.to_csv(out_path, index=False)
            logging.info(f"Wrote DataFrame '{base_name}' to CSV at {out_path}")
        else:
            # Attempt JSON serialisation for generic Python objects.
            try:
                json_str = json.dumps(obj, indent=2)
            except (TypeError, ValueError) as exc:
                logging.warning(
                    f"Result '{base_name}' is not JSON‑serialisable and will be skipped: {exc}"
                )
                continue

            out_path = processed_dir / f"{base_name}.json"
            with out_path.open("w", encoding="utf-8") as f:
                f.write(json_str)
            logging.info(f"Wrote JSON serialisable result '{base_name}' to {out_path}")

    logging.debug("All provided results have been written to the processed data directory.")

# -------------------------------------------------------------------------
# New utility: compute_content_hashes
# -------------------------------------------------------------------------
from utils.hashing import compute_directory_hashes

def compute_content_hashes() -> Dict[str, str]:
    """
    Compute SHA‑256 hashes for all files under the ``data/processed`` directory.

    Returns
    -------
    dict
        Mapping of relative file paths (relative to ``data/processed``) to their
        hexadecimal SHA‑256 hash strings.

    Side‑effects
    ------------
    Writes a ``content_hashes.json`` file in the ``data/processed`` directory
    containing the same mapping for downstream reproducibility checks.
    """
    # Resolve the processed data directory using the central config utility.
    project_paths = get_project_paths()
    processed_dir = Path(project_paths.get("data_processed", "data/processed"))

    if not processed_dir.is_dir():
        logging.error(f"Processed data directory does not exist: {processed_dir}")
        raise FileNotFoundError(f"Processed data directory not found: {processed_dir}")

    # Compute hashes for every file (recursively) in the directory.
    # ``compute_directory_hashes`` is expected to return a dict where keys are
    # absolute Path objects (or strings) and values are hash strings.
    absolute_hashes = compute_directory_hashes(processed_dir)

    # Convert absolute paths to paths relative to the processed directory for
    # a cleaner, portable representation.
    relative_hashes: Dict[str, str] = {}
    for file_path, hash_val in absolute_hashes.items():
        # Ensure we are working with Path objects.
        path_obj = Path(file_path) if not isinstance(file_path, Path) else file_path
        try:
            rel_path = str(path_obj.relative_to(processed_dir))
        except ValueError:
            # In the unlikely event the path is not under the processed_dir,
            # fall back to the original string.
            rel_path = str(path_obj)
        relative_hashes[rel_path] = hash_val

    # Persist the hashes to a JSON file for later inspection / state updates.
    output_path = processed_dir / "content_hashes.json"
    try:
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(relative_hashes, f, indent=2)
        logging.info(f"Content hashes written to {output_path}")
    except Exception as exc:
        logging.error(f"Failed to write content hashes to {output_path}: {exc}")
        raise

    return relative_hashes

# -------------------------------------------------------------------------
# New utility: update_state_hash
# -------------------------------------------------------------------------
from utils.hashing import load_state_file, save_state_file

def update_state_hash() -> None:
    """
    Compute content hashes for the processed data directory and store them in the
    project's state YAML file under ``state/projects/PROJ-110-...yaml``.
    """
    # Step 1 – compute the current content hashes.
    hashes = compute_content_hashes()

    # Step 2 – locate the appropriate state file.
    # The convention is ``state/projects/PROJ-110-*.yaml``.
    state_dir = Path("state/projects")
    if not state_dir.is_dir():
        logging.error(f"State directory does not exist: {state_dir}")
        raise FileNotFoundError(f"State directory not found: {state_dir}")

    # Find the first YAML file that matches the project prefix.
    yaml_candidates = list(state_dir.glob("PROJ-110*.yaml"))
    if not yaml_candidates:
        logging.error(
            f"No state YAML file found in {state_dir} matching pattern 'PROJ-110*.yaml'"
        )
        raise FileNotFoundError(
            f"State YAML file for project PROJ-110 not found in {state_dir}"
        )
    state_path = yaml_candidates[0]  # Assume the first match is the correct one.

    # Step 3 – load existing state (if any) and update it.
    try:
        state_data = load_state_file(state_path) if state_path.is_file() else {}
    except Exception as exc:
        logging.error(f"Failed to load state file {state_path}: {exc}")
        raise

    # Insert or replace the content hashes.
    state_data["content_hashes"] = hashes

    # Step 4 – persist the updated state.
    try:
        save_state_file(state_path, state_data)
        logging.info(f"Updated state file {state_path} with new content hashes.")
    except Exception as exc:
        logging.error(f"Failed to save updated state file {state_path}: {exc}")
        raise

# -------------------------------------------------------------------------
# End of added utilities
# -------------------------------------------------------------------------