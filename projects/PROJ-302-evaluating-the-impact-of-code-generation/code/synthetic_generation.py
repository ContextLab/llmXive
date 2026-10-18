"""
Synthetic generation module for the evaluation pipeline.

This placeholder creates empty parquet files for the two LLM
cohorts (context‑based and prompt‑only) with the required column
names. No actual model inference is performed.
"""

import pandas as pd
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main() -> None:
    """
    Produce empty ``context_based.parquet`` and ``prompt_based.parquet``
    files containing the column headers required by downstream stages.
    """
    ctx_path = paths.data("synthetic", "context_based.parquet")
    prm_path = paths.data("synthetic", "prompt_based.parquet")
    ctx_path.parent.mkdir(parents=True, exist_ok=True)
    prm_path.parent.mkdir(parents=True, exist_ok=True)

    ctx_columns = [
        "pr_id",
        "code_content",
        "generation_source",
        "generation_time_sec",
        "model_version",
        "generation_params"
    ]
    prm_columns = ctx_columns.copy()

    pd.DataFrame(columns=ctx_columns).to_parquet(ctx_path, index=False)
    pd.DataFrame(columns=prm_columns).to_parquet(prm_path, index=False)

    log.info(f"Context‑based synthetic data written to {ctx_path}")
    log.info(f"Prompt‑based synthetic data written to {prm_path}")
