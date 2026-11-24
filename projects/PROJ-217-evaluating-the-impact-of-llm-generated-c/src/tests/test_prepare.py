"""
Tests for src/data/prepare.py

The tests construct minimal in‑memory fixtures, write them to the expected
locations under ``data/``, run the ``main`` function, and then verify that
the merged CSV exists and conforms to the contract schema.
"""

import csv
import json
import os
from pathlib import Path

import pandas as pd
import pytest
from llmxive_toolkit import paths

from src.data.prepare import main as prepare_main


@pytest.fixture
def minimal_fixture(tmp_path: Path):
    """Create a tiny, valid dataset consisting of one snippet evaluated by
    two participants."""
    # ------------------------------------------------------------------
    # Human study responses
    # ------------------------------------------------------------------
    responses = [
        # participant 1
        {
            "participant_id": "p1",
            "snippet_id": "s001",
            "condition": "llm",
            "completion_time_sec": 12.3,
            "accuracy": 1,
            "subjective_helpfulness": 4,
        },
        {
            "participant_id": "p1",
            "snippet_id": "s001",
            "condition": "human",
            "completion_time_sec": 15.0,
            "accuracy": 1,
            "subjective_helpfulness": 5,
        },
        {
            "participant_id": "p1",
            "snippet_id": "s001",
            "condition": "none",
            "completion_time_sec": 20.1,
            "accuracy": 0,
            "subjective_helpfulness": 1,
        },
        # participant 2
        {
            "participant_id": "p2",
            "snippet_id": "s001",
            "condition": "llm",
            "completion_time_sec": 11.8,
            "accuracy": 1,
            "subjective_helpfulness": 3,
        },
        {
            "participant_id": "p2",
            "snippet_id": "s001",
            "condition": "human",
            "completion_time_sec": 14.5,
            "accuracy": 1,
            "subjective_helpfulness": 4,
        },
        {
            "participant_id": "p2",
            "snippet_id": "s001",
            "condition": "none",
            "completion_time_sec": 19.9,
            "accuracy": 0,
            "subjective_helpfulness": 2,
        },
    ]
    responses_path = paths.data("human_study_responses.csv")
    pd.DataFrame(responses).to_csv(responses_path, index=False)

    # ------------------------------------------------------------------
    # Readability metrics (matching the three conditions)
    # ------------------------------------------------------------------
    metrics = [
        {
            "snippet_id": "s001",
            "condition": "llm",
            "code": "def add(a, b):\n    return a + b",
            "human_comment": "Adds two numbers together.",
            "llm_comment": "Adds two numbers together.",
            "no_comment": "",
            "BLEU_vs_source": 1.0,
            "BLEU_vs_human": 1.0,
            "ROUGE_L_vs_source": 1.0,
            "ROUGE_L_vs_human": 1.0,
            "Semantic_Similarity_vs_source": 1.0,
            "Semantic_Similarity_vs_human": 1.0,
            "Comment_Length": 26,
            "Flesch_Kincaid_Grade": 7.2,
        },
        {
            "snippet_id": "s001",
            "condition": "human",
            "code": "def add(a, b):\n    return a + b",
            "human_comment": "Adds two numbers together.",
            "llm_comment": "Adds two numbers together.",
            "no_comment": "",
            "BLEU_vs_source": 1.0,
            "BLEU_vs_human": 1.0,
            "ROUGE_L_vs_source": 1.0,
            "ROUGE_L_vs_human": 1.0,
            "Semantic_Similarity_vs_source": 1.0,
            "Semantic_Similarity_vs_human": 1.0,
            "Comment_Length": 26,
            "Flesch_Kincaid_Grade": 7.2,
        },
        {
            "snippet_id": "s001",
            "condition": "none",
            "code": "def add(a, b):\n    return a + b",
            "human_comment": "Adds two numbers together.",
            "llm_comment": "Adds two numbers together.",
            "no_comment": "",
            "BLEU_vs_source": None,
            "BLEU_vs_human": None,
            "ROUGE_L_vs_source": None,
            "ROUGE_L_vs_human": None,
            "Semantic_Similarity_vs_source": None,
            "Semantic_Similarity_vs_human": None,
            "Comment_Length": 0,
            "Flesch_Kincaid_Grade": 0,
        },
    ]
    metrics_path = paths.data("readability_metrics.csv")
    pd.DataFrame(metrics).to_csv(metrics_path, index=False, quoting=csv.QUOTE_NONNUMERIC)

    # Return the paths for later verification
    return {
        "responses_path": responses_path,
        "metrics_path": metrics_path,
        "merged_path": paths.data("merged_dataset.csv"),
    }


def test_prepare_success(minimal_fixture):
    """Running ``src.data.prepare`` on a valid fixture should produce a
    merged CSV that conforms to the contract."""
    # Execute the preparation script
    prepare_main()

    merged_path = minimal_fixture["merged_path"]
    assert merged_path.is_file(), "merged_dataset.csv was not created"

    merged_df = pd.read_csv(merged_path)

    # Expected number of rows = participants * conditions = 2 * 3 = 6
    assert len(merged_df) == 6

    # Spot‑check a few columns
    first_row = merged_df.iloc[0]
    assert first_row["snippet_id"] == "s001"
    assert first_row["condition"] in {"llm", "human", "none"}
    # Metric columns for the ``none`` condition must be null / NaN
    none_rows = merged_df[merged_df["condition"] == "none"]
    for col in [
        "BLEU_vs_source",
        "BLEU_vs_human",
        "ROUGE_L_vs_source",
        "ROUGE_L_vs_human",
        "Semantic_Similarity_vs_source",
        "Semantic_Similarity_vs_human",
    ]:
        assert none_rows[col].isna().all()


def test_design_violation_raises(tmp_path: Path):
    """If a participant lacks one of the three conditions, the script
    should raise a RuntimeError."""
    # Write a broken responses CSV (missing the ``none`` condition for p1)
    bad_responses = [
        {
            "participant_id": "p1",
            "snippet_id": "s001",
            "condition": "llm",
            "completion_time_sec": 10,
            "accuracy": 1,
            "subjective_helpfulness": 4,
        },
        {
            "participant_id": "p1",
            "snippet_id": "s001",
            "condition": "human",
            "completion_time_sec": 12,
            "accuracy": 1,
            "subjective_helpfulness": 5,
        },
    ]
    responses_path = paths.data("human_study_responses.csv")
    pd.DataFrame(bad_responses).to_csv(responses_path, index=False)

    # Provide a minimal, valid metrics file so the script can get past loading
    metrics = [
        {
            "snippet_id": "s001",
            "condition": "llm",
            "code": "def f(): pass",
            "human_comment": "",
            "llm_comment": "",
            "no_comment": "",
            "BLEU_vs_source": None,
            "BLEU_vs_human": None,
            "ROUGE_L_vs_source": None,
            "ROUGE_L_vs_human": None,
            "Semantic_Similarity_vs_source": None,
            "Semantic_Similarity_vs_human": None,
            "Comment_Length": 0,
            "Flesch_Kincaid_Grade": 0,
        },
        {
            "snippet_id": "s001",
            "condition": "human",
            "code": "def f(): pass",
            "human_comment": "",
            "llm_comment": "",
            "no_comment": "",
            "BLEU_vs_source": None,
            "BLEU_vs_human": None,
            "ROUGE_L_vs_source": None,
            "ROUGE_L_vs_human": None,
            "Semantic_Similarity_vs_source": None,
            "Semantic_Similarity_vs_human": None,
            "Comment_Length": 0,
            "Flesch_Kincaid_Grade": 0,
        },
    ]
    metrics_path = paths.data("readability_metrics.csv")
    pd.DataFrame(metrics).to_csv(metrics_path, index=False)

    # The preparation should fail
    with pytest.raises(RuntimeError, match="Design violation"):
        prepare_main()