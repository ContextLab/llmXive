"""``is_free_model`` LKG-backed outage fallback (spec 026, Slice 8 task 2;
hardened post-review with a bounded freshness bound, Finding 2).

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

A review found BOTH steps of the ladder had no freshness bound: the
in-process ``free_chat_models`` cache lived for the entire process, and
``_lkg_free_models`` never consulted ``observed_at`` at all — either one
could serve an arbitrarily stale "free" verdict, which bypasses
``paid_call_allowed`` at the spend-authorization boundary (``chat()``). Both
now expire against the SAME bound as spec 026's high-stakes
``max_catalog_age_s`` (``profiles.PROFILES["independent_review"]`` = 900s):
the in-process cache TTLs out and refetches; a "catalog" LKG entry older than
the bound reads as absent (fail closed). The tests below cover both the
"still fresh" (outage protection preserved) and "now stale" (fails closed)
sides of that bound, plus the ``chat()``-level assertion that a stale cached
"free" cannot bypass the paid guard.

Real LKG reads/writes throughout (Constitution III) — only the true network
boundary (``free_chat_models`` / ``_fetch_cloud_models``) is stubbed to
simulate a live-catalog outage; the LKG file itself is a REAL file under a
hermetic ``LLMXIVE_REPO_ROOT``.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import pytest

from llmxive.backends import dartmouth as dm
from llmxive.backends.base import ChatMessage
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
    """``free_chat_models`` caches process-wide (now with a bounded TTL —
    Finding 2); every test controls it directly via monkeypatch so the
    module cache (value AND fill-timestamp) never leaks between tests."""
    monkeypatch.setattr(dm, "_FREE_MODELS_CACHE", None)
    monkeypatch.setattr(dm, "_FREE_MODELS_CACHE_AT", None)


def test_is_free_model_live_catalog_hit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Step 1 of the ladder: a reachable live catalog is authoritative, and a
    model absent from it is NOT free even if it would be in the LKG."""
    monkeypatch.setattr(dm, "free_chat_models", lambda **_kw: frozenset({SYNTHETIC_FREE_MODEL}))
    assert dm.is_free_model(SYNTHETIC_FREE_MODEL) is True
    assert dm.is_free_model(SYNTHETIC_PAID_MODEL) is False


def test_is_free_model_catalog_outage_with_lkg_stays_free(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """THE outage-protection test: live catalog unreachable, but a FRESH real
    LKG record exists — a known-free model must STILL read as free. This is
    what fails if ``KNOWN_FREE_MODELS`` is deleted without the LKG fallback,
    and it is exactly what the Finding-2 freshness bound must NOT break: a
    genuinely recent observation still protects against a transient outage.
    """
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    store = LKGStore(tmp_path / "state" / "model_selection" / "lkg_snapshot.json")
    _write_catalog_lkg(store, now=datetime.now(UTC))
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


def test_is_free_model_catalog_outage_with_expired_lkg_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Finding 2 (HIGH): the flip side of the outage-protection test. An LKG
    record exists but is older than the spend-authorization freshness bound
    -- it must fail CLOSED (never free), not trust an arbitrarily old
    pricing observation to bypass the paid guard (SC-003: "stale/unknown
    pricing fails closed"). Pre-fix, ``_lkg_free_models`` ignored
    ``observed_at`` entirely, so this returned True forever."""
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    store = LKGStore(tmp_path / "state" / "model_selection" / "lkg_snapshot.json")
    _write_catalog_lkg(store, now=datetime.now(UTC) - timedelta(hours=2))
    monkeypatch.setattr(dm, "free_chat_models", lambda **_kw: None)  # live outage

    assert dm.is_free_model(SYNTHETIC_FREE_MODEL) is False


def test_expired_cache_refetch_failure_falls_through_to_fresh_lkg(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """The in-process cache expiring is not itself a failure — it should just
    trigger a refetch. When that refetch ALSO fails (still an outage), the
    ladder must fall through to a FRESH LKG record rather than re-serving
    the now-untrustworthy expired cache value."""
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    store = LKGStore(tmp_path / "state" / "model_selection" / "lkg_snapshot.json")
    _write_catalog_lkg(store, now=datetime.now(UTC))

    # Cache remembers the model as free, but the fill is long expired.
    monkeypatch.setattr(dm, "_FREE_MODELS_CACHE", frozenset({SYNTHETIC_FREE_MODEL}))
    monkeypatch.setattr(dm, "_FREE_MODELS_CACHE_AT", time.monotonic() - 100_000)
    monkeypatch.setattr(
        dm, "_fetch_cloud_models", lambda: (_ for _ in ()).throw(RuntimeError("still down"))
    )

    assert dm.is_free_model(SYNTHETIC_FREE_MODEL) is True
    assert dm.is_free_model(SYNTHETIC_PAID_MODEL) is False


def test_free_chat_models_cache_expires_and_refetches_after_ttl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fresh in-process cache is served without refetching; once its TTL
    (the spend-authorization freshness bound) elapses, the next call
    refetches instead of serving the same value for the process lifetime."""
    calls = {"n": 0}

    def fake_fetch():
        calls["n"] += 1
        return [
            {"id": SYNTHETIC_FREE_MODEL, "input_cost_per_token": 0, "output_cost_per_token": 0}
        ]

    monkeypatch.setattr(dm, "_fetch_cloud_models", fake_fetch)

    first = dm.free_chat_models()
    assert first == frozenset({SYNTHETIC_FREE_MODEL})
    assert calls["n"] == 1

    # Still within the TTL -- served from cache, no refetch.
    second = dm.free_chat_models()
    assert second == frozenset({SYNTHETIC_FREE_MODEL})
    assert calls["n"] == 1

    # Simulate the TTL having elapsed.
    monkeypatch.setattr(
        dm,
        "_FREE_MODELS_CACHE_AT",
        dm._FREE_MODELS_CACHE_AT - dm._free_model_freshness_bound_s() - 1,
    )

    third = dm.free_chat_models()
    assert third == frozenset({SYNTHETIC_FREE_MODEL})
    assert calls["n"] == 2  # refetched, not served stale


def test_stale_cached_free_cannot_bypass_paid_call_allowed_at_chat_level(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Finding 2, asserted at the boundary that actually matters:
    ``DartmouthBackend.chat()``. An EXPIRED in-process "free" cache entry —
    the exact bypass this finding closes — must fail through to
    ``is_free_model() -> False`` and therefore reach ``paid_call_allowed()``;
    with the paid opt-in off (the test default), that refuses the call
    (``PaidGuardDenied``) instead of silently invoking the client."""
    monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "test-key")
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))  # no LKG file -> cold start

    # An EXPIRED cache that still (pre-fix) remembers the model as free.
    monkeypatch.setattr(dm, "_FREE_MODELS_CACHE", frozenset({SYNTHETIC_FREE_MODEL}))
    monkeypatch.setattr(dm, "_FREE_MODELS_CACHE_AT", time.monotonic() - 100_000)
    # The refetch is unreachable (the outage this cache was protecting
    # against), and there is no LKG record either -> the ladder must fail
    # CLOSED, i.e. paid_call_allowed() must be consulted.
    monkeypatch.setattr(
        dm, "_fetch_cloud_models", lambda: (_ for _ in ()).throw(RuntimeError("down"))
    )

    def _client_must_not_be_reached(self, model):
        raise AssertionError(
            "chat() must not reach the client; the paid guard should refuse first"
        )

    monkeypatch.setattr(dm.DartmouthBackend, "_client", _client_must_not_be_reached)

    backend = dm.DartmouthBackend()
    with pytest.raises(dm.PaidGuardDenied):
        backend.chat([ChatMessage(role="user", content="hi")], model=SYNTHETIC_FREE_MODEL)


def test_is_fresh_enough_accepts_naive_and_aware_datetimes() -> None:
    """``observed_at`` may be tz-naive or tz-aware depending on how it was
    persisted — both must be handled without raising."""
    aware_now = datetime.now(UTC)
    naive_now = datetime.now(UTC).replace(tzinfo=None)

    assert dm._is_fresh_enough(aware_now) is True
    assert dm._is_fresh_enough(naive_now) is True


def test_is_fresh_enough_never_raises_on_garbage_input() -> None:
    """Any failure in the freshness computation must return False (fail
    closed), never raise — this sits on the call path of every LLM
    request."""
    assert dm._is_fresh_enough(None) is False  # type: ignore[arg-type]
    assert dm._is_fresh_enough("not-a-datetime") is False  # type: ignore[arg-type]


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
                observed_at=datetime.now(UTC),
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
                observed_at=datetime.now(UTC),
                payload={"balance": 1.0},
            )
        }
    )
    assert dm._lkg_free_models(lkg_store=LKGStore(path)) is None


def test_lkg_free_models_expired_entry_treated_as_absent(tmp_path) -> None:
    """Finding 2's second unbounded cache: a "catalog" LKG entry whose
    ``observed_at`` is older than the spend-authorization freshness bound
    must be treated as absent (-> ``None`` -> fail closed by the caller),
    no matter how genuinely it was once observed. Pre-fix, ``observed_at``
    was read off the entry but never consulted."""
    path = tmp_path / "lkg.json"
    store = LKGStore(path)
    stale = datetime.now(UTC) - timedelta(hours=2)
    refs = [ModelRef("dartmouth", "https://x", SYNTHETIC_FREE_MODEL, "synthetic", "test")]
    pricing = {SYNTHETIC_FREE_MODEL: ModelPricing(0.0, 0.0)}
    store.record(
        {"catalog": LKGEntry(observed_at=stale, payload=_models_to_payload((refs, pricing)))}
    )

    assert dm._lkg_free_models(lkg_store=LKGStore(path)) is None


def test_lkg_free_models_real_read_returns_only_zero_priced_ids(tmp_path) -> None:
    """End-to-end real LKG round trip: only the $0-priced model id comes back,
    never the paid one, and never a model with UNKNOWN (None) pricing."""
    path = tmp_path / "lkg.json"
    store = LKGStore(path)
    now = datetime.now(UTC)
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
