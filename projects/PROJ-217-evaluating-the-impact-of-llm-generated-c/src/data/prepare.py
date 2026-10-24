"""
src/data/prepare.py

Merge the human study responses, LLM comment data, and readability metrics
into a single analysis‑ready dataset, and validate it against the
contract schema.

The script is invoked as a module:
    python -m src.data.prepare

It performs the following steps:

1. Load ``data/human_study_responses.csv`` – the raw human‑evaluation
   results.
2. Load ``data/readability_metrics.csv`` – the automatically computed
   readability scores for each ``snippet_id``/``condition`` pair.
3. Verify the within‑subject design:
   * Every participant must have exactly three rows for each snippet,
     covering the conditions ``llm``, ``human`` and ``none``.
   * Consequently each snippet appears in each condition the same number
     of times across participants.
4. Merge the two tables on ``snippet_id`` and ``condition`` producing a
   dataframe that contains the required columns defined in
   ``contracts/dataset.schema.yaml``.
5. Validate each merged record against the JSON‑Schema contract.
   Any violation raises a ``RuntimeError`` with a clear message.
6. Write the merged dataset to ``data/merged_dataset.csv`` (CSV format,
   header row, no index column).

The implementation streams data using ``pandas`` which is memory‑efficient
for the dataset sizes expected (< 7 GB).  All paths are obtained through
``llmxive_toolkit.paths`` to guarantee they reside inside the project
directory.
"""

import csv
import json
import sys
from pathlib import Path

import pandas as pd
from jsonschema import Draft7Validator, ValidationError

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_human_responses() -> pd.DataFrame:
    """Load the human study responses CSV.

    Returns
    -------
    pd.DataFrame
        Columns expected (at minimum):
        participant_id, snippet_id, condition,
        completion_time_sec, accuracy, subjective_helpfulness
    """
    csv_path = paths.data("human_study_responses.csv")
    if not csv_path.is_file():
        raise FileNotFoundError(f"Human study responses not found at {csv_path}")
    log.info(f"Loading human study responses from {csv_path}")
    df = pd.read_csv(csv_path, dtype=str)

    # Cast numeric columns to appropriate dtypes
    numeric_cols = ["completion_time_sec", "accuracy", "subjective_helpfulness"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="raise")
    return df


def _load_readability_metrics() -> pd.DataFrame:
    """Load the readability metrics CSV.

    Returns
    -------
    pd.DataFrame
        Must contain at least the columns required by the contract plus
        ``snippet_id`` and ``condition``.
    """
    csv_path = paths.data("readability_metrics.csv")
    if not csv_path.is_file():
        raise FileNotFoundError(f"Readability metrics not found at {csv_path}")
    log.info(f"Loading readability metrics from {csv_path}")
    df = pd.read_csv(csv_path, dtype=str)

    # Convert metric columns that are numeric to float, keeping empty strings as NaN
    metric_cols = [
        "BLEU_vs_source",
        "BLEU_vs_human",
        "ROUGE_L_vs_source",
        "ROUGE_L_vs_human",
        "Semantic_Similarity_vs_source",
        "Semantic_Similarity_vs_human",
        "Comment_Length",
        "Flesch_Kincaid_Grade",
    ]
    for col in metric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _verify_within_subject_design(responses: pd.DataFrame) -> None:
    """Ensure each participant has exactly three rows per snippet covering
    all three conditions, and that each snippet appears equally often in each
    condition across participants.

    Parameters
    ----------
    responses : pd.DataFrame
        Human study response rows.

    Raises
    ------
    RuntimeError
        If any design violation is detected.
    """
    required_conditions = {"llm", "human", "none"}

    # Check per participant‑snippet grouping
    grouping = responses.groupby(["participant_id", "snippet_id"])
    for (pid, sid), group in grouping:
        conds = set(group["condition"].unique())
        if conds != required_conditions:
            raise RuntimeError(
                f"Design violation: participant '{pid}' snippet '{sid}' has conditions {conds} "
                f"instead of required {required_conditions}"
            )
        if len(group) != 3:
            raise RuntimeError(
                f"Design violation: participant '{pid}' snippet '{sid}' has {len(group)} rows "
                "(expected exactly 3)."
            )

    # Verify equal representation of each condition per snippet
    snippet_cond_counts = responses.groupby(["snippet_id", "condition"]).size().unstack(fill_value=0)
    # All rows should have the same count across conditions
    if not snippet_cond_counts.nunique().eq(1).all():
        # Find the offending snippet(s)
        problematic = snippet_cond_counts[
            snippet_cond_counts.nunique(axis=1) != 1
        ].index.tolist()
        raise RuntimeError(
            f"Design violation: snippets {problematic} do not have equal counts across conditions."
        )
    log.info("Within‑subject design verification passed.")


def _merge_datasets(
    responses: pd.DataFrame, metrics: pd.DataFrame
) -> pd.DataFrame:
    """Merge human responses with readability metrics.

    The merge is performed on ``snippet_id`` and ``condition``.  All
    columns required by the contract are retained; additional columns are
    kept as‑is.

    Parameters
    ----------
    responses : pd.DataFrame
    metrics : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    merged = pd.merge(
        responses,
        metrics,
        on=["snippet_id", "condition"],
        how="inner",
        suffixes=("", "_metrics"),
    )
    # Ensure the column order matches the contract where possible
    contract_order = [
        "snippet_id",
        "condition",
        "code",
        "human_comment",
        "llm_comment",
        "no_comment",
        "BLEU_vs_source",
        "BLEU_vs_human",
        "ROUGE_L_vs_source",
        "ROUGE_L_vs_human",
        "Semantic_Similarity_vs_source",
        "Semantic_Similarity_vs_human",
        "completion_time_sec",
        "accuracy",
        "subjective_helpfulness",
    ]
    # Append any extra columns after the contract ones
    extra_cols = [c for c in merged.columns if c not in contract_order]
    final_cols = contract_order + extra_cols
    merged = merged[final_cols]
    return merged


def _load_schema() -> dict:
    """Load the JSON‑Schema for the merged dataset."""
    schema_path = (
        paths.root
        / "specs"
        / "001-evaluating-the-impact-of-llm-generated-c"
        / "contracts"
        / "dataset.schema.yaml"
    )
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    return schema


def _validate_against_schema(df: pd.DataFrame) -> None:
    """Validate each row of ``df`` against the dataset contract.

    Parameters
    ----------
    df : pd.DataFrame

    Raises
    ------
    RuntimeError
        If any row violates the schema.
    """
    import yaml  # Imported lazily to avoid unnecessary dependency at import time

    schema = _load_schema()
    validator = Draft7Validator(schema)

    errors = []
    for idx, row in df.iterrows():
        # Convert pandas scalars / NaN to native Python types
        record = row.where(pd.notnull(row), None).to_dict()
        try:
            validator.validate(record)
        except ValidationError as ve:
            errors.append(f"Row {idx}: {ve.message}")

    if errors:
        error_msg = "\n".join(errors)
        raise RuntimeError(f"Schema validation failed:\n{error_msg}")
    log.info("All merged records conform to the dataset schema.")


def main() -> None:
    """Entry point for ``python -m src.data.prepare``."""
    try:
        # 1. Load inputs
        responses_df = _load_human_responses()
        metrics_df = _load_readability_metrics()

        # 2. Verify within‑subject design
        _verify_within_subject_design(responses_df)

        # 3. Merge datasets
        merged_df = _merge_datasets(responses_df, metrics_df)

        # 4. Validate against JSON schema
        _validate_against_schema(merged_df)

        # 5. Write merged dataset
        out_path = paths.data("merged_dataset.csv")
        merged_df.to_csv(out_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
        log.info(f"Merged dataset written to {out_path}")

    except Exception as e:
        log.error(f"Preparation failed: {e}")
        # Propagate the exception so the process exits with a non‑zero status
        raise
