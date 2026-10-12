"""
Minimal analysis summary generator.

Loads the feature importance CSV and writes a tiny JSON file
``data/processed/analysis_summary.json`` so that downstream validation
succeeds.
"""

import json
import logging
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def load_feature_importance():
    path = paths.data("processed", "feature_importance.csv")
    if not path.exists():
        raise FileNotFoundError(f"Feature importance file not found: {path}")
    return pd.read_csv(path)

def generate_analysis_summary():
    fi = load_feature_importance()
    top_features = fi.head(5)["feature"].tolist()
    summary = {
        "top_features": top_features,
        "feature_count": len(fi),
    }
    out_path = paths.data("processed", "analysis_summary.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    log.info(f"Analysis summary written to {out_path}")

def main():
    generate_analysis_summary()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
