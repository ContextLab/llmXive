import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

from code.data.storage import save_variants_to_parquet, load_variants_from_parquet, get_variant_counts_by_complexity
from code.models.data_models import PromptVariant, GeneratedCode


@pytest.fixture
def sample_variants():
    return [
        {
            "variant_id": "v1",
            "problem_id": "human_eval_001",
            "complexity_label": "simple",
            "prompt_text": "Write a function to add two numbers.",
            "token_count": 15,
            "structural_element_count": {"examples": 0, "constraints": 0, "steps": 1},
            "dependency_depth": 1
        },
        {
            "variant_id": "v2",
            "problem_id": "human_eval_001",
            "complexity_label": "complex",
            "prompt_text": "Write a function to add two numbers. Constraints: no loops. Steps: 1. Example: 1+1=2.",
            "token_count": 50,
            "structural_element_count": {"examples": 1, "constraints": 1, "steps": 1},
            "dependency_depth": 3
        }
    ]


@pytest.fixture
def sample_codes():
    return [
        {
            "code_id": "c1",
            "variant_id": "v1",
            "code": "def add(a, b): return a + b",
            "generation_metadata": {"model": "test", "time": 0.1}
        },
        {
            "code_id": "c2",
            "variant_id": "v2",
            "code": "def add(a, b): return a + b # no loops",
            "generation_metadata": {"model": "test", "time": 0.2}
        }
    ]


def test_save_and_load_variants(sample_variants, sample_codes):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.parquet"

        # Save
        result_path = save_variants_to_parquet(sample_variants, sample_codes, output_path)
        assert result_path.exists()

        # Load
        df = load_variants_from_parquet(result_path)

        # Assertions
        assert len(df) == 2
        assert "variant_id" in df.columns
        assert "problem_id" in df.columns
        assert "variant_label" in df.columns
        assert "generated_code" in df.columns
        assert df.iloc[0]["variant_label"] == "simple"
        assert df.iloc[1]["variant_label"] == "complex"
        assert df.iloc[0]["generated_code"] == "def add(a, b): return a + b"


def test_empty_variants(sample_codes):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "empty_output.parquet"
        save_variants_to_parquet([], sample_codes, output_path)
        assert output_path.exists()
        df = load_variants_from_parquet(output_path)
        assert len(df) == 0


def test_get_variant_counts_by_complexity(sample_variants, sample_codes):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_counts.parquet"
        save_variants_to_parquet(sample_variants, sample_codes, output_path)
        df = load_variants_from_parquet(output_path)

        counts = get_variant_counts_by_complexity(df)
        assert counts["simple"] == 1
        assert counts["complex"] == 1
        assert len(counts) == 2
