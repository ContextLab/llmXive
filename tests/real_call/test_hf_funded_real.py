"""Real-call lane (spec 027, Task 21): Hugging Face as a FUNDED provider, end to end.

With Dartmouth made unreachable, each kind of task picks a Hugging Face model from the
LIVE leaderboard + router catalog, reserves budget on the production funded ledger, makes
a short real chat, and settles the real charge. This spends real money (cents) and writes
to the production funded ledger (``refs/llmxive/funded-ledger``) on the shared remote.

Spend bound: every routed call carries ``max_tokens=1024``, ``retries=1`` and
``max_credits=100`` ($0.10 reservation ceiling). Worst case for the lane: 7 billed chats
(5 profiles + JSON + vision) x $0.10 = $0.70 reserved; the wrong-bill-to router test is
refused before inference and settles at $0.00, so only a rare fail-after-send case could
add up to one further $0.10 hold per candidate tried. Typical spend is cents.

Required (a missing one FAILS the module, naming it, before any network request):
``HF_TOKEN`` (or the Keychain item), ``LLMXIVE_HF_BILL_TO``, ``LLMXIVE_FUNDED_LEDGER_ANCHOR``.
Optional: ``LLMXIVE_FUNDED_LEDGER_REMOTE`` (default ``origin``).

Only the ``huggingface`` backend is reachable: every other backend (Dartmouth AND local)
raises ``BackendUnavailable``, so no local model is ever downloaded or run.

Output discipline: model ids, token counts, dollar amounts and counts only — never a
leaderboard rating, the token, or the bill-to id.
"""

from __future__ import annotations

import os
from collections.abc import Iterable

import pytest

from llmxive.backends.base import (
    BackendUnavailable,
    BaseBackend,
    ChatMessage,
    ChatResponse,
    ImagePart,
    TextPart,
)
from llmxive.backends.hf_budget import fetch_org_balance_usd
from llmxive.backends.huggingface import (
    HFCredentialRejected,
    HuggingFaceBackend,
    PreInferenceRejection,
    fetch_router_catalog,
)
from llmxive.backends.router import CandidateDisposition, disposition_of, make_backend
from llmxive.config import repo_root
from llmxive.credentials import load_hf_token
from llmxive.librarian.data_source_discovery import _extract_json_object
from llmxive.model_selection.attempt_hooks import (
    DispatchCompleted,
    DispatchStarted,
    ReservationOpened,
)
from llmxive.model_selection.execute import ChainExhausted
from llmxive.model_selection.leaderboard import PAGE_LENGTH, fetch_arena_scores, join_scores
from llmxive.model_selection.ledger_transport import (
    FUNDED_LEDGER_REF,
    fetch_ledger,
    funded_ledger_config_from_env,
    read_events,
)
from llmxive.model_selection.policy import FUNDED_POLICY
from llmxive.model_selection.profiles import build_requirement
from llmxive.model_selection.reservations import project
from llmxive.model_selection.route import route_chat
from llmxive.model_selection.select import select
from llmxive.model_selection.snapshot import _parse_hf_catalog, runtime_snapshot
from llmxive.model_selection.strength import level_qualifiers, repo_of, track_population
from llmxive.model_selection.types import CallBudget, RequirementOverrides

from .test_vision_real import _red_square_png

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="real-call test; set LLMXIVE_REAL_TESTS=1",
)

#: Hard spend bound per routed call: 100 credits = $0.10. A mis-selection that would
#: reserve more is refused by ``select`` before any request is made.
_MAX_CREDITS = 100
_BOUND = RequirementOverrides(max_credits=_MAX_CREDITS)
_BAD_BILL_TO = "000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def _require_settings():
    """Fail (never skip) naming each missing setting — before any network request."""
    missing = [v for v in ("LLMXIVE_HF_BILL_TO", "LLMXIVE_FUNDED_LEDGER_ANCHOR") if not os.environ.get(v)]
    if not missing and not load_hf_token():  # env vars first: no Keychain lookup when already failing
        missing.append("HF_TOKEN")
    assert not missing, (
        "the real-call funded lane needs these settings and they are missing: " + ", ".join(missing)
    )


@pytest.fixture(scope="module")
def snap():
    return runtime_snapshot()


class _Down(BaseBackend):
    """A backend made unreachable (the same outage the fallback test induces)."""

    is_paid = False

    def __init__(self, name: str) -> None:
        self.name = name

    def list_models(self) -> list[str]:
        raise BackendUnavailable(f"{self.name} made unreachable for the funded lane")

    def chat(self, messages: Iterable[ChatMessage], *, model: str, max_tokens: int | None = None,
             temperature: float | None = None) -> ChatResponse:
        raise BackendUnavailable(f"{self.name} made unreachable for the funded lane")

    def healthcheck(self) -> bool:
        return False


def _dartmouth_down(name: str) -> BaseBackend:
    """Only Hugging Face is reachable: Dartmouth AND local are down, so no local model
    can be downloaded or run by this lane."""
    return make_backend(name) if name == "huggingface" else _Down(name)


class _Sink:
    """A recording ``RouteAudit``: captures THIS route's funded hold ids and which one
    completed, so the lane keys every ledger assertion to this call's own reservation."""

    def __init__(self) -> None:
        self.opened: list[str] = []
        self.completed: list[str] = []
        self._claimed: set[str] = set()

    def record(self, event) -> None:
        if isinstance(event, ReservationOpened):
            self.opened.append(event.reservation_id)
        elif isinstance(event, DispatchCompleted) and event.reservation_id:
            self.completed.append(event.reservation_id)

    def claim_dispatch(self, event: DispatchStarted) -> bool:
        if event.event_id in self._claimed:
            return False
        self._claimed.add(event.event_id)
        return True

    def dispatch_claimed(self, event: DispatchStarted) -> bool:
        return event.event_id in self._claimed


def _route(messages, sink: _Sink, **kwargs) -> ChatResponse:
    """route_chat with the lane's fixed bounds and this call's audit sink."""
    kwargs.setdefault("backend_factory", _dartmouth_down)
    kwargs.setdefault("max_tokens", 1024)
    return route_chat(
        messages, retries=1, overrides=_BOUND, route_audit=sink,
        prompt_digest="funded-lane", context_digest="funded-lane", **kwargs,
    )


def _ledger_events() -> list[dict]:
    fetch_ledger(repo_root(), funded_ledger_config_from_env())
    return read_events(repo_root(), ref=FUNDED_LEDGER_REF)


def _assert_one_bounded_settlement(r: ChatResponse, sink: _Sink) -> None:
    """THIS call's winning reservation has exactly one settlement event; its charge equals
    the response's settled cost, is within the reservation, which is within the bound."""
    assert sink.completed, "no dispatch completed for this route"
    rid = sink.completed[-1]
    events = _ledger_events()
    settlements = [e for e in events if e.get("type") == "reconciled" and e.get("reservation_id") == rid]
    assert len(settlements) == 1, f"expected one settlement for this call's reservation, found {len(settlements)}"
    s = project(events)[rid]
    assert s.model == r.model
    assert s.charged is not None and s.charged == pytest.approx(r.cost_estimate_usd)
    assert s.charged <= s.worst_case_credits + 1e-12
    assert s.worst_case_credits <= _MAX_CREDITS / 1000.0 + 1e-12
    print(f"model={r.model} in={r.input_tokens} out={r.output_tokens} "
          f"reserved=${s.worst_case_credits:.6f} charged=${s.charged:.6f}")


def test_live_catalog_and_leaderboard_parse_page_and_join():  # keyless, free
    refs, pricing, _ = _parse_hf_catalog(fetch_router_catalog())
    assert refs and all(p.input_usd_per_token is None or p.input_usd_per_token >= 0 for p in pricing.values())
    arena = fetch_arena_scores()
    assert arena is not None and set(arena) == {"reasoning", "coding"}
    assert all(len(v) > PAGE_LENGTH for v in arena.values())
    scores, ambiguous = join_scores({r.model_id.rsplit(":", 1)[0] for r in refs}, arena)
    print(f"matched reasoning={sum(s.reasoning is not None for s in scores.values())} "
          f"coding={sum(s.coding is not None for s in scores.values())} ambiguous={list(ambiguous)}")
    assert any(s.reasoning for s in scores.values()) and any(s.coding for s in scores.values())


def test_org_balance_reads_or_declines_cleanly():
    bal = fetch_org_balance_usd()
    assert bal is None or bal >= 0


_PROFILES = ["cheap_structured", "standard_generation", "deep_review", "deep_code", "independent_review"]


@pytest.mark.parametrize("profile", _PROFILES)
def test_each_profile_leader_is_the_cheapest_qualifier_at_its_level(snap, profile):  # pure, live snapshot
    req = build_requirement(profile, CallBudget(2_000, 1_024))
    chain = select(req, snap)
    funded = [c for c in chain.candidates if c.cost_class == "funded"]
    pop = track_population(
        snap.scores, req.track, today=snap.observed_at.date(),
        max_publish_age_days=FUNDED_POLICY.max_publish_age_days,
    )
    q = level_qualifiers(pop, req.strength, FUNDED_POLICY)
    assert funded and all(repo_of(c.model_ref.model_id) in q for c in funded)
    assert funded[0].worst_case_credits == min(c.worst_case_credits for c in funded)


@pytest.mark.parametrize("profile", _PROFILES)
def test_each_profile_is_served_by_hugging_face_and_spend_equals_usage_times_price(snap, profile):
    sink = _Sink()
    r = _route([ChatMessage("user", "Reply with the single word: ready")], sink, profile=profile, snapshot=snap)
    assert r.backend == "huggingface"
    # A strong reasoning model may spend all max_tokens on reasoning and return no visible
    # text; the lane is about routing and spend, so report it rather than fail on it.
    print(f"profile={profile} visible_text_empty={not r.text.strip()}")
    assert r.input_tokens and r.input_tokens > 0 and r.output_tokens and r.output_tokens > 0
    price = snap.pricing[r.model]
    expected = r.input_tokens * price.input_usd_per_token + r.output_tokens * price.output_usd_per_token
    assert r.cost_estimate_usd == pytest.approx(expected)
    _assert_one_bounded_settlement(r, sink)


def test_strict_json_probe():
    sink = _Sink()
    r = _route(
        [ChatMessage("user", 'Return only this JSON object: {"hf_funded": "ok"}.')],
        sink, profile="cheap_structured",
    )
    assert _extract_json_object(r.text) == {"hf_funded": "ok"}
    _assert_one_bounded_settlement(r, sink)


def test_vision_probe_reads_a_red_square():
    sink = _Sink()
    img = ImagePart.from_bytes("image/png", _red_square_png()[0])
    r = _route(
        [ChatMessage("user", (TextPart("What colour is this image? One word."), img))],
        sink, profile="vision",
    )
    assert r.backend == "huggingface" and "red" in r.text.lower()
    _assert_one_bounded_settlement(r, sink)


def test_wrong_bill_to_is_a_403_rejection_not_a_charge_to_another_account(snap):
    # The recorded router reply for this all-zero id is 403 "Organization or resource
    # group ... not found" (tests/fixtures/hf_funded/chat_403.json): a credential-class
    # rejection before inference, which the router skips past to the next candidate.
    model = sorted(m.model_id for m in snap.models if m.backend == "huggingface")[0]
    with pytest.raises(HFCredentialRejected) as ei:
        HuggingFaceBackend(bill_to=_BAD_BILL_TO).chat([ChatMessage("user", "hi")], model=model, max_tokens=8)
    assert isinstance(ei.value, PreInferenceRejection)
    assert disposition_of(ei.value) is CandidateDisposition.SKIP
    assert load_hf_token() not in str(ei.value)


def test_wrong_bill_to_through_the_router_is_charged_zero(snap):  # spec 5.9.2 amended, against the real ledger
    sink = _Sink()

    def bad(name: str) -> BaseBackend:
        return HuggingFaceBackend(bill_to=_BAD_BILL_TO) if name == "huggingface" else _Down(name)

    with pytest.raises(ChainExhausted):
        _route([ChatMessage("user", "hi")], sink, profile="deep_review", max_tokens=8,
               snapshot=snap, backend_factory=bad)
    assert sink.opened, "the route opened no funded hold, so nothing was exercised"
    events = _ledger_events()
    projected = project(events)
    for rid in sink.opened:  # the holds THIS route opened, and only those
        assert projected[rid].state == "reconciled" and projected[rid].charged == 0.0
        assert sum(1 for e in events if e.get("type") == "reconciled" and e.get("reservation_id") == rid) == 1
    print(f"holds opened by this route={len(sink.opened)} all settled at $0.00")
