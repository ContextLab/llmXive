"""The recovery probe against LIVE free Dartmouth models.

The unit suite drives the breaker's decision with an injected callable; this
one makes the genuine bounded request, because the whole point of the probe is
that a real free model answers it in seconds rather than in a full request
deadline. Gated by ``LLMXIVE_REAL_TESTS=1`` like every real-call test.
"""

from __future__ import annotations

import time

import pytest

from llmxive.backends import dartmouth as dm

#: Every FREE model the pipeline currently routes to. Re-verified live on
#: 2026-10-10; a retired id must fail this test rather than silently become a
#: permanently-open circuit.
FREE_MODELS = [
    "openai.gpt-oss-120b",
    "zai-org.glm-5.3",
    "qwen.qwen3.5-122b",
    "google.gemma-4-31B-it",
]


@pytest.fixture(scope="module")
def backend():
    from llmxive.credentials import load_dartmouth_key

    if not load_dartmouth_key():
        pytest.skip("no Dartmouth credential available")
    return dm.DartmouthBackend()


@pytest.mark.parametrize("model", FREE_MODELS)
def test_a_live_free_model_answers_the_probe_quickly(backend, model):
    started = time.monotonic()
    verdict = backend._liveness_ok(model)
    elapsed = time.monotonic() - started

    assert verdict is True, f"{model} did not answer a bounded liveness probe"
    # The probe exists to be cheap: it must come back far inside its own
    # deadline, and nowhere near a full request budget.
    assert elapsed < dm._LIVENESS_DEADLINE_S, f"{model} took {elapsed:.1f}s"


@pytest.mark.parametrize("model", FREE_MODELS)
def test_every_routed_model_is_still_classified_free(model):
    """A retired id fails HERE, loudly.

    ``_liveness_ok`` returns ``None`` for anything not classified free, so a
    model that quietly leaves the catalog would stop being probed cheaply and
    its circuit would go back to costing a full request per cooldown. This
    asserts the live classification rather than a hardcoded allowlist.
    """
    assert dm.is_free_model(model) is True, f"{model} is no longer a free model"


def test_an_unlisted_model_is_not_pinged(backend):
    """Not known free -> no verdict, no spend.

    A typo'd or retired id is neither free nor billable, but the classifier
    cannot tell it from a paid model, so the probe declines to ask and the
    breaker keeps its original probe-with-the-real-request behavior.
    """
    assert backend._liveness_ok("openai.gpt-oss-120b-retired-does-not-exist") is None
