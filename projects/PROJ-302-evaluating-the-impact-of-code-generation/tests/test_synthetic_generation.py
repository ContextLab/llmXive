import pandas as pd
import json
from pathlib import Path
from llmxive_toolkit import paths

def test_synthetic_artifacts_exist():
    """Verify that T004 produced the required artifacts."""
    ctx_path = paths.data("synthetic", "context_based.parquet")
    prm_path = paths.data("synthetic", "prompt_based.parquet")
    val_path = paths.data("synthetic", "validation.json")

    assert ctx_path.exists(), "context_based.parquet is missing"
    assert prm_path.exists(), "prompt_based.parquet is missing"
    assert val_path.exists(), "validation.json is missing"

def test_synthetic_data_quality():
    """Verify the content of the generated cohorts."""
    ctx_df = pd.read_parquet(paths.data("synthetic", "context_based.parquet"))
    prm_df = pd.read_parquet(paths.data("synthetic", "prompt_based.parquet"))
    
    # Check minimum size
    assert len(ctx_df) >= 100, "Context-based cohort too small"
    assert len(prm_df) >= 100, "Prompt-based cohort too small"
    
    # Check required columns
    required_cols = {"pr_id", "code_content", "generation_source", "generation_time_sec", "model_version"}
    assert required_cols.issubset(set(ctx_df.columns)), "Missing columns in context_based.parquet"
    assert required_cols.issubset(set(prm_df.columns)), "Missing columns in prompt_based.parquet"
    
    # Check time constraint
    assert (ctx_df["generation_time_sec"] <= 30.0).all(), "Some snippets took > 30s"

def test_validation_report():
    """Verify the validation report and threshold."""
    with open(paths.data("synthetic", "validation.json"), "r") as f:
        val = json.load(f)
    
    assert "syntax_validity_rate" in val
    assert val["syntax_validity_rate"] >= 0.95, f"Validity rate {val['syntax_validity_rate']} below 0.95"