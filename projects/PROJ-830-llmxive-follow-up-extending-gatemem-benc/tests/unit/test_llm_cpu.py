"""
Unit test verifying that the LLM backbone runs on CPU‑only and can perform
a minimal inference using the 2.7 B int8 Llama‑3 model.
"""

import pytest

from utils.config import get_llm_singleton


@pytest.mark.timeout(120)
def test_llm_cpu_runs():
    """
    The test obtains the singleton LLM, checks that it reports a CPU
    device, runs a tiny generation, and asserts that the output is a
    non‑empty string.
    """
    llm = get_llm_singleton()

    # Verify that the wrapper reports CPU execution.
    assert getattr(llm, "device", None) == "cpu", "LLM is not running on CPU"

    # Perform a minimal inference; the prompt is deliberately short.
    output = llm.generate("Hello, LLM!")

    # The output should be a string containing the original prompt.
    assert isinstance(output, str)
    assert "Hello, LLM!" in output
    # Ensure the generation added at least one additional token.
    assert len(output.strip().split()) > 2, "Generation produced no additional tokens"