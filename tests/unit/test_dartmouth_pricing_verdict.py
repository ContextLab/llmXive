"""``model_pricing_verdict`` — the tri-state spend-authorization classifier
(spec 026 follow-up; maintainer-identified defect).

Before this, ``is_free_model()`` returned a bare ``bool``, so "I cannot verify
this model's pricing" had nowhere to go except ``False`` — indistinguishable
from a VERIFIED-paid model. ``DartmouthBackend.chat()`` then raised
``PaidGuardDenied`` (a ``PermanentBackendError`` -> ``router.disposition_of``
SKIP) for BOTH cases, so a transient catalog outage was reported as "this
model costs money / enable paid opt-in" instead of "the catalog is
unreachable right now".

``model_pricing_verdict`` splits the bool into three real outcomes:
  - FREE          verified cost-per-token == 0
  - PAID          verified cost-per-token > 0 (must be LISTED with a known cost)
  - UNVERIFIABLE  cannot determine right now (unreachable catalog + no fresh
                  LKG, OR a served-but-UNLISTED model on an otherwise-reachable
                  catalog — absence is unknown, never paid)

``chat()`` now raises the new ``PricingUnverifiable`` (a TransientBackendError
-> RETRY_ADVANCE) for UNVERIFIABLE, reserving ``PaidGuardDenied`` (a
PermanentBackendError -> SKIP) for a genuinely verified-PAID model the credit
guard declines. The invariant that must NOT regress: an unverifiable model
NEVER proceeds as free (SC-003) — only the classification/error type/operator
diagnosis changes.

Real LKG reads/writes throughout (Constitution III) — only the true network
boundary (``_fetch_cloud_models``) is stubbed to simulate catalog reachability.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from llmxive.backends import dartmouth as dm
from llmxive.backends.base import ChatMessage, PaidGuardDenied, PricingUnverifiable
from llmxive.backends.router import CandidateDisposition, disposition_of
from llmxive.model_selection.lkg import LKGEntry, LKGStore
from llmxive.model_selection.snapshot import _models_to_payload
from llmxive.model_selection.types import ModelPricing, ModelRef

FREE_MODEL = "test.synthetic-verdict-free-model"
PAID_MODEL = "test.synthetic-verdict-paid-model"
UNLISTED_MODEL = "test.synthetic-verdict-unlisted-model"


def _catalog_entry(model_id: str, *, in_cost: float | None, out_cost: float | None) -> dict:
    return {
        "id": model_id,
        "input_cost_per_token": in_cost,
        "output_cost_per_token": out_cost,
    }


def _fake_catalog_fetch():
    return [
        _catalog_entry(FREE_MODEL, in_cost=0, out_cost=0),
        _catalog_entry(PAID_MODEL, in_cost=1e-6, out_cost=5e-6),
        # UNLISTED_MODEL is deliberately absent.
    ]


def _write_catalog_lkg(store: LKGStore, *, now: datetime) -> None:
    refs = [
        ModelRef("dartmouth", "https://chat.dartmouth.edu", FREE_MODEL, "synthetic", "test"),
        ModelRef("dartmouth", "https://chat.dartmouth.edu", PAID_MODEL, "synthetic", "test"),
    ]
    pricing = {
        FREE_MODEL: ModelPricing(0.0, 0.0),
        PAID_MODEL: ModelPricing(1e-6, 5e-6),
    }
    store.record({"catalog": LKGEntry(observed_at=now, payload=_models_to_payload((refs, pricing)))})


@pytest.fixture(autouse=True)
def _reset_live_pricing_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """The live pricing cache is process-wide and TTL-bounded (mirrors the
    pre-existing ``free_chat_models`` cache) — reset around every test so
    nothing leaks between them."""
    monkeypatch.setattr(dm, "_LIVE_PRICING_CACHE", None)
    monkeypatch.setattr(dm, "_LIVE_PRICING_CACHE_AT", None)


# --------------------------------------------------------------------------- #
# Live catalog reachable
# --------------------------------------------------------------------------- #


def test_live_catalog_free_priced_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dm, "_fetch_cloud_models", _fake_catalog_fetch)
    assert dm.model_pricing_verdict(FREE_MODEL) is dm.PricingVerdict.FREE


def test_live_catalog_paid_priced_above_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dm, "_fetch_cloud_models", _fake_catalog_fetch)
    assert dm.model_pricing_verdict(PAID_MODEL) is dm.PricingVerdict.PAID


def test_live_catalog_absent_model_is_unverifiable_not_paid(monkeypatch: pytest.MonkeyPatch) -> None:
    """THE core defect: a served-but-unlisted model on a REACHABLE catalog must
    read as UNVERIFIABLE, never PAID — absence is unknown, not a cost fact."""
    monkeypatch.setattr(dm, "_fetch_cloud_models", _fake_catalog_fetch)
    assert dm.model_pricing_verdict(UNLISTED_MODEL) is dm.PricingVerdict.UNVERIFIABLE


def test_live_catalog_listed_with_unknown_cost_is_unverifiable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Listed (e.g. an embeddings/helper-bot entry with no pricing fields at
    all) but neither verified $0 nor verified >$0 -> UNVERIFIABLE, not FREE
    and not PAID."""

    def fetch():
        return [_catalog_entry("test.synthetic-no-pricing-info", in_cost=None, out_cost=None)]

    monkeypatch.setattr(dm, "_fetch_cloud_models", fetch)
    assert dm.model_pricing_verdict("test.synthetic-no-pricing-info") is dm.PricingVerdict.UNVERIFIABLE


# --------------------------------------------------------------------------- #
# Catalog outage + LKG
# --------------------------------------------------------------------------- #


def test_outage_with_fresh_lkg_three_way_split(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    store = LKGStore(tmp_path / "state" / "model_selection" / "lkg_snapshot.json")
    _write_catalog_lkg(store, now=datetime.now(UTC))
    monkeypatch.setattr(
        dm, "_fetch_cloud_models", lambda: (_ for _ in ()).throw(RuntimeError("catalog down"))
    )

    assert dm.model_pricing_verdict(FREE_MODEL) is dm.PricingVerdict.FREE
    assert dm.model_pricing_verdict(PAID_MODEL) is dm.PricingVerdict.PAID
    assert dm.model_pricing_verdict(UNLISTED_MODEL) is dm.PricingVerdict.UNVERIFIABLE


def test_outage_with_stale_lkg_is_unverifiable(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    store = LKGStore(tmp_path / "state" / "model_selection" / "lkg_snapshot.json")
    _write_catalog_lkg(store, now=datetime.now(UTC) - timedelta(hours=2))
    monkeypatch.setattr(
        dm, "_fetch_cloud_models", lambda: (_ for _ in ()).throw(RuntimeError("catalog down"))
    )

    assert dm.model_pricing_verdict(FREE_MODEL) is dm.PricingVerdict.UNVERIFIABLE
    assert dm.model_pricing_verdict(PAID_MODEL) is dm.PricingVerdict.UNVERIFIABLE


def test_outage_with_no_lkg_is_unverifiable(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))  # empty repo root, no LKG file
    monkeypatch.setattr(
        dm, "_fetch_cloud_models", lambda: (_ for _ in ()).throw(RuntimeError("catalog down"))
    )

    assert dm.model_pricing_verdict(FREE_MODEL) is dm.PricingVerdict.UNVERIFIABLE


# --------------------------------------------------------------------------- #
# is_free_model — thin wrapper, SC-003 preserved
# --------------------------------------------------------------------------- #


def test_is_free_model_false_for_unverifiable(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """An unverifiable model NEVER proceeds as free — ``is_free_model`` answers
    ONLY the "is this VERIFIED free" question."""
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    monkeypatch.setattr(
        dm, "_fetch_cloud_models", lambda: (_ for _ in ()).throw(RuntimeError("catalog down"))
    )
    assert dm.is_free_model(UNLISTED_MODEL) is False


def test_is_free_model_still_true_for_verified_free(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dm, "_fetch_cloud_models", _fake_catalog_fetch)
    assert dm.is_free_model(FREE_MODEL) is True
    assert dm.is_free_model(PAID_MODEL) is False


# --------------------------------------------------------------------------- #
# chat() rewiring: PricingUnverifiable vs PaidGuardDenied
# --------------------------------------------------------------------------- #


def test_chat_raises_pricing_unverifiable_not_paid_guard_denied(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "test-key")
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))  # no LKG -> cold start
    monkeypatch.setattr(
        dm, "_fetch_cloud_models", lambda: (_ for _ in ()).throw(RuntimeError("catalog down"))
    )

    def _client_must_not_be_reached(self, model):
        raise AssertionError("chat() must not reach the client for an UNVERIFIABLE model")

    monkeypatch.setattr(dm.DartmouthBackend, "_client", _client_must_not_be_reached)

    backend = dm.DartmouthBackend()
    with pytest.raises(PricingUnverifiable):
        backend.chat([ChatMessage(role="user", content="hi")], model=UNLISTED_MODEL)


def test_chat_still_raises_paid_guard_denied_for_verified_paid_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A genuinely VERIFIED-paid model with the credit guard off is still a
    PermanentBackendError SKIP (PaidGuardDenied), NOT the new transient."""
    monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "test-key")
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    monkeypatch.setattr(dm, "_fetch_cloud_models", _fake_catalog_fetch)

    def _client_must_not_be_reached(self, model):
        raise AssertionError("chat() must not reach the client when the paid guard denies")

    monkeypatch.setattr(dm.DartmouthBackend, "_client", _client_must_not_be_reached)

    backend = dm.DartmouthBackend()
    with pytest.raises(PaidGuardDenied):
        backend.chat([ChatMessage(role="user", content="hi")], model=PAID_MODEL)


# --------------------------------------------------------------------------- #
# router.disposition_of classification
# --------------------------------------------------------------------------- #


def test_disposition_of_pricing_unverifiable_is_retry_advance() -> None:
    assert disposition_of(PricingUnverifiable("x")) is CandidateDisposition.RETRY_ADVANCE


def test_disposition_of_paid_guard_denied_is_still_skip() -> None:
    assert disposition_of(PaidGuardDenied("x")) is CandidateDisposition.SKIP
