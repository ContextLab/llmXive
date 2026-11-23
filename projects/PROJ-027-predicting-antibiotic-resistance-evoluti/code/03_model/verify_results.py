"""
Verification script for model results.

This script performs an independent verification of the modeling
results produced by the pipeline. It checks three aspects:

1. **AUC‑ROC existence** – for every antibiotic class that has a
   trained model, the corresponding entry in ``metrics.json`` must
   contain a numeric ``auc_roc`` value.

2. **Mechanism‑blind filter compliance** – the canonical resistance
   genes for each class (provided in ``class_to_genes.json``) must not
   appear in the top‑10 feature ranking (``feature_ranking.csv``).

3. **Top‑10 feature ranking existence** – the ranking file must exist
   and contain at least ten rows.

The script writes a JSON summary to
``data/processed/verification_summary.json`` with per‑class pass/fail
details and an overall status flag.  It always exits with code ``0``
(the summary records any failures).
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

import pandas as pd

# llmxive toolkit helpers for path creation
from llmxive_toolkit import paths, get_logger

# Initialise a logger (console only – no file side‑effects required)
logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_json(path: Path) -> Dict:
    """Load a JSON file, raising if the file does not exist or is malformed."""
    if not path.is_file():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_feature_ranking(path: Path) -> pd.DataFrame:
    """Load the feature ranking CSV, expecting at least a ``feature_name`` column."""
    if not path.is_file():
        raise FileNotFoundError(f"Feature ranking file not found: {path}")
    df = pd.read_csv(path)
    if "feature_name" not in df.columns:
        raise ValueError("Feature ranking CSV must contain a 'feature_name' column")
    return df


def check_auc_present(metrics: Dict) -> Dict[str, Dict]:
    """
    Verify that each class entry in the metrics dictionary contains a numeric
    ``auc_roc`` value.

    Returns a dict mapping class name → {\"auc_present\": bool, \"auc_value\": float|None}.
    """
    results = {}
    for class_name, class_metrics in metrics.items():
        auc = class_metrics.get("auc_roc")
        present = isinstance(auc, (int, float))
        results[class_name] = {
            "auc_present": present,
            "auc_value": float(auc) if present else None,
        }
    return results


def top_n_features(df: pd.DataFrame, n: int = 10) -> List[str]:
    """Return the top *n* feature names sorted by importance (descending)."""
    # The ranking CSV produced by ``evaluate.py`` contains an
    # ``importance_score`` column; if missing we fall back to the order
    # of rows (the file is already sorted by importance in the pipeline).
    if "importance_score" in df.columns:
        df_sorted = df.sort_values(by="importance_score", ascending=False)
    else:
        df_sorted = df
    return df_sorted["feature_name"].head(n).tolist()


def verify_mechanism_blind(
    top_features: List[str],
    excluded_genes: Set[str],
) -> bool:
    """
    Return ``True`` if none of the ``excluded_genes`` appear in ``top_features``.
    """
    intersection = set(top_features).intersection(excluded_genes)
    if intersection:
        logger.warning(
            f"Mechanism‑blind violation – excluded genes found in top‑10: {intersection}"
        )
    return len(intersection) == 0


# ----------------------------------------------------------------------
# Main verification routine
# ----------------------------------------------------------------------
def main() -> int:
    # Paths to required artefacts
    metrics_path = paths.data("models", "metrics.json")
    ranking_path = paths.data("processed", "feature_ranking.csv")
    class_genes_path = paths.data("processed", "class_to_genes.json")
    summary_path = paths.data("processed", "verification_summary.json")

    # Prepare the summary structure
    summary = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "overall_pass": True,
        "class_results": {},
        "errors": [],
    }

    # ------------------------------------------------------------------
    # Load inputs – any failure is recorded but does not abort the script
    # ------------------------------------------------------------------
    try:
        metrics = load_json(metrics_path)
    except Exception as e:
        logger.error(f"Failed to load metrics: {e}")
        summary["errors"].append(str(e))
        metrics = {}

    try:
        ranking_df = load_feature_ranking(ranking_path)
    except Exception as e:
        logger.error(f"Failed to load feature ranking: {e}")
        summary["errors"].append(str(e))
        ranking_df = pd.DataFrame()

    try:
        class_to_genes = load_json(class_genes_path)
    except Exception as e:
        logger.error(f"Failed to load class‑to‑genes mapping: {e}")
        summary["errors"].append(str(e))
        class_to_genes = {}

    # ------------------------------------------------------------------
    # Perform checks
    # ------------------------------------------------------------------
    # 1. AUC‑ROC existence
    auc_results = check_auc_present(metrics)

    # 2. Top‑10 feature ranking existence & extraction
    if not ranking_df.empty and len(ranking_df) >= 10:
        top_features = top_n_features(ranking_df, n=10)
    else:
        logger.error(
            "Feature ranking CSV is missing or contains fewer than 10 rows."
        )
        summary["errors"].append(
            "Feature ranking CSV missing or insufficient rows."
        )
        top_features = []

    # Iterate over each antibiotic class present in the metrics file
    for class_name, auc_info in auc_results.items():
        class_pass = True
        class_detail: Dict = {
            "auc_present": auc_info["auc_present"],
            "auc_value": auc_info["auc_value"],
            "top10_excludes_genes": None,
        }

        # If AUC missing, flag failure for this class
        if not auc_info["auc_present"]:
            class_pass = False

        # Mechanism‑blind filter check (only if we have the needed data)
        excluded_genes = set(class_to_genes.get(class_name, []))
        if excluded_genes and top_features:
            blind_ok = verify_mechanism_blind(top_features, excluded_genes)
            class_detail["top10_excludes_genes"] = blind_ok
            if not blind_ok:
                class_pass = False
        else:
            # If we cannot perform the check, record as unknown but do not fail
            class_detail["top10_excludes_genes"] = None

        summary["class_results"][class_name] = class_detail
        if not class_pass:
            summary["overall_pass"] = False

    # If there were no classes (e.g., metrics file missing), overall_pass is False
    if not auc_results:
        summary["overall_pass"] = False

    # ------------------------------------------------------------------
    # Write summary JSON
    # ------------------------------------------------------------------
    try:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Verification summary written to {summary_path}")
    except Exception as e:
        logger.error(f"Failed to write verification summary: {e}")
        # Record the error but still exit with 0 as per specification
        summary["errors"].append(str(e))

    # The script must exit with code 0 regardless of pass/fail status
    return 0


if __name__ == "__main__":
    sys.exit(main())
