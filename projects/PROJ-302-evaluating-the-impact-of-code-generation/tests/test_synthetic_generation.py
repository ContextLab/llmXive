"""
Tests for the synthetic_generation module (T004).

The test suite checks that:
  1. The expected parquet files are created.
  2. The validation JSON exists and reports a syntax_validity_rate ≥ 0.95.
  3. All generated snippets are syntactically valid Python code.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from llmxive_toolkit import paths

# Import the module under test
import code.synthetic_generation as synth

@pytest.fixture(scope="module")
def run_generation():
    """Run the synthetic generation script once for the whole test module."""
    synth.main()
    yield
    # No cleanup – artefacts are kept for inspection if needed

def test_output_files_exist(run_generation):
    """Both parquet files and the validation JSON must exist."""
    ctx_path = paths.data("synthetic", "context_based.parquet")
    prm_path = paths.data("synthetic", "prompt_based.parquet")
    val_path = paths.data("synthetic", "validation.json")

    assert ctx_path.is_file(), f"Missing {ctx_path}"
    assert prm_path.is_file(), f"Missing {prm_path}"
    assert val_path.is_file(), f"Missing {val_path}"

def test_parquet_schema(run_generation):
    """Each parquet must contain the required columns and ≤ 30 s per snippet."""
    required_cols = {
        "pr_id",
        "code_content",
        "generation_source",
        "generation_time_sec",
        "model_version",
        "generation_params",
    }

    for fname in ["context_based.parquet", "prompt_based.parquet"]:
        df = pd.read_parquet(paths.data("synthetic", fname))
        assert set(df.columns) == required_cols, f"Unexpected columns in {fname}"
        # All generation times must respect the contract
        assert (df["generation_time_sec"] <= 30).all(), f"Generation time exceeded 30 s in {fname}"

def test_syntax_validity_rate(run_generation):
    """The validation JSON must report a rate ≥ 0.95 and the actual AST parse must agree."""
    val_path = paths.data("synthetic", "validation.json")
    with open(val_path, "r", encoding="utf-8") as f:
        validation = json.load(f)

    rate = validation.get("syntax_validity_rate")
    assert rate is not None, "validation JSON missing 'syntax_validity_rate'"
    assert rate >= 0.95, f"Validity rate too low: {rate:.2%}"

    # Double‑check by parsing all snippets
    ctx_df = pd.read_parquet(paths.data("synthetic", "context_based.parquet"))
    prm_df = pd.read_parquet(paths.data("synthetic", "prompt_based.parquet"))
    all_codes = pd.concat([ctx_df["code_content"], prm_df["code_content"]], ignore_index=True)

    valid = 0
    for code in all_codes:
        try:
            compile(code, "<string>", "exec")
            valid += 1
        except Exception:
            pass

    actual_rate = valid / len(all_codes)
    assert actual_rate >= 0.95, f"AST‑based validity {actual_rate:.2%} < 95 %"