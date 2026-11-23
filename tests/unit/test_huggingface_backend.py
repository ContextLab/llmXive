"""HuggingFaceBackend against a real local HTTP server replaying recorded router bodies."""

import json
from pathlib import Path

import pytest

from llmxive.backends.base import (
    BackendCredentialError,
    BackendUnavailable,
    ChatMessage,
    EmptyReplyError,
    PermanentBackendError,
    TransientBackendError,
)
from llmxive.backends.huggingface import (
    HFCredentialRejected,
    HFPaymentRequired,
    HuggingFaceBackend,
    PreInferenceRejection,
    fetch_router_catalog,
)
from llmxive.backends.router import make_backend
from llmxive.types import BackendName
from tests.helpers.replay_server import ReplayServer

_FIX = Path(__file__).parents[1] / "fixtures" / "hf_funded"


def _load(name):
    return json.loads((_FIX / name).read_text())


M = "acme/alpha-large:prov-a"
MSG = [ChatMessage("user", "hi")]
OK = (200, _load("chat_200.json")["payload"])
PAY = (402, _load("chat_402.json")["payload"])


def _be(srv, **kw):
    return HuggingFaceBackend(token="hf_t", bill_to="grp123", base_url=srv.base_url, **kw)


def test_chat_sends_pinned_provider_and_bill_to():
    with ReplayServer({("POST", "/chat/completions"): [OK]}) as srv:
        r = _be(srv).chat(MSG, model=M, max_tokens=64, temperature=0.0)
    req = srv.requests[0]
    assert req["headers"]["x-hf-bill-to"] == "grp123" and req["headers"]["authorization"] == "Bearer hf_t"
    assert req["json"]["model"] == M and req["json"]["max_tokens"] == 64 and req["json"]["stream"] is False
    assert r.backend == "huggingface" and r.model == M and r.text == "ok"
    assert (r.input_tokens, r.output_tokens) == (OK[1]["usage"]["prompt_tokens"], OK[1]["usage"]["completion_tokens"])


@pytest.mark.parametrize(
    "status,exc,pre",
    [
        (402, HFPaymentRequired, True),
        (401, HFCredentialRejected, True),
        (403, HFCredentialRejected, True),
        (429, TransientBackendError, False),
        (503, TransientBackendError, False),
        (400, PermanentBackendError, False),
    ],
)
def test_status_mapping(status, exc, pre):
    body = PAY[1] if status == 402 else {"error": "x"}
    with ReplayServer({("POST", "/chat/completions"): [(status, body)]}) as srv:
        with pytest.raises(exc) as ei:
            _be(srv).chat(MSG, model=M)
    assert isinstance(ei.value, PreInferenceRejection) is pre
    assert isinstance(HFPaymentRequired("x"), BackendUnavailable)
    assert isinstance(HFCredentialRejected("x", http_status=401), BackendCredentialError)
    assert len(srv.requests) == 1  # exactly one attempt, no hidden retry


def test_recorded_403_and_object_error_bodies_are_parsed():
    obj = (400, {"error": {"message": "bad thing", "type": "invalid"}})
    with ReplayServer({("POST", "/chat/completions"): [(403, _load("chat_403.json")["payload"]), obj]}) as srv:
        with pytest.raises(HFCredentialRejected, match="not found") as e403:
            _be(srv).chat(MSG, model=M)
        with pytest.raises(PermanentBackendError, match="bad thing"):
            _be(srv).chat(MSG, model=M)
    assert e403.value.http_status == 403


def test_missing_bill_to_or_token_fails_closed_without_a_request(monkeypatch):
    monkeypatch.delenv("LLMXIVE_HF_BILL_TO", raising=False)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with ReplayServer({}) as srv:
        with pytest.raises(HFCredentialRejected, match="LLMXIVE_HF_BILL_TO") as ei:
            HuggingFaceBackend(token="hf_t", base_url=srv.base_url).chat(MSG, model=M)
    assert ei.value.http_status is None and srv.requests == []


def test_empty_reply_is_transient_and_length_is_budget_exhaustion():
    def empty(fr):
        return (200, {"choices": [{"message": {"content": ""}, "finish_reason": fr}], "usage": {}})

    with ReplayServer({("POST", "/chat/completions"): [empty("stop"), empty("length")]}) as srv:
        with pytest.raises(EmptyReplyError):
            _be(srv).chat(MSG, model=M)
        with pytest.raises(TransientBackendError, match="reasoning budget exhausted"):
            _be(srv).chat(MSG, model=M)


def test_token_never_appears_in_an_error():
    with ReplayServer({("POST", "/chat/completions"): [(500, {"error": "boom hf_t grp123"})]}) as srv:
        with pytest.raises(TransientBackendError) as ei:
            _be(srv).chat(MSG, model=M)
    assert "hf_t" not in str(ei.value) and "grp123" not in str(ei.value)


def test_catalog_fetch_is_keyless_and_replay_records_query():
    with ReplayServer({("GET", "/models"): lambda req: (200, {"data": [], "echo": req["query"]})}) as srv:
        assert fetch_router_catalog(base_url=srv.base_url)["data"] == []
    assert "authorization" not in srv.requests[0]["headers"] and srv.requests[0]["json"] is None


def test_list_models_and_healthcheck_use_the_catalog():
    cat = (200, {"data": [{"id": "acme/alpha-large"}, {"id": "acme/beta"}, {"nope": 1}]})
    with ReplayServer({("GET", "/models"): [cat]}) as srv:
        be = _be(srv)
        assert be.list_models() == ["acme/alpha-large", "acme/beta"]
        assert be.healthcheck() is True


def test_registered_and_named():
    assert isinstance(make_backend("huggingface"), HuggingFaceBackend)
    assert BackendName("huggingface") is BackendName.HUGGINGFACE


@pytest.mark.parametrize(
    "status,exc",
    [(402, HFPaymentRequired), (403, HFCredentialRejected), (408, TransientBackendError),
     (500, TransientBackendError), (400, PermanentBackendError)],
)
def test_non_json_error_body_keeps_the_status_class(status, exc):
    with ReplayServer({("POST", "/chat/completions"): [(status, b"<html>gateway page</html>")]}) as srv:
        with pytest.raises(exc):
            _be(srv).chat(MSG, model=M)


def test_missing_token_alone_fails_closed_without_a_request(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setattr("llmxive.backends.huggingface.load_hf_token", lambda: None)
    with ReplayServer({}) as srv:
        with pytest.raises(HFCredentialRejected, match="HF_TOKEN") as ei:
            HuggingFaceBackend(bill_to="grp123", base_url=srv.base_url).chat(MSG, model=M)
    assert ei.value.http_status is None and srv.requests == []


@pytest.mark.parametrize(
    "body",
    [
        {"choices": ["not-a-dict"]},
        {"choices": [{"message": {"content": 5}}]},
        {"choices": [{"message": "str"}]},
        {"choices": []},
        {"no": "choices"},
    ],
)
def test_malformed_200_is_a_typed_transient_error(body):
    with ReplayServer({("POST", "/chat/completions"): [(200, body)]}) as srv:
        with pytest.raises(TransientBackendError, match="malformed 200"):
            _be(srv).chat(MSG, model=M)


def test_list_of_parts_content_joins_text_parts():
    parts = [{"type": "text", "text": "he"}, {"type": "image_url"}, {"type": "text", "text": "llo"}]
    body = {"choices": [{"message": {"content": parts}, "finish_reason": "stop"}], "usage": {}}
    with ReplayServer({("POST", "/chat/completions"): [(200, body)]}) as srv:
        assert _be(srv).chat(MSG, model=M).text == "hello"


def test_token_and_bill_to_are_stripped():
    with ReplayServer({("POST", "/chat/completions"): [OK]}) as srv:
        HuggingFaceBackend(token="hf_t\n", bill_to=" grp123\n", base_url=srv.base_url).chat(MSG, model=M)
    h = srv.requests[0]["headers"]
    assert h["authorization"] == "Bearer hf_t" and h["x-hf-bill-to"] == "grp123"


def test_make_backend_keeps_the_breaker_across_calls(monkeypatch):
    """A1: the per-model breaker must persist across ``make_backend`` calls, or an
    outage re-sends (and re-reserves) on every agent call. Failures are recorded
    through the first instance's real breaker; the second instance must refuse."""
    monkeypatch.setenv("HF_TOKEN", "hf_breaker_test")
    monkeypatch.setenv("LLMXIVE_HF_BILL_TO", "grp_breaker_test")
    model = "breaker-test/a1-persist:prov-z"

    def _fail():
        raise TransientBackendError("simulated outage via the real breaker")

    first = make_backend("huggingface")
    for _ in range(3):
        with pytest.raises(TransientBackendError):
            first._breaker(model).call(_fail)

    ran = []
    second = make_backend("huggingface")
    with pytest.raises(BackendUnavailable, match="circuit open"):
        second._breaker(model).call(lambda: ran.append(1))
    assert ran == []
    # Different credentials get their own breaker history.
    monkeypatch.setenv("LLMXIVE_HF_BILL_TO", "grp_breaker_other")
    make_backend("huggingface")._breaker(model).call(lambda: ran.append(1))
    assert ran == [1]
