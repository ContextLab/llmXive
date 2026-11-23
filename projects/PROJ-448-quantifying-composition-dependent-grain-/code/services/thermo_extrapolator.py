"""
Thermo Extrapolator Service
===========================

This module provides utilities to linearly extrapolate missing CALPHAD
thermodynamic parameters over a temperature range of 500‑900 K using
:pyfunc:`scipy.interpolate.interp1d`.

The core public API is the :func:`extrapolate_missing_parameters` function,
which reads a CALPHAD JSON file (as produced by ``code/data/download_calphad.py``),
identifies missing temperature points in the 500‑900 K window, performs linear
interpolation/extrapolation, and writes the completed dataset to a processed
location.

The module can also be executed as a script:
    ``python code/services/thermo_extrapolator.py``

which will operate on the default raw and processed paths defined in
``code.config``.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any

from scipy.interpolate import interp1d

from code.config import DATA_RAW_PATH, PROCESSED_PATH, get_logger

logger = get_logger(__name__)

# -------------------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------------------

def _load_json(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    logger.debug("Loading JSON file from %s", file_path)
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _save_json(data: Dict[str, Any], file_path: Path) -> None:
    """Save a dictionary as pretty‑printed JSON."""
    logger.debug("Saving JSON file to %s", file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

# -------------------------------------------------------------------------
# Core extrapolation logic
# -------------------------------------------------------------------------

def _interpolate_parameter(
    temperatures: List[float],
    values: List[float],
    target_temps: List[float],
) -> List[float]:
    """
    Interpolate (or extrapolate) a single parameter.

    Parameters
    ----------
    temperatures: List[float]
        Known temperature points (must be monotonic).
    values: List[float]
        Parameter values at the known temperatures.
    target_temps: List[float]
        Temperatures for which we need values (may lie outside the known range).

    Returns
    -------
    List[float]
        Interpolated/extrapolated values corresponding to ``target_temps``.
    """
    logger.debug(
        "Creating interp1d for temperatures %s with values %s",
        temperatures,
        values,
    )
    # ``fill_value="extrapolate"`` ensures linear extrapolation beyond the bounds.
    interpolator = interp1d(
        temperatures,
        values,
        kind="linear",
        fill_value="extrapolate",
        assume_sorted=True,
    )
    result = interpolator(target_temps).tolist()
    logger.debug(
        "Interpolated values for target temperatures %s: %s",
        target_temps,
        result,
    )
    return result

def extrapolate_missing_parameters(
    input_json_path: Path,
    output_json_path: Path,
    missing_temps: List[int] = None,
) -> None:
    """
    Fill missing CALPHAD parameters for the temperature range 500‑900 K.

    The function expects the input JSON to have the following structure::

        {
            "parameters": {
                "<param_name>": {
                    "temperatures": [list of float],
                    "values": [list of float]
                },
                ...
            }
        }

    Missing temperatures are identified from ``missing_temps`` (default:
    ``[500, 600, 700, 800, 900]``).  For each parameter we linearly
    interpolate/extrapolate values at those temperatures and merge them
    into the original dataset.

    Parameters
    ----------
    input_json_path: Path
        Path to the raw CALPHAD JSON file.
    output_json_path: Path
        Destination for the completed JSON file.
    missing_temps: List[int], optional
        Temperature points to generate.  If ``None`` the default range
        500‑900 K in 100 K increments is used.
    """
    if missing_temps is None:
        missing_temps = list(range(500, 901, 100))

    logger.info(
        "Extrapolating CALPHAD parameters from %s to %s",
        input_json_path,
        output_json_path,
    )
    raw_data = _load_json(input_json_path)

    if "parameters" not in raw_data:
        raise ValueError(
            f"The input file {input_json_path} does not contain a "
            "'parameters' key."
        )

    completed_data = {"parameters": {}}
    for param_name, param_info in raw_data["parameters"].items():
        temps = param_info.get("temperatures")
        vals = param_info.get("values")
        if temps is None or vals is None:
            logger.warning(
                "Parameter %s is missing 'temperatures' or 'values'; skipping.",
                param_name,
            )
            continue

        # Ensure temperatures are sorted (interp1d requires monotonic input)
        sorted_pairs = sorted(zip(temps, vals), key=lambda x: x[0])
        sorted_temps, sorted_vals = zip(*sorted_pairs)

        # Determine which of the target temps are already present
        existing_set = set(sorted_temps)
        to_compute = [t for t in missing_temps if t not in existing_set]

        if to_compute:
            logger.debug(
                "Parameter %s missing temperatures %s; computing.", param_name, to_compute
            )
            new_vals = _interpolate_parameter(
                list(sorted_temps), list(sorted_vals), to_compute
            )
            # Merge new points into the existing lists
            combined = list(zip(sorted_temps, sorted_vals)) + list(
                zip(to_compute, new_vals)
            )
            # Re‑sort after merging
            combined.sort(key=lambda x: x[0])
            final_temps, final_vals = zip(*combined)
        else:
            final_temps, final_vals = sorted_temps, sorted_vals

        completed_data["parameters"][param_name] = {
            "temperatures": list(final_temps),
            "values": list(final_vals),
        }

    _save_json(completed_data, output_json_path)
    logger.info("Extrapolation complete. Output written to %s", output_json_path)

# -------------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------------

def main() -> None:
    """
    Command‑line entry point.

    It reads ``data/raw/calphad_params.json`` (as defined by
    ``code.config.DATA_RAW_PATH``) and writes the extrapolated version to
    ``data/processed/extrapolated_calphad_params.json`` under the processed
    data directory.
    """
    input_path = DATA_RAW_PATH / "calphad_params.json"
    output_path = PROCESSED_PATH / "extrapolated_calphad_params.json"

    if not input_path.is_file():
        raise FileNotFoundError(
            f"Required CALPHAD input file not found at {input_path}"
        )

    extrapolate_missing_parameters(input_path, output_path)

if __name__ == "__main__":
    main()
