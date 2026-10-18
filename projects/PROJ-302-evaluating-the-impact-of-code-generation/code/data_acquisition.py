"""
Data acquisition module for the evaluation pipeline.

This placeholder implementation creates a minimal synthetic
dataset of commit messages required for downstream stages.
In a full implementation, this would stream PR metadata from
the GitHub REST API.
"""

import pandas as pd
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main() -> None:
    """
    Generate a tiny synthetic commit messages parquet file.

    The file is written to ``data/raw/commit_messages.parquet`` and
    contains a single row with placeholder values. This satisfies
    the downstream stage expectations without requiring external
    network access.
    """
    output_path = paths.data("raw", "commit_messages.parquet")
    # Ensure parent directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(
        [
            {"pr_id": 1, "commit_message": "Initial commit"}
        ]
    )
    df.to_parquet(output_path, index=False)
    log.info(f"Commit messages written to {output_path}")
