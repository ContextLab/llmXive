"""
Unit tests for the style scoring logic implemented in ``code/01_style_scoring.py``.

The tests verify:
1. The module provides a ``compute_style_score`` callable.
2. The callable returns a dictionary containing the expected metric keys.
3. All numeric scores are normalised to the range ``0.0`` – ``1.0``.
4. The composite score lies between the individual metric scores, confirming a
   simple aggregation (e.g., average) without assuming a specific weighting scheme.

The test suite purposefully avoids hard‑coding exact numeric expectations
because the concrete scoring algorithm will be defined in a later implementation
task (T013). The assertions focus on contract‑level properties that should hold
for any reasonable normalised scoring function.
"""

import importlib.util
import pathlib
import tempfile
import pytest


def load_style_scoring_module():
    """
    Dynamically load ``code/01_style_scoring.py`` as a module named ``style_scoring``.

    The file name starts with a digit, which is not a valid Python identifier,
    so we use ``importlib.util`` to load it from its absolute path.
    """
    # Resolve the absolute path to the target module
    module_path = (
        pathlib.Path(__file__)
        .resolve()
        .parents[2]               # Move from tests/unit/ to project root
        / "code"
        / "01_style_scoring.py"
    )
    if not module_path.is_file():
        pytest.fail(f"Expected module not found at {module_path}")

    spec = importlib.util.spec_from_file_location("style_scoring", module_path)
    if spec is None or spec.loader is None:
        pytest.fail("Failed to create import spec for style_scoring module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


@pytest.fixture(scope="module")
def style_scoring():
    """Load the style scoring module once per test session."""
    return load_style_scoring_module()


def test_compute_style_score_exists(style_scoring):
    """The module must expose a ``compute_style_score`` callable."""
    assert hasattr(style_scoring, "compute_style_score"), (
        "code/01_style_scoring.py must define a function named "
        "`compute_style_score(file_path: str) -> dict`"
    )
    assert callable(style_scoring.compute_style_score)


def test_score_range_and_aggregation(style_scoring):
    """
    Verify that the scoring function returns normalised scores and that the
    composite score is an aggregation of the individual metric scores.
    """
    # Create a minimal, syntactically correct Python file for analysis
    sample_code = "def hello():\n    return 'world'\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp_file:
        tmp_file.write(sample_code)
        tmp_path = pathlib.Path(tmp_file.name)

    # Run the scoring function
    result = style_scoring.compute_style_score(str(tmp_path))

    # Clean up the temporary file
    tmp_path.unlink()

    # Basic contract checks
    assert isinstance(result, dict), "Result should be a dictionary"

    # Expected metric keys (the implementation may add more)
    expected_keys = {"pylint_indent", "radon_line_len", "composite_score"}
    missing = expected_keys - result.keys()
    assert not missing, f"Missing expected keys in result: {missing}"

    # All scores must be floats in the [0.0, 1.0] interval
    for key in expected_keys:
        value = result[key]
        assert isinstance(value, float), f"{key} should be a float"
        assert 0.0 <= value <= 1.0, f"{key}={value} out of expected range [0.0, 1.0]"

    # The composite score should lie between the individual metric scores
    metric_vals = [result["pylint_indent"], result["radon_line_len"]]
    comp = result["composite_score"]
    assert min(metric_vals) <= comp <= max(metric_vals), (
        "Composite score should be bounded by the individual metric scores"
    )