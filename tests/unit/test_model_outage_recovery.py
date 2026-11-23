"""Cross-call outage memory and bounded recovery through the production router."""
import threading
from collections import Counter
from types import SimpleNamespace

import pytest

from llmxive.backends import dartmouth as dm
from llmxive.backends import router
from llmxive.backends.base import (
    BackendUnavailable,
    ChatMessage,
    ModelDownError,
    TransientBackendError,
)


@pytest.fixture(autouse=True)
def isolated_backend_cache(monkeypatch):
    # The deadline tests reload dartmouth to exercise environment defaults.
    monkeypatch.setattr(router, "DartmouthBackend", dm.DartmouthBackend)
    monkeypatch.setitem(router._REGISTRY, "dartmouth", dm.DartmouthBackend)
    router._dartmouth_backend.cache_clear()
    yield
    router._dartmouth_backend.cache_clear()


def test_independent_router_calls_share_outage_and_recover(monkeypatch):
    monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "outage-test-credential")
    # The chat-time free-first guard reads the tri-state pricing verdict (spec 026).
    monkeypatch.setattr(dm, "model_pricing_verdict", lambda _: dm.PricingVerdict.FREE)
    clock = [0.0]
    monkeypatch.setattr(dm.DartmouthBackend, "_new_breaker",
                        lambda _: dm._CircuitBreaker(clock=lambda: clock[0], cooldown_s=60))
    calls = Counter()
    primary = "zai-org.glm-5.3"
    peer = "qwen.qwen3.5-122b"  # next in the selector's free chain (offline snapshot)
    recovered = [False]

    class Client:
        def __init__(self, model):
            self.model = model

        def invoke(self, *args, **kwargs):
            calls[self.model] += 1
            if self.model == primary and not recovered[0]:
                raise ModelDownError("deadline exceeded")
            return SimpleNamespace(content="verified reply", response_metadata={"finish_reason": "stop"},
                                   additional_kwargs={})

    monkeypatch.setattr(dm.DartmouthBackend, "_client", lambda _, model: Client(model))
    messages = [ChatMessage(role="user", content="test")]

    def call():
        # Spec 026: the chain (primary, then its free peers) is the selector's.
        return router.chat_with_fallback(messages, profile="deep_review")

    assert call().model == peer
    assert call().model == peer
    assert calls == {primary: 1, peer: 2}
    # One failed recovery probe, followed by immediate fallback without re-probing.
    clock[0] = 61
    assert call().model == peer
    assert call().model == peer
    assert calls[primary] == 2
    recovered[0] = True
    # Two real requests were lost with no answer in between, so the circuit
    # waits two cooldowns (120 s) after the second loss, not one.
    clock[0] = 122
    assert call().model == peer
    assert calls[primary] == 2
    clock[0] = 182
    assert call().model == primary
    assert call().model == primary
    assert calls[primary] == 4


def test_backend_cache_isolated_by_credentials_and_endpoint(monkeypatch):
    endpoint = ["https://first.example/api/models"]
    monkeypatch.setattr(dm, "_cloud_models_url", lambda: endpoint[0])
    monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "credential-one")
    first = router.make_backend("dartmouth")
    assert router.make_backend("dartmouth") is first
    monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "credential-two")
    second = router.make_backend("dartmouth")
    assert second is not first
    endpoint[0] = "https://second.example/api/models"
    assert router.make_backend("dartmouth") is not second
    monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "credential-one")
    endpoint[0] = "https://first.example/api/models"
    assert router.make_backend("dartmouth") is first


def test_only_one_recovery_probe_runs_at_a_time():
    clock = [0.0]
    breaker = dm._CircuitBreaker(max_consecutive=1, cooldown_s=10, clock=lambda: clock[0])
    with pytest.raises(TransientBackendError):
        breaker.call(lambda: (_ for _ in ()).throw(TransientBackendError("down")))
    clock[0] = 11
    entered = threading.Event()
    release = threading.Event()
    results = []

    def probe():
        entered.set()
        assert release.wait(timeout=5)
        return "recovered"

    worker = threading.Thread(target=lambda: results.append(breaker.call(probe)))
    worker.start()
    try:
        assert entered.wait(timeout=5)
        with pytest.raises(BackendUnavailable):
            breaker.call(lambda: pytest.fail("concurrent recovery request"))
    finally:
        release.set()
        worker.join(timeout=5)
    assert results == ["recovered"]
    assert breaker.call(lambda: "healthy") == "healthy"
