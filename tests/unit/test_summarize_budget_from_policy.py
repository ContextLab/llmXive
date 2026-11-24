"""_MODEL_BUDGETS was a second, drifting copy of per-model context limits."""
from __future__ import annotations

from llmxive.model_selection.policy import CAPABILITY_POLICY
from llmxive.tools.summarize import DEFAULT_MODEL_BUDGET, usable_budget_for


def test_budget_comes_from_the_capability_policy():
    assert usable_budget_for("openai.gpt-oss-120b") <= CAPABILITY_POLICY.max_context_tokens(
        "gpt-oss"
    )
    assert usable_budget_for("qwen.qwen3.5-122b") <= CAPABILITY_POLICY.max_context_tokens(
        "qwen3.5"
    )


def test_unknown_model_falls_back_conservatively():
    assert usable_budget_for("not.a-real-model") > 0


def test_old_model_budgets_values_are_preserved_via_policy():
    """Equivalence proof, not an assumption: the deleted ``_MODEL_BUDGETS`` table
    covered exactly two models, both pinned at 128_000 (== ``DEFAULT_MODEL_BUDGET``
    at the time). The policy-derived path must reproduce the same final
    (margin-applied) budget for both, even though it reaches that number by two
    different routes: ``openai.gpt-oss-120b`` resolves to the ``gpt-oss`` policy
    family (128_000), while ``meta.llama-3.2-11b-vision-instruct`` has no policy
    family and falls back to ``DEFAULT_MODEL_BUDGET`` (also 128_000) — the same
    fallback the old table's ``dict.get(..., DEFAULT_MODEL_BUDGET)`` used.
    """
    old_model_budgets = {
        "openai.gpt-oss-120b": 128_000,
        "meta.llama-3.2-11b-vision-instruct": 128_000,
    }
    for model_id, old_raw in old_model_budgets.items():
        expected = max(1, int(old_raw * 0.75))  # old COMPLETION_RESERVE margin
        assert usable_budget_for(model_id) == expected
    assert DEFAULT_MODEL_BUDGET == 128_000
