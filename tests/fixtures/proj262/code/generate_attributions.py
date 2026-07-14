"""Generate a combined attributions JSON file.

This script aggregates feature importance rankings from permutation
importance (e.g., Random Forest) and saliency mapping (e.g., GNN) and
writes a single JSON file with the merged results.

The default input locations match the conventions used elsewhere in the
project (``results/permutation_importance.json`` and
``results/saliency_mapping.json``) and the default output location is
``results/attributions.json``.  All paths can be overridden via command‑line
arguments.

The output format is::

    {
        "permutation": [
            {"feature": "<name>", "importance": <float>},
            ...
        ],
        "saliency": [
            {"feature": "<name>", "importance": <float>},
            ...
        ]
    }

The feature lists are sorted in descending order of importance.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List, Tuple

def _load_importance(path: pathlib.Path) -> Dict[str, float]:
    """Load a JSON mapping ``feature -> importance``.

    If the file does not exist or cannot be parsed, an empty dict is
    returned.
    """
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        # Ensure we have a mapping of str -> float
        return {str(k): float(v) for k, v in data.items()}
    except Exception:
        # Any problem (malformed JSON, wrong types) results in empty dict
        return {}

def _rank_features(importance: Dict[str, float]) -> List[Tuple[str, float]]:
    """Return a list of (feature, importance) sorted descending."""
    return sorted(importance.items(), key=lambda kv: kv[1], reverse=True)

def generate_attributions(
    perm_path: pathlib.Path,
    saliency_path: pathlib.Path,
    output_path: pathlib.Path,
) -> None:
    """Create the combined attributions JSON file."""
    perm_imp = _load_importance(perm_path)
    sal_imp = _load_importance(saliency_path)

    ranked_perm = _rank_features(perm_imp)
    ranked_sal = _rank_features(sal_imp)

    result = {
        "permutation": [
            {"feature": name, "importance": score} for name, score in ranked_perm
        ],
        "saliency": [
            {"feature": name, "importance": score} for name, score in ranked_sal
        ],
    }

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=False)

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate combined attributions JSON."
    )
    parser.add_argument(
        "--perm",
        type=pathlib.Path,
        default=pathlib.Path("results/permutation_importance.json"),
        help="Path to permutation importance JSON file.",
    )
    parser.add_argument(
        "--saliency",
        type=pathlib.Path,
        default=pathlib.Path("results/saliency_mapping.json"),
        help="Path to saliency mapping JSON file.",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=pathlib.Path("results/attributions.json"),
        help="Path where the combined attributions JSON will be written.",
    )
    return parser

def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    generate_attributions(args.perm, args.saliency, args.output)

if __name__ == "__main__":
    main()
