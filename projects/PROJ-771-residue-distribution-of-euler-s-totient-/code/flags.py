"""
Flag generation module for the Euler Totient residue‑distribution pipeline.

This module reads a ``StatisticalResult`` JSON file produced by the
``stats`` module and writes a lightweight JSON flag file containing three
Boolean fields:

* ``alpha_pass`` – ``True`` if the p‑value exceeds the standard 0.05
  significance level.
* ``bonferroni_pass`` – ``True`` if the p‑value exceeds the Bonferroni‑
  corrected threshold (0.05 / 4).
* ``overall_pass`` – ``True`` only when *both* of the above are ``True``.

The output file is written to ``results/reports/flag_{prime}_{N}.json``,
where ``prime`` and ``N`` are extracted from the input JSON.
"""

import json
from typing import Dict

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def _extract_p_value(data: Dict) -> float:
    """
    Retrieve the appropriate p‑value from a ``StatisticalResult`` JSON
    payload.

    The primary field used throughout the codebase is
    ``chi_squared_p_value``.  If that field is absent, we fall back to a
    generic ``p_value`` key for compatibility with older artefacts.

    Parameters
    ----------
    data : dict
        Parsed JSON content of a ``StatisticalResult``.

    Returns
    -------
    float
        The p‑value to be evaluated.

    Raises
    ------
    ValueError
        If neither expected key is present.
    """
    if "chi_squared_p_value" in data:
        return float(data["chi_squared_p_value"])
    if "p_value" in data:
        return float(data["p_value"])
    raise ValueError("Statistical result JSON does not contain a p‑value field.")


def generate_flag_from_result(json_path: str) -> Dict[str, bool]:
    """
    Read a ``StatisticalResult`` JSON file and write the corresponding
    flag file.

    The function returns the flag dictionary for convenient testing.

    Parameters
    ----------
    json_path : str
        Path to the ``StatisticalResult`` JSON file.

    Returns
    -------
    dict
        ``{\"alpha_pass\": bool, \"bonferroni_pass\": bool,
        \"overall_pass\": bool}``
    """
    # Load the statistical result
    with open(json_path, "r") as f:
        data = json.load(f)

    # Extract required metadata
    prime = data.get("prime")
    N = data.get("N")
    if prime is None or N is None:
        raise ValueError("Statistical result JSON must contain 'prime' and 'N' fields.")

    # Determine the p‑value and compute flags
    p_val = _extract_p_value(data)
    alpha_pass = p_val > 0.05
    bonferroni_pass = p_val > (0.05 / 4)  # 0.0125
    overall_pass = alpha_pass and bonferroni_pass

    flag_dict = {
        "alpha_pass": alpha_pass,
        "bonferroni_pass": bonferroni_pass,
        "overall_pass": overall_pass,
    }

    # Write the flag file to the prescribed location
    output_path = paths.results("reports", f"flag_{prime}_{N}.json")
    with open(output_path, "w") as f:
        json.dump(flag_dict, f, indent=2)

    log.info(
        "Flag file written for prime=%s, N=%s → %s",
        prime,
        N,
        output_path,
    )
    return flag_dict


__all__ = ["generate_flag_from_result"]
