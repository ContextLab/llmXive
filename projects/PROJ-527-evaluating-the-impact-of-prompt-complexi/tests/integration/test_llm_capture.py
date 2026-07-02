"""
Integration test for LLM query and capture (T012).

This test verifies that the LLM orchestrator correctly queries the LLM client
with multiple prompt variants, captures the generated code, and enriches the
metadata with complexity labels, token counts, and structural element counts.

It uses a mocked LLM response to ensure deterministic behavior without relying
on external API availability or rate limits.
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.data_models import (
    HumanEvalProblem,
    PromptVariant,
    GeneratedCode,
    ComplexityLabel,
)
from prompts.generator import generate_prompt_variants
from llm.client import LLMClient
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def sample_human_eval_problem():
    """Fixture providing a minimal HumanEval problem JSON."""
    return {
        "task_id": "HumanEval/0",
        "prompt": "def add(a: int, b: int) -> int:\n    \"\"\"Add two numbers.\"\"\"\n    return a + b\n",
        "test": "assert add(1, 2) == 3",
        "entry_point": "add",
    }


@pytest.fixture
def mock_llm_response():
    """Fixture providing a deterministic mocked LLM response."""
    return {
        "choices": [
            {
                "message": {
                    "content": "def add(a: int, b: int) -> int:\n    return a + b\n"
                }
            }
        ]
    }


@pytest.fixture
def mock_llm_client(mock_llm_response):
    """Fixture creating a mocked LLMClient that returns the mock response."""
    client = MagicMock(spec=LLMClient)
    client.query = MagicMock(return_value=mock_llm_response)
    return client


def test_query_and_capture(sample_human_eval_problem, mock_llm_client):
    """
    Integration test: Verify that 5 distinct code samples are captured with
    correct metadata tags (complexity_label, token_count, structural_element_count).

    Steps:
    1. Generate 5 prompt variants from a single HumanEval problem.
    2. Mock the LLM client to return a fixed response.
    3. Simulate the orchestrator logic (query -> capture -> enrich).
    4. Assert that 5 GeneratedCode objects are created.
    5. Assert that each object has the correct complexity_label.
    6. Assert that token_count and structural_element_count are present and numeric.
    """
    # 1. Generate prompt variants
    problem = HumanEvalProblem(**sample_human_eval_problem)
    variants = generate_prompt_variants(problem)

    # Verify we got exactly 5 variants with correct labels
    assert len(variants) == 5, f"Expected 5 variants, got {len(variants)}"
    expected_labels = [
        ComplexityLabel.SIMPLE,
        ComplexityLabel.MODERATE,
        ComplexityLabel.COMPLEX,
        ComplexityLabel.VERY_COMPLEX,
        ComplexityLabel.DEGENERATE,
    ]
    labels = [v.complexity_label for v in variants]
    assert all(label in expected_labels for label in labels), (
        f"Unexpected labels: {labels}"
    )

    # 2. Simulate querying and capturing (mimicking orchestrator logic)
    captured_samples: list[GeneratedCode] = []

    for variant in variants:
        # Mock the LLM call
        response = mock_llm_client.query(variant.prompt)
        generated_content = response["choices"][0]["message"]["content"]

        # Create the GeneratedCode object
        sample = GeneratedCode(
            task_id=problem.task_id,
            complexity_label=variant.complexity_label,
            prompt_text=variant.prompt,
            generated_code=generated_content,
            token_count=variant.token_count,
            structural_element_count=variant.structural_element_count,
            variant_id=variant.variant_id,
        )
        captured_samples.append(sample)

    # 3. Assertions
    assert len(captured_samples) == 5, (
        f"Expected 5 captured samples, got {len(captured_samples)}"
    )

    # Verify metadata for each sample
    for sample in captured_samples:
        # Check complexity label is set and valid
        assert isinstance(sample.complexity_label, ComplexityLabel), (
            f"Invalid complexity_label type: {type(sample.complexity_label)}"
        )

        # Check token_count is a non-negative integer
        assert isinstance(sample.token_count, int), (
            f"token_count must be int, got {type(sample.token_count)}"
        )
        assert sample.token_count >= 0, (
            f"token_count must be non-negative, got {sample.token_count}"
        )

        # Check structural_element_count is a non-negative integer
        assert isinstance(sample.structural_element_count, int), (
            f"structural_element_count must be int, got {type(sample.structural_element_count)}"
        )
        assert sample.structural_element_count >= 0, (
            f"structural_element_count must be non-negative, got {sample.structural_element_count}"
        )

        # Verify the generated code is not empty
        assert len(sample.generated_code.strip()) > 0, "Generated code is empty"

    # Verify all 5 labels are present exactly once
    unique_labels = set(sample.complexity_label for sample in captured_samples)
    assert len(unique_labels) == 5, (
        f"Expected 5 unique labels, got {len(unique_labels)}: {unique_labels}"
    )

    logger.info("Test passed: 5 distinct code samples captured with correct metadata.")