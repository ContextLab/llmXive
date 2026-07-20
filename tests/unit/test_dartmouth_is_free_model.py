"""``is_free_model`` LKG-backed outage fallback (spec 026, Slice 8 task 2).

The maintainer-approved ladder (see
``notes/2026-07-19-spec-026-slice8-plan.md`` S8-T2): live catalog first: on a
live-catalog OUTAGE, fall back to the last-known-good (LKG) catalog
observation — a REAL, timestamped pricing snapshot, not a hardcoded
allowlist — and only fail closed (never free) when NEITHER is available.

This is the test that proves deleting the old ``KNOWN_FREE_MODELS`` allowlist
bare (without the LKG path) would be a platform-wide outage: with
``LLMXIVE_PAID_OPT_IN`` off (the default), ``dartmouth.chat()`` refuses any
model ``is_free_model`` calls paid, so a transient catalog-listing blip must
never make a genuinely-free model look paid.

Real LKG reads/writes throughout (Constitution III) — only the true network
boundary (``free_chat_models``) is stubbed to simulate a live-catalog outage;
the LKG file itself is a REAL file under a hermetic ``LLMXIVE_REPO_ROOT``.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from llmxive.backends import dartmouth as dm
from llmxive.model_selection.lkg import LKGEntry, LKGStore
from llmxive.model_selection.snapshot import _models_to_payload
from llmxive.model_selection.types import ModelPricing, ModelRef

#: A model id that is NOT a member of the (soon-to-be-deleted) hardcoded
#: KNOWN_FREE_MODELS allowlist — proves the LKG path itself is what makes it
#: free, not a leftover hardcoded entry.
SYNTHETIC_FREE_MODEL = "test.synthetic-lkg-free-model"
SYNTHETIC_PAID_MODEL = "test.synthetic-lkg-paid-model"


def _write_catalog_lkg(store: LKGStore, *, now: datetime) -> None:
    """Record a REAL "catalog" LKG component: one free + one paid model."""
    refs = [
        ModelRef("dartmouth", "https://chat.dartmouth.edu", SYNTHETIC_FREE_MODEL, "synthetic", "test"),
        ModelRef("dartmouth", "https://chat.dartmouth.edu", SYNTHETIC_PAID_MODEL, "synthetic", "test"),
    ]
    pricing = {
        SYNTHETIC_FREE_MODEL: ModelPricing(0.0, 0.0),
        SYNTHETIC_PAID_MODEL: ModelPricing(1e-6, 5e-6),
    }
    store.record({"catalog": LKGEntry(observed_at=now, payload=_models_to_payload((refs, pricing)))})


@pytest.fixture(autouse=True)
def _reset_live_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """``free_chat_models`` caches process-wide; every test controls it directly
    via monkeypatch so the module cache never leaks between tests."""
    monkeypatch.setattr(dm, "_FREE_MODELS_CACHE", None)


def test_is_free_model_live_catalog_hit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Step 1 of the ladder: a reachable live catalog is authoritative, and a
    model absent from it is NOT free even if it would be in the LKG."""
    monkeypatch.setattr(dm, "free_chat_models", lambda **_kw: frozenset({SYNTHETIC_FREE_MODEL}))
    assert dm.is_free_model(SYNTHETIC_FREE_MODEL) is True
    assert dm.is_free_model(SYNTHETIC_PAID_MODEL) is False


def test_is_free_model_catalog_outage_with_lkg_stays_free(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """THE outage-protection test: live catalog unreachable, but a real LKG
    record exists — a known-free model must STILL read as free. This is what
    fails if ``KNOWN_FREE_MODELS`` is deleted without the LKG fallback."""
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    store = LKGStore(tmp_path / "state" / "model_selection" / "lkg_snapshot.json")
    _write_catalog_lkg(store, now=datetime(2026, 7, 18, tzinfo=UTC))
    monkeypatch.setattr(dm, "free_chat_models", lambda **_kw: None)  # live outage

    assert dm.is_free_model(SYNTHETIC_FREE_MODEL) is True
    assert dm.is_free_model(SYNTHETIC_PAID_MODEL) is False
    # A model the LKG has never heard of is unknown -> never free (SC-003).
    assert dm.is_free_model("test.totally-unheard-of-model") is False


def test_is_free_model_catalog_outage_without_lkg_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Cold start: live catalog unreachable AND no LKG record exists yet ->
    fail CLOSED (never free), never raise."""
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))  # empty repo root, no LKG file
    monkeypatch.setattr(dm, "free_chat_models", lambda **_kw: None)

    assert dm.is_free_model(SYNTHETIC_FREE_MODEL) is False


def test_lkg_free_models_absent_store_returns_none(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    assert dm._lkg_free_models() is None


def test_lkg_free_models_corrupt_file_treated_as_absent(tmp_path) -> None:
    path = tmp_path / "lkg.json"
    path.write_text("{ not valid json")
    assert dm._lkg_free_models(lkg_store=LKGStore(path)) is None


def test_lkg_free_models_malformed_catalog_payload_treated_as_absent(tmp_path) -> None:
    """A "catalog" entry whose payload doesn't match the expected shape
    (``ModelRef``/``ModelPricing`` (de)serialization) must not raise -- just
    read as absent."""
    path = tmp_path / "lkg.json"
    store = LKGStore(path)
    store.record(
        {
            "catalog": LKGEntry(
                observed_at=datetime(2026, 7, 18, tzinfo=UTC),
                payload={"refs": [["only", "three", "fields"]], "pricing": {}},
            )
        }
    )
    assert dm._lkg_free_models(lkg_store=LKGStore(path)) is None


def test_lkg_free_models_missing_catalog_component_returns_none(tmp_path) -> None:
    """The LKG file exists and is valid, but has no "catalog" component yet
    (e.g. only "credit" ever succeeded live)."""
    path = tmp_path / "lkg.json"
    store = LKGStore(path)
    store.record(
        {
            "credit": LKGEntry(
                observed_at=datetime(2026, 7, 18, tzinfo=UTC),
                payload={"balance": 1.0},
            )
        }
    )
    assert dm._lkg_free_models(lkg_store=LKGStore(path)) is None


def test_lkg_free_models_real_read_returns_only_zero_priced_ids(tmp_path) -> None:
    """End-to-end real LKG round trip: only the $0-priced model id comes back,
    never the paid one, and never a model with UNKNOWN (None) pricing."""
    path = tmp_path / "lkg.json"
    store = LKGStore(path)
    now = datetime(2026, 7, 18, tzinfo=UTC)
    refs = [
        ModelRef("dartmouth", "https://x", SYNTHETIC_FREE_MODEL, "synthetic", "test"),
        ModelRef("dartmouth", "https://x", SYNTHETIC_PAID_MODEL, "synthetic", "test"),
        ModelRef("dartmouth", "https://x", "test.synthetic-unknown-model", "synthetic", "test"),
    ]
    pricing = {
        SYNTHETIC_FREE_MODEL: ModelPricing(0.0, 0.0),
        SYNTHETIC_PAID_MODEL: ModelPricing(1e-6, 5e-6),
        "test.synthetic-unknown-model": ModelPricing(None, None),
    }
    store.record({"catalog": LKGEntry(observed_at=now, payload=_models_to_payload((refs, pricing)))})

    result = dm._lkg_free_models(lkg_store=LKGStore(path))

    assert result == frozenset({SYNTHETIC_FREE_MODEL})


def test_lkg_free_models_never_raises_on_any_failure(tmp_path) -> None:
    """Sweep of failure modes -- none may propagate an exception (this sits on
    the call path of every LLM request)."""
    missing = LKGStore(tmp_path / "does-not-exist.json")
    assert dm._lkg_free_models(lkg_store=missing) is None

    class _ExplodingStore:
        def load(self):
            raise RuntimeError("disk on fire")

    assert dm._lkg_free_models(lkg_store=_ExplodingStore()) is None  # type: ignore[arg-type]
