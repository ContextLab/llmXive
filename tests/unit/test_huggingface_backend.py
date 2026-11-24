"""HuggingFaceBackend against a real local HTTP server replaying recorded router bodies."""

import json
import threading
import time
from pathlib import Path

import pytest

from llmxive.backends.base import (
    BackendCredentialError,
    BackendUnavailable,
    ChatMessage,
    DeadlineExceededError,
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
    request_was_sent,
)
from llmxive.backends.router import make_backend
from llmxive.types import BackendName
from tests.helpers.replay_server import ReplayServer, Stream

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
    assert req["json"]["model"] == M and req["json"]["max_tokens"] == 64 and req["json"]["stream"] is True
    assert req["json"]["stream_options"] == {"include_usage": True}
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


# The router's reply when the pinned provider cannot serve THIS request (seen live
# 2026-11-23 for an image request to a provider that served the same model's text
# calls). Provider names here are placeholders.
_NO_PROVIDER_404 = {"error": "No allowed providers are available for the selected model. "
                             "Providers serving acme/alpha-large: prov-b, prov-c"}


def test_router_404_is_route_unavailable_and_advances_the_chain():
    from llmxive.backends.huggingface import HFRouteUnavailable
    from llmxive.backends.router import CandidateDisposition, disposition_of

    with ReplayServer({("POST", "/chat/completions"): [(404, _NO_PROVIDER_404)]}) as srv:
        with pytest.raises(HFRouteUnavailable, match="No allowed providers") as ei:
            _be(srv).chat(MSG, model=M)
    assert isinstance(ei.value, BackendUnavailable)          # the unavailable-backend class
    assert not isinstance(ei.value, PreInferenceRejection)   # owner rule: not a zero-charge rejection
    assert disposition_of(ei.value) is CandidateDisposition.RETRY_ADVANCE
    assert len(srv.requests) == 1


@pytest.mark.parametrize("status", [400, 422])
def test_malformed_request_stays_permanent_and_aborts(status):
    from llmxive.backends.huggingface import HFRouteUnavailable
    from llmxive.backends.router import CandidateDisposition, disposition_of

    with ReplayServer({("POST", "/chat/completions"): [(status, {"error": "bad request"})]}) as srv:
        with pytest.raises(PermanentBackendError) as ei:
            _be(srv).chat(MSG, model=M)
    assert not isinstance(ei.value, (HFRouteUnavailable, BackendUnavailable))
    assert disposition_of(ei.value) is CandidateDisposition.ABORT


def test_route_unavailable_does_not_trip_the_model_breaker():
    """A pair that cannot serve image input still serves text: repeated 404s must not
    open the per-model breaker that its text calls share."""
    from llmxive.backends.huggingface import HFRouteUnavailable

    script = [(404, _NO_PROVIDER_404)] * 4 + [OK]
    with ReplayServer({("POST", "/chat/completions"): script}) as srv:
        be = _be(srv)
        for _ in range(4):
            with pytest.raises(HFRouteUnavailable):
                be.chat(MSG, model=M)
        assert be.chat(MSG, model=M).text == "ok"
    assert len(srv.requests) == 5


def test_breaker_creation_is_race_free_under_threads():
    """Concurrent first use of one model id must yield ONE breaker, so no recorded
    failure is lost on a breaker that was then replaced. Against the old
    check-then-set code this fails within the 200 rounds."""
    import sys
    import threading

    be = HuggingFaceBackend(token="hf_t", bill_to="grp123")
    model = "race/one:prov-a"

    def one_round() -> bool:
        be._breakers.clear()
        barrier, got = threading.Barrier(16), []
        lock = threading.Lock()

        def worker():
            barrier.wait()
            br = be._breaker(model)
            with lock:
                got.append(br)

        threads = [threading.Thread(target=worker) for _ in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return len({id(b) for b in got}) == 1 and be._breakers[model] is got[0]

    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)  # switch threads as often as possible to expose the race
    try:
        rounds = [one_round() for _ in range(200)]
    finally:
        sys.setswitchinterval(old)
    assert all(rounds), f"{rounds.count(False)} of {len(rounds)} rounds built more than one breaker"


# --- streamed replies (long generations) ------------------------------------------
# The router streams server-sent events when asked (``stream: true``); with
# ``stream_options.include_usage`` an extra chunk with empty ``choices`` carries the
# whole request's usage just before ``data: [DONE]``. Long code-writing replies took
# longer than the old fixed total deadline, so the deadline now bounds SILENCE.

def _delta(text=None, *, finish=None, reasoning=None):
    d = {}
    if text is not None:
        d["content"] = text
    if reasoning is not None:
        d["reasoning_content"] = reasoning
    return Stream.sse({"choices": [{"index": 0, "delta": d, "finish_reason": finish}], "usage": None})


_USAGE = Stream.sse({"choices": [], "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18}})
_DONE = Stream.sse("[DONE]")


def test_slow_stream_longer_than_the_deadline_succeeds_with_usage():
    """Data keeps arriving, so a reply that takes ~4x the deadline completes."""
    parts = [_delta(reasoning="thinking ")]
    for i in range(10):
        parts += [0.25, _delta(f"w{i} ")]
    parts += [_delta("", finish="stop"), _USAGE, _DONE]
    with ReplayServer({("POST", "/chat/completions"): [(200, Stream(parts))]}) as srv:
        t = time.monotonic()
        r = _be(srv).chat(MSG, model=M, deadline_s=0.6)
        elapsed = time.monotonic() - t
    assert elapsed > 2.0  # really did outlast the 0.6 s deadline
    assert r.text == "".join(f"w{i} " for i in range(10))
    assert (r.input_tokens, r.output_tokens) == (11, 7)
    assert srv.requests[0]["json"]["stream"] is True


def test_stream_that_goes_silent_times_out_and_is_abandoned():
    s = Stream([_delta("a"), 3.0] + [_delta("b"), 0.05] * 40)
    with ReplayServer({("POST", "/chat/completions"): [(200, s)]}) as srv:
        t = time.monotonic()
        with pytest.raises(DeadlineExceededError, match="went silent") as ei:
            _be(srv).chat(MSG, model=M, deadline_s=0.5)
        assert time.monotonic() - t < 2.0
        assert s.disconnected.wait(10)  # the abandoned worker stopped reading and closed
    assert request_was_sent(ei.value)


def test_silent_server_still_times_out_before_any_data():
    release = threading.Event()

    def hang(req):
        release.wait(10)
        return OK

    with ReplayServer({("POST", "/chat/completions"): hang}) as srv:
        try:
            with pytest.raises(DeadlineExceededError, match="no response received"):
                _be(srv).chat(MSG, model=M, deadline_s=0.5)
        finally:
            release.set()


def test_stream_past_the_total_deadline_is_stopped(monkeypatch):
    monkeypatch.setenv("LLMXIVE_HF_TOTAL_DEADLINE_S", "1.0")
    s = Stream([_delta("x"), 0.1] * 60)
    with ReplayServer({("POST", "/chat/completions"): [(200, s)]}) as srv:
        t = time.monotonic()
        with pytest.raises(DeadlineExceededError, match="total deadline"):
            _be(srv).chat(MSG, model=M, deadline_s=0.5)
        assert time.monotonic() - t < 2.5
        assert s.disconnected.wait(10)


def test_stream_without_usage_reports_none_so_the_ledger_charges_the_hold():
    s = Stream([_delta("hi"), _delta(None, finish="stop"), _DONE])
    with ReplayServer({("POST", "/chat/completions"): [(200, s)]}) as srv:
        r = _be(srv).chat(MSG, model=M)
    assert r.text == "hi" and (r.input_tokens, r.output_tokens) == (None, None)


def test_truncated_stream_is_transient_not_a_partial_reply():
    s = Stream([_delta("half a rep")])  # connection closes: no finish_reason, no [DONE]
    with ReplayServer({("POST", "/chat/completions"): [(200, s)]}) as srv:
        with pytest.raises(TransientBackendError, match="ended before"):
            _be(srv).chat(MSG, model=M)


def test_error_event_inside_a_stream_is_transient_and_secret_free():
    s = Stream([_delta("a"), Stream.sse({"error": {"message": "upstream overloaded hf_t grp123"}})])
    with ReplayServer({("POST", "/chat/completions"): [(200, s)]}) as srv:
        with pytest.raises(TransientBackendError, match="upstream overloaded") as ei:
            _be(srv).chat(MSG, model=M)
    assert "hf_t" not in str(ei.value) and "grp123" not in str(ei.value)


def test_streamed_empty_reply_keeps_the_empty_and_length_classes():
    def empty(fr):
        return (200, Stream([_delta(reasoning="hmm"), _delta(None, finish=fr), _USAGE, _DONE]))

    with ReplayServer({("POST", "/chat/completions"): [empty("stop"), empty("length")]}) as srv:
        with pytest.raises(EmptyReplyError):
            _be(srv).chat(MSG, model=M)
        with pytest.raises(TransientBackendError, match="reasoning budget exhausted"):
            _be(srv).chat(MSG, model=M)


def test_malformed_stream_chunk_is_a_typed_transient_error():
    s = Stream([b"data: {not json\n\n"])
    with ReplayServer({("POST", "/chat/completions"): [(200, s)]}) as srv:
        with pytest.raises(TransientBackendError, match="malformed stream"):
            _be(srv).chat(MSG, model=M)


def test_recorded_router_stream_replays():
    """A real router SSE body (scripts/hf/capture_fixtures.py), replayed byte for byte."""
    fx = _load("chat_stream_200.json")
    raw = fx["payload_sse"].encode()
    with ReplayServer({("POST", "/chat/completions"): [(200, Stream([raw]))]}) as srv:
        r = _be(srv).chat(MSG, model=M)
    assert r.text.strip() == fx["expected_text"]
    assert (r.input_tokens, r.output_tokens) == (fx["expected_usage"]["prompt_tokens"],
                                                 fx["expected_usage"]["completion_tokens"])


def test_error_text_removes_a_secret_that_straddles_the_length_limit() -> None:
    """Shortening before redaction would leave the first part of the secret."""
    import httpx

    from llmxive.backends import huggingface as hf

    secret = "hf_" + "s3cr3t" * 6
    pad = "x" * (hf._MAX_ERROR_CHARS - 5)
    resp = httpx.Response(500, json={"error": {"message": f"{pad}{secret} tail"}})
    text = hf._error_text(resp, (secret,))
    assert secret[:8] not in text
    assert len(text) <= hf._MAX_ERROR_CHARS
    assert hf._safe_error_text(f"{pad}{secret}", (secret,)) == pad + "<reda"
