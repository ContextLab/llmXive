"""
rank_contributions.py

Rank structural contributions to molecular dipole moments using the outputs of
the permutation‑importance and saliency‑mapping steps.

The script aggregates importance scores for two structural aspects that are
of interest for the project:

1. **Electronegative atom placement** – contributions of atoms with high
   electronegativity (O, N, F, Cl, Br, I).  These are extracted from the
   saliency‑mapping output where per‑atom contributions are reported.

2. **Local bond angles** – features whose name contains the word ``angle``.
   These are typically produced by the 2‑D descriptor pipeline (e.g. angle
   descriptors) and appear in the permutation‑importance JSON.

The resulting ranking is written to ``results/attributions.json`` as a list
of ``{ "contribution": <name>, "score": <float> }`` objects sorted in
descending order of importance.

The script can be executed directly:

.. code-block:: console

    $ python code/attribution/rank_contributions.py \
          --perm-path results/permutation_importance.json \
          --saliency-path results/saliency.json \
          --output results/attributions.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Dict, List, Tuple

__all__ = [
    "load_json",
    "extract_structural_scores",
    "rank_structural_contributions",
    "main",
]


def load_json(path: pathlib.Path) -> Dict:
    """Load a JSON file and return its contents.

    Parameters
    ----------
    path:
        Path to the JSON file.

    Returns
    -------
    dict:
        Parsed JSON data.

    Raises
    ------
    FileNotFoundError:
        If the file does not exist.
    json.JSONDecodeError:
        If the file is not valid JSON.
    """
    if not path.is_file():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_structural_scores(
    perm_importance: Dict[str, float],
    saliency: Dict,
) -> Dict[str, float]:
    """
    Combine permutation‑importance scores and saliency contributions that
    correspond to structural features of interest.

    Parameters
    ----------
    perm_importance:
        Mapping from feature name to importance score (as produced by
        ``permutation_importance``).

    saliency:
        Dictionary produced by ``saliency_mapping``.  Expected keys are:

        * ``atom_contributions`` – mapping from atom index (as string) to a
          float contribution.
        * ``atom_types`` – mapping from atom index (as string) to the element
          symbol (e.g. ``"O"``, ``"C"``).

    Returns
    -------
    dict:
        Mapping from a readable contribution label to an aggregated score.
    """
    # ------------------------------------------------------------------
    # 1.  Permutation‑importance: look for features that refer to angles or
    #     electronegative‑related descriptors.
    # ------------------------------------------------------------------
    structural_scores: Dict[str, float] = {}
    for feature, importance in perm_importance.items():
        lname = feature.lower()
        if "angle" in lname:
            # Any feature mentioning an angle is considered a local‑bond‑angle
            # descriptor.
            key = f"angle_feature:{feature}"
            structural_scores[key] = structural_scores.get(key, 0.0) + importance
        elif "electronegative" in lname:
            # Some pipelines may explicitly name electronegative‑atom features.
            key = f"electronegativity_feature:{feature}"
            structural_scores[key] = structural_scores.get(key, 0.0) + importance

    # ------------------------------------------------------------------
    # 2.  Saliency‑mapping: aggregate contributions of electronegative atoms.
    # ------------------------------------------------------------------
    atom_contribs = saliency.get("atom_contributions", {})
    atom_types = saliency.get("atom_types", {})

    # Define a set of electronegative element symbols (lower‑case for comparison)
    electronegative_elements = {"o", "n", "f", "cl", "br", "i"}

    for atom_idx, contrib in atom_contribs.items():
        # ``atom_idx`` may be an int or a string; treat it as string for lookup.
        atom_type = atom_types.get(str(atom_idx), "").lower()
        if atom_type in electronegative_elements:
            key = f"electronegative_atom:{atom_type.upper()}_{atom_idx}"
            structural_scores[key] = structural_scores.get(key, 0.0) + contrib

    return structural_scores


def rank_structural_contributions(
    perm_importance_path: pathlib.Path,
    saliency_path: pathlib.Path,
) -> List[Tuple[str, float]]:
    """
    Load the two attribution artefacts, compute aggregated structural scores,
    and return a sorted ranking.

    Parameters
    ----------
    perm_importance_path:
        Path to the JSON file containing permutation‑importance results.
    saliency_path:
        Path to the JSON file containing saliency‑mapping results.

    Returns
    -------
    list of (contribution, score):
        Sorted in descending order of ``score``.
    """
    perm_data = load_json(perm_importance_path)
    saliency_data = load_json(saliency_path)

    # The permutation‑importance JSON is expected to be a simple mapping
    # ``{feature_name: importance}``.  If it is wrapped in a top‑level key
    # (e.g. ``{"importance": {...}}``) we fall back to the first dict value.
    if not isinstance(perm_data, dict):
        raise ValueError("Permutation‑importance JSON must be a mapping.")
    if any(isinstance(v, dict) for v in perm_data.values()):
        # Heuristic: find the first dict‑valued entry.
        for v in perm_data.values():
            if isinstance(v, dict):
                perm_data = v
                break

    # Saliency JSON may have a richer structure; we keep it as‑is.
    scores = extract_structural_scores(perm_data, saliency_data)

    # Sort by score (high → low) and return a list of tuples.
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return ranked


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rank structural contributions to dipole moments using "
        "permutation‑importance and saliency‑mapping artefacts."
    )
    parser.add_argument(
        "--perm-path",
        type=pathlib.Path,
        default=pathlib.Path("results/permutation_importance.json"),
        help="Path to permutation‑importance JSON file.",
    )
    parser.add_argument(
        "--saliency-path",
        type=pathlib.Path,
        default=pathlib.Path("results/saliency.json"),
        help="Path to saliency‑mapping JSON file.",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=pathlib.Path("results/attributions.json"),
        help="Path where the ranked contributions will be written.",
    )
    args = parser.parse_args()

    try:
        ranking = rank_structural_contributions(args.perm_path, args.saliency_path)
    except Exception as exc:
        print(f"[ERROR] Failed to compute ranking: {exc}", file=sys.stderr)
        sys.exit(1)

    # Prepare JSON‑serialisable structure.
    json_out = [
        {"contribution": name, "score": float(score)} for name, score in ranking
    ]

    # Ensure parent directory exists.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(json_out, f, indent=2)

    # Friendly console output.
    print(f"Structural contribution ranking written to: {args.output}")
    print("Top 5 contributions:")
    for name, score in ranking[:5]:
        print(f"  {name}: {score:.4f}")


if __name__ == "__main__":
    main()