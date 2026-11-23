import pytest
from unittest.mock import patch, MagicMock
from models.data_models import HumanEvalProblem
from prompts.generator import generate_prompt_variants
from llm.orchestrator import query_variant

@pytest.fixture
def sample_problem():
    return HumanEvalProblem(
        problem_id="test_001",
        prompt="Write a function that returns the sum of two numbers.",
        canonical_solution="def add(a, b): return a + b",
        test_list=["assert add(1, 2) == 3"],
    )

@patch("llm.client.LLMClient.generate")
def test_query_and_capture(mock_generate, sample_problem):
    """
    Integration test: mock LLM response and verify capture of code with metadata.
    """
    # Setup mock
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="def add(a, b):\n    return a + b"))]
    mock_generate.return_value = mock_response

    variants = generate_prompt_variants(sample_problem)
    assert len(variants) == 5

    # Query each variant (mocked)
    results = []
    for variant in variants:
        result = query_variant(variant)
        results.append(result)

    # Verify results
    assert len(results) == 5
    for i, r in enumerate(results):
        assert r.code_id is not None
        assert r.variant_id == variants[i].variant_id
        assert r.code is not None
        assert r.generation_metadata["complexity_label"] == variants[i].complexity_label
        assert r.generation_metadata["token_count"] == variants[i].token_count