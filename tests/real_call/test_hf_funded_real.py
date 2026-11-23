"""Real-call lane (spec 027, Task 21): Hugging Face as a FUNDED provider, end to end.

With Dartmouth made unreachable, each kind of task picks a Hugging Face model from the
LIVE leaderboard + router catalog, reserves budget on the production funded ledger, makes
a short real chat, and settles the real charge. This spends real money (cents) and writes
to the production funded ledger (``refs/llmxive/funded-ledger``) on the shared remote.

Required (a missing one FAILS the module, naming it, before any network request):
``HF_TOKEN`` (or the Keychain item), ``LLMXIVE_HF_BILL_TO``, ``LLMXIVE_FUNDED_LEDGER_ANCHOR``.
Optional: ``LLMXIVE_FUNDED_LEDGER_REMOTE`` (default ``origin``).

Output discipline: model ids, token counts, dollar amounts and counts only — never a
leaderboard rating, the token, or the bill-to id.
"""

from __future__ import annotations

import json
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
    HFPaymentRequired,
    HuggingFaceBackend,
    PreInferenceRejection,
    fetch_router_catalog,
)
from llmxive.backends.router import CandidateDisposition, disposition_of, make_backend
from llmxive.config import repo_root
from llmxive.credentials import load_hf_token
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

#: Hard spend bound per routed call: 50 credits = $0.05. A mis-selection that would
#: reserve more is refused by ``select`` before any request is made.
_MAX_CREDITS = 50
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


class _DartmouthDown(BaseBackend):
    """Dartmouth made unreachable (the same outage the fallback test induces)."""

    name = "dartmouth"
    is_paid = False

    def list_models(self) -> list[str]:
        raise BackendUnavailable("dartmouth made unreachable for the funded lane")

    def chat(self, messages: Iterable[ChatMessage], *, model: str, max_tokens: int | None = None,
             temperature: float | None = None) -> ChatResponse:
        raise BackendUnavailable("dartmouth made unreachable for the funded lane")

    def healthcheck(self) -> bool:
        return False


def _dartmouth_down(name: str) -> BaseBackend:
    return _DartmouthDown() if name == "dartmouth" else make_backend(name)


def _ledger_events() -> list[dict]:
    fetch_ledger(repo_root(), funded_ledger_config_from_env())
    return read_events(repo_root(), ref=FUNDED_LEDGER_REF)


def _reconciled_events() -> list[dict]:
    return [e for e in _ledger_events() if e.get("type") == "reconciled"]


def _reconciled_ids() -> set[str]:
    return {e["reservation_id"] for e in _reconciled_events()}


def _new_settlements(before: set[str]) -> list:
    """Projected reservations settled since ``before`` (each carries model, reserved
    amount and charge)."""
    events = _ledger_events()
    settled = {e["reservation_id"] for e in events if e.get("type") == "reconciled"} - before
    projected = project(events)
    return [projected[rid] for rid in sorted(settled)]


def _assert_one_bounded_settlement(r: ChatResponse, before: set[str]) -> None:
    """Exactly one new settlement is for the model that answered; its charge equals the
    response's settled cost and is within the reservation, which is within the bound."""
    mine = [s for s in _new_settlements(before) if s.model == r.model]
    assert len(mine) == 1, f"expected one new settlement for {r.model}, found {len(mine)}"
    s = mine[0]
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
    before = _reconciled_ids()
    r = route_chat(
        [ChatMessage("user", "Reply with the single word: ready")], profile=profile,
        max_tokens=1024, retries=1, snapshot=snap, backend_factory=_dartmouth_down, overrides=_BOUND,
    )
    assert r.backend == "huggingface" and r.text.strip()
    price = snap.pricing[r.model]
    expected = r.input_tokens * price.input_usd_per_token + r.output_tokens * price.output_usd_per_token
    assert r.cost_estimate_usd == pytest.approx(expected)
    _assert_one_bounded_settlement(r, before)


def test_strict_json_probe():
    before = _reconciled_ids()
    r = route_chat(
        [ChatMessage("user", 'Return only this JSON object: {"hf_funded": "ok"}.')],
        profile="cheap_structured", max_tokens=1024, retries=1,
        backend_factory=_dartmouth_down, overrides=_BOUND,
    )
    assert json.loads(r.text) == {"hf_funded": "ok"}
    _assert_one_bounded_settlement(r, before)


def test_vision_probe_reads_a_red_square():
    before = _reconciled_ids()
    img = ImagePart.from_bytes("image/png", _red_square_png()[0])
    r = route_chat(
        [ChatMessage("user", (TextPart("What colour is this image? One word."), img))],
        profile="vision", max_tokens=1024, retries=1,
        backend_factory=_dartmouth_down, overrides=_BOUND,
    )
    assert r.backend == "huggingface" and "red" in r.text.lower()
    _assert_one_bounded_settlement(r, before)


def test_wrong_bill_to_is_a_402_outage_not_a_charge_to_another_account(snap):
    model = sorted(m.model_id for m in snap.models if m.backend == "huggingface")[0]
    with pytest.raises(HFPaymentRequired) as ei:
        HuggingFaceBackend(bill_to=_BAD_BILL_TO).chat([ChatMessage("user", "hi")], model=model, max_tokens=8)
    assert isinstance(ei.value, PreInferenceRejection)
    assert disposition_of(ei.value) is CandidateDisposition.RETRY_ADVANCE
    assert load_hf_token() not in str(ei.value)


def test_wrong_bill_to_through_the_router_is_charged_zero(snap):  # spec 5.9.2 amended, against the real ledger
    before = _reconciled_ids()

    def bad(name: str) -> BaseBackend:
        return HuggingFaceBackend(bill_to=_BAD_BILL_TO) if name == "huggingface" else _dartmouth_down(name)

    with pytest.raises(ChainExhausted):
        route_chat(
            [ChatMessage("user", "hi")], profile="deep_review", max_tokens=8, retries=1,
            snapshot=snap, backend_factory=bad, overrides=_BOUND,
        )
    new = _new_settlements(before)
    assert new and all(s.charged == 0.0 for s in new)
