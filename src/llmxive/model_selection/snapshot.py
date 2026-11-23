"""Acquisition layer (spec 026, slice 1): assemble a composite ``RuntimeSnapshot``.

This is the ONLY networked / environment-reading layer. It fetches every
configured backend's inventory + per-model USD pricing, plus a FRESH
(cache-bypassing) credit-guard observation, and records each component's
provenance (``live`` / ``last_known_good`` / ``unavailable``, with its true age).
``select`` then consumes the snapshot as a pure function.

Per-component last-known-good fallback (FR-007): when a live fetch FAILS, the
component falls back to the last successfully-observed value from the LKG store
(``lkg.py``), marked ``source=last_known_good`` with its TRUE age — distinct from
a SUCCESSFUL fetch that omits a model (``unavailable``). Cold start (no live AND
no LKG) → ``unavailable``. Only components that succeed live are written back.

Spec 027 adds three components: ``hf_catalog`` (the Hugging Face router catalog:
one ``ModelRef`` per live provider, real pricing, observed context/feature flags),
``leaderboard`` (LMArena scores, joined to the catalog per repo) — both with their
own LKG — and ``funded`` (the allowance guard; ``live`` or ``unavailable``, no LKG:
money is never priced from a stale ledger read). The leaderboard LKG stores the
parsed arena data, not the join, so an LKG leaderboard still joins against a live
catalog. Raw ratings are persisted only in the gitignored LKG store.

Reuses (Constitution I): the Dartmouth catalog fetch + pricing extraction, the
local backend inventory, and the credit guard's balance/fraction helpers.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import time
from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import TypeVar

from llmxive.model_selection.lkg import LKGEntry, LKGStore
from llmxive.model_selection.types import (
    ArenaScore,
    CreditGuardSnapshot,
    FundedGuardSnapshot,
    ModelPricing,
    ModelRef,
    ModelScores,
    ObservedModel,
    RuntimeSnapshot,
    SnapshotProvenance,
    Track,
)

logger = logging.getLogger(__name__)

_DARTMOUTH_BACKEND = "dartmouth"
_LOCAL_BACKEND = "local"
_HF_BACKEND = "huggingface"

#: A resolved models component: (refs, pricing) — catalog and local share this shape.
_ModelsData = tuple[list[ModelRef], dict[str, ModelPricing]]
#: The Hugging Face catalog component: (refs, pricing, observed flags), keyed by model_id.
_HFCatalogData = tuple[list[ModelRef], dict[str, ModelPricing], dict[str, ObservedModel]]
#: The leaderboard component: per track, ``{normalised arena name: ArenaScore}``.
_ArenaData = dict[Track, dict[str, ArenaScore]]

_T = TypeVar("_T")

#: Per-component refresh intervals (seconds): a stored LKG entry younger than this
#: is served (with its TRUE observed time and age, as ``last_known_good``) instead
#: of re-fetching, so routed calls do not re-page the leaderboard or re-read the
#: catalog every time the route cache (``route._SNAPSHOT_TTL_S``) expires.
#: ``runtime_snapshot(refresh=True)`` bypasses them. ``funded`` is never reused.
LEADERBOARD_REFRESH_S = 6 * 3600.0
HF_CATALOG_REFRESH_S = 15 * 60.0

#: After a remote fetch fails (Dartmouth catalog, Dartmouth credit balance, Hugging
#: Face catalog, leaderboard), the same fetch is not attempted again for this many
#: seconds: snapshot builds inside the interval resolve that component as if the
#: fetch had failed (last-known-good, else unavailable). ``refresh=True`` bypasses
#: it. The funded guard and the local inventory are never held back.
FETCH_FAILURE_BACKOFF_S = 120.0

#: Monotonic clock for :data:`FETCH_FAILURE_BACKOFF_S` (module-level so tests can
#: freeze it); separate from the snapshot's ``now``, which is an observation time.
_monotonic: Callable[[], float] = time.monotonic

#: Component name -> monotonic time of its last failed remote fetch.
_FETCH_FAILED_AT: dict[str, float] = {}


def reset_fetch_failures() -> None:
    """Forget every remembered failed remote fetch."""
    _FETCH_FAILED_AT.clear()


def _vendor_of(model_id: str) -> str:
    """Vendor = the id's leading namespace (``openai.gpt-oss-120b`` → ``openai``;
    ``Qwen/Qwen2.5-3B-Instruct`` → ``qwen``)."""
    if "/" in model_id:
        return model_id.split("/", 1)[0].lower()
    if "." in model_id:
        return model_id.split(".", 1)[0].lower()
    return model_id.lower()


def _family_of(model_id: str, vendor: str) -> str:
    """Model family (vendor-stripped, size/variant/date suffix removed) — a stable
    identifier for capability + independence. E.g. ``google.gemma-4-31B-it`` →
    ``gemma-4``; ``qwen.qwen3.5-122b`` → ``qwen3.5``; ``Qwen/Qwen2.5-3B-Instruct``
    → ``qwen2.5``; ``anthropic.claude-haiku-4-5-20251001`` → ``claude-haiku-4-5``.
    (Slice 2's CapabilityPolicy may override family for known models.)
    """
    tail = model_id
    if "/" in model_id:
        tail = model_id.split("/", 1)[1]
    elif model_id.lower().startswith(vendor + "."):
        tail = model_id[len(vendor) + 1 :]
    tail = re.sub(r"[-.:]\d+[bB]\b.*$", "", tail)  # drop size (…-122b, …-31B-it)
    tail = re.sub(r"-\d{6,}\b.*$", "", tail)  # drop date stamp (…-20251001)
    return tail.lower()


# --------------------------------------------------------------------------- #
# Live fetches — return the observed data, or ``None`` on a live FAILURE (which
# triggers the per-component LKG fallback). A SUCCESSFUL-but-empty fetch returns
# ``([], {})`` (confirmed absence), NOT ``None``.
# --------------------------------------------------------------------------- #


def _fetch_dartmouth() -> _ModelsData | None:
    """Fetch the Dartmouth catalog → ModelRefs + pricing, or ``None`` on failure."""
    try:
        from llmxive.backends.dartmouth import (
            _cloud_models_url,
            _fetch_cloud_models,
            _model_token_costs,
        )

        endpoint = _cloud_models_url()
        raw = _fetch_cloud_models()
    except Exception as exc:  # network / key / import — live failure → LKG fallback
        logger.warning("dartmouth catalog fetch failed: %s: %s", type(exc).__name__, exc)
        return None

    refs: list[ModelRef] = []
    pricing: dict[str, ModelPricing] = {}
    for m in raw:
        mid = m.get("id")
        if not mid:
            continue
        mid = str(mid)
        vendor = _vendor_of(mid)
        refs.append(
            ModelRef(
                backend=_DARTMOUTH_BACKEND,
                serving_endpoint=endpoint,
                model_id=mid,
                model_family=_family_of(mid, vendor),
                vendor=vendor,
            )
        )
        in_cost, out_cost = _model_token_costs(m)
        pricing[mid] = ModelPricing(input_usd_per_token=in_cost, output_usd_per_token=out_cost)
    return refs, pricing


def _fetch_local() -> _ModelsData | None:
    """The local transformers fallback inventory (a first-class candidate, so
    backend fallback needs no hidden second selector). ``None`` on failure."""
    try:
        from llmxive.backends.local import LocalBackend

        ids = LocalBackend().list_models()
    except Exception as exc:
        logger.warning("local backend inventory fetch failed: %s: %s", type(exc).__name__, exc)
        return None
    refs: list[ModelRef] = []
    pricing: dict[str, ModelPricing] = {}
    for mid in ids:
        vendor = _vendor_of(mid)
        refs.append(
            ModelRef(
                backend=_LOCAL_BACKEND,
                serving_endpoint=_LOCAL_BACKEND,
                model_id=mid,
                model_family=_family_of(mid, vendor),
                vendor=vendor,
            )
        )
        pricing[mid] = ModelPricing(input_usd_per_token=0.0, output_usd_per_token=0.0)  # local = free
    return refs, pricing


def _fetch_credit(*, now: datetime) -> CreditGuardSnapshot | None:
    """FRESH (cache-bypassing) credit-guard observation, or ``None`` if the
    balance fetch fails. ``paid_opt_in``/``budget_fraction`` are read from local
    config (never network), so they stay authoritative even under LKG fallback."""
    from llmxive.backends.credits import (
        budget_fraction,
        fetch_credit_balance,
        paid_opt_in_enabled,
    )

    opt_in = paid_opt_in_enabled()
    fraction = budget_fraction()
    try:
        bal = fetch_credit_balance()  # bypasses the ~30s cache (direct fetch)
    except Exception as exc:
        logger.warning("credit balance fetch failed: %s: %s", type(exc).__name__, exc)
        return None
    effective_cap = fraction * bal.max_budget
    return CreditGuardSnapshot(
        balance=bal.remaining, spend=bal.spend, max_budget=bal.max_budget,
        paid_opt_in=opt_in, budget_fraction=fraction, effective_cap=effective_cap,
        available_headroom=max(0.0, effective_cap - bal.spend),
        budget_reset_at=bal.budget_reset_at, observed_at=now, source="live",
    )


def _usd_per_million(value: object) -> float | None:
    """A catalog price (USD per million tokens) as USD per token, or ``None`` (unknown,
    never free) unless it is a finite non-negative number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value) or value < 0:
        return None
    return float(value) / 1e6


def _parse_hf_catalog(raw: dict) -> _HFCatalogData:
    """Router ``/models`` body → one ``ModelRef`` per (repo, provider) whose status is
    ``live``. ``model_id`` is ``<repo>:<provider>``; family and vendor come from the
    repo id alone. Raises ``ValueError`` when the body has no ``data`` list or yields
    no live provider at all (an empty catalog is a failed fetch, so it never
    overwrites a good last-known-good copy)."""
    data = raw.get("data") if isinstance(raw, dict) else None
    if not isinstance(data, list):
        raise ValueError("Hugging Face catalog has no 'data' list")
    refs: list[ModelRef] = []
    pricing: dict[str, ModelPricing] = {}
    observed: dict[str, ObservedModel] = {}
    for model in data:
        if not isinstance(model, dict) or not isinstance(model.get("id"), str) or not model["id"]:
            continue
        repo = model["id"]
        vendor = _vendor_of(repo)
        family = _family_of(repo, vendor)
        arch = model.get("architecture")
        modalities = arch.get("input_modalities") if isinstance(arch, dict) else None
        vision = isinstance(modalities, list) and "image" in modalities
        for prov in model.get("providers") or []:
            if not isinstance(prov, dict) or prov.get("status") != "live":
                continue
            provider = prov.get("provider")
            if not isinstance(provider, str) or not provider:
                continue
            mid = f"{repo}:{provider}"
            if mid in pricing:
                continue  # a repeated (repo, provider) row: the first one stands
            refs.append(ModelRef(_HF_BACKEND, provider, mid, family, vendor))
            price = prov.get("pricing") if isinstance(prov.get("pricing"), dict) else {}
            pricing[mid] = ModelPricing(
                _usd_per_million(price.get("input")), _usd_per_million(price.get("output"))
            )
            ctx = prov.get("context_length")
            features = {
                name for name, on in (
                    ("structured", prov.get("supports_structured_output") is True),
                    ("tools", prov.get("supports_tools") is True),
                    ("vision", vision),
                ) if on
            }
            observed[mid] = ObservedModel(
                context_length=ctx if isinstance(ctx, int) and not isinstance(ctx, bool) else None,
                features=frozenset(features),
            )
    if not refs:
        raise ValueError("Hugging Face catalog lists no live provider")
    return refs, pricing, observed


def _fetch_huggingface(*, base_url: str | None = None) -> _HFCatalogData | None:
    """The Hugging Face router catalog (keyless), or ``None`` on a live failure
    (transport, non-200, or a malformed body)."""
    try:
        from llmxive.backends.huggingface import ROUTER_BASE_URL, fetch_router_catalog

        return _parse_hf_catalog(fetch_router_catalog(base_url=base_url or ROUTER_BASE_URL))
    except Exception as exc:  # network / shape — live failure → LKG fallback
        logger.warning("hugging face catalog fetch failed: %s: %s", type(exc).__name__, exc)
        return None


def _fetch_leaderboard() -> _ArenaData | None:
    """Both tracks' LMArena scores, or ``None`` (already logged) on failure."""
    from llmxive.model_selection.leaderboard import fetch_arena_scores

    return fetch_arena_scores()


def _fetch_funded_guard(*, now: datetime) -> FundedGuardSnapshot | None:
    """The funded allowance guard, or ``None`` when funded spend is unavailable
    (no bill-to id / token / ledger anchor, the ledger cannot sync, or ANY other
    failure — ``runtime_snapshot`` never raises). The guard
    fetches the org balance ONCE and records it as ``org_balance_usd``; whatever
    reserves against this snapshot passes the guard itself to
    ``hf_budget.reserve_funded`` so it prices with that same balance."""
    # The imports sit inside the ``try`` so an import failure is unavailable too.
    # Only the exception TYPE is logged, never its message: FundedUnavailable and
    # LedgerError wrap lower-level errors (git stderr, remote URLs, HTTP bodies)
    # whose text is not guaranteed free of a token or the bill-to id.
    try:
        from llmxive.backends.hf_budget import FundedUnavailable, funded_guard
        from llmxive.config import repo_root
        from llmxive.model_selection.ledger_transport import LedgerError
    except Exception as exc:
        logger.warning("funded guard unavailable: cannot import its modules (%s)", type(exc).__name__)
        return None
    try:
        return funded_guard(repo_root(), now=now)
    except (FundedUnavailable, LedgerError) as exc:
        logger.warning("funded guard unavailable: %s (message withheld)", type(exc).__name__)
        return None
    except Exception as exc:
        logger.warning("funded guard unavailable: unexpected %s", type(exc).__name__)
        return None


# --------------------------------------------------------------------------- #
# LKG (de)serialization — domain-type ↔ JSON payload. Kept here (snapshot owns
# the domain types); ``lkg.py`` stays generic over the payload dict.
# --------------------------------------------------------------------------- #


def _models_to_payload(data: _ModelsData) -> dict:
    refs, pricing = data
    return {
        "refs": [[m.backend, m.serving_endpoint, m.model_id, m.model_family, m.vendor] for m in refs],
        "pricing": {k: [p.input_usd_per_token, p.output_usd_per_token] for k, p in pricing.items()},
    }


def _models_from_payload(payload: dict) -> _ModelsData:
    refs = [ModelRef(*row) for row in payload["refs"]]
    pricing = {k: ModelPricing(v[0], v[1]) for k, v in payload["pricing"].items()}
    return refs, pricing


def _credit_to_payload(c: CreditGuardSnapshot) -> dict:
    # observed_at + source are provenance-derived; everything else is the datum.
    return {
        "balance": c.balance, "spend": c.spend, "max_budget": c.max_budget,
        "paid_opt_in": c.paid_opt_in, "budget_fraction": c.budget_fraction,
        "effective_cap": c.effective_cap, "available_headroom": c.available_headroom,
        "budget_reset_at": c.budget_reset_at,
    }


def _credit_from_payload(payload: dict, *, observed_at: datetime) -> CreditGuardSnapshot:
    return CreditGuardSnapshot(
        balance=payload["balance"], spend=payload["spend"], max_budget=payload["max_budget"],
        paid_opt_in=payload["paid_opt_in"], budget_fraction=payload["budget_fraction"],
        effective_cap=payload["effective_cap"], available_headroom=payload["available_headroom"],
        budget_reset_at=payload["budget_reset_at"], observed_at=observed_at,
        source="last_known_good",
    )


def _observed_row(o: ObservedModel) -> list:
    return [o.context_length, sorted(o.features)]


def _hf_catalog_to_payload(data: _HFCatalogData) -> dict:
    refs, pricing, observed = data
    return {
        **_models_to_payload((refs, pricing)),
        "observed": {k: _observed_row(o) for k, o in observed.items()},
    }


def _hf_catalog_from_payload(payload: dict) -> _HFCatalogData:
    refs, pricing = _models_from_payload(payload)
    observed = {k: ObservedModel(v[0], frozenset(v[1])) for k, v in payload["observed"].items()}
    return refs, pricing, observed


def _score_row(s: ArenaScore) -> list:
    return [s.rating, s.rating_lower, s.rating_upper, s.publish_date.isoformat()]


def _arena_to_payload(arena: _ArenaData) -> dict:
    """``{track: {name: [rating, lower, upper, "YYYY-MM-DD"]}}`` (gitignored LKG only)."""
    return {track: {name: _score_row(s) for name, s in table.items()} for track, table in arena.items()}


def _arena_from_payload(payload: dict) -> _ArenaData:
    return {
        track: {
            name: ArenaScore(float(v[0]), float(v[1]), float(v[2]), date.fromisoformat(v[3]))
            for name, v in table.items()
        }
        for track, table in payload.items()
    }


# --------------------------------------------------------------------------- #
# Per-component resolution: live → last_known_good → unavailable, emitting the
# component's provenance and staging an LKG write-back on live success.
# --------------------------------------------------------------------------- #


def _resolve_component(
    name: str,
    fetch: Callable[[], _T | None],
    to_payload: Callable[[_T], dict],
    from_payload: Callable[[dict, datetime], _T],
    empty: _T,
    lkg: dict[str, LKGEntry],
    now: datetime,
    updates: dict[str, LKGEntry],
    *,
    reuse_within_s: float | None = None,
    remote: bool = False,
    refresh: bool = False,
) -> tuple[_T, SnapshotProvenance]:
    """The one live → last_known_good → unavailable resolver every LKG-backed
    component goes through. ``from_payload`` receives the entry's original
    ``observed_at``; ``empty`` is the cold-start value.

    ``reuse_within_s``: when the stored entry is younger than this (and not from
    the future), it is served WITHOUT fetching, as ``last_known_good`` with its
    true observed time and age — never restamped as fresh. A stored entry stamped
    in the future is never served: after a failed fetch it counts as absent.

    ``remote``: a failed fetch is remembered, and for
    :data:`FETCH_FAILURE_BACKOFF_S` afterwards the fetch is skipped and treated as
    failed, unless ``refresh`` is set."""
    entry = lkg.get(name)
    if reuse_within_s is not None and entry is not None:
        age = (now - entry.observed_at).total_seconds()
        if 0.0 <= age < reuse_within_s:
            try:
                data = from_payload(entry.payload, entry.observed_at)
            except (KeyError, TypeError, ValueError, IndexError, AttributeError) as exc:
                logger.warning("LKG %s payload invalid (%s); refetching", name, exc)
            else:
                return data, SnapshotProvenance("last_known_good", entry.observed_at, age)

    failed_at = _FETCH_FAILED_AT.get(name) if remote and not refresh else None
    if failed_at is not None and 0.0 <= _monotonic() - failed_at < FETCH_FAILURE_BACKOFF_S:
        live = None
    else:
        live = fetch()
        if remote:
            if live is None:
                _FETCH_FAILED_AT[name] = _monotonic()
            else:
                _FETCH_FAILED_AT.pop(name, None)
    if live is not None:
        updates[name] = LKGEntry(observed_at=now, payload=to_payload(live))
        return live, SnapshotProvenance(source="live", observed_at=now, age_s=0.0)

    if entry is not None:
        age = (now - entry.observed_at).total_seconds()
        if age < 0.0:
            # A copy stamped in the future cannot be aged: clamping it to 0 would
            # make it look fresh, so it is treated as absent.
            logger.warning("LKG %s is stamped in the future; treating as absent", name)
        else:
            try:
                data = from_payload(entry.payload, entry.observed_at)
            except (KeyError, TypeError, ValueError, IndexError, AttributeError) as exc:
                logger.warning("LKG %s payload invalid (%s); treating as absent", name, exc)
            else:
                return data, SnapshotProvenance("last_known_good", entry.observed_at, age)

    return empty, SnapshotProvenance(source="unavailable", observed_at=now, age_s=0.0)


def _resolve_models_component(
    name: str,
    fetch: Callable[[], _ModelsData | None],
    lkg: dict[str, LKGEntry],
    now: datetime,
    updates: dict[str, LKGEntry],
    *,
    remote: bool = False,
    refresh: bool = False,
) -> tuple[_ModelsData, SnapshotProvenance]:
    return _resolve_component(
        name, fetch, _models_to_payload, lambda p, _at: _models_from_payload(p),
        ([], {}), lkg, now, updates, remote=remote, refresh=refresh,
    )


def _resolve_credit_component(
    lkg: dict[str, LKGEntry],
    now: datetime,
    updates: dict[str, LKGEntry],
    *,
    refresh: bool = False,
) -> tuple[CreditGuardSnapshot, SnapshotProvenance]:
    unavailable = CreditGuardSnapshot(
        balance=0.0, spend=0.0, max_budget=0.0, paid_opt_in=False,
        budget_fraction=0.0, effective_cap=0.0, available_headroom=0.0,
        budget_reset_at="", observed_at=now, source="unavailable",
    )
    return _resolve_component(
        "credit", lambda: _fetch_credit(now=now), _credit_to_payload,
        lambda p, at: _credit_from_payload(p, observed_at=at), unavailable, lkg, now, updates,
        remote=True, refresh=refresh,
    )


def _join_hf_scores(refs: list[ModelRef], arena: _ArenaData) -> dict[str, ModelScores]:
    """Scores per Hugging Face ``model_id``: the arena joined by repo id against EVERY
    catalog repo (so uniqueness is judged across the whole catalog), then fanned out
    to each provider of a matched repo. Ambiguous names are logged, never ratings."""
    from llmxive.model_selection.leaderboard import join_scores

    repo_of = {r.model_id: r.model_id.rsplit(":", 1)[0] for r in refs}
    by_repo, ambiguous = join_scores(repo_of.values(), arena)
    if ambiguous:
        logger.warning("leaderboard names shared by several catalog repos (left unscored): %s",
                       ", ".join(ambiguous))
    return {mid: by_repo[repo] for mid, repo in repo_of.items() if repo in by_repo}


def _digest(
    models: tuple[ModelRef, ...],
    pricing: dict[str, ModelPricing],
    health: dict[str, str],
    credit: CreditGuardSnapshot,
    observed_at: datetime,
    sources: dict[str, SnapshotProvenance],
    *,
    funded: FundedGuardSnapshot | None = None,
    scores: dict[str, ModelScores] | None = None,
    observed: dict[str, ObservedModel] | None = None,
) -> str:
    """SHA-256 over the COMPLETE canonical RuntimeSnapshot (FR-004, #5): every input
    that can change a decision — models, pricing, health, the FULL credit-guard
    observation, the snapshot ``observed_at``, each component's full provenance
    (source + observation time + age, since freshness gates eligibility per FR-007),
    and (spec 027) every score's four ``ArenaScore`` fields per track, the observed
    context/feature flags, and the FULL funded guard (``None`` when unavailable).
    Two snapshots taken at different times are DIFFERENT snapshots (distinct
    ``observed_at``) → distinct digests, which is correct; ``select`` determinism
    (SC-001) is over a FIXED snapshot, not across time."""
    scores = scores or {}
    observed = observed or {}
    payload = {
        "observed_at": observed_at.isoformat(),
        "models": sorted(
            [m.backend, m.serving_endpoint, m.model_id, m.model_family, m.vendor] for m in models
        ),
        "pricing": {
            k: [pricing[k].input_usd_per_token, pricing[k].output_usd_per_token]
            for k in sorted(pricing)
        },
        "health": {k: health[k] for k in sorted(health)},
        "credit": {
            "balance": credit.balance, "spend": credit.spend, "max_budget": credit.max_budget,
            "paid_opt_in": credit.paid_opt_in, "budget_fraction": credit.budget_fraction,
            "effective_cap": credit.effective_cap, "available_headroom": credit.available_headroom,
            "budget_reset_at": credit.budget_reset_at, "observed_at": credit.observed_at.isoformat(),
            "source": credit.source,
        },
        "sources": {
            k: [sources[k].source, sources[k].observed_at.isoformat(), sources[k].age_s]
            for k in sorted(sources)
        },
        "scores": {
            k: {
                track: None if (s := scores[k].for_track(track)) is None else _score_row(s)
                for track in ("reasoning", "coding")
            }
            for k in sorted(scores)
        },
        "observed": {k: _observed_row(observed[k]) for k in sorted(observed)},
        "funded": None if funded is None else {
            "monthly_usd": funded.monthly_usd, "spent_month_usd": funded.spent_month_usd,
            "spent_before_today_usd": funded.spent_before_today_usd,
            "outstanding_usd": funded.outstanding_usd, "org_balance_usd": funded.org_balance_usd,
            "effective_cap_usd": funded.effective_cap_usd, "available_usd": funded.available_usd,
            "epoch": funded.epoch, "observed_at": funded.observed_at.isoformat(),
            "source": funded.source,
        },
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def runtime_snapshot(
    *, now: datetime | None = None, lkg_store: LKGStore | None = None, refresh: bool = False
) -> RuntimeSnapshot:
    """Assemble the composite runtime snapshot across all backends + credit guard.

    The single networked/env-reading entry point; ``select`` consumes its result
    purely. ``now`` and ``lkg_store`` are injectable for deterministic tests.
    ``refresh=True`` fetches ``hf_catalog`` and ``leaderboard`` even when their
    stored copy is within :data:`HF_CATALOG_REFRESH_S` / :data:`LEADERBOARD_REFRESH_S`
    (preflight / reports), and retries a remote fetch that failed within
    :data:`FETCH_FAILURE_BACKOFF_S`.
    """
    observed_at = now or datetime.now(UTC)
    store = lkg_store or LKGStore()
    lkg = store.load()
    updates: dict[str, LKGEntry] = {}

    (d_refs, d_pricing), d_prov = _resolve_models_component(
        "catalog", _fetch_dartmouth, lkg, observed_at, updates, remote=True, refresh=refresh
    )
    (l_refs, l_pricing), l_prov = _resolve_models_component(
        "local", _fetch_local, lkg, observed_at, updates
    )
    credit, c_prov = _resolve_credit_component(lkg, observed_at, updates, refresh=refresh)
    (h_refs, h_pricing, h_observed), h_prov = _resolve_component(
        "hf_catalog", _fetch_huggingface, _hf_catalog_to_payload,
        lambda p, _at: _hf_catalog_from_payload(p), ([], {}, {}), lkg, observed_at, updates,
        reuse_within_s=None if refresh else HF_CATALOG_REFRESH_S, remote=True, refresh=refresh,
    )
    arena, lb_prov = _resolve_component(
        "leaderboard", _fetch_leaderboard, _arena_to_payload,
        lambda p, _at: _arena_from_payload(p), {}, lkg, observed_at, updates,
        reuse_within_s=None if refresh else LEADERBOARD_REFRESH_S, remote=True, refresh=refresh,
    )
    funded = _fetch_funded_guard(now=observed_at)  # no LKG: live or unavailable
    f_prov = SnapshotProvenance(
        source="live" if funded is not None else "unavailable", observed_at=observed_at, age_s=0.0
    )

    store.record(updates)  # persist only the components that succeeded live

    models = tuple(d_refs + l_refs + h_refs)
    pricing = {**d_pricing, **l_pricing, **h_pricing}
    health = {m.model_id: "ok" for m in models}  # advisory only (see RuntimeSnapshot.health)
    scores = _join_hf_scores(h_refs, arena)
    sources = {
        "catalog": d_prov, "local": l_prov, "credit": c_prov,
        "hf_catalog": h_prov, "leaderboard": lb_prov, "funded": f_prov,
    }
    digest = _digest(
        models, pricing, health, credit, observed_at, sources,
        funded=funded, scores=scores, observed=h_observed,
    )
    return RuntimeSnapshot(
        models=models, pricing=pricing, health=health, credit=credit,
        observed_at=observed_at, sources=sources, digest=digest,
        funded=funded, scores=scores, observed=h_observed,
    )
