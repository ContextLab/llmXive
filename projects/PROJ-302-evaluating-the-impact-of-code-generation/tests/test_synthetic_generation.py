import json
from pathlib import Path

import pandas as pd
import pytest

from code.synthetic_generation import (
    _load_prompts,
    _simple_code_from_prompt,
    main,
)
from llmxive_toolkit import paths

def test_simple_code_is_valid():
    """The stub generator must produce syntactically valid Python."""
    code = _simple_code_from_prompt("123", "Do something simple")
    # Should parse without error
    import ast
    ast.parse(code)  # will raise if invalid

def test_load_prompts_fallback(tmp_path, monkeypatch):
    """When the real prompts file is missing we should get a deterministic placeholder."""
    # Point the toolkit to a temporary project root so that paths.data resolves inside tmp_path
    monkeypatch.setattr("llmxive_toolkit.paths.root", tmp_path, raising=False)

    # Ensure no intent_prompts.parquet exists
    prompts_path = paths.data("processed", "intent_prompts.parquet")
    if prompts_path.is_file():
        prompts_path.unlink()

    df = _load_prompts()
    assert len(df) == 100
    assert set(df.columns) == {"pr_id", "prompt", "complexity_indicator"}

def test_main_creates_artifacts(tmp_path, monkeypatch):
    """Running main() must create the three expected artefacts."""
    # Redirect the project's root to a temporary directory for isolation
    monkeypatch.setattr("llmxive_toolkit.paths.root", tmp_path, raising=False)

    # Ensure fallback will be used (no real prompts file)
    prompts_path = paths.data("processed", "intent_prompts.parquet")
    if prompts_path.is_file():
        prompts_path.unlink()

    # Run the generation
    main()

    ctx_path = paths.data("synthetic", "context_based.parquet")
    prm_path = paths.data("synthetic", "prompt_based.parquet")
    val_path = paths.data("synthetic", "validation.json")

    for p in (ctx_path, prm_path):
        assert p.is_file(), f"{p} was not created"
        df = pd.read_parquet(p)
        assert len(df) == 100
        assert set(df.columns) >= {
            "pr_id",
            "code_content",
            "generation_source",
            "generation_time_sec",
            "model_version",
            "generation_params",
        }

    assert val_path.is_file(), "validation.json missing"
    with open(val_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_snippets"] == 200
    assert data["syntax_validity_rate"] >= 0.95