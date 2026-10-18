"""
Feature extraction module for the evaluation pipeline.

This placeholder reads the (optional) PR data and creates an empty
``merged_features.parquet`` together with a ``covariate_config.json``
that lists the five required covariates.
"""

import json
import pandas as pd
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

COVARIATES = [
    "file_size_loc",
    "complexity_score",
    "repo_activity_level",
    "ci_build_time",
    "semantic_similarity"
]

def main() -> None:
    """
    Write an empty ``merged_features.parquet`` with the expected
    schema and a JSON configuration listing the covariates.
    """
    output_parquet = paths.data("processed", "merged_features.parquet")
    config_path = paths.data("processed", "covariate_config.json")
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    columns = ["pr_id"] + COVARIATES
    pd.DataFrame(columns=columns).to_parquet(output_parquet, index=False)
    log.info(f"Merged features written to {output_parquet}")

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(COVARIATES, f, indent=2)
    log.info(f"Covariate config written to {config_path}")
