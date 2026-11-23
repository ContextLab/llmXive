import pytest
from models.data_models import HumanEvalProblem
from prompts.generator import generate_prompt_variants

@pytest.fixture
def sample_problem():
    return HumanEvalProblem(
        problem_id="test_001",
        prompt="Write a function that returns the sum of two numbers.",
        canonical_solution="def add(a, b): return a + b",
        test_list=["assert add(1, 2) == 3"],
    )

def test_generates_5_variants(sample_problem):
    """
    Contract test: ensure exactly 5 variants are generated with correct labels.
    """
    variants = generate_prompt_variants(sample_problem)
    assert len(variants) == 5

    labels = [v.complexity_label for v in variants]
    expected_labels = ['simple', 'moderate', 'complex', 'very_complex', 'degenerate']
    assert all(label in expected_labels for label in labels)
    assert set(labels) == set(expected_labels)

def test_variants_have_metadata(sample_problem):
    """
    Ensure each variant has computed metadata (token_count, structural_element_count, dependency_depth).
    """
    variants = generate_prompt_variants(sample_problem)
    for v in variants:
        assert v.token_count > 0
        assert v.structural_element_count.examples >= 0
        assert v.structural_element_count.constraints >= 0
        assert v.structural_element_count.steps >= 0
        assert v.dependency_depth > 0
        assert v.variant_id.startswith(sample_problem.problem_id)
